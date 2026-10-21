"""Drive the Gazebo 'quarry' car along the scripted target path (simulation only).

target_mover publishes the ground-truth path on /swarm/target_track; this node
moves the car model so the drones' CAMERAS see a real moving vehicle. The
swarm itself never reads /swarm/target_track in Gazebo mode - it tracks the
car from detections, exactly as it would on hardware.
"""
import math
import subprocess
import time

import rclpy
from rclpy.node import Node

from swarm_common.config import load_fleet
from swarm_interfaces.msg import TargetTrack


class GzQuarry(Node):
    def __init__(self):
        super().__init__('gz_quarry')
        self.declare_parameter('world', 'swarm')
        self.declare_parameter('model', 'quarry')
        self.declare_parameter('rate_hz', 4.0)
        self.world = self.get_parameter('world').value
        self.model = self.get_parameter('model').value
        self.period = 1.0 / float(self.get_parameter('rate_hz').value)
        self.origin = load_fleet().swarm.origin
        self.last = 0.0
        self.create_subscription(TargetTrack, '/swarm/target_track', self.on_track, 10)
        self.get_logger().info(f'moving gazebo model {self.model!r} along /swarm/target_track')

    def on_track(self, m: TargetTrack):
        now = time.time()
        if now - self.last < self.period:
            return
        self.last = now
        x, y = self.origin.to_enu(m.lat, m.lon)
        yaw = math.atan2(m.vel_n, m.vel_e)
        req = (f'name: "{self.model}", position: {{x: {x:.2f}, y: {y:.2f}, z: 0.8}}, '
               f'orientation: {{z: {math.sin(yaw / 2):.4f}, w: {math.cos(yaw / 2):.4f}}}')
        try:
            subprocess.Popen(['gz', 'service', '-s', f'/world/{self.world}/set_pose', '--reqtype',
                              'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean', '--timeout', '300',
                              '--req', req], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            self.get_logger().error('gz CLI not found', throttle_duration_sec=30)


def main(args=None):
    rclpy.init(args=args)
    node = GzQuarry()
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
