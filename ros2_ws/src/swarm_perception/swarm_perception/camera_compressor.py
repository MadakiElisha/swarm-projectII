"""Raw camera images (e.g. bridged from Gazebo) -> JPEG on /swarm/<label>/camera/compressed.

That is the same topic a real drone's camera driver publishes, so perception
and everything downstream are identical in Gazebo and on hardware.
"""
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, Image


class CameraCompressor(Node):
    def __init__(self):
        super().__init__('camera_compressor')
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('max_hz', 3.0)
        self.declare_parameter('jpeg_quality', 85)
        self.label = self.get_parameter('drone_label').value
        self.period = 1.0 / max(0.1, float(self.get_parameter('max_hz').value))
        self.q = int(self.get_parameter('jpeg_quality').value)
        self.last = 0.0
        self.pub = self.create_publisher(CompressedImage, f'/swarm/{self.label}/camera/compressed', 5)
        self.create_subscription(Image, f'/swarm/{self.label}/camera/image', self.on_image,
                                 qos_profile_sensor_data)
        self.get_logger().info(f'{self.label}: compressing camera to /swarm/{self.label}/camera/compressed')

    def on_image(self, m: Image):
        now = time.time()
        if now - self.last < self.period:
            return
        self.last = now
        ch = {'rgb8': 3, 'bgr8': 3, 'rgba8': 4, 'bgra8': 4, 'mono8': 1}.get(m.encoding)
        if ch is None:
            self.get_logger().warn(f'unsupported encoding {m.encoding}', throttle_duration_sec=10)
            return
        img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.step // ch, ch)[:, :m.width]
        if m.encoding.startswith('rgb'):
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if ch == 3 else cv2.COLOR_RGBA2BGR)
        elif m.encoding == 'bgra8':
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        ok, enc = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), self.q])
        if not ok:
            return
        out = CompressedImage()
        out.header = m.header
        out.header.frame_id = self.label
        out.format = 'jpeg'
        out.data = enc.tobytes()
        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = CameraCompressor()
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
