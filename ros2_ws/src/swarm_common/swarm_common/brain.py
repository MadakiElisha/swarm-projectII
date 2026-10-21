"""DroneBrain: the complete per-drone autonomy, transport-agnostic.

Exactly the same class runs inside the ROS 2 `drone_brain` node and inside
the ROS-free simulator (swarm_common.sim), so what the tests prove is what
flies. One brain per drone; brains only interact through packets.

Inputs                                    Outputs (BrainOutput, per tick)
  on_vehicle(OwnState)   own vehicle        packets      -> broadcast to whoever can hear
  on_packet(dict)        from neighbours    setpoint     -> vehicle_manager (FSM decides)
  on_operator_task(...)  operator uplink    assignments  -> for the GCS
  on_detection(...)      own camera         events/suggestions/logs
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .cbba import CBBA
from .config import Fleet
from .coverage import CoverageGrid, next_waypoint, partition
from .energy import DrainCalibrator, EnergyModel
from .gossip import NeighborTable, Roster, RosterEntry
from .motion import altitude_layer, arrived, avoid, limit_accel, preferred_velocity
from .perception import Observation, TargetTracker, Track, WorldModel, footprint_radius
from .planner import Planner
from .tasks import (DONE, FORMATION, GOTO, INTERCEPT, OPEN, RESCUE, SEARCH, SUGGESTED,
                    CANCELLED, Task, TaskRegistry, WorkItem, derive_work_items, ring_slot_xy)
from .vehicle_fsm import (GROUND, LAND, RTL, ESTOP, SP_HOLD, SP_IDLE, SP_LAND, SP_VEL,
                          Setpoint)

PROTO_VERSION = 1
ROSTER_ALIVE_S = 10.0
IDLE_RTB_S = 30.0
BEACON_FRESH_S = 1.0
GROUND_TAKEOFF_PENALTY_S = 20.0
MAX_OBS_PER_PACKET = 60
TERMINAL_TASK_KEEP_S = 300.0
CLAIM_SETTLE_S = 2.5          # hold a fresh claim this long before acting on it
PERSON, TARGET = "person", "target"
TRACK_CLASSES = {"target", "vehicle"}      # what an intercept may follow (sim sensor, detector)


@dataclass
class OwnState:
    t: float
    x: float
    y: float
    alt: float
    vx: float = 0.0
    vy: float = 0.0
    battery: float = 100.0
    armed: bool = False
    fsm_state: str = GROUND
    latch: str = ""
    wind: float = 0.0


@dataclass
class Assignment:
    item_id: str            # "" when the drone dropped its task
    parent: str
    kind: str
    x: float = 0.0
    y: float = 0.0
    radius: float = 0.0


@dataclass
class BrainOutput:
    packets: List[dict] = field(default_factory=list)
    setpoint: Optional[Setpoint] = None
    assignments: List[Assignment] = field(default_factory=list)
    events: List[Tuple[str, str, str]] = field(default_factory=list)   # (task, event, detail)
    suggestions: List[Task] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


_GRIDS = {}


def _grid_for_area(area):
    """Rasterise an area once per process (every brain in a sim shares it)."""
    from .area import height_grid
    key = id(area)
    if key not in _GRIDS:
        _GRIDS[key] = height_grid(area, cell=10.0)
    return _GRIDS[key]


class DroneBrain:
    def __init__(self, fleet: Fleet, drone_id: int):
        self.fleet = fleet
        self.cfg = fleet.swarm
        self.id = drone_id
        self.label = f"D{drone_id}"
        self.home = fleet.home_enu(drone_id)
        self.alt = altitude_layer(drone_id, self.cfg.motion)
        self.energy = EnergyModel(self.cfg.energy)
        self.calib = DrainCalibrator(self.energy)
        self.cbba = CBBA(drone_id, self.cfg.cbba.max_bundle, self.cfg.cbba.rebid_margin)
        self.registry = TaskRegistry()
        self.roster = Roster()
        self.neighbors = NeighborTable(self.cfg.neighbor_timeout_s)
        self.world = WorldModel(self.cfg.perception)
        self.grids: Dict[str, CoverageGrid] = {}
        self.kin: Dict[int, Tuple[float, float, float, float, float, float]] = {}  # beacons
        self.own: Optional[OwnState] = None
        self.items: Dict[str, WorkItem] = {}
        self._seq = 0
        self._obs_seq = 0
        self._last_beacon = -1e9
        self._last_state = -1e9
        self._dirty = True
        self._cur_item = ""
        self._hold_started: Dict[str, float] = {}
        self._won_since: Dict[str, float] = {}
        self._idle_since: Optional[float] = None
        self._isolated_since: Optional[float] = None
        self._going_home = False
        self._formed: Dict[str, bool] = {}
        self._formed_since: Dict[str, float] = {}
        self._tracks: Dict[str, Track] = {}
        self._trackers: Dict[str, TargetTracker] = {}
        self._released_events = set()
        self._suggested_seen = set()
        self._vel = (0.0, 0.0)
        self._last_tick = None
        self.phase = "IDLE"
        self.logs: List[str] = []
        self.planner = Planner(_grid_for_area(fleet.area)) if fleet.area else None
        self._route = {"goal": None, "alt": None, "t": -1e9, "wps": []}

    # ================================================================ inputs
    def on_vehicle(self, s: OwnState):
        self.own = s

    def on_packet(self, pkt: dict, now: float):
        """Handle one packet heard over the radio. Never raises."""
        try:
            if pkt.get("v") != PROTO_VERSION:
                return
            src, seq, kind = int(pkt["src"]), int(pkt["seq"]), pkt["k"]
            if src == self.id:
                return
            self.neighbors.heard(src, seq, now)
            d = pkt.get("d") or {}
            if kind == "B":
                self.kin[src] = (now, float(d["x"]), float(d["y"]), float(d["z"]),
                                 float(d["vx"]), float(d["vy"]))
            elif kind == "S":
                self._merge_state(src, d, now)
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            self._log(f"dropped malformed packet: {e}")

    def _merge_state(self, src: int, d: dict, now: float):
        ch = False
        self.roster.merge(d.get("r", []))       # roster changes alone never force a resend
        ch |= self.registry.merge(d.get("tasks", []))
        self.world.merge(d.get("obs", []))
        for tid, cells in (d.get("cov") or {}).items():
            g = self._grid_for(tid)
            if g is not None:
                g.merge(cells)
        self.items = self._derive_items(now)
        if "cbba" in d:
            ch |= self.cbba.receive(src, d["cbba"], now, known_items=set(self.items))
        if ch:
            self._dirty = True

    def on_operator_task(self, task_id: str, x: float, y: float, now: float,
                         desc: str = "", params: Optional[dict] = None) -> str:
        """An operator request heard by THIS drone. Gossip spreads it to the rest."""
        params = dict(params or {})
        if task_id.startswith("CANCEL-"):
            self.registry.set_status(task_id[len("CANCEL-"):], CANCELLED, now)
            self._dirty = True
            return "cancel"
        existing = self.registry.get(task_id)
        if existing is not None:
            if existing.status == SUGGESTED:
                self.registry.set_status(task_id, OPEN, now)
                self._log(f"{task_id}: operator confirmed")
                self._dirty = True
                return "confirmed"
            return "duplicate"
        kind = self._kind_for(task_id)
        if kind in (FORMATION, INTERCEPT):
            avail = [i for i in self.roster.alive(now, ROSTER_ALIVE_S) if self._available_peer(i)]
            if self.id not in avail and self._available_self(now):
                avail.append(self.id)
            params.setdefault("n_slots", max(1, min(self.cfg.formation.max_slots, len(avail))))
            params.setdefault("radius", self.cfg.formation.ring_radius_m)
            params.setdefault("hold_s", self.cfg.formation.hold_s)
            # hard upper bound in case the ring can never fully form
            params.setdefault("expires_at", now + 600.0 + self.cfg.formation.hold_s)
        params.setdefault("desc", desc)
        self.registry.upsert(Task(task_id, kind, x, y, now, self.id, OPEN, now, params))
        if kind == SEARCH:
            self._grid_for(task_id)
        self._log(f"{task_id}: accepted {kind} from operator")
        self._dirty = True
        return "created"

    def on_detection(self, cls: str, gx: float, gy: float, conf: float, now: float,
                     vx: float = 0.0, vy: float = 0.0):
        """A detection from MY camera, already projected to the ground."""
        self._obs_seq += 1
        self.world.add(Observation(f"{self.id}-{self._obs_seq}", cls, gx, gy, conf, now,
                                   self.id, vx, vy))
        self._dirty = cls == PERSON or self._dirty

    # ================================================================== tick
    def tick(self, now: float) -> BrainOutput:
        out = BrainOutput()
        s = self.own
        if s is None:
            return out
        dt = 0.1 if self._last_tick is None else max(1e-3, min(1.0, now - self._last_tick))
        self._last_tick = now
        pos = (s.x, s.y)
        airborne = s.alt > 1.0
        self.calib.update(now, s.battery, math.hypot(s.vx, s.vy), airborne)

        self.world.prune(now)
        self._maintain_registry(now, out)
        self.items = self._derive_items(now)
        alive = set(self.roster.alive(now, ROSTER_ALIVE_S)) | {self.id}
        if self.cbba.sync_items(self.items.keys(), alive):
            self._dirty = True

        # ---------------- availability & battery self-check (one energy model)
        available = self._available_self(now)
        if not available:
            if self.cbba.release_all():
                self._log(f"releasing all work (fsm={s.fsm_state} latch={s.latch or '-'})")
                self._dirty = True
        elif self.cbba.path and self._path_score(self.cbba.path, s) is None:
            j = self.cbba.path[0]
            self.cbba.release(j)
            self._log(f"relinquish {j}: battery no longer covers task + return home")
            self._going_home = True
            self._dirty = True
        if available and not self._going_home:
            if self.cbba.build_bundle(self.items.keys(), lambda p: self._path_score(p, s),
                                      lambda j: self.items[j].group if j in self.items else "",
                                      now):
                self._dirty = True

        # claims must survive a consensus window before we act on them
        mine = {j for j in self.cbba.path if self.cbba.winner(j) == self.id}
        for j in list(self._won_since):
            if j not in mine:
                del self._won_since[j]
        for j in mine:
            self._won_since.setdefault(j, now)

        # ---------------- execution
        target, tvel, sp_kind = self._execute(now, s, out)

        # ---------------- motion
        if sp_kind == SP_VEL and target is not None:
            alt = self.alt
            if self.phase == "SEARCH":
                alt = self.cfg.coverage.search_alt_m + (self.alt - self.cfg.motion.base_alt_m)
            wp = self._route_to(pos, target, alt, now)
            if wp is not target:                  # a corner of a planned detour
                pref = preferred_velocity(pos, wp, self.cfg.motion, (0.0, 0.0), slow_radius_m=12.0)
            else:
                pref = preferred_velocity(pos, target, self.cfg.motion, tvel)
            nbrs = [((k[1], k[2]), (k[4], k[5]), k[3]) for i, k in self.kin.items()
                    if now - k[0] <= BEACON_FRESH_S]
            v = avoid(pos, (s.vx, s.vy), pref, s.alt, nbrs, self.cfg.motion, dt) if airborne else pref
            v = limit_accel(self._vel, v, self.cfg.motion.max_accel_mps2, dt)
            self._vel = v
            out.setpoint = Setpoint(now, SP_VEL, v[0], v[1], 0.0, alt=alt)
        else:
            self._vel = (0.0, 0.0)
            out.setpoint = Setpoint(now, sp_kind, x=s.x, y=s.y, alt=self.alt)

        # ---------------- coverage: what my camera footprint has seen
        if airborne and s.alt > 10.0:
            r = footprint_radius(s.alt, self.cfg.perception)
            for g in self.grids.values():
                if g.mark_footprint(s.x, s.y, r):
                    self._dirty = True

        # ---------------- my roster entry (the only one I ever write)
        self.roster.update(RosterEntry(self.id, now, s.x, s.y, s.alt, s.vx, s.vy, s.battery,
                                       self.phase, self._cur_item, airborne, available,
                                       round(self.energy.scale, 3)))
        self._mission_events(now, out)

        # ---------------- radio
        if now - self._last_beacon >= 1.0 / self.cfg.beacon_hz:
            self._last_beacon = now
            out.packets.append(self._packet("B", {"x": s.x, "y": s.y, "z": s.alt,
                                                  "vx": s.vx, "vy": s.vy}, now))
        due = now - self._last_state >= 1.0 / self.cfg.state_hz
        if due or (self._dirty and now - self._last_state >= 0.2):
            self._last_state = now
            self._dirty = False
            out.packets.append(self._packet("S", self._state_payload(now), now))
        out.logs, self.logs = self.logs, []
        return out

    # ============================================================ execution
    def _execute(self, now: float, s: OwnState, out: BrainOutput):
        pos = (s.x, s.y)
        airborne = s.alt > 1.0
        # isolation watchdog
        if self.neighbors.neighbors(now):
            self._isolated_since = None
        elif self._isolated_since is None:
            self._isolated_since = now

        if s.latch or s.fsm_state in (RTL, LAND, ESTOP):
            self._set_item("", out)
            self.phase = "FAILSAFE" if s.latch and not s.latch.startswith("brain") else "RTB"
            return None, (0.0, 0.0), SP_IDLE

        item_id = self.cbba.path[0] if self.cbba.path else ""
        item = self.items.get(item_id)
        settled = (item_id == self._cur_item or
                   now - self._won_since.get(item_id, now) >= CLAIM_SETTLE_S)
        if item is not None and self.cbba.winner(item_id) == self.id and not settled:
            self.phase = "CLAIMING"
            return None, (0.0, 0.0), (SP_HOLD if airborne else SP_IDLE)
        if item is not None and self.cbba.winner(item_id) == self.id:
            self._going_home = False
            self._idle_since = None
            self._set_item(item_id, out)
            return self._fly_item(item, now, s)

        self._set_item("", out)
        # no allocated work: help search, otherwise go home after a while
        search = self._search_waypoint(now, s)
        if search is not None and not self._going_home:
            self._idle_since = None
            self.phase = "SEARCH"
            return search, (0.0, 0.0), SP_VEL
        if not airborne:
            self.phase = "LANDED" if self._near_home(pos) else "IDLE"
            self._going_home = False
            return None, (0.0, 0.0), SP_IDLE
        if self._idle_since is None:
            self._idle_since = now
        isolated = self._isolated_since is not None and now - self._isolated_since > self.cfg.isolation_rtb_s
        if self._going_home or now - self._idle_since > IDLE_RTB_S or isolated:
            self._going_home = True
            self.phase = "RTB"
            # land only when centred over my own pad (pads can be ~10 m apart)
            if arrived(pos, self.home, 2.5) and math.hypot(s.vx, s.vy) < 1.0:
                return None, (0.0, 0.0), SP_LAND
            return self.home, (0.0, 0.0), SP_VEL
        self.phase = "IDLE"
        return None, (0.0, 0.0), SP_HOLD

    def _fly_item(self, it: WorkItem, now: float, s: OwnState):
        pos = (s.x, s.y)
        tvel = (0.0, 0.0)
        if it.kind in (FORMATION, INTERCEPT):
            parent = self.registry.get(it.parent)
            cx, cy, vx, vy = self._centre(parent, now)
            r = float(parent.params.get("radius", self.cfg.formation.ring_radius_m))
            tx, ty = ring_slot_xy(cx, cy, r, it.slot, it.n_slots, now, parent.created_t,
                                  self.cfg.formation.ring_period_s)
            # ring rotation + centre motion feed-forward, blended in only near
            # the slot (far away it would just bend the approach path)
            w = 2 * math.pi / self.cfg.formation.ring_period_s
            d_slot = math.hypot(tx - pos[0], ty - pos[1])
            band = self.cfg.formation.on_station_band_m
            k = max(0.0, min(1.0, (5 * band - d_slot) / (4 * band)))
            tvel = (k * (-w * (ty - cy) + vx), k * (w * (tx - cx) + vy))
            if it.kind == INTERCEPT and it.slot in (0, 1) and (vx or vy):
                lt = self.cfg.formation.lead_time_s           # cutters lead the quarry
                tx, ty = tx + vx * lt, ty + vy * lt
            on = math.hypot(tx - pos[0], ty - pos[1]) <= self.cfg.formation.on_station_band_m
            self.phase = "ON_STATION" if on else "ENROUTE"
            return (tx, ty), tvel, SP_VEL
        # GOTO / RESCUE: fly there (or to the nearest reachable point), hold, mark done
        target = self._approach((it.x, it.y), self.alt)
        if arrived(pos, target, self.cfg.motion.arrive_radius_m) and s.alt > 1.0:
            t0 = self._hold_started.setdefault(it.id, now)
            self.phase = "ON_TASK"
            if now - t0 >= it.hold_s:
                self.registry.set_status(it.parent, DONE, now, done_by=self.id)
                self.cbba.release(it.id)
                self._log(f"{it.id}: complete")
                self._dirty = True
        else:
            self.phase = "ENROUTE"
        return target, tvel, SP_VEL

    def _centre(self, parent: Task, now: float):
        if parent.kind == INTERCEPT:
            tk = self._trackers.get(parent.id)
            if tk is None:             # the operator clicked on the target: that is the first fix
                tk = self._trackers[parent.id] = TargetTracker(parent.x, parent.y, parent.created_t,
                                                               TRACK_CLASSES)
            tr = tk.update(self.world.obs.values(), now)
            if tr is not None:
                self._tracks[parent.id] = tr
                return tr.x, tr.y, tr.vx, tr.vy
            last = parent.params.get("last_fix")
            if last:
                return last[0], last[1], 0.0, 0.0
        return parent.x, parent.y, 0.0, 0.0

    def _search_waypoint(self, now: float, s: OwnState):
        active = [t for t in self.registry.active() if t.kind == SEARCH and t.status == OPEN]
        if not active or not self._available_self(now):
            return None
        t = sorted(active, key=Task.def_key)[0]
        g = self._grid_for(t.id)
        if g is None:
            return None
        participants = [e.id for e in self.roster.entries.values()
                        if now - e.t <= ROSTER_ALIVE_S and e.available and
                        (e.phase in ("SEARCH", "IDLE", "LANDED") and not e.task)]
        if self.id not in participants:
            participants.append(self.id)
        share = partition(g, participants).get(self.id, [])
        wp = next_waypoint(g, share, (s.x, s.y))
        if wp is None:
            return None
        # energy: only search while I can still get home
        if not self.energy.feasible(s.battery, self.energy.plan_pct((s.x, s.y), [(wp, 0.0)],
                                                                    self.home, s.wind) + 2.0):
            self._going_home = True
            return None
        return wp

    # ====================================================== registry upkeep
    def _maintain_registry(self, now: float, out: BrainOutput):
        reg = self.registry
        for t in reg.active():
            if t.kind in (FORMATION, INTERCEPT) and now >= float(t.params.get("expires_at", 1e18)):
                reg.set_status(t.id, DONE, now)
                self._dirty = True
            if t.kind == SEARCH:
                g = self._grid_for(t.id)
                if g is not None and g.fraction() >= 0.98:
                    reg.set_status(t.id, DONE, now)
                    self._log(f"{t.id}: area fully covered")
                    self._dirty = True
            if t.kind == INTERCEPT and t.id in self._tracks:
                tr = self._tracks[t.id]
                t.params["last_fix"] = [tr.x, tr.y]
        # perception -> RESCUE suggestions (deterministic ids => natural dedup)
        for tr in self.world.static_tracks(PERSON):
            near = [t for t in reg.tasks.values() if t.kind == RESCUE and
                    math.hypot(t.x - tr.x, t.y - tr.y) <= 2 * self.cfg.perception.fuse_radius_m]
            if near:
                continue
            status = SUGGESTED if self.cfg.cbba.hitl_required else OPEN
            reg.upsert(Task(f"RESCUE-{tr.tid}", RESCUE, tr.x, tr.y, tr.t, self.id, status, now,
                            {"desc": f"person seen ({tr.n} obs)"}))
            self._dirty = True
        if reg.resolve_duplicates(RESCUE, 2 * self.cfg.perception.fuse_radius_m, now):
            self._dirty = True
        for t in reg.tasks.values():
            if t.kind == RESCUE and t.status == SUGGESTED and t.id not in self._suggested_seen:
                self._suggested_seen.add(t.id)
                out.suggestions.append(t)

    def _mission_events(self, now: float, out: BrainOutput):
        for t in self.registry.tasks.values():
            if t.kind not in (FORMATION, INTERCEPT):
                continue
            if t.terminal:
                if t.id not in self._released_events and self._formed.get(t.id) is not None:
                    self._released_events.add(t.id)
                    out.events.append((t.id, "RELEASED", "swarm released"))
                continue
            n = int(t.params.get("n_slots", 0))
            on = sum(1 for e in self.roster.entries.values()
                     if now - e.t <= 5.0 and e.task.startswith(t.id + "/") and e.phase == "ON_STATION")
            formed = n > 0 and on >= n
            prev = self._formed.get(t.id)
            if formed and not prev:
                out.events.append((t.id, "PERIMETER_FORMED", f"{on}/{n} on station"))
            elif prev and not formed:
                out.events.append((t.id, "PERIMETER_DEGRADED", f"{on}/{n} on station"))
            self._formed[t.id] = formed
            # the hold clock starts once the ring is formed (any drone may end it;
            # DONE is idempotent in the registry lattice)
            if formed or prev:
                since = self._formed_since.setdefault(t.id, now)
                if now - since >= float(t.params.get("hold_s", self.cfg.formation.hold_s)):
                    self.registry.set_status(t.id, DONE, now)
                    self._dirty = True

    # =============================================================== helpers
    def _route_to(self, pos, target, alt, now):
        """Next waypoint towards target around buildings taller than my layer.

        Re-verified every tick from where the drone actually IS: momentum, ORCA
        nudges and moving goals (ring slots) can all put a corner in the way.
        """
        if self.planner is None:
            return target
        r = self._route
        g = r["goal"]
        stale = (g is None or math.hypot(g[0] - target[0], g[1] - target[1]) > 20.0
                 or abs((r["alt"] or 0) - alt) > 3.0 or now - r["t"] > 8.0 or not r["wps"])
        if not stale:
            wps = r["wps"]
            while len(wps) > 1 and math.hypot(wps[0][0] - pos[0], wps[0][1] - pos[1]) < 12.0:
                wps.pop(0)
            nxt = self._leg_end(wps, target)
            stale = not self.planner.line_clear(pos, nxt, alt)
        if stale:
            free = self.planner.nearest_free(target, alt)
            wps = self.planner.plan(pos, free, alt) or [free]
            r.update(goal=target, alt=alt, t=now, wps=wps,
                     adjusted=math.hypot(free[0] - target[0], free[1] - target[1]) > 1.0)
        return self._leg_end(r["wps"], target)

    def _leg_end(self, wps, target):
        if len(wps) > 1:
            return wps[0]
        if self._route.get("adjusted"):
            return wps[0]                        # goal is inside a building: hold beside it
        return target                            # open last leg: track the (moving) goal

    def _approach(self, target, alt):
        """Reachable point for a task whose location is inside a tall building."""
        if self.planner is None:
            return target
        return self.planner.nearest_free(target, alt)

    def _path_score(self, path: List[str], s: OwnState) -> Optional[float]:
        """CBBA score of doing `path` in order from my current state (None = infeasible)."""
        lam = self.cfg.cbba.discount_per_s
        v = self.cfg.motion.cruise_speed_mps
        t = 0.0 if s.alt > 1.0 else GROUND_TAKEOFF_PENALTY_S
        cur = (s.x, s.y)
        score, legs = 0.0, []
        for j in path:
            it = self.items.get(j)
            if it is None:
                return None
            d = math.hypot(it.x - cur[0], it.y - cur[1])
            t += d / v
            score += it.reward * (lam ** t)
            t += it.hold_s
            legs.append(((it.x, it.y), it.hold_s))
            cur = (it.x, it.y)
        if path and not self.energy.feasible(s.battery, self.energy.plan_pct(
                (s.x, s.y), legs, self.home, s.wind)):
            return None
        return score

    def _available_self(self, now: float) -> bool:
        s = self.own
        if s is None or s.latch or s.fsm_state in (RTL, LAND, ESTOP):
            return False
        if self.energy.critical(s.battery):
            return False
        return not self.energy.must_go_home(s.battery, (s.x, s.y), self.home, s.wind)

    def _available_peer(self, i: int) -> bool:
        e = self.roster.get(i)
        return e is not None and e.available

    def _derive_items(self, now: float) -> Dict[str, WorkItem]:
        def centre_of(t):
            c = self._centre(t, now)
            return c[0], c[1]
        return derive_work_items(self.registry, now, self.cfg.formation, centre_of)

    def _grid_for(self, task_id: str) -> Optional[CoverageGrid]:
        g = self.grids.get(task_id)
        if g is not None:
            return g
        t = self.registry.get(task_id)
        if t is None or t.kind != SEARCH or "area" not in t.params:
            return None
        x0, y0, x1, y1 = t.params["area"]
        g = CoverageGrid(x0, y0, x1, y1, self.cfg.coverage.cell_m)
        self.grids[task_id] = g
        return g

    def _set_item(self, item_id: str, out: BrainOutput):
        if item_id == self._cur_item:
            return
        self._cur_item = item_id
        it = self.items.get(item_id)
        if it is None:
            out.assignments.append(Assignment("", "", ""))
            return
        parent = self.registry.get(it.parent)
        radius = float(parent.params.get("radius", 0.0)) if it.kind in (FORMATION, INTERCEPT) else 0.0
        out.assignments.append(Assignment(it.id, it.parent, it.kind,
                                          parent.x if parent else it.x,
                                          parent.y if parent else it.y, radius))
        self._log(f"now executing {it.id} ({it.kind})")

    def _near_home(self, pos) -> bool:
        return math.hypot(pos[0] - self.home[0], pos[1] - self.home[1]) <= 3 * self.cfg.motion.arrive_radius_m

    @staticmethod
    def _kind_for(task_id: str) -> str:
        for prefix, kind in (("SWARM-", FORMATION), ("INTERCEPT-", INTERCEPT),
                             ("RESCUE-", RESCUE), ("SEARCH-", SEARCH)):
            if task_id.startswith(prefix):
                return kind
        return GOTO

    def _packet(self, kind: str, data: dict, now: float) -> dict:
        self._seq += 1
        p = (self.own.x, self.own.y) if self.own else (0.0, 0.0)
        return {"v": PROTO_VERSION, "src": self.id, "seq": self._seq, "t": now, "k": kind,
                "p": [p[0], p[1]], "d": data}

    def _state_payload(self, now: float) -> dict:
        obs = self.world.recent_wire(now, 300.0)
        obs.sort(key=lambda o: o["t"], reverse=True)
        self.cbba.s[self.id] = now
        return {
            "r": self.roster.to_wire(),
            "tasks": self.registry.to_wire(TERMINAL_TASK_KEEP_S, now),
            "cbba": self.cbba.message(),
            "obs": obs[:MAX_OBS_PER_PACKET],
            "cov": {tid: g.to_wire() for tid, g in self.grids.items()
                    if (self.registry.get(tid) and not self.registry.get(tid).terminal)},
        }

    def _log(self, msg: str):
        self.logs.append(f"{self.label}: {msg}")

    # ---------------------------------------------------------- introspection
    def current_item(self) -> str:
        return self._cur_item
