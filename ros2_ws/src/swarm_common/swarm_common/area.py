"""Operating area: buildings, water and roads from OpenStreetMap, in the swarm's ENU frame.

One area file (areas/<name>/area.json) feeds:
  * the Gazebo world generator (scripts/gz/make_world.py) - what the drones physically fly in
  * every drone's brain - an obstacle height map for path planning around buildings
  * the GCS - which already draws the same OSM buildings through Cesium

Format (version 1):
  {"v": 1, "name": str, "origin": [lat, lon], "bbox": [s, w, n, e],
   "buildings": [{"id": str, "h": metres, "base": metres, "kind": str, "poly": [[x, y], ...]}],
   "water": [{"poly": [[x, y], ...]}], "roads": [{"w": metres, "line": [[x, y], ...]}],
   "launch": [x, y], "max_h": metres}
"""
import json
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .geo import Origin

Pt = Tuple[float, float]

# Rough heights when OSM has no height/levels tag (Lagos-typical defaults)
DEFAULT_HEIGHT = {
    "house": 7.0, "residential": 9.0, "detached": 7.0, "apartments": 15.0, "commercial": 14.0,
    "retail": 8.0, "office": 24.0, "industrial": 10.0, "warehouse": 9.0, "church": 14.0,
    "mosque": 14.0, "school": 10.0, "hospital": 16.0, "hotel": 30.0, "yes": 9.0,
}
LEVEL_M = 3.2

PRESETS: Dict[str, Tuple[float, float, float, float, str]] = {
    # name: (south, west, north, east, description)
    "eko": (6.4440, 3.3830, 6.4610, 3.4040, "Lagos Island (Eko): Marina, Broad Street, Tinubu Square"),
    "victoria-island": (6.4210, 3.4040, 6.4380, 3.4330, "Victoria Island waterfront and Bar Beach"),
    "lekki-phase1": (6.4330, 3.4520, 6.4520, 3.4800, "Lekki Phase 1 (flood-prone low ground)"),
    "ajegunle": (6.4430, 3.3250, 6.4600, 3.3450, "Ajegunle (dense, frequent flooding)"),
    "ikeja": (6.5900, 3.3300, 6.6080, 3.3550, "Ikeja GRA and Allen"),
    "yaba": (6.4980, 3.3700, 6.5150, 3.3900, "Yaba and Unilag lagoon front"),
}


def parse_height(tags: dict) -> Optional[float]:
    for key in ("height", "building:height"):
        v = tags.get(key)
        if v:
            m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", str(v))
            if m:
                h = float(m.group(1))
                if "ft" in str(v) or "'" in str(v):
                    h *= 0.3048
                if 1.0 <= h <= 500.0:
                    return h
    lv = tags.get("building:levels")
    if lv:
        m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", str(lv))
        if m and 0 < float(m.group(1)) < 150:
            return float(m.group(1)) * LEVEL_M + 1.0
    return None


def building_height(tags: dict) -> float:
    h = parse_height(tags)
    if h is not None:
        return h
    return DEFAULT_HEIGHT.get(tags.get("building", "yes"), DEFAULT_HEIGHT["yes"])


def polygon_area(poly: Sequence[Pt]) -> float:
    a = 0.0
    for (x1, y1), (x2, y2) in zip(poly, list(poly[1:]) + [poly[0]]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def point_in_poly(x: float, y: float, poly: Sequence[Pt]) -> bool:
    inside, n = False, len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def from_overpass(osm: dict, name: str, bbox: Tuple[float, float, float, float]) -> dict:
    """Convert an Overpass `out geom` JSON response into an area dict."""
    s, w, n, e = bbox
    origin = Origin((s + n) / 2.0, (w + e) / 2.0)
    buildings, water, roads = [], [], []
    for el in osm.get("elements", []):
        tags = el.get("tags") or {}
        geom = el.get("geometry")
        if not geom:
            continue
        pts = [origin.to_enu(g["lat"], g["lon"]) for g in geom]
        closed = len(pts) >= 4 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6
        if "building" in tags and closed:
            poly = pts[:-1]
            if polygon_area(poly) < 8.0:
                continue
            h = building_height(tags)
            base = parse_height({"height": tags.get("min_height")}) or 0.0
            buildings.append({"id": str(el.get("id")), "h": round(h, 1), "base": round(base, 1),
                              "kind": tags.get("building", "yes"),
                              "poly": [[round(x, 2), round(y, 2)] for x, y in poly]})
        elif closed and (tags.get("natural") == "water" or tags.get("waterway") == "riverbank"
                         or tags.get("landuse") == "reservoir"):
            water.append({"poly": [[round(x, 2), round(y, 2)] for x, y in pts[:-1]]})
        elif "highway" in tags and not closed:
            width = {"motorway": 14, "trunk": 12, "primary": 10, "secondary": 8, "tertiary": 7,
                     "residential": 6, "service": 4}.get(tags["highway"], 0)
            if width:
                roads.append({"w": width, "line": [[round(x, 2), round(y, 2)] for x, y in pts]})
    area = {"v": 1, "name": name, "origin": [origin.lat, origin.lon], "bbox": [s, w, n, e],
            "buildings": buildings, "water": water, "roads": roads}
    area["max_h"] = max([b["h"] for b in buildings], default=0.0)
    area["launch"] = list(find_launch_site(area))
    return area


@dataclass
class HeightGrid:
    """Max obstacle height per cell (metres above ground); 0 = open."""
    x0: float
    y0: float
    cell: float
    nx: int
    ny: int
    h: List[float]          # row-major, index = j * nx + i
    water: List[bool]

    def idx(self, x: float, y: float) -> Optional[int]:
        i, j = int((x - self.x0) // self.cell), int((y - self.y0) // self.cell)
        if 0 <= i < self.nx and 0 <= j < self.ny:
            return j * self.nx + i
        return None

    def height_at(self, x: float, y: float) -> float:
        k = self.idx(x, y)
        return self.h[k] if k is not None else 0.0

    def is_water(self, x: float, y: float) -> bool:
        k = self.idx(x, y)
        return self.water[k] if k is not None else False

    def centre(self, i: int, j: int) -> Pt:
        return (self.x0 + (i + 0.5) * self.cell, self.y0 + (j + 0.5) * self.cell)


def height_grid(area: dict, cell: float = 10.0, margin: float = 200.0, dilate: bool = True) -> HeightGrid:
    """Rasterise building footprints (dilated by one cell for clearance unless dilate=False)."""
    xs = [p[0] for b in area["buildings"] for p in b["poly"]] or [0.0]
    ys = [p[1] for b in area["buildings"] for p in b["poly"]] or [0.0]
    x0, y0 = min(xs) - margin, min(ys) - margin
    nx = int(math.ceil((max(xs) + margin - x0) / cell))
    ny = int(math.ceil((max(ys) + margin - y0) / cell))
    h = [0.0] * (nx * ny)
    for b in area["buildings"]:
        poly = b["poly"]
        bx0, bx1 = min(p[0] for p in poly), max(p[0] for p in poly)
        by0, by1 = min(p[1] for p in poly), max(p[1] for p in poly)
        i0, i1 = int((bx0 - x0) // cell), int((bx1 - x0) // cell)
        j0, j1 = int((by0 - y0) // cell), int((by1 - y0) // cell)
        for j in range(max(0, j0), min(ny, j1 + 1)):
            for i in range(max(0, i0), min(nx, i1 + 1)):
                cx, cy = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
                hit = point_in_poly(cx, cy, poly) or any(
                    abs(px - cx) <= cell / 2 and abs(py - cy) <= cell / 2 for px, py in poly)
                if hit:
                    k = j * nx + i
                    h[k] = max(h[k], b["h"])
    # dilate one cell: keep wing tips clear of walls
    dil = list(h)
    for j in range(ny if dilate else 0):
        for i in range(nx):
            v = h[j * nx + i]
            if v <= 0:
                continue
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < nx and 0 <= jj < ny:
                        dil[jj * nx + ii] = max(dil[jj * nx + ii], v)
    water = [False] * (nx * ny)
    for wpoly in area.get("water", []):
        poly = wpoly["poly"]
        bx0, bx1 = min(p[0] for p in poly), max(p[0] for p in poly)
        by0, by1 = min(p[1] for p in poly), max(p[1] for p in poly)
        for j in range(max(0, int((by0 - y0) // cell)), min(ny, int((by1 - y0) // cell) + 1)):
            for i in range(max(0, int((bx0 - x0) // cell)), min(nx, int((bx1 - x0) // cell) + 1)):
                if point_in_poly(x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell, poly):
                    water[j * nx + i] = True
    return HeightGrid(x0, y0, cell, nx, ny, dil, water)


def corridor_max_height(grid: "HeightGrid", a: Pt, b: Pt, half_width: float = 15.0) -> float:
    """Tallest obstacle within half_width of the straight segment a->b (e.g. an autopilot's RTL path)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    n = max(1, int(d / (grid.cell / 2)))
    ux, uy = (dx / d, dy / d) if d > 1e-6 else (1.0, 0.0)
    best = 0.0
    k = max(1, int(half_width / (grid.cell / 2)))
    for i in range(n + 1):
        x, y = a[0] + dx * i / n, a[1] + dy * i / n
        for j in range(-k, k + 1):
            off = half_width * j / k
            best = max(best, grid.height_at(x - uy * off, y + ux * off))
    return best


def find_launch_site(area: dict, clear_m: float = 40.0) -> Pt:
    """Open dry ground near the centre with no building within clear_m (a square, a field)."""
    if not area["buildings"]:
        return (0.0, 0.0)
    g = height_grid(area, cell=10.0, margin=60.0)
    r = int(math.ceil(clear_m / g.cell))
    best, best_d = None, 1e18
    for j in range(r, g.ny - r):
        for i in range(r, g.nx - r):
            if g.water[j * g.nx + i]:
                continue
            ok = True
            for dj in range(-r, r + 1):
                row = (j + dj) * g.nx
                for di in range(-r, r + 1):
                    if g.h[row + i + di] > 0:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                cx, cy = g.centre(i, j)
                d = cx * cx + cy * cy
                if d < best_d:
                    best, best_d = (cx, cy), d
    return best or (0.0, 0.0)


def load_area(path: str) -> dict:
    with open(path) as f:
        a = json.load(f)
    if a.get("v") != 1:
        raise ValueError(f"unsupported area file version in {path}")
    return a


def save_area(area: dict, path: str):
    with open(path, "w") as f:
        json.dump(area, f, separators=(",", ":"))


def synthetic_city(blocks: int = 6, block_m: float = 120.0, street_m: float = 30.0,
                   seed: int = 0, tall_every: int = 5) -> dict:
    """A grid city for tests and the simulator: blocks of buildings, a few towers, a square."""
    import random
    rnd = random.Random(seed)
    b, k = [], 0
    off = blocks * (block_m + street_m) / 2.0
    for bi in range(blocks):
        for bj in range(blocks):
            if (bi, bj) == (blocks // 2, blocks // 2):
                continue                      # central square = launch site
            x0 = bi * (block_m + street_m) - off
            y0 = bj * (block_m + street_m) - off
            for q in range(4):
                qx, qy = x0 + (q % 2) * block_m / 2 + 5, y0 + (q // 2) * block_m / 2 + 5
                s = block_m / 2 - 10
                k += 1
                tall = k % tall_every == 0
                h = rnd.uniform(60, 110) if tall else rnd.uniform(8, 24)
                b.append({"id": f"b{k}", "h": round(h, 1), "base": 0.0, "kind": "office" if tall else "yes",
                          "poly": [[qx, qy], [qx + s, qy], [qx + s, qy + s], [qx, qy + s]]})
    # street grid along the gaps between blocks; every crossing is a shared vertex (like OSM nodes)
    lines = [bi * (block_m + street_m) - off - street_m / 2 for bi in range(blocks + 1)]
    roads = []
    for c in lines:
        roads.append({"w": 10, "line": [[c, v] for v in lines]})       # north-south street
        roads.append({"w": 10, "line": [[v, c] for v in lines]})       # east-west street
    area = {"v": 1, "name": "synthetic", "origin": [6.4525, 3.3935], "bbox": [0, 0, 0, 0],
            "buildings": b, "water": [], "roads": roads}
    area["max_h"] = max(x["h"] for x in b)
    area["launch"] = list(find_launch_site(area))
    return area
