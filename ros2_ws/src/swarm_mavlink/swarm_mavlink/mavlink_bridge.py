"""MAVLink<->ROS2 bridge v6: uses VehicleAdapter for drone-agnostic operation."""
import threading
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
LATCH = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)


from swarm_interfaces.msg import (
    DroneTelemetry, DroneCommand, TaskRequest, TaskAssignment,
)
from swarm_common.validation import (
    validate_lat, validate_lon, validate_battery, validate_label, ValidationError,
)
from swarm_backends import MavlinkBackend, CommandRequest


def _first(m, *names):
    for n in names:
        v = getattr(m, n, None)
        if v is not None:
            return v
    return None


from swarm_interfaces.msg import MissionStatus
from swarm_interfaces.msg import TargetTrack


class MavlinkBridge(Node):
    def __init__(self):
        super().__init__('mavlink_bridge')
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('mavlink_url', 'tcp:127.0.0.1:5770')
        self.label = self.get_parameter('drone_label').value
        self.url = self.get_parameter('mavlink_url').value
        self.publisher_ = self.create_publisher(DroneTelemetry, '/swarm/telemetry', 10)
        self.status_pub = self.create_publisher(MissionStatus, '/swarm/mission_status', 10)
        self._slot = None
        self._my = None
        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_own_telem, 10)
        self.create_timer(1.0, self.status_tick)
        self.track = None
        self.create_subscription(TargetTrack, '/swarm/target_track', self.on_track, 10)
        self.create_subscription(DroneCommand, '/swarm/commands', self.on_cmd, 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_task_req, 10)
        self.create_subscription(TaskAssignment, '/swarm/task_assignments', self.on_assignment, LATCH)
        self.tasks = {}
        self._stop = False
        self.get_logger().info(f'MAVLink bridge starting for {self.label} on {self.url}')
        
        # The adapter
        self.backend = MavlinkBackend(self.url)
        
        threading.Thread(target=self._telemetry_loop, daemon=True).start()
        self.timer = self.create_timer(0.2, self.publish_state)

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

    def on_track(self, m):
        self.track = (m.lat, m.lon, m.vel_n, m.vel_e, time.time())

    def on_own_telem(self, m):
        if m.label == self.label:
            self._my = (m.lat, m.lon)

    def status_tick(self):
        if not self._slot or not self._my:
            return
        tid, clat, clon, R = self._slot
        dr = math.hypot((self._my[0] - clat) * 111320.0,
                        (self._my[1] - clon) * 111320.0 * math.cos(math.radians(clat)))
        d = abs(dr - R)
        m = MissionStatus()
        m.header.stamp = self.get_clock().now().to_msg()
        m.label = self.label
        m.task_id = tid
        m.phase = 'ON_STATION' if d < 120.0 else 'ENROUTE'
        m.dist_to_slot_m = float(d)
        self.status_pub.publish(m)

    def on_assignment(self, m):
        try:
            age = time.time() - (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
            if age > 60.0:
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

    def _sync_mission(self, m):
        try:
            tid = _first(m, 'task_id', 'id')
            exec_at = float(getattr(m, 'execute_at', 0.0))
            ox = float(getattr(m, 'offset_x', 0.0))
            oy = float(getattr(m, 'offset_y', 0.0))
            R = float(getattr(m, 'orbit_radius', 0.0)) or 300.0
            arrive_by = float(getattr(m, 'arrive_by', 0.0))
            pos = self.tasks.get(tid)
            if pos is None:
                self.get_logger().error(f'{self.label}: SWARM {tid} no target coords - aborting')
                return
            lat, lon = pos
            self.get_logger().info(
                f'{self.label}: SWARM {tid} plan center={lat:.5f},{lon:.5f} '
                f'offset=({ox:.0f},{oy:.0f}) R={R:.0f}')
            delay = exec_at - time.time() - 8.0
            if delay > 0:
                self.get_logger().info(f'{self.label}: SWARM {tid} lift in {delay:.0f}s')
                time.sleep(delay)
            self.backend.abort.clear()   # this mission now owns the vehicle
            batt = getattr(self.backend, '_battery', 100.0)
            if batt < 20.0:
                self.get_logger().error(f'{self.label}: SWARM {tid} NO-GO battery {batt:.0f}%')
                return
            alt = 30.0 + 6.0 * int(self.label[1:])
            self.get_logger().warn(f'{self.label}: SWARM {tid} LIFT (alt {alt:.0f}m)')
            self.backend.execute(CommandRequest('takeoff', {'alt': 30}))
            time.sleep(2)
            self.backend.execute(CommandRequest('takeoff', {'alt': 30}))
            bearing0 = math.atan2(ox, oy)
            hold_until = (arrive_by or time.time() + 60.0) + 180.0
            omega = 2 * math.pi / 240.0
            t0 = time.time()
            pursue = tid.startswith('INTERCEPT-')
            cutter = (int(self.label[1:]) % 5) in (1, 2)
            while time.time() < hold_until and not self.backend.abort.is_set():
                clat, clon, lead_n, lead_e = lat, lon, 0.0, 0.0
                if pursue and self.track and (time.time() - self.track[4]) < 6.0:
                    clat, clon = self.track[0], self.track[1]
                    if cutter:
                        lead_n, lead_e = self.track[2] * 6.0, self.track[3] * 6.0
                cf = max(0.2, math.cos(math.radians(clat)))
                th = bearing0 + omega * (time.time() - t0)
                alat = clat + (R * math.sin(th) + lead_n) / 111320.0
                alon = clon + (R * math.cos(th) + lead_e) / (111320.0 * cf)
                self._slot = (tid, clat, clon, R)
                self.backend.execute(CommandRequest('goto', {'lat': alat, 'lon': alon, 'alt': alt}))
                time.sleep(4.0)
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
        self.backend.abort.clear()
        lat, lon = pos
        self.get_logger().info(f'{self.label}: flying to {task_id} @ {lat:.5f},{lon:.5f}')
        status = self.backend.execute(CommandRequest('takeoff', {'alt': 30}))
        if not status.accepted:
            self.get_logger().warning(f'{self.label}: takeoff denied: {status.reason}')
            return
        time.sleep(6)
        status = self.backend.execute(CommandRequest('goto', {'lat': lat, 'lon': lon, 'alt': 30}))
        if status.accepted:
            self.get_logger().info(f'{self.label}: enroute to {task_id}')
        else:
            self.get_logger().warning(f'{self.label}: goto denied: {status.reason}')

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

    def destroy_node(self):
        self._stop = True
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
