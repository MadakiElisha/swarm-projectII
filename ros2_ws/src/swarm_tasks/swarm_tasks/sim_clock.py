"""Gazebo's clock for the swarm nodes, at a rate Python nodes can afford (simulation only).

Gazebo steps physics at 1 kHz and publishes its clock every step. When the PC can't keep up,
simulated time runs slower than the wall clock (real-time factor < 1): drones fly "10 m/s" in
simulated seconds but cover less ground per real second. Brains that kept wall-clock time then
expect too much (a rotating ring slot they can never catch, a car that outruns them).

In Gazebo mode the brains run on simulated time (use_sim_time). This node relays the bridged
Gazebo clock (/gz/clock, 1 kHz) to /clock at <= rate_hz, so each node gets 50 msgs/s, not 1000.
"""
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rosgraph_msgs.msg import Clock


class SimClock(Node):
    def __init__(self):
        super().__init__('sim_clock')
        self.declare_parameter('rate_hz', 50.0)
        self.period = 1.0 / float(self.get_parameter('rate_hz').value)
        self.last = 0.0
        self.pub = self.create_publisher(Clock, '/clock', 10)
        self.create_subscription(Clock, '/gz/clock', self.on_clock,
                                 QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
        self.n = 0

    def on_clock(self, m: Clock):
        now = time.monotonic()
        if now - self.last < self.period:
            return
        self.last = now
        self.pub.publish(m)
        if self.n == 0:
            self.get_logger().info('relaying Gazebo clock to /clock: swarm nodes run on simulated time')
        self.n += 1


def main(args=None):
    rclpy.init(args=args)
    node = SimClock()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
