"""
Phase 4 - Computer vision: real object detection on drone-style imagery.

Uses YOLOv8 (a real, widely deployed detection model - the same
family used in actual industry drone/vision pipelines) to detect
people and objects in an image, then converts the raw detections
into a structured report - the same shape of data a "spotter drone"
would send back over the mesh in a real deployment.

NOTE ON THE TEST IMAGE: this uses a stock ground-level test image
bundled with the YOLO library (people boarding a bus) rather than
real aerial/drone footage, because we don't have real flood-zone
drone imagery yet. This proves the DETECTION PIPELINE works
end-to-end (model loads, runs, outputs usable structured data) - it
is NOT a claim that this exact model is tuned for aerial imagery.
Real deployment would need a model fine-tuned on actual drone-angle,
disaster-zone imagery, which is a later, separate step.
"""
import os
from ultralytics import YOLO


def run_detection(image_path, output_json_path=None):
    print(f"[Vision] Loading YOLOv8 model (nano - smallest, fastest, "
          f"realistic for onboard/edge use)...")
    model = YOLO("yolov8n.pt")  # 'n' = nano, the size actually feasible on a Jetson/edge device

    print(f"[Vision] Running detection on: {image_path}")
    results = model(image_path, verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0]]
            detections.append({
                "class": class_name,
                "confidence": round(confidence, 3),
                "bbox_xyxy": [x1, y1, x2, y2],
            })

    print(f"\n[Vision] Detected {len(detections)} objects:")
    for d in detections:
        print(f"  - {d['class']} (confidence: {d['confidence']:.0%}) at {d['bbox_xyxy']}")

    people_count = sum(1 for d in detections if d["class"] == "person")
    print(f"\n[Vision] SUMMARY: {people_count} person(s) detected in frame.")
    print(f"[Vision] This is the exact structured output a scout drone "
          f"would relay over the mesh (Phase 2) as a task report.")

    return detections


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    # Using the sample image bundled with ultralytics for this proof-of-pipeline
    import ultralytics
    sample_image = os.path.join(
        os.path.dirname(ultralytics.__file__), "assets", "bus.jpg"
    )
    run_detection(sample_image)
