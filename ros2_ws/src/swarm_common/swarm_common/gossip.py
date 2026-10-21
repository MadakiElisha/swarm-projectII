"""Neighbour discovery and the replicated swarm roster.

* NeighborTable: who I can hear *directly*, with link quality measured from
  packet sequence numbers (packet-receipt ratio), not inferred from GPS.
* Roster: a last-writer-wins map (per drone) of everyone's self-reported
  state, relayed multi-hop by gossip. Each drone only ever writes its OWN
  entry, so LWW-by-timestamp is conflict-free.
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional


@dataclass
class LinkStats:
    first_seq: int
    last_seq: int
    received: int
    last_seen: float
    # recent window for packet-receipt ratio
    window: List[int] = field(default_factory=list)

    def prr(self) -> float:
        """Fraction of the recent sequence range that actually arrived."""
        if not self.window:
            return 0.0
        span = self.window[-1] - self.window[0] + 1
        return min(1.0, len(self.window) / max(1, span))


class NeighborTable:
    WINDOW = 20

    def __init__(self, timeout_s: float):
        self.timeout_s = timeout_s
        self.links: Dict[int, LinkStats] = {}

    def heard(self, src: int, seq: int, now: float):
        ls = self.links.get(src)
        if ls is None or seq < ls.last_seq - 1000:      # new peer or peer rebooted
            ls = LinkStats(seq, seq, 0, now)
            self.links[src] = ls
        if seq in ls.window:
            return                                       # duplicate
        ls.received += 1
        ls.last_seq = max(ls.last_seq, seq)
        ls.last_seen = now
        ls.window.append(seq)
        ls.window.sort()
        del ls.window[:-self.WINDOW]

    def neighbors(self, now: float) -> List[int]:
        return sorted(k for k, v in self.links.items() if now - v.last_seen <= self.timeout_s)

    def quality(self, src: int, now: float) -> float:
        ls = self.links.get(src)
        if ls is None or now - ls.last_seen > self.timeout_s:
            return 0.0
        return ls.prr()


@dataclass
class RosterEntry:
    id: int
    t: float                 # time the drone itself wrote this entry
    x: float
    y: float
    z: float
    vx: float = 0.0
    vy: float = 0.0
    battery: float = 100.0
    phase: str = "IDLE"      # IDLE / ENROUTE / ON_TASK / ON_STATION / RTB / LANDED / FAILSAFE
    task: str = ""           # work item currently executed
    airborne: bool = False
    available: bool = True   # willing to accept work
    drain: float = 1.0       # learned battery drain vs model (energy calibration)

    def to_wire(self) -> dict:
        return asdict(self)


class Roster:
    def __init__(self):
        self.entries: Dict[int, RosterEntry] = {}

    def update(self, e: RosterEntry) -> bool:
        cur = self.entries.get(e.id)
        if cur is None or e.t > cur.t:
            self.entries[e.id] = e
            return True
        return False

    def merge(self, wire: List[dict]) -> bool:
        changed = False
        known = set(RosterEntry.__dataclass_fields__)
        for d in wire:
            try:
                # ignore fields from newer peers instead of dropping the entry
                changed |= self.update(RosterEntry(**{k: v for k, v in d.items() if k in known}))
            except (TypeError, AttributeError):
                continue
        return changed

    def alive(self, now: float, max_age_s: float) -> List[int]:
        return sorted(i for i, e in self.entries.items() if now - e.t <= max_age_s)

    def get(self, i: int) -> Optional[RosterEntry]:
        return self.entries.get(i)

    def to_wire(self) -> List[dict]:
        return [e.to_wire() for e in self.entries.values()]
