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
    """Battery-percent cost model, self-calibrating in flight.

    `scale` multiplies the configured costs. DrainCalibrator measures the
    real drain against what the model predicted and adjusts it, so a drone
    with a worn battery, a heavier payload or a different airframe stops
    bidding on work it can no longer afford.
    """

    MIN_SCALE, MAX_SCALE = 0.5, 8.0

    def __init__(self, cfg: EnergyCfg):
        self.cfg = cfg
        self.scale = 1.0

    def travel_pct(self, dist_m: float, wind_mps: float = 0.0) -> float:
        per_m = self.cfg.pct_per_m + max(0.0, wind_mps) * self.cfg.pct_per_mps_wind_per_km / 1000.0
        return max(0.0, dist_m) * per_m * self.scale

    def hover_pct(self, seconds: float) -> float:
        return max(0.0, seconds) * self.cfg.pct_per_s_hover * self.scale

    def raw_rate_pct_s(self, speed_mps: float) -> float:
        """Uncalibrated predicted drain rate at a given ground speed."""
        return self.cfg.pct_per_s_hover + max(0.0, speed_mps) * self.cfg.pct_per_m

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


class DrainCalibrator:
    """Learn the ratio real/predicted battery drain from own telemetry.

    Autopilots report battery in whole percent, so a measurement is taken
    only once the battery has dropped by `min_drop_pct` since the anchor.
    The result is an exponentially-weighted ratio applied to EnergyModel.scale.
    """

    def __init__(self, model: EnergyModel, min_drop_pct: float = 2.0, alpha: float = 0.5,
                 min_window_s: float = 10.0):
        self.model = model
        self.min_drop = min_drop_pct
        self.alpha = alpha
        self.min_window_s = min_window_s
        self._anchor = None          # (t, battery)
        self._predicted = 0.0        # raw predicted % since anchor
        self._last_t = None
        self.samples = 0

    def update(self, t: float, battery: float, speed_mps: float, airborne: bool):
        if not airborne or battery < 0:
            self._anchor, self._last_t, self._predicted = None, None, 0.0
            return
        if self._anchor is None:
            self._anchor, self._last_t, self._predicted = (t, battery), t, 0.0
            return
        dt = max(0.0, t - self._last_t)
        self._last_t = t
        self._predicted += self.model.raw_rate_pct_s(speed_mps) * dt
        t0, b0 = self._anchor
        drop = b0 - battery
        if battery > b0:                       # battery swap / sensor jump: restart
            self._anchor, self._predicted = (t, battery), 0.0
            return
        if drop >= self.min_drop and t - t0 >= self.min_window_s and self._predicted > 1e-6:
            ratio = drop / self._predicted
            ratio = max(EnergyModel.MIN_SCALE, min(EnergyModel.MAX_SCALE, ratio))
            # first sample is trusted more: a badly wrong prior is the dangerous case
            a = 0.8 if self.samples == 0 else self.alpha
            self.model.scale = (1 - a) * self.model.scale + a * ratio
            self.samples += 1
            self._anchor, self._predicted = (t, battery), 0.0
