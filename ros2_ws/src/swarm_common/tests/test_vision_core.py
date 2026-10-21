from swarm_common.vision_core import filter_detections, PERSON


def test_filters_low_confidence():
    raw = [{"class_name": PERSON, "confidence": 0.2, "bbox": [0, 0, 1, 1]},
           {"class_name": PERSON, "confidence": 0.9, "bbox": [0, 0, 1, 1]}]
    kept = filter_detections(raw, 0.5, {PERSON})
    assert len(kept) == 1 and kept[0]["confidence"] == 0.9


def test_filters_foreign_classes():
    raw = [{"class_name": "car", "confidence": 0.95, "bbox": [0, 0, 1, 1]}]
    assert filter_detections(raw, 0.5, {PERSON}) == []


def test_water_cells_grid():
    from swarm_common.vision_core import water_cells
    w, h = 80, 50
    mask = [[1 if x < 40 else 0 for x in range(w)] for _ in range(h)]   # left half flooded
    cells = water_cells(mask, cols=8, rows=5)
    assert len(cells) == 4 * 5
    assert all(c[2] <= 0.5 + 1e-9 and c[4] == 1.0 for c in cells)
    assert water_cells([[0] * w for _ in range(h)]) == []
