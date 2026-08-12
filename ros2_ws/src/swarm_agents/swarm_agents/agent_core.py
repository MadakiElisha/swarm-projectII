"""Pure, pytest-testable mini-agent core: sense-model-decide.
Deterministic spine; probabilistic advisors may layer on top later."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Belief:
    label: str
    battery_pct: float
    alt: float
    current_task: Optional[str] = None
    neighbor_count: int = 0
    distance_home_m: float = 0.0


@dataclass
class Relinquish:
    task_id: str
    reason: str


@dataclass
class ReturnHome:
    reason: str
    
    
class DroneAgent:
    """Adaptive but deterministic: reserve grows with distance from home
    (~0.005 %/m ≈ 5 %/km, real multirotor cruise energetics)."""

    def __init__(self, reserve_pct: float = 30.0, critical_pct: float = 15.0,
                 pct_per_meter: float = 0.005):
        self.reserve_pct = reserve_pct
        self.critical_pct = critical_pct
        self.pct_per_meter = pct_per_meter

    def effective_reserve(self, b: Belief) -> float:
        return self.reserve_pct + self.pct_per_meter * b.distance_home_m

    def step(self, b: Belief) -> List[object]:
        intents: List[object] = []
        if b.battery_pct < self.critical_pct:
            intents.append(ReturnHome(reason='critical_battery'))
        elif b.current_task is not None and b.battery_pct < self.effective_reserve(b):
            intents.append(Relinquish(
                task_id=b.current_task,
                reason=f'low_battery (need {self.effective_reserve(b):.0f}% at '
                       f'{b.distance_home_m / 1000.0:.1f} km from home)'))
        return intents
