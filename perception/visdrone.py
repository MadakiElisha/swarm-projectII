#!/usr/bin/env python3
"""VisDrone detector for the swarm: train, evaluate, export.

    python3 perception/visdrone.py train  --model yolo11s.pt --epochs 120 --imgsz 1024 --batch 8
    python3 perception/visdrone.py eval   --weights runs/visdrone/yolo11s/weights/best.pt [--sliced]
    python3 perception/visdrone.py export --weights .../best.pt --format engine     # Jetson TensorRT
    python3 perception/visdrone.py export --weights .../best.pt --format onnx       # Hailo DFC input
    python3 perception/visdrone.py install --weights .../best.pt                    # -> ~/swarm_models/

VisDrone2019-DET: ~10k aerial images, 10 classes (pedestrian, people, bicycle,
car, van, truck, tricycle, awning-tricycle, bus, motor). Ultralytics downloads
and converts it on first use ("VisDrone.yaml", ~2.3 GB).

RTX 5060 8 GB guide: yolo11s @ imgsz 1024, batch 8 (AMP) fits; ~3-5 h for
120 epochs. Use imgsz 640 / batch 16 for a quick first model (~1.5 h).
"""
import argparse
import os
import shutil
import sys

SWARM_CLASSES = {          # VisDrone -> what the swarm brain reasons about
    "pedestrian": "person", "people": "person",
    "car": "vehicle", "van": "vehicle", "truck": "vehicle", "bus": "vehicle", "motor": "vehicle",
    "bicycle": "bicycle", "tricycle": "vehicle", "awning-tricycle": "vehicle",
}


def train(a):
    from ultralytics import YOLO
    m = YOLO(a.model)
    m.train(data="VisDrone.yaml", epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, device=a.device,
            project="runs/visdrone", name=os.path.splitext(os.path.basename(a.model))[0],
            cos_lr=True, close_mosaic=10, mosaic=1.0, scale=0.6, degrees=10.0, flipud=0.5, fliplr=0.5,
            hsv_v=0.5, patience=30, workers=a.workers, cache=False, amp=True, plots=True)


def evaluate(a):
    from ultralytics import YOLO
    m = YOLO(a.weights)
    r = m.val(data="VisDrone.yaml", imgsz=a.imgsz, batch=a.batch, device=a.device, split="val")
    print(f"mAP50-95 {r.box.map:.3f}  mAP50 {r.box.map50:.3f}")
    for i, name in m.names.items():
        try:
            print(f"  {name:18s} AP50 {r.box.ap50[i]:.3f}")
        except (IndexError, TypeError):
            pass
    if a.sliced:
        sliced_demo(a)


def sliced_demo(a):
    """Sliced (SAHI) inference on a few val images: recovers tiny people at altitude."""
    import glob
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction
    det = AutoDetectionModel.from_pretrained(model_type="ultralytics", model_path=a.weights,
                                             confidence_threshold=0.3, device=a.device_sahi)
    imgs = sorted(glob.glob(os.path.expanduser("~/datasets/VisDrone/VisDrone2019-DET-val/images/*.jpg")))[:5]
    os.makedirs("runs/visdrone/sliced", exist_ok=True)
    for p in imgs:
        res = get_sliced_prediction(p, det, slice_height=640, slice_width=640,
                                    overlap_height_ratio=0.2, overlap_width_ratio=0.2)
        res.export_visuals(export_dir="runs/visdrone/sliced", file_name=os.path.basename(p))
        print(f"{os.path.basename(p)}: {len(res.object_prediction_list)} objects")


def export(a):
    from ultralytics import YOLO
    m = YOLO(a.weights)
    kw = {"format": a.format, "imgsz": a.imgsz}
    if a.format == "engine":
        kw.update(half=True, device=0)          # build ON the Jetson for its TensorRT version
    if a.format == "onnx":
        kw.update(opset=11, simplify=True)      # Hailo Dataflow Compiler friendly
    print("exported:", m.export(**kw))
    if a.format == "onnx":
        print("Hailo-8L: compile with the Hailo Dataflow Compiler / hailomz (needs a Hailo developer "
              "account), e.g.  hailomz compile --ckpt best.onnx --hw-arch hailo8l --yaml yolov8s.yaml "
              "--classes 10  (calibrate with ~1k VisDrone images)")


def install(a):
    dst = os.path.expanduser("~/swarm_models")
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, a.name)
    shutil.copy(a.weights, out)
    print(f"installed {out}  (swarm_gazebo.launch.py model:={out})")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("train")
    t.add_argument("--model", default="yolo11s.pt")
    t.add_argument("--epochs", type=int, default=120)
    t.add_argument("--imgsz", type=int, default=1024)
    t.add_argument("--batch", type=int, default=8)
    t.add_argument("--workers", type=int, default=6)
    t.add_argument("--device", default="0")
    e = sp.add_parser("eval")
    e.add_argument("--weights", required=True)
    e.add_argument("--imgsz", type=int, default=1024)
    e.add_argument("--batch", type=int, default=8)
    e.add_argument("--device", default="0")
    e.add_argument("--device-sahi", default="cuda:0")
    e.add_argument("--sliced", action="store_true")
    x = sp.add_parser("export")
    x.add_argument("--weights", required=True)
    x.add_argument("--format", default="onnx", choices=["onnx", "engine", "openvino", "tflite"])
    x.add_argument("--imgsz", type=int, default=1024)
    i = sp.add_parser("install")
    i.add_argument("--weights", required=True)
    i.add_argument("--name", default="visdrone_yolo11s.pt")
    a = ap.parse_args()
    {"train": train, "eval": evaluate, "export": export, "install": install}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
