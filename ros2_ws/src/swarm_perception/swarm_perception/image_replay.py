"""Simulated camera: republishes JPEGs from a directory as CompressedImage.

header.frame_id carries the drone label; stands in for a real/Gazebo camera.
"""
import glob
import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage

DEFAULT_DIR = '~/swarm-projectII/swarm-project/vision/test_images'


class ImageReplay(Node):
    def __init__(self):
        super().__init__('image_replay')
        self.declare_parameter('drone_label', 'D5')
        self.declare_parameter('period_s', 4.0)
        self.declare_parameter('image_dir', DEFAULT_DIR)
        self.label = self.get_parameter('drone_label').value
        d = os.path.expanduser(self.get_parameter('image_dir').value)
        self.paths = sorted(
            glob.glob(os.path.join(d, '*.jpg')) + glob.glob(os.path.join(d, '*.png'))
        )
        self.idx = 0
        self.pub = self.create_publisher(CompressedImage, '/swarm/camera/compressed', 10)
        self.timer = self.create_timer(self.get_parameter('period_s').value, self.tick)
        self.get_logger().info(
            f'Image replay camera for {self.label}: {len(self.paths)} image(s) from {d}')

    def tick(self):
        if not self.paths:
            self.get_logger().warning('no images found in image_dir')
            return
        path = self.paths[self.idx % len(self.paths)]
        self.idx += 1
        with open(path, 'rb') as f:
            data = f.read()
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.label
        msg.format = 'jpeg'
        msg.data = data
        self.pub.publish(msg)
        self.get_logger().info(f'camera {self.label}: frame published ({os.path.basename(path)})')


def main(args=None):
    rclpy.init(args=args)
    node = ImageReplay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
