"""Decentralized area coverage for SEARCH tasks.

* The area is a grid of cells. Which cells have been seen is a grow-only set
  (G-Set CRDT) gossiped between drones and merged by union.
* Each participating drone computes the SAME partition of the remaining
  cells from the same inputs (sorted participant ids + covered set), takes
  its own share, and sweeps it boustrophedon-style. When a drone joins,
  leaves or dies, every survivor recomputes and the gap is re-covered.
"""
import math
from typing import Dict, Iterable, List, Optional, Set, Tuple

Cell = Tuple[int, int]


class CoverageGrid:
    def __init__(self, x0: float, y0: float, x1: float, y1: float, cell_m: float):
        self.x0, self.y0 = min(x0, x1), min(y0, y1)
        self.x1, self.y1 = max(x0, x1), max(y0, y1)
        self.cell = cell_m
        self.nx = max(1, int(math.ceil((self.x1 - self.x0) / cell_m)))
        self.ny = max(1, int(math.ceil((self.y1 - self.y0) / cell_m)))
        self.covered: Set[Cell] = set()
        self._bits = 0
        self._part_cache = None

    def all_cells(self) -> List[Cell]:
        return [(i, j) for i in range(self.nx) for j in range(self.ny)]

    def centre(self, c: Cell) -> Tuple[float, float]:
        return (self.x0 + (c[0] + 0.5) * self.cell, self.y0 + (c[1] + 0.5) * self.cell)

    def cell_of(self, x: float, y: float) -> Optional[Cell]:
        i, j = int((x - self.x0) // self.cell), int((y - self.y0) // self.cell)
        return (i, j) if 0 <= i < self.nx and 0 <= j < self.ny else None

    def mark_footprint(self, x: float, y: float, radius_m: float) -> bool:
        """Mark every cell whose centre is inside the sensor footprint."""
        changed = False
        r = int(math.ceil(radius_m / self.cell))
        c = self.cell_of(x, y)
        if c is None:
            return False
        for i in range(c[0] - r, c[0] + r + 1):
            for j in range(c[1] - r, c[1] + r + 1):
                if 0 <= i < self.nx and 0 <= j < self.ny and (i, j) not in self.covered:
                    cx, cy = self.centre((i, j))
                    if math.hypot(cx - x, cy - y) <= radius_m:
                        self.covered.add((i, j))
                        self._bits |= 1 << (i * self.ny + j)
                        changed = True
        return changed

    def merge(self, wire) -> bool:
        """Union with a peer's covered set (hex bitmap, or a list of [i, j])."""
        before = len(self.covered)
        if isinstance(wire, str):
            try:
                bits = int(wire, 16) if wire else 0
            except ValueError:
                return False
            if bits == self._bits:
                return False
            new = bits & ~self._bits
            k = 0
            while new:
                if new & 1:
                    i, j = divmod(k, self.ny)
                    if i < self.nx:
                        self.covered.add((i, j))
                new >>= 1
                k += 1
        else:
            for c in wire or []:
                try:
                    i, j = int(c[0]), int(c[1])
                except (TypeError, ValueError, IndexError):
                    continue
                if 0 <= i < self.nx and 0 <= j < self.ny:
                    self.covered.add((i, j))
        if len(self.covered) != before:
            self._sync_bits()
            return True
        return False

    def _sync_bits(self):
        b = 0
        for i, j in self.covered:
            b |= 1 << (i * self.ny + j)
        self._bits = b

    def remaining(self) -> List[Cell]:
        return [c for c in self.all_cells() if c not in self.covered]

    def fraction(self) -> float:
        return len(self.covered) / float(self.nx * self.ny)

    def to_wire(self) -> str:
        """Compact hex bitmap (bit i*ny+j set = cell (i, j) covered)."""
        return format(self._bits, "x")


def partition(grid: CoverageGrid, participants: List[int]) -> Dict[int, List[Cell]]:
    """Split remaining cells into contiguous column strips, one per participant.

    Deterministic: same participants + same covered set -> same answer on
    every drone. Cells are ordered column by column in a serpentine, so each
    share is a compact, sweepable strip.
    """
    key = (tuple(sorted(participants)), len(grid.covered))
    if grid._part_cache is not None and grid._part_cache[0] == key:
        return grid._part_cache[1]
    order: List[Cell] = []
    for i in range(grid.nx):
        col = range(grid.ny) if i % 2 == 0 else range(grid.ny - 1, -1, -1)
        order.extend((i, j) for j in col if (i, j) not in grid.covered)
    ps = sorted(participants)
    out: Dict[int, List[Cell]] = {p: [] for p in ps}
    if not ps or not order:
        return out
    k = len(ps)
    for idx, p in enumerate(ps):
        a = idx * len(order) // k
        b = (idx + 1) * len(order) // k
        out[p] = order[a:b]
    grid._part_cache = (key, out)
    return out


def next_waypoint(grid: CoverageGrid, share: List[Cell], pos: Tuple[float, float]):
    """Next cell to visit in my share: start at the nearer end, then follow order."""
    if not share:
        return None
    first, last = grid.centre(share[0]), grid.centre(share[-1])
    if math.hypot(last[0] - pos[0], last[1] - pos[1]) < math.hypot(first[0] - pos[0], first[1] - pos[1]):
        return grid.centre(share[-1])
    return grid.centre(share[0])
