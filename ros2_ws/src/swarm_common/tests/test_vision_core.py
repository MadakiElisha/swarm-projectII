from swarm_common.vision_core import filter_detections, PERSON


def test_filters_low_confidence():
    raw = [{"class_name": PERSON, "confidence": 0.2, "bbox": [0, 0, 1, 1]},
           {"class_name": PERSON, "confidence": 0.9, "bbox": [0, 0, 1, 1]}]
    kept = filter_detections(raw, 0.5, {PERSON})
    assert len(kept) == 1 and kept[0]["confidence"] == 0.9


def test_filters_foreign_classes():
    raw = [{"class_name": "car", "confidence": 0.95, "bbox": [0, 0, 1, 1]}]
    assert filter_detections(raw, 0.5, {PERSON}) == []
