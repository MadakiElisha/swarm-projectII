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
from swarm_common.vision_core import (WATER, WATER_HSV_HI, WATER_HSV_LO, filter_detections, swarm_class,
                                      water_cells)


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
        # simulation: ONE process (one model on the GPU) serving several drones' cameras.
        # On hardware every drone runs its own node with just drone_label.
        self.declare_parameter('drone_labels', [''])
        self.declare_parameter('sliced', False)
        self.declare_parameter('slice_px', 640)
        self.declare_parameter('imgsz', 1024)
        # flood mapping: '' (off) | 'hsv' (colour baseline, simulation) | path to a YOLO-seg model
        # whose class names contain "water"/"flood" (e.g. trained on FloodNet)
        self.declare_parameter('water_model', '')
        self.declare_parameter('water_hz', 1.0)
        self.declare_parameter('annotated_hz', 2.0)     # camera image with the boxes drawn (0 = off)
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
        self.water_mode = os.path.expanduser(str(self.get_parameter('water_model').value or ''))
        self.water_seg = None
        if self.water_mode and self.water_mode != 'hsv':
            self.water_seg = YOLO(self.water_mode)
        labels = [x for x in self.get_parameter('drone_labels').value if x] or [self.label]
        self._last_water = {lab: 0.0 for lab in labels}
        self.pubs, self.ann_pubs, self._last_ann = {}, {}, {}
        for lab in labels:
            self.ann_pubs[lab] = self.create_publisher(CompressedImage, f'/swarm/{lab}/camera/annotated', 2)
            self.pubs[lab] = self.create_publisher(DetectionArray, f'/swarm/{lab}/detections', 10)
            self.create_subscription(CompressedImage, f'/swarm/{lab}/camera/compressed',
                                     lambda m, lab=lab: self.on_image(m, lab), 2)
        self.get_logger().info(f'Perception ready for {", ".join(labels)} (model={model_path})')

    def on_image(self, msg: CompressedImage, label: str = ''):
        label = label or self.label
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
        out.header.frame_id = label
        for d in kept:
            x1, y1, x2, y2 = d["bbox"]
            det = Detection()
            det.class_name = swarm_class(d["class_name"])
            det.confidence = d["confidence"]
            det.bbox_x, det.bbox_y = x1 / w, y1 / h
            det.bbox_w, det.bbox_h = (x2 - x1) / w, (y2 - y1) / h
            out.detections.append(det)
        out.detections.extend(self._water(frame, label))
        out.count = len(out.detections)

        self.pubs[label].publish(out)
        self._annotate(frame, out, label)
        if out.count:
            self.get_logger().info(f'[{label}] {out.count} detection(s): '
                                   f'{sorted({d.class_name for d in out.detections})}',
                                   throttle_duration_sec=2.0)

    def _annotate(self, frame, out, label):
        hz = float(self.get_parameter('annotated_hz').value)
        now = self.get_clock().now().nanoseconds * 1e-9
        if hz <= 0 or now - self._last_ann.get(label, 0.0) < 1.0 / hz:
            return
        self._last_ann[label] = now
        from swarm_common.annotate import draw_detections, to_jpeg
        img = frame.copy()
        if img.shape[1] > 960:
            img = cv2.resize(img, (960, int(img.shape[0] * 960 / img.shape[1])))
        dets = [{'class': d.class_name, 'conf': d.confidence, 'u0': d.bbox_x, 'v0': d.bbox_y,
                 'w': d.bbox_w, 'h': d.bbox_h} for d in out.detections]
        draw_detections(img, dets, f'{label}  YOLO')
        m = CompressedImage()
        m.header = out.header
        m.format = 'jpeg'
        m.data = to_jpeg(img)
        self.ann_pubs[label].publish(m)

    def _water(self, frame, label):
        """Water cells in this frame as "water" detections (flood recon), at water_hz."""
        if not self.water_mode:
            return []
        now = self.get_clock().now().nanoseconds * 1e-9
        if now - self._last_water.get(label, 0.0) < 1.0 / max(0.1, float(self.get_parameter('water_hz').value)):
            return []
        self._last_water[label] = now
        if self.water_seg is None:                      # colour baseline
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array(WATER_HSV_LO, np.uint8), np.array(WATER_HSV_HI, np.uint8)) > 0
        else:
            mask = np.zeros(frame.shape[:2], bool)
            for r in self.water_seg.predict(frame, imgsz=self.imgsz, verbose=False):
                if r.masks is None:
                    continue
                names = self.water_seg.names
                for m, c in zip(r.masks.data.cpu().numpy(), r.boxes.cls.cpu().numpy()):
                    n = str(names[int(c)]).lower()
                    if 'water' in n or 'flood' in n:
                        mask |= cv2.resize(m, (frame.shape[1], frame.shape[0])) > 0.5
        dets = []
        for (u0, v0, u1, v1, frac) in water_cells(mask):
            d = Detection()
            d.class_name, d.confidence = WATER, float(frac)
            d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h = u0, v0, u1 - u0, v1 - v0
            dets.append(d)
        return dets


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
