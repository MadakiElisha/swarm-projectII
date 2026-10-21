"""Pure vision logic - unit-testable, no ROS."""

PERSON = "person"

# COCO and VisDrone class names -> what the swarm brain reasons about
SWARM_CLASS = {
    "person": "person", "pedestrian": "person", "people": "person",
    "car": "vehicle", "van": "vehicle", "truck": "vehicle", "bus": "vehicle", "motor": "vehicle",
    "motorcycle": "vehicle", "tricycle": "vehicle", "awning-tricycle": "vehicle",
    "bicycle": "bicycle", "boat": "boat",
}


def swarm_class(name: str) -> str:
    return SWARM_CLASS.get(name, name)


def filter_detections(raw_detections, min_confidence=0.5, classes=None):
    """Keep detections passing confidence + class filter, best first.

    raw_detections: list of dicts with class_name, confidence, bbox.
    classes=None means keep every class.
    """
    kept = [
        d for d in raw_detections
        if d.get("confidence", 0.0) >= min_confidence
        and (classes is None or d.get("class_name") in classes)
    ]
    return sorted(kept, key=lambda d: d["confidence"], reverse=True)


def has_person(detections) -> bool:
    return any(d["class_name"] == PERSON for d in detections)
