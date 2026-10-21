"""Swarm eyes: YOLO over this drone's camera -> DetectionArray for this drone's brain.

Works with COCO weights (yolov8n.pt / yolo11n.pt) or a VisDrone-trained model
(perception/visdrone.py). Class names are normalised to what the brain reasons
about: person / vehicle / bicycle (swarm_common.vision_core.SWARM_CLASS).
Optional sliced inference (SAHI) finds small people from altitude.

One instance per drone. Video AND raw detections stay in the drone's own
namespace (/swarm/<label>/...). The brain projects detections onto the
ground and only compact, fused observations cross the radio by gossip.
"""
import os

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from swarm_interfaces.msg import Detection, DetectionArray
from swarm_common.vision_core import filter_detections, swarm_class


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')
        self.declare_parameter('model_path', 'yolo11n.pt')
        self.declare_parameter('fallback_model', 'yolo11n.pt')
        self.declare_parameter('min_confidence', 0.4)
        # detector class names to keep (VisDrone and COCO names; mapped to person / vehicle)
        self.declare_parameter('classes', ['person', 'pedestrian', 'people', 'car', 'van', 'truck', 'bus',
                                           'motor', 'motorcycle'])
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('sliced', False)
        self.declare_parameter('slice_px', 640)
        self.declare_parameter('imgsz', 1024)
        self.label = self.get_parameter('drone_label').value
        self.min_conf = self.get_parameter('min_confidence').value
        self.classes = set(self.get_parameter('classes').value)
        self.imgsz = int(self.get_parameter('imgsz').value)
        model_path = os.path.expanduser(self.get_parameter('model_path').value)
        if not os.path.isfile(model_path) and os.sep in model_path:
            fb = self.get_parameter('fallback_model').value
            self.get_logger().warn(f'{model_path} not found - using {fb} (COCO). Train a VisDrone '
                                   f'model with perception/visdrone.py for aerial accuracy.')
            model_path = fb
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        self.sahi = None
        if self.get_parameter('sliced').value:
            try:
                from sahi import AutoDetectionModel
                self.sahi = AutoDetectionModel.from_pretrained(model_type='ultralytics', model_path=model_path,
                                                               confidence_threshold=self.min_conf)
            except Exception as e:      # optional dependency
                self.get_logger().warn(f'sliced inference unavailable ({e}); using full-frame')
        self.topic = f'/swarm/{self.label}/camera/compressed'
        self.pub = self.create_publisher(DetectionArray, f'/swarm/{self.label}/detections', 10)
        self.create_subscription(CompressedImage, self.topic, self.on_image, 10)
        self.get_logger().info(
            f'Perception[{self.label}] ready (model={model_path}, listening {self.topic})')

    def on_image(self, msg: CompressedImage):
        frame = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            self.get_logger().warning('Received undecodable image - skipping')
            return
        h, w = frame.shape[:2]

        raw = []
        if self.sahi is not None:
            from sahi.predict import get_sliced_prediction
            sp = int(self.get_parameter('slice_px').value)
            res = get_sliced_prediction(frame[:, :, ::-1], self.sahi, slice_height=sp, slice_width=sp,
                                        overlap_height_ratio=0.2, overlap_width_ratio=0.2, verbose=0)
            for p in res.object_prediction_list:
                b = p.bbox
                raw.append({"class_name": p.category.name, "confidence": float(p.score.value),
                            "bbox": [b.minx, b.miny, b.maxx, b.maxy]})
        else:
            for r in self.model.predict(frame, imgsz=self.imgsz, verbose=False):
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
        out.header.frame_id = self.label
        for d in kept:
            x1, y1, x2, y2 = d["bbox"]
            det = Detection()
            det.class_name = swarm_class(d["class_name"])
            det.confidence = d["confidence"]
            det.bbox_x, det.bbox_y = x1 / w, y1 / h
            det.bbox_w, det.bbox_h = (x2 - x1) / w, (y2 - y1) / h
            out.detections.append(det)
        out.count = len(out.detections)

        self.pub.publish(out)
        if out.count:
            self.get_logger().info(f'[{self.label}] {out.count} detection(s): '
                                   f'{sorted({d.class_name for d in out.detections})}',
                                   throttle_duration_sec=2.0)


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
