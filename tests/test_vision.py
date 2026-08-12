from swarm_common.vision_core import filter_detections, has_person


def _d(cls, conf):
    return {"class_name": cls, "confidence": conf, "bbox": [0, 0, 1, 1]}


def test_filter_drops_low_confidence():
    assert filter_detections([_d("person", 0.1)], 0.5, {"person"}) == []


def test_filter_keeps_only_requested_classes():
    kept = filter_detections([_d("person", 0.9), _d("bus", 0.9)], 0.5, {"person"})
    assert len(kept) == 1 and kept[0]["class_name"] == "person"


def test_filter_sorts_by_confidence():
    kept = filter_detections([_d("person", 0.6), _d("person", 0.95)], 0.5, None)
    assert kept[0]["confidence"] == 0.95


def test_has_person():
    assert has_person([_d("person", 0.9)])
    assert not has_person([_d("bus", 0.9)])
