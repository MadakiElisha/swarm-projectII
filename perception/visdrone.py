#!/usr/bin/env python3
"""VisDrone detector for the swarm: check, train, evaluate, see it work, export.

    python3 perception/visdrone.py check                 # GPU / packages / dataset / model status
    python3 perception/visdrone.py train --quick         # ~1-1.5 h on an RTX 5060, then installs itself
    python3 perception/visdrone.py train                 # full: imgsz 1024, 120 epochs (~3-5 h)
    python3 perception/visdrone.py demo                  # annotated aerial images -> runs/visdrone/demo/
    python3 perception/visdrone.py eval [--sliced]       # mAP on VisDrone val (+ SAHI sliced demo)
    python3 perception/visdrone.py export --format engine   # Jetson TensorRT   (onnx: Hailo DFC)

The trained model is installed to ~/swarm_models/visdrone_yolo11s.pt, which is
what the Gazebo launch file and the drones load by default.

VisDrone2019-DET: ~10k aerial images, 10 classes (pedestrian, people, bicycle,
car, van, truck, tricycle, awning-tricycle, bus, motor). Ultralytics downloads
and converts it on the first `train` (~2.3 GB) into its datasets folder.
Close Gazebo while training: the 8 GB of VRAM is the limit.
"""
import argparse
import glob
import os
import shutil
import sys

MODEL_DIR = os.path.expanduser("~/swarm_models")
DEFAULT = os.path.join(MODEL_DIR, "visdrone_yolo11s.pt")
SWARM_CLASSES = {          # VisDrone -> what the swarm brain reasons about
    "pedestrian": "person", "people": "person",
    "car": "vehicle", "van": "vehicle", "truck": "vehicle", "bus": "vehicle", "motor": "vehicle",
    "bicycle": "bicycle", "tricycle": "vehicle", "awning-tricycle": "vehicle",
}


def _datasets_dir():
    try:
        from ultralytics.utils import SETTINGS
        return SETTINGS["datasets_dir"]
    except Exception:
        return os.path.expanduser("~/datasets")


def _val_images(n):
    imgs = sorted(glob.glob(os.path.join(_datasets_dir(), "VisDrone", "VisDrone2019-DET-val", "images", "*.jpg")))
    return imgs[:n]


def check(a):
    ok = True
    try:
        import torch
        if torch.cuda.is_available():
            x = torch.randn(512, 512, device="cuda")
            (x @ x).sum().item()
            print(f"✓ torch {torch.__version__}  GPU {torch.cuda.get_device_name(0)} "
                  f"sm_{''.join(map(str, torch.cuda.get_device_capability(0)))}  "
                  f"{torch.cuda.get_device_properties(0).total_memory / 2**30:.1f} GB")
        else:
            ok = False
            print(f"✗ torch {torch.__version__} has no CUDA -> STEPS=torch scripts/setup_ubuntu2404.sh")
    except Exception as e:
        ok = False
        print(f"✗ torch: {e}")
    try:
        import ultralytics
        print(f"✓ ultralytics {ultralytics.__version__}")
    except Exception:
        ok = False
        print("✗ ultralytics missing -> pip install -c scripts/venv-constraints.txt -r perception/requirements.txt")
    n = len(_val_images(10**6))
    print(("✓" if n else "·") + f" VisDrone val images in {_datasets_dir()}: {n}"
          + ("" if n else "  (downloaded automatically by `train`)"))
    print(("✓" if os.path.isfile(DEFAULT) else "·") + f" installed model: {DEFAULT}"
          + ("" if os.path.isfile(DEFAULT) else "  (not yet - run `train --quick`)"))
    return 0 if ok else 1


def train(a):
    from ultralytics import YOLO
    if a.quick:
        a.imgsz, a.batch, a.epochs = 640, 16, 60
    m = YOLO(a.model)
    m.train(data="VisDrone.yaml", epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, device=a.device,
            project=os.path.abspath("runs/visdrone"), name=os.path.splitext(os.path.basename(a.model))[0],
            exist_ok=True, cos_lr=True, close_mosaic=10, mosaic=1.0, scale=0.6, degrees=10.0, flipud=0.5,
            fliplr=0.5, hsv_v=0.5, patience=30, workers=a.workers, cache=False, amp=True, plots=True)
    best = str(m.trainer.best)
    print(f"\nbest weights: {best}")
    a.weights, a.name = best, os.path.basename(DEFAULT)
    install(a)
    print("next: python3 perception/visdrone.py demo   (look at runs/visdrone/demo/*.jpg)")
    return 0


def demo(a):
    """Run the model on VisDrone validation images and save them annotated: see what it sees."""
    from ultralytics import YOLO
    w = a.weights if os.path.isfile(a.weights) else "yolo11n.pt"
    if w != a.weights:
        print(f"{a.weights} not found - showing the stock COCO model for comparison")
    imgs = _val_images(a.n)
    if not imgs:
        print("no VisDrone images yet (they are downloaded by `train`); pass your own: --images 'dir/*.jpg'")
    imgs = sorted(glob.glob(os.path.expanduser(a.images)))[:a.n] if a.images else imgs
    out = os.path.abspath("runs/visdrone/demo")
    os.makedirs(out, exist_ok=True)
    m = YOLO(w)
    for p in imgs:
        r = m.predict(p, imgsz=a.imgsz, conf=0.3, verbose=False)[0]
        names = [m.names[int(c)] for c in r.boxes.cls]
        swarm = {}
        for n in names:
            k = SWARM_CLASSES.get(n, n)
            swarm[k] = swarm.get(k, 0) + 1
        r.save(filename=os.path.join(out, os.path.basename(p)))
        print(f"{os.path.basename(p)}: {len(names)} objects  {swarm}")
    print(f"annotated images: {out}")
    return 0


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
    return 0


def sliced_demo(a):
    """Sliced (SAHI) inference on a few val images: recovers tiny people at altitude."""
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction
    det = AutoDetectionModel.from_pretrained(model_type="ultralytics", model_path=a.weights,
                                             confidence_threshold=0.3, device=a.device_sahi)
    os.makedirs("runs/visdrone/sliced", exist_ok=True)
    for p in _val_images(5):
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
    return 0


def install(a):
    os.makedirs(MODEL_DIR, exist_ok=True)
    out = os.path.join(MODEL_DIR, a.name)
    if os.path.abspath(a.weights) != os.path.abspath(out):
        shutil.copy(a.weights, out)
    print(f"installed {out}  (the Gazebo launch file loads this by default)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    t = sp.add_parser("train")
    t.add_argument("--quick", action="store_true", help="imgsz 640, batch 16, 60 epochs")
    t.add_argument("--model", default="yolo11s.pt")
    t.add_argument("--epochs", type=int, default=120)
    t.add_argument("--imgsz", type=int, default=1024)
    t.add_argument("--batch", type=int, default=8)
    t.add_argument("--workers", type=int, default=6)
    t.add_argument("--device", default="0")
    d = sp.add_parser("demo")
    d.add_argument("--weights", default=DEFAULT)
    d.add_argument("--images", default=None, help="glob of your own images")
    d.add_argument("--n", type=int, default=8)
    d.add_argument("--imgsz", type=int, default=1024)
    e = sp.add_parser("eval")
    e.add_argument("--weights", default=DEFAULT)
    e.add_argument("--imgsz", type=int, default=1024)
    e.add_argument("--batch", type=int, default=8)
    e.add_argument("--device", default="0")
    e.add_argument("--device-sahi", default="cuda:0")
    e.add_argument("--sliced", action="store_true")
    x = sp.add_parser("export")
    x.add_argument("--weights", default=DEFAULT)
    x.add_argument("--format", default="onnx", choices=["onnx", "engine", "openvino", "tflite"])
    x.add_argument("--imgsz", type=int, default=1024)
    i = sp.add_parser("install")
    i.add_argument("--weights", required=True)
    i.add_argument("--name", default=os.path.basename(DEFAULT))
    a = ap.parse_args()
    return {"check": check, "train": train, "demo": demo, "eval": evaluate, "export": export,
            "install": install}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
