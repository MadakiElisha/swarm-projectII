"""Per-drone camera simulator: cycles disaster scenes into a namespaced pipe.

Each instance owns /swarm/<label>/camera/compressed, mirroring how a real
per-drone camera driver publishes on hardware. frame_offset makes each
'camera' see different scenes.
"""
import glob
import os

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage

DEFAULT = os.path.join(os.path.dirname(__file__), '..', 'assets')


class ImageReplay(Node):
    def __init__(self):
        super().__init__('image_replay')
        self.declare_parameter('assets_dir', DEFAULT)
        self.declare_parameter('rate_hz', 0.5)
        self.declare_parameter('stride', 7)
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('frame_offset', 0)
        self.label = self.get_parameter('drone_label').value
        d = self.get_parameter('assets_dir').value
        allf = sorted(
            glob.glob(os.path.join(d, '**', '*.jpg'), recursive=True) +
            glob.glob(os.path.join(d, '**', '*.jpeg'), recursive=True) +
            glob.glob(os.path.join(d, '**', '*.png'), recursive=True))
        self.files = allf[::max(1, int(self.get_parameter('stride').value))]
        if not self.files:
            try:
                from ultralytics.utils import ASSETS_DIR
                self.files = sorted(glob.glob(os.path.join(ASSETS_DIR, '*.jpg')))
            except Exception:
                pass
        self.i = int(self.get_parameter('frame_offset').value)
        self.topic = f'/swarm/{self.label}/camera/compressed'
        self.pub = self.create_publisher(CompressedImage, self.topic, 10)
        self.create_timer(1.0 / max(0.1, self.get_parameter('rate_hz').value), self.tick)
        self.get_logger().info(f'image_replay[{self.label}]: {len(self.files)} scenes -> {self.topic}')

    def tick(self):
        if not self.files:
            return
        frame = cv2.imread(self.files[self.i % len(self.files)])
        self.i += 1
        if frame is None:
            return
        ok, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.label
        msg.format = 'jpeg'
        msg.data = enc.tobytes()
        self.pub.publish(msg)


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
