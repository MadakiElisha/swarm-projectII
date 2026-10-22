"""vehicle_manager: the per-drone vehicle authority (one process per drone).

The ONLY node that talks to the flight controller. It runs the pure
swarm_common.vehicle_fsm.VehicleFSM, so failsafes and operator overrides
cannot be bypassed by the mission layer:

  /swarm/<label>/setpoint     (Setpoint, from this drone's brain)   -> FSM
  /swarm/commands             (DroneCommand, operator)              -> FSM (priority)
  FSM actions                 -> VehicleAdapter (MAVLink or sim)
  /swarm/<label>/vehicle_state (VehicleState, 10 Hz)                -> brain
  /swarm/telemetry            (DroneTelemetry, 5 Hz)                -> GCS

If the brain crashes, setpoints stop: the FSM holds position, then returns
home. If this node crashes, the autopilot's own GCS/RC failsafes apply.
"""
import math
from concurrent.futures import ThreadPoolExecutor

import rclpy
from rclpy.node import Node

from swarm_common.config import load_fleet
from swarm_common.motion import altitude_layer
from swarm_common.vehicle_fsm import FsmCfg, Setpoint, VehicleFSM, VehicleObs
from swarm_interfaces.msg import DroneCommand, DroneTelemetry
from swarm_interfaces.msg import Setpoint as SetpointMsg
from swarm_interfaces.msg import VehicleState

ALT_GAIN = 0.8          # vertical speed per metre of altitude error
MAX_VZ = 4.0             # m/s (autopilot allows WPNAV_SPEED_UP = 5 m/s)


class VehicleManager(Node):
    def __init__(self):
        super().__init__('vehicle_manager')
        self.declare_parameter('drone_id', 1)
        self.declare_parameter('backend', 'mavlink')        # mavlink | sim
        self.declare_parameter('mavlink_url', '')           # '' -> from fleet.yaml
        self.declare_parameter('fleet_file', '')
        self.declare_parameter('rate_hz', 10.0)
        self.declare_parameter('stagger_rtl_alt', True)

        self.id = int(self.get_parameter('drone_id').value)
        self.fleet = load_fleet(self.get_parameter('fleet_file').value or None)
        self.spec = self.fleet.by_id(self.id)
        self.label = self.spec.label
        sw = self.fleet.swarm
        self.origin = sw.origin
        self.backend = self._make_backend(self.get_parameter('backend').value)
        hx, hy = self.fleet.home_enu(self.id)
        fence_c = (0.0, 0.0)
        self.fsm = VehicleFSM(FsmCfg(
            critical_pct=sw.energy.critical_pct, fence_radius_m=sw.geofence.radius_m,
            fence_max_alt_m=sw.geofence.max_alt_m, fence_center=fence_c,
            brain_stale_s=sw.brain_stale_s, brain_dead_s=sw.brain_dead_s))
        self.home = (hx, hy)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f'{self.label}-cmd')
        self._pending = None
        self._obs = None
        self._rtl_alt_set = not self.get_parameter('stagger_rtl_alt').value
        self._unknown_batt_warned = False

        self.state_pub = self.create_publisher(VehicleState, f'/swarm/{self.label}/vehicle_state', 10)
        self.telem_pub = self.create_publisher(DroneTelemetry, '/swarm/telemetry', 10)
        self.create_subscription(SetpointMsg, f'/swarm/{self.label}/setpoint', self.on_setpoint, 10)
        self.create_subscription(DroneCommand, '/swarm/commands', self.on_command, 10)
        self.create_timer(1.0 / float(self.get_parameter('rate_hz').value), self.tick)
        self.create_timer(0.2, self.publish_telemetry)
        self.get_logger().info(f'{self.label}: vehicle manager up '
                               f'(backend={self.get_parameter("backend").value})')

    # ------------------------------------------------------------ backend
    def _make_backend(self, kind):
        if kind == 'sim':
            from swarm_backends.sim_backend import SimBackend
            return SimBackend(self.spec.home_lat, self.spec.home_lon, self.origin,
                              rtl_alt_m=altitude_layer(self.id, self.fleet.swarm.motion))
        if kind == 'mavlink':
            from swarm_backends.mavlink_backend import MavlinkBackend
            url = self.get_parameter('mavlink_url').value or self.spec.mavlink_url
            if not url:
                raise RuntimeError(f'{self.label}: no mavlink_url (param or fleet.yaml)')
            return MavlinkBackend(url)
        raise RuntimeError(f'unknown backend {kind!r}')

    # ------------------------------------------------------------- inputs
    def on_setpoint(self, m: SetpointMsg):
        now = self._now()
        self.fsm.on_setpoint(Setpoint(now, m.kind, m.vx, m.vy, m.vz, m.x, m.y, m.alt), now)

    def on_command(self, m: DroneCommand):
        if m.label not in (self.label, 'ALL', '*'):
            return
        self.get_logger().warn(f'{self.label}: operator command {m.command}')
        acts = self.fsm.on_operator(m.command, self._now(), self._obs)
        self._execute(acts)
        self._drain_events()

    # --------------------------------------------------------------- loop
    def tick(self):
        snap = self.backend.snapshot()
        now = self._now()
        for t in self.backend.status_texts():
            self.get_logger().info(f'[{self.label} FC] {t}')
        if not snap.connected:
            self._publish_state(snap, connected=False)
            return
        if not self._rtl_alt_set:
            self._rtl_alt_set = True
            alt_cm = altitude_layer(self.id, self.fleet.swarm.motion) * 100.0
            self.pool.submit(self._set_rtl_alt, alt_cm)
        batt = snap.battery_pct
        if batt < 0:
            if not self._unknown_batt_warned:
                self.get_logger().warn(f'{self.label}: battery unknown - assuming 50%')
                self._unknown_batt_warned = True
            batt = 50.0
        x, y = self.origin.to_enu(snap.lat, snap.lon)
        self._obs = VehicleObs(now, x, y, snap.alt, batt, snap.armed, snap.mode)
        self._execute(self.fsm.tick(self._obs, now))
        self._drain_events()
        self._publish_state(snap, connected=True, x=x, y=y, batt=batt)

    def _execute(self, actions):
        for a in actions:
            k, p = a.kind, a.params
            if k == 'velocity':
                alt = self._obs.alt if self._obs else 0.0
                vz_up = max(-MAX_VZ, min(MAX_VZ, ALT_GAIN * (p.get('alt', alt) - alt)))
                self.backend.velocity(p['vy'], p['vx'], -vz_up)        # ENU -> NED
            elif k == 'position':
                lat, lon = self.origin.to_latlon(p['x'], p['y'])
                self.backend.goto(lat, lon, p['alt'])
            elif k == 'hold':
                self.backend.hold()
            elif k in ('takeoff', 'rtl', 'land'):
                self._submit(k, p)

    def _submit(self, kind, params):
        # urgent mode changes may not wait behind a slow takeoff
        if self._pending is not None and not self._pending.done() and kind == 'takeoff':
            return
        fn = {'takeoff': lambda: self.backend.takeoff(params.get('alt', 30.0)),
              'rtl': self.backend.rtl, 'land': self.backend.land}[kind]

        def run():
            st = fn()
            if st.accepted:
                self.get_logger().info(f'{self.label}: {kind} accepted')
            else:
                self.get_logger().error(f'{self.label}: {kind} FAILED: {st.reason}')
        self._pending = self.pool.submit(run)

    def _set_rtl_alt(self, alt_cm):
        st = self.backend.set_param('RTL_ALT', alt_cm)
        self.get_logger().info(f'{self.label}: RTL_ALT={alt_cm:.0f} cm '
                               f'{"set" if st.accepted else "not set: " + st.reason}')

    def _drain_events(self):
        for e in self.fsm.events:
            self.get_logger().warn(f'{self.label} FSM: {e}')
        self.fsm.events.clear()

    # ------------------------------------------------------------ outputs
    def _publish_state(self, snap, connected, x=0.0, y=0.0, batt=0.0):
        m = VehicleState()
        m.header.stamp = self.get_clock().now().to_msg()
        m.drone_id, m.label, m.connected = self.id, self.label, bool(connected)
        m.lat, m.lon, m.x, m.y, m.alt = snap.lat, snap.lon, x, y, snap.alt
        m.vx, m.vy = snap.ve, snap.vn
        m.battery_pct = float(batt)
        m.armed, m.mode = bool(snap.armed), str(snap.mode)
        m.fsm_state, m.latch = self.fsm.state, self.fsm.latch or ''
        m.roll, m.pitch = float(snap.roll), float(-snap.pitch)
        m.yaw_enu = float(math.pi / 2 - snap.yaw)
        m.wind_speed = float(snap.wind_speed)
        self.state_pub.publish(m)

    def publish_telemetry(self):
        snap = self.backend.snapshot()
        if not snap.connected:
            return
        m = DroneTelemetry()
        m.header.stamp = self.get_clock().now().to_msg()
        m.label = self.label
        m.lat, m.lon, m.alt = snap.lat, snap.lon, snap.alt
        m.battery_pct = max(0.0, min(100.0, snap.battery_pct)) if snap.battery_pct >= 0 else 50.0
        m.roll, m.pitch, m.yaw = float(snap.roll), float(snap.pitch), float(snap.yaw)
        m.wind_speed, m.wind_dir = float(snap.wind_speed), float(snap.wind_dir)
        self.telem_pub.publish(m)

    def _now(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9

    def destroy_node(self):
        self.pool.shutdown(wait=False)
        self.backend.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VehicleManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
