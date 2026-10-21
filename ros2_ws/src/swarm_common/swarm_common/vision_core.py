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


# ------------------------------------------------------------------ water
WATER = "water"
# murky flood water seen from above: blue-grey/teal, moderately saturated (OpenCV HSV, H in 0..179).
# A colour baseline for simulation; on real imagery use a segmentation model (FloodNet).
WATER_HSV_LO = (90, 50, 35)
WATER_HSV_HI = (120, 255, 220)


def water_cells(mask, cols: int = 8, rows: int = 5, min_frac: float = 0.5):
    """Split a binary water mask (2-D array, truthy = water) into a cols x rows grid.

    Returns [(u0, v0, u1, v1, frac)] in normalised image coords for every cell
    that is at least min_frac water. Each becomes one "water" detection that the
    brain projects to the ground and adds to the shared flood map.
    """
    h = len(mask)
    w = len(mask[0]) if h else 0
    out = []
    if not h or not w:
        return out
    for r in range(rows):
        y0, y1 = r * h // rows, (r + 1) * h // rows
        for c in range(cols):
            x0, x1 = c * w // cols, (c + 1) * w // cols
            n = (y1 - y0) * (x1 - x0)
            if n <= 0:
                continue
            try:
                wet = int(mask[y0:y1, x0:x1].astype(bool).sum())     # numpy fast path
            except (AttributeError, TypeError):           # plain lists (tests)
                wet = sum(1 for yy in range(y0, y1) for xx in range(x0, x1) if mask[yy][xx])
            frac = wet / n
            if frac >= min_frac:
                out.append((x0 / w, y0 / h, x1 / w, y1 / h, frac))
    return out
