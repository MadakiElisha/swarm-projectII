"""Simulated camera + detector (ground truth -> what a drone's YOLO would report).

The light way to fly the whole swarm on real ArduPilot without rendering
anything: every frame, each object in the scene is projected into each
drone's camera with the same camera model the brain uses to project
detections back to the ground (world_to_image is the exact inverse of
project_bbox). Whether it is detected depends on how many pixels it covers,
like a real detector (tiny people from high up are often missed), plus
random misses and a few false positives. Water is reported as image cells,
the same way the water-segmentation path does.

Scene (ENU metres): people, parked cars, flood polygons; the moving target is
passed in per frame. Deterministic for a given seed.
"""
import math
import random
from typing import Dict, List, Sequence, Tuple

from .area import height_grid, point_in_poly
from .config import PerceptionCfg
from .perception import footprint_radius, project_bbox, world_to_image

Pt = Tuple[float, float]

# object size (m) and how a VisDrone-trained YOLO11s behaves on it
OBJ = {"person": {"size": 0.6, "px50": 7.0, "pmax": 0.85},     # 50 % detection at ~7 px
       "vehicle": {"size": 4.2, "px50": 9.0, "pmax": 0.95}}


def make_scene(area: dict, seed: int = 1, people: int = 10, cars: int = 14, flood: bool = False,
               centre: Pt = (0.0, 0.0), radius: float = 700.0, avoid: Sequence[Pt] = ()) -> dict:
    """Random people / parked cars on open ground (not inside buildings or water)."""
    rnd = random.Random(seed)
    g = height_grid(area, cell=5.0, margin=0.0, dilate=False) if area.get("buildings") else None

    def open_pts(n, min_sep):
        pts, tries = [], 0
        while len(pts) < n and tries < 30000:
            tries += 1
            a, r = rnd.uniform(0, 2 * math.pi), radius * math.sqrt(rnd.random())
            x, y = centre[0] + r * math.cos(a), centre[1] + r * math.sin(a)
            if g is not None and (g.height_at(x, y) > 0 or g.is_water(x, y)):
                continue
            if any(point_in_poly(x, y, w["poly"]) for w in area.get("water", [])):
                continue
            if any(math.hypot(x - p[0], y - p[1]) < min_sep for p in list(pts) + list(avoid)):
                continue
            pts.append((round(x, 1), round(y, 1)))
        return pts
    sc = {"seed": seed, "people": open_pts(people, 40.0), "cars": open_pts(cars, 25.0), "flood": []}
    if flood:
        for _ in range(2):
            c = open_pts(1, 150.0)
            cx, cy = c[0] if c else centre
            w, h = rnd.uniform(180, 320), rnd.uniform(140, 260)
            sc["flood"].append([[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2],
                                [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2]])
    return sc


def _p_detect(cls: str, px: float) -> float:
    o = OBJ[cls]
    return o["pmax"] / (1.0 + math.exp(-(px - o["px50"]) / 1.5))


class SimCamera:
    def __init__(self, cfg: PerceptionCfg, scene: dict, width_px: int = 1280, seed: int = 0,
                 false_pos_rate: float = 0.02, water_grid: Tuple[int, int] = (8, 5)):
        self.cfg, self.scene, self.w = cfg, scene, width_px
        self.rnd = random.Random(seed)
        self.fp = false_pos_rate
        self.grid = water_grid

    def detect(self, x: float, y: float, alt: float, roll: float, pitch: float, yaw: float,
               movers: Sequence[Pt] = ()) -> List[Dict]:
        """-> [{class, conf, u0, v0, w, h}] in normalised image coordinates."""
        out: List[Dict] = []
        if alt < 3.0:
            return out
        r = footprint_radius(alt, self.cfg) * 1.6
        gsd = 2.0 * alt * math.tan(math.radians(self.cfg.hfov_deg) / 2) / self.w   # m per pixel
        objs = [("person", p) for p in self.scene.get("people", [])] + \
               [("vehicle", c) for c in self.scene.get("cars", [])] + [("vehicle", m) for m in movers]
        for cls, (ox, oy) in objs:
            if abs(ox - x) > r or abs(oy - y) > r:
                continue
            uv = world_to_image(ox, oy, x, y, alt, roll, pitch, yaw, self.cfg)
            if uv is None or not (0.0 <= uv[0] <= 1.0 and 0.0 <= uv[1] <= 1.0):
                continue
            px = OBJ[cls]["size"] / max(gsd, 1e-3)
            if self.rnd.random() > _p_detect(cls, px):
                continue
            bw = max(px / self.w, 0.004)
            u = uv[0] + self.rnd.gauss(0, 0.004)
            v = uv[1] + self.rnd.gauss(0, 0.004)
            out.append({"class": cls, "conf": round(min(0.97, 0.45 + 0.05 * px), 2),
                        "u0": u - bw / 2, "v0": v - bw / 2, "w": bw, "h": bw})
        if self.rnd.random() < self.fp:                  # an occasional false positive
            u, v = self.rnd.random(), self.rnd.random()
            out.append({"class": self.rnd.choice(["person", "vehicle"]), "conf": 0.4,
                        "u0": u, "v0": v, "w": 0.01, "h": 0.01})
        if self.scene.get("flood"):
            cols, rows = self.grid
            for i in range(cols):
                for j in range(rows):
                    u0, v0 = i / cols, j / rows
                    hits = 0
                    for du in (0.25, 0.75):
                        for dv in (0.25, 0.75):
                            g = project_bbox(u0 + du / cols, v0 + dv / rows, x, y, alt, roll, pitch, yaw, self.cfg)
                            if g and any(point_in_poly(g[0], g[1], f) for f in self.scene["flood"]):
                                hits += 1
                    if hits >= 2:
                        out.append({"class": "water", "conf": hits / 4.0, "u0": u0, "v0": v0,
                                    "w": 1.0 / cols, "h": 1.0 / rows})
        return out
