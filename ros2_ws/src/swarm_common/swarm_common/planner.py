"""Building-aware path planning on the area height grid.

Each drone plans for its OWN altitude layer: cells whose obstacle height is
above (altitude - clearance) are blocked. A* on an 8-connected grid, then
line-of-sight smoothing so drones fly straight legs between corners.
ORCA still handles drone-drone avoidance on top of this.
"""
import heapq
import math
from typing import List, Optional, Tuple

from .area import HeightGrid

Pt = Tuple[float, float]
SQ2 = math.sqrt(2.0)


class Planner:
    def __init__(self, grid: HeightGrid, clearance_m: float = 8.0, max_expand: int = 60000):
        self.g = grid
        self.clear = clearance_m
        self.max_expand = max_expand

    def blocked(self, i: int, j: int, alt: float) -> bool:
        g = self.g
        if not (0 <= i < g.nx and 0 <= j < g.ny):
            return False                         # outside the mapped area: open
        return g.h[j * g.nx + i] > alt - self.clear

    def roof_top(self, p: Pt) -> float:
        """Tallest roof in my cell and its neighbours (0 over open ground)."""
        ci, cj = self._cell(p)
        g, top = self.g, 0.0
        for j in range(cj - 1, cj + 2):
            for i in range(ci - 1, ci + 2):
                if 0 <= i < g.nx and 0 <= j < g.ny:
                    top = max(top, g.h[j * g.nx + i])
        return top

    def _cell(self, p: Pt) -> Tuple[int, int]:
        return int((p[0] - self.g.x0) // self.g.cell), int((p[1] - self.g.y0) // self.g.cell)

    def line_clear(self, a: Pt, b: Pt, alt: float) -> bool:
        """Sample the segment at quarter-cell steps."""
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / (self.g.cell * 0.25)))
        for k in range(n + 1):
            t = k / n
            i, j = self._cell((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            if self.blocked(i, j, alt):
                return False
        return True

    def nearest_free(self, p: Pt, alt: float, max_r: int = 30) -> Pt:
        ci, cj = self._cell(p)
        if not self.blocked(ci, cj, alt):
            return p
        for r in range(1, max_r):
            best = None
            for dj in range(-r, r + 1):
                for di in (-r, r) if abs(dj) != r else range(-r, r + 1):
                    if not self.blocked(ci + di, cj + dj, alt):
                        c = self.g.centre(ci + di, cj + dj)
                        dd = math.hypot(c[0] - p[0], c[1] - p[1])
                        if best is None or dd < best[0]:
                            best = (dd, c)
            if best:
                return best[1]
        return p

    def plan(self, start: Pt, goal: Pt, alt: float) -> Optional[List[Pt]]:
        """Waypoints from start to goal (excluding start). None if unreachable."""
        if self.line_clear(start, goal, alt):
            return [goal]
        goal = self.nearest_free(goal, alt)
        s, t = self._cell(start), self._cell(goal)
        openq = [(0.0, 0.0, s)]
        came = {s: None}
        cost = {s: 0.0}
        expanded = 0
        while openq:
            _, gc, cur = heapq.heappop(openq)
            if cur == t:
                break
            if gc > cost.get(cur, 1e18) + 1e-9:
                continue
            expanded += 1
            if expanded > self.max_expand:
                return None
            ci, cj = cur
            for di, dj, w in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1),
                              (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)):
                ni, nj = ci + di, cj + dj
                if self.blocked(ni, nj, alt) and (ni, nj) != t:
                    continue
                if di and dj and (self.blocked(ci + di, cj, alt) or self.blocked(ci, cj + dj, alt)):
                    continue                     # no corner cutting
                nc = gc + w
                if nc < cost.get((ni, nj), 1e18):
                    cost[(ni, nj)] = nc
                    came[(ni, nj)] = cur
                    h = math.hypot(ni - t[0], nj - t[1])
                    heapq.heappush(openq, (nc + h, nc, (ni, nj)))
        if t not in came:
            return None
        cells = []
        c = t
        while c is not None:
            cells.append(c)
            c = came[c]
        cells.reverse()
        pts = [start] + [self.g.centre(i, j) for i, j in cells[1:-1]] + [goal]
        # line-of-sight smoothing
        out, k = [], 0
        while k < len(pts) - 1:
            far = len(pts) - 1
            while far > k + 1 and not self.line_clear(pts[k], pts[far], alt):
                far -= 1
            out.append(pts[far])
            k = far
        return out


def path_length(start: Pt, wps: List[Pt]) -> float:
    total, cur = 0.0, start
    for p in wps:
        total += math.hypot(p[0] - cur[0], p[1] - cur[1])
        cur = p
    return total
