"""MAVLink<->ROS2 bridge v6: uses VehicleAdapter for drone-agnostic operation."""
import threading
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


class MavlinkBridge(Node):
    def __init__(self):
        super().__init__('mavlink_bridge')
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('mavlink_url', 'tcp:127.0.0.1:5770')
        self.label = self.get_parameter('drone_label').value
        self.url = self.get_parameter('mavlink_url').value
        self.publisher_ = self.create_publisher(DroneTelemetry, '/swarm/telemetry', 10)
        self.create_subscription(DroneCommand, '/swarm/commands', self.on_cmd, 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_task_req, 10)
        self.create_subscription(TaskAssignment, '/swarm/task_assignments', self.on_assignment, LATCH)
        self.tasks = {}
        self._stop = False
        self.get_logger().info(f'MAVLink bridge starting for {self.label} on {self.url}')
        
        # The adapter
        self.backend = MavlinkBackend(self.url)
        
        threading.Thread(target=self._telemetry_loop, daemon=True).start()
        self.timer = self.create_timer(1.0, self.publish_state)

    def on_task_req(self, m):
        try:
            self.backend.abort.clear()
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
            if age > 60.0:
                self.get_logger().info(f'{self.label}: ignoring stale assignment'); return
            age = time.time() - (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
            if age > 60.0:
                self.get_logger().info(f'{self.label}: ignoring stale assignment'); return
            winner = _first(m, 'winner_label', 'assigned_to', 'winner', 'label')
            if winner != self.label:
                return
            self.backend.abort.clear()
            self.backend.abort.clear()
            tid = _first(m, 'task_id', 'id')
            pos = self.tasks.get(tid)
            if pos is None:
                self.get_logger().warning(f'{self.label}: won {tid} but no coords yet')
                return
            threading.Thread(target=self._fly_to, args=(tid, pos), daemon=True).start()
        except Exception as e:
            self.get_logger().warning(f'{self.label}: assignment parse error: {e}')

    def _fly_to(self, task_id, pos):
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
