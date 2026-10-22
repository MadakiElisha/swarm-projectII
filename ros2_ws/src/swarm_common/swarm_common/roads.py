"""Road graph from the area's OSM roads: lets simulated vehicles drive on streets.

Used only by simulation props (the moving target / intruder). Pure Python.
"""
import heapq
import math
import random
from typing import Dict, List, Optional, Tuple

Pt = Tuple[float, float]


class RoadGraph:
    def __init__(self, roads: List[dict], snap_m: float = 4.0):
        self.nodes: List[Pt] = []
        self.adj: Dict[int, List[int]] = {}
        self._grid: Dict[Tuple[int, int], List[int]] = {}
        self.snap = snap_m
        for r in roads:
            line = r.get("line") or []
            prev = None
            for p in line:
                k = self._node((float(p[0]), float(p[1])))
                if prev is not None and prev != k:
                    self.adj.setdefault(prev, []).append(k)
                    self.adj.setdefault(k, []).append(prev)
                prev = k

    def _cell(self, p: Pt):
        return int(p[0] // self.snap), int(p[1] // self.snap)

    def _node(self, p: Pt) -> int:
        cx, cy = self._cell(p)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k in self._grid.get((cx + dx, cy + dy), []):
                    q = self.nodes[k]
                    if math.hypot(q[0] - p[0], q[1] - p[1]) <= self.snap:
                        return k
        self.nodes.append(p)
        k = len(self.nodes) - 1
        self._grid.setdefault((cx, cy), []).append(k)
        return k

    def nearest(self, p: Pt) -> Optional[int]:
        if not self.nodes:
            return None
        return min(range(len(self.nodes)),
                   key=lambda k: (self.nodes[k][0] - p[0]) ** 2 + (self.nodes[k][1] - p[1]) ** 2)

    def drive(self, start: Pt, length_m: float, rnd: Optional[random.Random] = None,
              heading: Optional[float] = None) -> List[Pt]:
        """A plausible drive along streets from near `start`, about length_m long:
        prefer going straight at junctions, never U-turn unless at a dead end."""
        rnd = rnd or random.Random(0)
        k = self.nearest(start)
        if k is None:
            return [start]
        path = [self.nodes[k]]
        prev, done = None, 0.0
        while done < length_m:
            nbrs = [n for n in self.adj.get(k, []) if n != prev] or self.adj.get(k, [])
            if not nbrs:
                break
            cur = self.nodes[k]
            if heading is None and prev is None:
                nxt = rnd.choice(nbrs)
            else:
                h = heading if prev is None else math.atan2(cur[1] - self.nodes[prev][1],
                                                            cur[0] - self.nodes[prev][0])

                def turn(n):
                    q = self.nodes[n]
                    a = math.atan2(q[1] - cur[1], q[0] - cur[0]) - h
                    return abs(math.atan2(math.sin(a), math.cos(a)))
                nbrs.sort(key=turn)
                nxt = nbrs[0] if rnd.random() < 0.7 or len(nbrs) == 1 else rnd.choice(nbrs[1:])
            q = self.nodes[nxt]
            done += math.hypot(q[0] - cur[0], q[1] - cur[1])
            path.append(q)
            prev, k = k, nxt
        return path

    def shortest(self, a: Pt, b: Pt) -> List[Pt]:
        s, g = self.nearest(a), self.nearest(b)
        if s is None or g is None:
            return [a, b]
        dist, back, pq = {s: 0.0}, {}, [(0.0, s)]
        while pq:
            d, k = heapq.heappop(pq)
            if k == g:
                break
            if d > dist.get(k, 1e18):
                continue
            for n in self.adj.get(k, []):
                nd = d + math.hypot(self.nodes[n][0] - self.nodes[k][0], self.nodes[n][1] - self.nodes[k][1])
                if nd < dist.get(n, 1e18):
                    dist[n], back[n] = nd, k
                    heapq.heappush(pq, (nd, n))
        if g not in dist:
            return [a, b]
        out, k = [self.nodes[g]], g
        while k != s:
            k = back[k]
            out.append(self.nodes[k])
        return out[::-1]


def along(path: List[Pt], s: float) -> Tuple[Pt, float]:
    """Point and heading (rad, ENU) at arc length s along a polyline."""
    if len(path) < 2:
        return (path[0] if path else (0.0, 0.0)), 0.0
    for a, b in zip(path, path[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if s <= seg:
            t = min(1.0, s / seg) if seg > 1e-9 else 1.0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        s -= seg
    a, b = path[-2], path[-1]
    return b, math.atan2(b[1] - a[1], b[0] - a[0])
