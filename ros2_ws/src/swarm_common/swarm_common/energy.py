"""One energy model for the whole drone.

The SAME function decides (a) whether a drone may bid on a task and
(b) whether it must give a task up. Using one model for both removes the
old assign-then-immediately-relinquish thrash, where the auction used a
15 %/4 %-per-km rule and the agent a 30 %/5 %-per-km rule.
"""
import math
from typing import Iterable, Sequence, Tuple

from .config import EnergyCfg

Point = Tuple[float, float]


class EnergyModel:
    def __init__(self, cfg: EnergyCfg):
        self.cfg = cfg

    def travel_pct(self, dist_m: float, wind_mps: float = 0.0) -> float:
        per_m = self.cfg.pct_per_m + max(0.0, wind_mps) * self.cfg.pct_per_mps_wind_per_km / 1000.0
        return max(0.0, dist_m) * per_m

    def hover_pct(self, seconds: float) -> float:
        return max(0.0, seconds) * self.cfg.pct_per_s_hover

    def plan_pct(self, start: Point, legs: Iterable[Tuple[Point, float]], home: Point,
                 wind_mps: float = 0.0) -> float:
        """Energy for: start -> each (point, hold_s) in order -> home."""
        total, cur = 0.0, start
        for pt, hold_s in legs:
            total += self.travel_pct(math.hypot(pt[0] - cur[0], pt[1] - cur[1]), wind_mps)
            total += self.hover_pct(hold_s)
            cur = pt
        total += self.travel_pct(math.hypot(home[0] - cur[0], home[1] - cur[1]), wind_mps)
        return total

    def margin(self, battery_pct: float, plan_pct: float) -> float:
        """Battery left above the landing reserve after the plan (may be < 0)."""
        return battery_pct - plan_pct - self.cfg.reserve_pct

    def feasible(self, battery_pct: float, plan_pct: float) -> bool:
        return self.margin(battery_pct, plan_pct) >= 0.0

    def must_go_home(self, battery_pct: float, pos: Point, home: Point,
                     wind_mps: float = 0.0) -> bool:
        """True when only the trip home (+reserve) is still affordable."""
        return not self.feasible(battery_pct, self.plan_pct(pos, [], home, wind_mps))

    def critical(self, battery_pct: float) -> bool:
        return battery_pct < self.cfg.critical_pct


def path_length(points: Sequence[Point]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))
