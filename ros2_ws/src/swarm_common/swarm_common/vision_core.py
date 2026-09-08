"""Pure vision logic - unit-testable, no ROS."""

PERSON = "person"


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
