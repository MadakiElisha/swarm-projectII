"""Resident fleeing-target service: auto-starts on INTERCEPT- task requests."""
import math
import threading
import time

import rclpy
from rclpy.node import Node
from swarm_interfaces.msg import TargetTrack, TaskRequest


class TargetMover(Node):
    def __init__(self):
        super().__init__('target_mover')
        self.declare_parameter('speed', 8.0)
        self.declare_parameter('bearing', 75.0)
        self.declare_parameter('duration', 150.0)
        self.pub = self.create_publisher(TargetTrack, '/swarm/target_track', 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_request, 10)
        self.thread = None
        self.stop_flag = threading.Event()
        self.get_logger().info('target mover resident - arms on INTERCEPT- requests')

    def on_request(self, msg):
        if not msg.task_id.startswith('INTERCEPT-'):
            return
        self.stop_flag.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.stop_flag = threading.Event()
        self.thread = threading.Thread(target=self.run, args=(msg.lat, msg.lon), daemon=True)
        self.thread.start()
        self.get_logger().warn(f'MOVER STARTED for {msg.task_id} at {msg.lat:.5f},{msg.lon:.5f}')

    def run(self, lat0, lon0):
        speed = self.get_parameter('speed').value
        bearing = self.get_parameter('bearing').value
        duration = self.get_parameter('duration').value
        vn = speed * math.cos(math.radians(bearing))
        ve = speed * math.sin(math.radians(bearing))
        t0 = time.time()
        while not self.stop_flag.is_set() and time.time() - t0 < duration:
            dt = time.time() - t0
            m = TargetTrack()
            m.header.stamp = self.get_clock().now().to_msg()
            m.lat = lat0 + (vn * dt) / 111320.0
            m.lon = lon0 + (ve * dt) / (111320.0 * math.cos(math.radians(lat0)))
            m.vel_n, m.vel_e = vn, ve
            m.source = 'auto_mover'
            self.pub.publish(m)
            time.sleep(0.5)
        self.get_logger().info('mover finished - track stale, swarm holds last fix')


def main(args=None):
    rclpy.init(args=args)
    node = TargetMover()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
