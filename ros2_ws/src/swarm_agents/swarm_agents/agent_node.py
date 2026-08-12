"""Per-drone mini-agent: builds belief from the bus, acts on its own."""
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
LATCH = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)


from swarm_interfaces.msg import (
    DroneTelemetry, TaskAssignment, TaskRelinquish, DroneCommand,
)
from swarm_agents.agent_core import Belief, DroneAgent, Relinquish, ReturnHome


class AgentNode(Node):
    def __init__(self):
        super().__init__('agent_node')
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('reserve_pct', 30.0)
        self.declare_parameter('critical_pct', 15.0)
        self.declare_parameter('home_lat', 6.5244)
        self.declare_parameter('home_lon', 3.3792)
        self.label = self.get_parameter('drone_label').value
        self.home_lat = self.get_parameter('home_lat').value
        self.home_lon = self.get_parameter('home_lon').value
        self.agent = DroneAgent(
            self.get_parameter('reserve_pct').value,
            self.get_parameter('critical_pct').value)
        self.telemetry = {}
        self.current_task = None
        self._fired = set()
        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telemetry, 10)
        self.create_subscription(TaskAssignment, '/swarm/task_assignments', self.on_assignment, LATCH)
        self.relinquish_pub = self.create_publisher(TaskRelinquish, '/swarm/task_relinquish', 10)
        self.cmd_pub = self.create_publisher(DroneCommand, '/swarm/commands', 10)
        self.create_timer(1.0, self.step)
        self.get_logger().info(f'{self.label}: agent online (reserve={self.agent.reserve_pct}%)')

    def on_telemetry(self, m):
        self.telemetry[m.label] = m

    def on_assignment(self, m):
        age = time.time() - (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
        if age > 60.0:
            return
        age = time.time() - (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
        if age > 60.0:
            return
        winner = getattr(m, 'winner_label', None) or getattr(m, 'assigned_to', None)
        if winner == self.label:
            self.current_task = getattr(m, 'task_id', None)

    def _dist_home(self, lat, lon):
        dy = (lat - self.home_lat) * 111320.0
        dx = (lon - self.home_lon) * 111320.0 * math.cos(math.radians(lat))
        return math.hypot(dx, dy)

    def _send_cmd(self, command, once=False, key=None):
        k = key or command
        if once and k in self._fired:
            return
        self._fired.add(k)
        cmd = DroneCommand()
        cmd.label = self.label
        cmd.command = command
        self.cmd_pub.publish(cmd)
        self.get_logger().error(f'{self.label}: autonomous {command}')

    def step(self):
        me = self.telemetry.get(self.label)
        if me is None:
            return
        belief = Belief(
            label=self.label,
            battery_pct=me.battery_pct,
            alt=me.alt,
            current_task=self.current_task,
            neighbor_count=len(self.telemetry) - 1,
            distance_home_m=self._dist_home(me.lat, me.lon))
        self._dbg = getattr(self, '_dbg', 0) + 1
        if self._dbg % 10 == 0:
            self.get_logger().info(
                f'{self.label}: dbg batt={belief.battery_pct:.0f}% task={belief.current_task} '
                f'dist_home={belief.distance_home_m / 1000.0:.2f}km')
        self._dbg = getattr(self, '_dbg', 0) + 1
        if self._dbg % 10 == 0:
            self.get_logger().info(
                f'{self.label}: dbg batt={belief.battery_pct:.0f}% task={belief.current_task} '
                f'dist_home={belief.distance_home_m / 1000.0:.2f}km')
        for intent in self.agent.step(belief):
            if isinstance(intent, Relinquish):
                msg = TaskRelinquish()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.task_id = intent.task_id
                msg.label = self.label
                msg.reason = intent.reason
                self.relinquish_pub.publish(msg)
                self.get_logger().warn(
                              f'{self.label}: relinquishing {intent.task_id} - {intent.reason}; '
                    f'aborting, returning home')
                self.current_task = None
                self._send_cmd('RTL')          # relinquish = abort + return
            elif isinstance(intent, ReturnHome):
                _now = time.time()
                if _now - getattr(self, '_last_rtl', 0) > 20:
                    self._last_rtl = _now
                    self._send_cmd('RTL')


def main(args=None):
    rclpy.init(args=args)
    node = AgentNode()
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
