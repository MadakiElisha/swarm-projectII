"""Replicated task registry (a state-based CRDT) + derived work items.

There is NO task server. Any drone that hears an operator request (or makes
a perception-based suggestion) inserts the task into its local registry, and
registries are merged pairwise by gossip. The merge is commutative,
associative and idempotent, so every drone converges to the same task set
regardless of message order, loss or duplication:

  * definition fields: the version with the smallest (created_t, creator) wins
  * status: monotone lattice SUGGESTED < OPEN < DONE < CANCELLED < MERGED

Composite tasks (formations, intercepts) are stored ONCE as a parent; their
per-drone slots are *derived* deterministically, so all drones agree on the
slot list without exchanging it.
"""
import math
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, Iterable, List, Optional, Tuple

SUGGESTED, OPEN, DONE, CANCELLED, MERGED = "SUGGESTED", "OPEN", "DONE", "CANCELLED", "MERGED"
STATUS_RANK = {SUGGESTED: 0, OPEN: 1, DONE: 2, CANCELLED: 3, MERGED: 4}
TERMINAL = {DONE, CANCELLED, MERGED}

GOTO, RESCUE, FORMATION, INTERCEPT, SEARCH = "GOTO", "RESCUE", "FORMATION", "INTERCEPT", "SEARCH"
KINDS = {GOTO, RESCUE, FORMATION, INTERCEPT, SEARCH}

DEFAULT_HOLD_S = {GOTO: 60.0, RESCUE: 120.0}


@dataclass
class Task:
    id: str
    kind: str
    x: float
    y: float
    created_t: float
    creator: int
    status: str = OPEN
    status_t: float = 0.0
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown task kind {self.kind}")
        if self.status not in STATUS_RANK:
            raise ValueError(f"unknown task status {self.status}")

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL

    def def_key(self):
        return (self.created_t, self.creator, self.id)

    def to_wire(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_wire(d: dict) -> "Task":
        return Task(**d)


def merge_task(a: Task, b: Task) -> Task:
    """CRDT join of two versions of the same task."""
    assert a.id == b.id
    base = a if a.def_key() <= b.def_key() else b
    ra, rb = STATUS_RANK[a.status], STATUS_RANK[b.status]
    if ra != rb:
        st = a if ra > rb else b
    else:
        st = a if a.status_t >= b.status_t else b
    params = dict(base.params)
    if st.params.get("merged_into"):
        params["merged_into"] = st.params["merged_into"]
    return Task(id=base.id, kind=base.kind, x=base.x, y=base.y, created_t=base.created_t,
                creator=base.creator, status=st.status, status_t=st.status_t, params=params)


class TaskRegistry:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.version = 0          # bumps on any change (cheap change detection)

    def __contains__(self, tid):
        return tid in self.tasks

    def get(self, tid) -> Optional[Task]:
        return self.tasks.get(tid)

    def upsert(self, t: Task) -> bool:
        cur = self.tasks.get(t.id)
        new = t if cur is None else merge_task(cur, t)
        if cur is None or new != cur:
            self.tasks[t.id] = new
            self.version += 1
            return True
        return False

    def merge(self, wire_tasks: Iterable[dict]) -> bool:
        changed = False
        for d in wire_tasks:
            try:
                changed |= self.upsert(Task.from_wire(d))
            except (TypeError, ValueError):
                continue   # malformed entries from the network never break the registry
        return changed

    def set_status(self, tid: str, status: str, now: float, **params) -> bool:
        cur = self.tasks.get(tid)
        if cur is None or STATUS_RANK[status] < STATUS_RANK[cur.status]:
            return False
        p = dict(cur.params)
        p.update(params)
        return self.upsert(Task(cur.id, cur.kind, cur.x, cur.y, cur.created_t, cur.creator,
                                status, now, p))

    def active(self) -> List[Task]:
        return [t for t in self.tasks.values() if not t.terminal]

    def to_wire(self, max_terminal_age_s: Optional[float] = None, now: float = 0.0) -> List[dict]:
        out = []
        for t in self.tasks.values():
            if (max_terminal_age_s is not None and t.terminal
                    and now - t.status_t > max_terminal_age_s):
                continue
            out.append(t.to_wire())
        return out

    def resolve_duplicates(self, kind: str, radius_m: float, now: float) -> List[str]:
        """Deterministically fold near-duplicate tasks of `kind` into the oldest one.

        Two drones that see the same survivor create two RESCUE tasks before
        gossip reaches them. Every drone runs this same rule on the same set,
        so they agree which one survives. Returns ids newly marked MERGED.
        """
        live = sorted((t for t in self.tasks.values() if t.kind == kind and not t.terminal),
                      key=Task.def_key)
        kept: List[Task] = []
        merged = []
        for t in live:
            twin = next((k for k in kept if math.hypot(k.x - t.x, k.y - t.y) <= radius_m), None)
            if twin is None:
                kept.append(t)
                continue
            if STATUS_RANK[t.status] > STATUS_RANK[twin.status]:   # confirmed beats suggested
                self.set_status(twin.id, t.status, now)
            self.set_status(t.id, MERGED, now, merged_into=twin.id)
            merged.append(t.id)
        return merged


# ----------------------------------------------------------------------
# derived work items: the things CBBA actually allocates
# ----------------------------------------------------------------------
@dataclass
class WorkItem:
    id: str                 # unique; slots are "<parent>/s<i>"
    parent: str
    kind: str
    x: float
    y: float
    hold_s: float
    reward: float = 100.0
    group: str = ""         # a drone may hold at most one item per group
    slot: int = -1
    n_slots: int = 0


def ring_slot_xy(cx, cy, radius, slot, n_slots, t, created_t, period_s):
    """Slot position on a ring rotating with period_s (shared clock -> all agree)."""
    th = 2 * math.pi * slot / max(1, n_slots) + 2 * math.pi * (t - created_t) / period_s
    return cx + radius * math.cos(th), cy + radius * math.sin(th)


def derive_work_items(reg: TaskRegistry, now: float, formation_cfg,
                      centre_of: Callable[[Task], Optional[Tuple[float, float]]] = None
                      ) -> Dict[str, WorkItem]:
    """Expand the registry into allocatable work items (pure + deterministic)."""
    items: Dict[str, WorkItem] = {}
    for t in reg.active():
        if t.status != OPEN:
            continue          # SUGGESTED tasks wait for a human; SEARCH is not auctioned
        if t.kind in (GOTO, RESCUE):
            hold = float(t.params.get("hold_s", DEFAULT_HOLD_S[t.kind]))
            reward = 150.0 if t.kind == RESCUE else 100.0
            items[t.id] = WorkItem(t.id, t.id, t.kind, t.x, t.y, hold, reward)
        elif t.kind in (FORMATION, INTERCEPT):
            n = int(t.params.get("n_slots", formation_cfg.max_slots))
            r = float(t.params.get("radius", formation_cfg.ring_radius_m))
            centre = (centre_of(t) if centre_of else None) or (t.x, t.y)
            for s in range(n):
                sx, sy = ring_slot_xy(centre[0], centre[1], r, s, n, now, t.created_t,
                                      formation_cfg.ring_period_s)
                hold = max(0.0, float(t.params.get("expires_at", now)) - now)
                items[f"{t.id}/s{s}"] = WorkItem(f"{t.id}/s{s}", t.id, t.kind, sx, sy, hold,
                                                 reward=120.0, group=t.id, slot=s, n_slots=n)
    return items
