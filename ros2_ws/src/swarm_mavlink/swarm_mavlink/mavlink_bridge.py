"""MAVLink<->ROS2 bridge: the per-drone nerve center (v7, consolidation pass).

One instance per drone. Responsibilities:
  * publish validated telemetry at 5 Hz from the VehicleAdapter backend
  * intake operator commands (/swarm/commands) and the task flow
    (/swarm/task_requests, /swarm/task_assignments)
  * execute missions: single-point fly-to, and synchronized ring missions
    (SWARM-/INTERCEPT-) with rotating slots, lead-pursuit cutters,
    battery GO/NO-GO and auto-release RTL
  * self-report mission state on /swarm/mission_status
    (ENROUTE / ON_STATION / RELEASED) via a radial band test

BEHAVIOR IS FROZEN: this is a readability rewrite of v6. All timings,
thresholds, log lines and topic semantics are unchanged; the regression
gate (C1-C6) is the equivalence proof.
"""
import math
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy

from swarm_interfaces.msg import (
    DroneTelemetry, DroneCommand, TaskRequest, TaskAssignment,
    MissionStatus, TargetTrack,
)
from swarm_common.validation import (
    validate_lat, validate_lon, validate_battery, validate_label, ValidationError,
)
from swarm_backends import MavlinkBackend, CommandRequest

# Latched QoS: late-joining bridges must still see stored assignments.
LATCH = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)

# --- mission geometry & timing (frozen from v6) ---
M_PER_DEG = 111320.0            # metres per degree of latitude
ON_STATION_BAND_M = 120.0       # radial band that counts as ON_STATION
DEFAULT_RING_RADIUS_M = 300.0   # ring radius when the message omits it
RING_PERIOD_S = 240.0           # one full rotation of the ring slots
RING_STEP_S = 4.0               # ring re-centre cadence
BASE_ALT_M = 30.0               # takeoff / fly-to altitude
ALT_STAGGER_M = 6.0             # per-drone altitude separation in the ring
PRE_LIFT_LEAD_S = 8.0           # lift this many seconds before execute_at
HOLD_AFTER_ARRIVE_S = 180.0     # hold the ring this long after arrive_by
STALE_ASSIGNMENT_S = 60.0       # ignore assignments older than this
TRACK_FRESH_S = 6.0             # quarry track freshness window
LEAD_TIME_S = 6.0               # cutter lead = quarry velocity * this
NOGO_BATTERY_PCT = 20.0         # below this: refuse the synchronized lift
TAKEOFF_SETTLE_S = 2.0          # pause between the two takeoff calls
GOTO_SETTLE_S = 6.0             # pause after takeoff, before goto


def _first(m, *names):
    """Tolerant field accessor: return the first non-None named attribute."""
    for n in names:
        v = getattr(m, n, None)
        if v is not None:
            return v
    return None


class MavlinkBridge(Node):
    def __init__(self):
        super().__init__('mavlink_bridge')
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('mavlink_url', 'tcp:127.0.0.1:5770')
        self.label = self.get_parameter('drone_label').value
        self.url = self.get_parameter('mavlink_url').value

        # --- publishers ---
        self.publisher_ = self.create_publisher(DroneTelemetry, '/swarm/telemetry', 10)
        self.status_pub = self.create_publisher(MissionStatus, '/swarm/mission_status', 10)

        # --- mission state ---
        self._slot = None          # (task_id, centre_lat, centre_lon, R) while in a ring
        self._my = None            # own last known (lat, lon)
        self.track = None          # last quarry track (lat, lon, vel_n, vel_e, t)
        self.tasks = {}            # task_id -> (lat, lon) from task requests

        # --- subscriptions ---
        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_own_telem, 10)
        self.create_subscription(TargetTrack, '/swarm/target_track', self.on_track, 10)
        self.create_subscription(DroneCommand, '/swarm/commands', self.on_cmd, 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_task_req, 10)
        self.create_subscription(TaskAssignment, '/swarm/task_assignments', self.on_assignment, LATCH)

        # --- timers & backend ---
        self.create_timer(1.0, self.status_tick)
        self.get_logger().info(f'MAVLink bridge starting for {self.label} on {self.url}')
        self.backend = MavlinkBackend(self.url)
        threading.Thread(target=self._telemetry_loop, daemon=True).start()
        self.timer = self.create_timer(0.2, self.publish_state)

    # ------------------------------------------------------------------
    # inbound: own telemetry & quarry track
    # ------------------------------------------------------------------
    def on_own_telem(self, m):
        if m.label == self.label:
            self._my = (m.lat, m.lon)

    def on_track(self, m):
        self.track = (m.lat, m.lon, m.vel_n, m.vel_e, time.time())

    # ------------------------------------------------------------------
    # inbound: task flow & operator commands
    # ------------------------------------------------------------------
    def on_task_req(self, m):
        try:
            self.backend.abort.set()   # preempt any in-flight mission
            if getattr(m, 'execute_at', 0.0) > 0:
                threading.Thread(target=self._sync_mission, args=(m,), daemon=True).start()
                return
            self.backend.abort.clear()
            tid = _first(m, 'task_id', 'id')
            lat = _first(m, 'lat', 'latitude')
            lon = _first(m, 'lon', 'longitude')
            if tid is not None and lat is not None and lon is not None:
                self.tasks[tid] = (float(lat), float(lon))
        except Exception as e:
            self.get_logger().warning(f'{self.label}: task req parse error: {e}')

    def on_assignment(self, m):
        try:
            age = time.time() - (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
            if age > STALE_ASSIGNMENT_S:
                self.get_logger().info(f'{self.label}: ignoring stale assignment')
                return
            winner = _first(m, 'winner_label', 'assigned_to', 'winner', 'label')
            if winner != self.label:
                return
            self.backend.abort.set()   # preempt any in-flight mission
            tid = _first(m, 'task_id', 'id')
            if float(getattr(m, 'execute_at', 0.0)) > 0:
                threading.Thread(target=self._sync_mission, args=(m,), daemon=True).start()
                return
            pos = self.tasks.get(tid)
            if pos is None:
                self.get_logger().warning(f'{self.label}: no coords for {tid}')
                return
            threading.Thread(target=self._fly_to, args=(tid, pos), daemon=True).start()
        except Exception as e:
            self.get_logger().error(f'{self.label}: on_assignment: {e}')

    def on_cmd(self, m):
        try:
            label = _first(m, 'label', 'drone_label')
            if label != self.label:
                return
            cmd = str(_first(m, 'command', 'cmd', '')).lower()
            threading.Thread(target=self._execute, args=(cmd,), daemon=True).start()
        except Exception as e:
            self.get_logger().warning(f'{self.label}: cmd parse error: {e}')

    def _execute(self, cmd):
        status = self.backend.execute(CommandRequest(cmd))
        if status.accepted:
            self.get_logger().info(f'{self.label}: sent {cmd}')
        else:
            self.get_logger().warning(f'{self.label}: {cmd} denied: {status.reason}')

    # ------------------------------------------------------------------
    # mission execution
    # ------------------------------------------------------------------
    def _sync_mission(self, m):
        """Synchronized ring mission: lift together, rotate slots, pursue if
        INTERCEPT-, hold, then auto-release to RTL."""
        try:
            tid = _first(m, 'task_id', 'id')
            exec_at = float(getattr(m, 'execute_at', 0.0))
            ox = float(getattr(m, 'offset_x', 0.0))
            oy = float(getattr(m, 'offset_y', 0.0))
            R = float(getattr(m, 'orbit_radius', 0.0)) or DEFAULT_RING_RADIUS_M
            arrive_by = float(getattr(m, 'arrive_by', 0.0))
            pos = self.tasks.get(tid)
            if pos is None:
                self.get_logger().error(f'{self.label}: SWARM {tid} no target coords - aborting')
                return
            lat, lon = pos
            self.get_logger().info(
                f'{self.label}: SWARM {tid} plan center={lat:.5f},{lon:.5f} '
                f'offset=({ox:.0f},{oy:.0f}) R={R:.0f}')
            delay = exec_at - time.time() - PRE_LIFT_LEAD_S
            if delay > 0:
                self.get_logger().info(f'{self.label}: SWARM {tid} lift in {delay:.0f}s')
                time.sleep(delay)
            self.backend.abort.clear()   # this mission now owns the vehicle
            batt = getattr(self.backend, '_battery', 100.0)  # frozen private accessor
            if batt < NOGO_BATTERY_PCT:
                self.get_logger().error(f'{self.label}: SWARM {tid} NO-GO battery {batt:.0f}%')
                return
            alt = BASE_ALT_M + ALT_STAGGER_M * int(self.label[1:])
            self.get_logger().warn(f'{self.label}: SWARM {tid} LIFT (alt {alt:.0f}m)')
            self.backend.execute(CommandRequest('takeoff', {'alt': BASE_ALT_M}))
            time.sleep(TAKEOFF_SETTLE_S)
            self.backend.execute(CommandRequest('takeoff', {'alt': BASE_ALT_M}))  # intentional retry
            bearing0 = math.atan2(ox, oy)
            hold_until = (arrive_by or time.time() + 60.0) + HOLD_AFTER_ARRIVE_S
            omega = 2 * math.pi / RING_PERIOD_S
            t0 = time.time()
            pursue = tid.startswith('INTERCEPT-')
            cutter = (int(self.label[1:]) % 5) in (1, 2)
            while time.time() < hold_until and not self.backend.abort.is_set():
                clat, clon, lead_n, lead_e = lat, lon, 0.0, 0.0
                if pursue and self.track and (time.time() - self.track[4]) < TRACK_FRESH_S:
                    clat, clon = self.track[0], self.track[1]
                    if cutter:
                        lead_n, lead_e = self.track[2] * LEAD_TIME_S, self.track[3] * LEAD_TIME_S
                cf = max(0.2, math.cos(math.radians(clat)))
                th = bearing0 + omega * (time.time() - t0)
                alat = clat + (R * math.sin(th) + lead_n) / M_PER_DEG
                alon = clon + (R * math.cos(th) + lead_e) / (M_PER_DEG * cf)
                self._slot = (tid, clat, clon, R)
                self.backend.execute(CommandRequest('goto', {'lat': alat, 'lon': alon, 'alt': alt}))
                time.sleep(RING_STEP_S)
            self.get_logger().warn(f'{self.label}: SWARM {tid} released - RTL')
            rel = MissionStatus()
            rel.header.stamp = self.get_clock().now().to_msg()
            rel.label = self.label
            rel.task_id = tid
            rel.phase = 'RELEASED'
            self.status_pub.publish(rel)
            self.backend.execute(CommandRequest('rtl'))
        except Exception as e:
            self.get_logger().error(f'{self.label}: _sync_mission failed: {e}')

    def _fly_to(self, task_id, pos):
        """Single-point mission: takeoff, then fly to the task coordinates."""
        self.backend.abort.clear()
        lat, lon = pos
        self.get_logger().info(f'{self.label}: flying to {task_id} @ {lat:.5f},{lon:.5f}')
        status = self.backend.execute(CommandRequest('takeoff', {'alt': BASE_ALT_M}))
        if not status.accepted:
            self.get_logger().warning(f'{self.label}: takeoff denied: {status.reason}')
            return
        time.sleep(GOTO_SETTLE_S)
        status = self.backend.execute(CommandRequest('goto', {'lat': lat, 'lon': lon, 'alt': BASE_ALT_M}))
        if status.accepted:
            self.get_logger().info(f'{self.label}: enroute to {task_id}')
        else:
            self.get_logger().warning(f'{self.label}: goto denied: {status.reason}')

    # ------------------------------------------------------------------
    # mission state self-report (1 Hz while in a ring)
    # ------------------------------------------------------------------
    def status_tick(self):
        if not self._slot or not self._my:
            return
        tid, clat, clon, R = self._slot
        dr = math.hypot((self._my[0] - clat) * M_PER_DEG,
                        (self._my[1] - clon) * M_PER_DEG * math.cos(math.radians(clat)))
        d = abs(dr - R)
        m = MissionStatus()
        m.header.stamp = self.get_clock().now().to_msg()
        m.label = self.label
        m.task_id = tid
        m.phase = 'ON_STATION' if d < ON_STATION_BAND_M else 'ENROUTE'
        m.dist_to_slot_m = float(d)
        self.status_pub.publish(m)

    # ------------------------------------------------------------------
    # telemetry out (5 Hz, validated)
    # ------------------------------------------------------------------
    def _telemetry_loop(self):
        for frame in self.backend.telemetry():
            self._last_frame = frame

    def publish_state(self):
        frame = getattr(self, '_last_frame', None)
        if frame is None or frame.battery_pct < 0:
            return
        try:
            msg = DroneTelemetry()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.label = validate_label(self.label)
            msg.lat = validate_lat(frame.lat)
            msg.lon = validate_lon(frame.lon)
            msg.alt = float(frame.alt)
            msg.roll = float(frame.roll)
            msg.pitch = float(frame.pitch)
            msg.yaw = float(frame.yaw)
            msg.wind_speed = float(frame.wind_speed)
            msg.wind_dir = float(frame.wind_dir)
            msg.battery_pct = validate_battery(frame.battery_pct)
        except ValidationError as e:
            self.get_logger().error(f'{self.label}: telemetry failed validation: {e}')
            return
        self.publisher_.publish(msg)

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def destroy_node(self):
        self.backend.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MavlinkBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
