"""Camera views with detection boxes, for people to look at (GCS camera panel, rqt_image_view).

* draw_detections: boxes + labels on a real camera frame (perception_node, Gazebo / hardware)
* render_sim_view: what a simulated camera "sees" (light mode, no rendering engine): the
  area's roads, buildings, water, people and cars projected with the same camera model the
  brain uses, plus the detection boxes. Clearly labelled SIMULATED.
OpenCV is imported lazily; nothing here is needed to fly.
"""
import math
from typing import Dict, List, Optional, Sequence

from .config import PerceptionCfg
from .perception import footprint_radius, world_to_image

COLORS = {"person": (60, 60, 240), "vehicle": (40, 200, 250), "water": (220, 140, 40)}   # BGR


def draw_detections(img, dets: Sequence[Dict], title: str = "", sim: bool = False):
    """dets: [{class, conf, u0, v0, w, h}] (normalised). Draws in place, returns img."""
    import cv2
    h, w = img.shape[:2]
    for d in dets:
        c = COLORS.get(d["class"], (200, 200, 200))
        x0, y0 = int(d["u0"] * w), int(d["v0"] * h)
        x1, y1 = int((d["u0"] + d["w"]) * w), int((d["v0"] + d["h"]) * h)
        if d["class"] == "water":
            ov = img.copy()
            cv2.rectangle(ov, (x0, y0), (x1, y1), c, -1)
            cv2.addWeighted(ov, 0.25, img, 0.75, 0, img)
            continue
        x0, y0, x1, y1 = x0 - 3, y0 - 3, max(x1, x0 + 6) + 3, max(y1, y0 + 6) + 3
        cv2.rectangle(img, (x0, y0), (x1, y1), c, 2)
        txt = f"{d['class']} {d.get('conf', 0):.2f}"
        fs = 0.55 * w / 640
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, fs, 1)
        cv2.rectangle(img, (x0, y0 - th - 8), (x0 + tw + 6, y0), c, -1)
        cv2.putText(img, txt, (x0 + 3, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, fs, (15, 15, 15), 1, cv2.LINE_AA)
    bar = f"{title}  {sum(1 for d in dets if d['class'] != 'water')} detections" + ("   SIMULATED CAMERA" if sim else "")
    fs = 0.62 * w / 640
    cv2.rectangle(img, (0, 0), (w, int(30 * w / 640)), (20, 20, 20), -1)
    cv2.putText(img, bar, (10, int(21 * w / 640)), cv2.FONT_HERSHEY_SIMPLEX, fs, (235, 235, 235), 1, cv2.LINE_AA)
    return img


def to_jpeg(img, quality: int = 70) -> bytes:
    import cv2
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return buf.tobytes() if ok else b""


class SimViewRenderer:
    """Draws the scene below a drone as its nadir camera would frame it."""

    def __init__(self, cfg: PerceptionCfg, area: Optional[dict], scene: dict, w: int = 640, h: int = 400):
        self.cfg, self.scene, self.w, self.h = cfg, scene, w, h
        area = area or {}
        self.blds = [(sum(p[0] for p in b["poly"]) / len(b["poly"]), sum(p[1] for p in b["poly"]) / len(b["poly"]),
                      b["poly"], b.get("h", 10.0)) for b in area.get("buildings", []) if len(b.get("poly", [])) >= 3]
        self.roads = [r["line"] for r in area.get("roads", []) if len(r.get("line", [])) >= 2]
        self.water = [wt["poly"] for wt in area.get("water", []) if len(wt.get("poly", [])) >= 3]

    def _px(self, gx, gy, pose, gz=0.0):
        x, y, alt, ro, pi, ya = pose
        uv = world_to_image(gx, gy, x, y, alt, ro, pi, ya, self.cfg, gz)
        if uv is None:
            return None
        return int(uv[0] * self.w), int(uv[1] * self.h)

    def render(self, pose, dets: Sequence[Dict], title: str, movers: Sequence = ()):
        import cv2
        import numpy as np
        x, y, alt = pose[0], pose[1], pose[2]
        img = np.zeros((self.h, self.w, 3), np.uint8)
        img[:] = (70, 92, 84)                                   # ground
        r = footprint_radius(max(alt, 5.0), self.cfg) * 2.2 + 30
        near = lambda px, py: abs(px - x) < r and abs(py - y) < r        # noqa: E731

        def poly(pts, gz=0.0):
            out = [self._px(p[0], p[1], pose, gz) for p in pts]
            return None if any(p is None for p in out) else np.array(out, np.int32)
        for wpoly in self.water:
            if any(near(p[0], p[1]) for p in wpoly):
                q = poly(wpoly)
                if q is not None:
                    cv2.fillPoly(img, [q], (120, 80, 40))
        for f in self.scene.get("flood", []):
            q = poly(f)
            if q is not None:
                ov = img.copy()
                cv2.fillPoly(ov, [q], (115, 85, 50))
                cv2.addWeighted(ov, 0.8, img, 0.2, 0, img)
        for line in self.roads:
            if any(near(p[0], p[1]) for p in line):
                q = poly(line)
                if q is not None:
                    cv2.polylines(img, [q], False, (88, 88, 92), 9, cv2.LINE_AA)
        for cx, cy, pts, hgt in self.blds:
            if near(cx, cy) and hgt < alt - 1.0:
                q = poly(pts, min(hgt, alt - 2.0))              # roofs, seen from above
                if q is not None:
                    cv2.fillPoly(img, [q], (150, 158, 166))
                    cv2.polylines(img, [q], True, (95, 100, 108), 1, cv2.LINE_AA)
        for k, (cx, cy) in enumerate(self.scene.get("cars", []) + [tuple(m) for m in movers]):
            if near(cx, cy):
                p = self._px(cx, cy, pose)
                if p:
                    s = max(2, int(4.4 / max(0.02, 2 * alt * math.tan(math.radians(self.cfg.hfov_deg) / 2) / self.w) / 2))
                    cv2.rectangle(img, (p[0] - s, p[1] - s // 2), (p[0] + s, p[1] + s // 2),
                                  (40, 200, 250) if k >= len(self.scene.get("cars", [])) else (190, 190, 200), -1)
        for cx, cy in self.scene.get("people", []):
            if near(cx, cy):
                p = self._px(cx, cy, pose)
                if p:
                    cv2.circle(img, p, 2, (60, 60, 230), -1)
        return draw_detections(img, dets, title, sim=True)


def summarize(dets: List[Dict]) -> str:
    n = {}
    for d in dets:
        n[d["class"]] = n.get(d["class"], 0) + 1
    return ", ".join(f"{k}:{v}" for k, v in sorted(n.items()))
