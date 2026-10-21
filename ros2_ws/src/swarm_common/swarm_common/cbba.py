"""Consensus-Based Bundle Algorithm (CBBA) - leaderless task allocation.

Reference: H.-L. Choi, L. Brunet, J. P. How, "Consensus-Based Decentralized
Auctions for Robust Task Allocation", IEEE Trans. Robotics 25(4), 2009.

Every drone runs one CBBA instance. There is no auctioneer and no leader:

  Phase 1 (bundle building)  - each drone scores work items with ITS OWN
      state (position, battery, wind) and greedily claims the ones where it
      would beat the best bid it currently knows of.
  Phase 2 (consensus)        - drones exchange (winning bids y, winners z,
      info timestamps s) with whoever they can hear, and resolve conflicts
      with the CBBA decision table. Losing a task releases every task added
      to the bundle after it.

With a connected (even multi-hop, lossy) network this converges to a
conflict-free allocation; under partition each side converges on its own and
the sides reconcile automatically when the network heals.

Agent ids are positive ints; NONE (0) means "no winner".
"""
from typing import Callable, Dict, Iterable, List, Optional, Set

NONE = 0
EPS = 1e-9


def _higher(y1: float, z1: int, y2: float, z2: int) -> bool:
    """Total order on bids: larger value wins, ties go to the lower agent id."""
    if y1 > y2 + EPS:
        return True
    if abs(y1 - y2) <= EPS:
        if z1 == NONE:
            return False
        return z2 == NONE or z1 < z2
    return False


class CBBA:
    def __init__(self, agent_id: int, max_bundle: int = 1, rebid_margin: float = 0.0):
        if agent_id <= 0:
            raise ValueError("agent ids must be positive")
        self.i = agent_id
        self.L = max(1, int(max_bundle))
        self.margin = max(0.0, rebid_margin)
        self.y: Dict[str, float] = {}
        self.z: Dict[str, int] = {}
        self.s: Dict[int, float] = {}
        self.bundle: List[str] = []
        self.path: List[str] = []

    # ------------------------------------------------------------------ util
    def winner(self, j: str) -> int:
        return self.z.get(j, NONE)

    def assignments(self) -> Dict[str, int]:
        return {j: k for j, k in self.z.items() if k != NONE}

    def _reset(self, j: str):
        self.y[j] = 0.0
        self.z[j] = NONE

    def _drop_from(self, n: int):
        """Remove bundle[n:] from bundle and path.

        Items added AFTER bundle[n] were scored assuming bundle[n] would be
        done first, so any of them we still claim are reset (CBBA rule).
        bundle[n] itself keeps whatever winner consensus gave it.
        """
        tail = self.bundle[n:]
        for idx, j in enumerate(tail):
            if idx > 0 and self.z.get(j) == self.i:
                self._reset(j)
            if j in self.path:
                self.path.remove(j)
        del self.bundle[n:]

    # ------------------------------------------------------------- lifecycle
    def sync_items(self, item_ids: Iterable[str], alive: Optional[Set[int]] = None) -> bool:
        """Forget items that no longer exist and claims held by dead agents."""
        ids = set(item_ids)
        changed = False
        for j in list(self.z):
            if j not in ids:
                self.z.pop(j, None)
                self.y.pop(j, None)
                changed = True
            elif alive is not None and self.z[j] not in (NONE, self.i) and self.z[j] not in alive:
                self._reset(j)
                changed = True
        for n, j in enumerate(self.bundle):
            if j not in ids:
                self._drop_from(n)
                changed = True
                break
        return changed

    def release(self, j: str) -> bool:
        """Voluntarily give a task up (battery, completion, failsafe)."""
        if j in self.bundle:
            self._drop_from(self.bundle.index(j))
            if self.z.get(j) == self.i:
                self._reset(j)
            return True
        if self.z.get(j) == self.i:
            self._reset(j)
            return True
        return False

    def release_all(self) -> bool:
        changed = bool(self.bundle)
        while self.bundle:
            self.release(self.bundle[0])
        return changed

    # ------------------------------------------------------- phase 1: bundle
    def build_bundle(self, item_ids: Iterable[str],
                     path_score: Callable[[List[str]], Optional[float]],
                     group_of: Callable[[str], str] = lambda j: "",
                     now: float = 0.0) -> bool:
        """Greedy bundle construction.

        path_score(path) -> total score of executing `path` in order, or None
        if infeasible (e.g. not enough battery to do it and get home).
        """
        changed = False
        candidates = [j for j in sorted(item_ids)]
        while len(self.bundle) < self.L:
            base = path_score(self.path)
            if base is None:
                base = 0.0
            held_groups = {group_of(j) for j in self.bundle if group_of(j)}
            best_j, best_c, best_pos = None, 0.0, 0
            for j in candidates:
                if j in self.bundle:
                    continue
                g = group_of(j)
                if g and g in held_groups:
                    continue
                c_j, pos_j = 0.0, None
                for n in range(len(self.path) + 1):
                    cand = self.path[:n] + [j] + self.path[n:]
                    sc = path_score(cand)
                    if sc is None:
                        continue
                    if sc - base > c_j:
                        c_j, pos_j = sc - base, n
                if pos_j is None or c_j <= EPS:
                    continue
                if not self._can_outbid(j, c_j):
                    continue
                if best_j is None or _higher(c_j, self.i, best_c, self.i) or \
                        (abs(c_j - best_c) <= EPS and j < best_j):
                    best_j, best_c, best_pos = j, c_j, pos_j
            if best_j is None:
                break
            self.bundle.append(best_j)
            self.path.insert(best_pos, best_j)
            self.y[best_j] = best_c
            self.z[best_j] = self.i
            changed = True
        if changed:
            self.s[self.i] = now
        return changed

    def _can_outbid(self, j: str, c: float) -> bool:
        yj, zj = self.y.get(j, 0.0), self.z.get(j, NONE)
        if zj == NONE or yj <= EPS:
            return True
        if zj == self.i:
            return False
        # hysteresis: stealing a held task needs a clear improvement
        return _higher(c, self.i, yj * (1.0 + self.margin), zj)

    # ---------------------------------------------------- phase 2: consensus
    def message(self) -> dict:
        return {"y": dict(self.y), "z": dict(self.z), "s": {str(k): v for k, v in self.s.items()}}

    def receive(self, k: int, msg: dict, now: float, known_items: Optional[Set[str]] = None) -> bool:
        """Apply one neighbour's (y, z, s) using the CBBA decision table."""
        if k == self.i:
            return False
        i = self.i
        try:
            yk = {str(j): float(v) for j, v in msg.get("y", {}).items()}
            zk = {str(j): int(v) for j, v in msg.get("z", {}).items()}
            sk = {int(a): float(t) for a, t in msg.get("s", {}).items()}
        except (TypeError, ValueError, AttributeError):
            return False
        si = self.s
        changed = False

        def s_newer(m):            # sender has newer info about agent m than I do
            return sk.get(m, -1.0) > si.get(m, -1.0)

        for j in set(zk) | set(yk):
            if known_items is not None and j not in known_items:
                continue
            zkj, ykj = zk.get(j, NONE), yk.get(j, 0.0)
            zij, yij = self.z.get(j, NONE), self.y.get(j, 0.0)
            act = "leave"
            if zkj == k:
                if zij == i:
                    act = "update" if _higher(ykj, k, yij, i) else "leave"
                elif zij == k:
                    act = "update"
                elif zij == NONE:
                    act = "update"
                else:  # zij = m
                    m = zij
                    act = "update" if (s_newer(m) or _higher(ykj, k, yij, m)) else "leave"
            elif zkj == i:
                if zij == i:
                    act = "leave"
                elif zij == k:
                    act = "reset"
                elif zij == NONE:
                    act = "leave"
                else:
                    act = "reset" if s_newer(zij) else "leave"
            elif zkj == NONE:
                if zij == i:
                    act = "leave"
                elif zij == k:
                    act = "update"
                elif zij == NONE:
                    act = "leave"
                else:
                    act = "update" if s_newer(zij) else "leave"
            else:  # zkj = m (third party)
                m = zkj
                if zij == i:
                    act = "update" if (s_newer(m) and _higher(ykj, m, yij, i)) else "leave"
                elif zij == k:
                    act = "update" if s_newer(m) else "reset"
                elif zij == m:
                    act = "update" if s_newer(m) else "leave"
                elif zij == NONE:
                    act = "update" if s_newer(m) else "leave"
                else:  # zij = n, a fourth party
                    n = zij
                    if s_newer(m) and s_newer(n):
                        act = "update"
                    elif s_newer(m) and _higher(ykj, m, yij, n):
                        act = "update"
                    elif s_newer(n) and not s_newer(m):
                        act = "reset"
            if act == "update":
                if self.z.get(j) != zkj or abs(self.y.get(j, 0.0) - ykj) > EPS:
                    changed = True
                self.y[j], self.z[j] = ykj, zkj
            elif act == "reset":
                if self.z.get(j, NONE) != NONE:
                    changed = True
                self._reset(j)

        # timestamps: direct contact with k now; transitive info otherwise
        si[k] = now
        for m, t in sk.items():
            if m != i and t > si.get(m, -1.0):
                si[m] = t

        # outbid on bundle[n]? then everything added after it is invalid too
        for n, j in enumerate(self.bundle):
            if self.z.get(j) != i:
                self._drop_from(n)
                changed = True
                break
        return changed
