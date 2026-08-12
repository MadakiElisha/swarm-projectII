"""Swarm eyes: YOLOv8 over CompressedImage -> typed DetectionArray.

Camera-source-agnostic: today image_replay feeds it, tomorrow a Gazebo
camera topic can, with zero changes here.
"""
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from swarm_interfaces.msg import Detection, DetectionArray
from swarm_common.vision_core import filter_detections
from ultralytics import YOLO


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('min_confidence', 0.5)
        self.declare_parameter('classes', ['person'])
        self.min_conf = self.get_parameter('min_confidence').value
        self.classes = set(self.get_parameter('classes').value)
        model_path = self.get_parameter('model_path').value
        self.model = YOLO(model_path)
        self.pub = self.create_publisher(DetectionArray, '/swarm/detections', 10)
        self.create_subscription(CompressedImage, '/swarm/camera/compressed', self.on_image, 10)
        self.get_logger().info(
            f'Perception node ready (model={model_path}, classes={sorted(self.classes)})')

    def on_image(self, msg: CompressedImage):
        frame = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            self.get_logger().warning('Received undecodable image - skipping')
            return
        h, w = frame.shape[:2]

        raw = []
        for r in self.model.predict(frame, verbose=False):
            for box in r.boxes:
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                raw.append({
                    "class_name": self.model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": [x1, y1, x2, y2],
                })

        kept = filter_detections(raw, self.min_conf, self.classes)
        out = DetectionArray()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = msg.header.frame_id
        for d in kept:
            x1, y1, x2, y2 = d["bbox"]
            det = Detection()
            det.class_name = d["class_name"]
            det.confidence = d["confidence"]
            det.bbox_x, det.bbox_y = x1 / w, y1 / h
            det.bbox_w, det.bbox_h = (x2 - x1) / w, (y2 - y1) / h
            out.detections.append(det)
        out.count = len(out.detections)

        self.pub.publish(out)
        self.get_logger().info(f'[{msg.header.frame_id}] {out.count} target detection(s)')


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
