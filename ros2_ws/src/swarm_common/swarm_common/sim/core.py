"""ROS-free swarm simulator.

Runs the REAL DroneBrain and the REAL VehicleFSM for every drone, over a
broadcast radio model with range, loss, latency and scripted partitions.
Deterministic for a given seed, fast enough for CI (10 drones x 10 min of
flight in a few seconds of wall time).

What is simplified (honest list):
  * vehicles are point masses with first-order velocity tracking, not
    full multirotor dynamics (SITL covers that);
  * the camera is an ideal footprint detector with position noise and a
    per-frame detection probability, not YOLO;
  * the network is a disc model + random loss + fixed latency, not RF.
"""
import heapq
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

from ..brain import DroneBrain, OwnState, PERSON, TARGET
from ..config import Fleet
from ..perception import footprint_radius
from ..vehicle_fsm import FsmCfg, VehicleFSM, VehicleObs


# ---------------------------------------------------------------- vehicle
@dataclass
class SimVehicle:
    x: float
    y: float
    home: Tuple[float, float]
    alt: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    battery: float = 100.0
    armed: bool = False
    mode: str = "STABILIZE"
    target_alt: float = 0.0
    cmd_v: Tuple[float, float] = (0.0, 0.0)
    rtl_alt: float = 15.0
    drain_factor: float = 1.0     # >1: real consumption worse than the model predicts
    pct_per_m: float = 0.005
    pct_per_s_hover: float = 0.025
    alive: bool = True
    climb_rate: float = 3.0
    tau: float = 0.8              # velocity tracking time constant

    def apply(self, action):
        k, p = action.kind, action.params
        if k == "takeoff":
            self.armed, self.mode, self.target_alt = True, "GUIDED", float(p.get("alt", 30.0))
            self.cmd_v = (0.0, 0.0)
        elif k == "velocity":
            if self.armed and self.mode in ("GUIDED", "LOITER"):
                self.mode = "GUIDED"
                self.cmd_v = (float(p["vx"]), float(p["vy"]))
                self.target_alt = float(p.get("alt", self.target_alt))
        elif k == "position":
            if self.armed:
                self.mode = "GUIDED"
                dx, dy = p["x"] - self.x, p["y"] - self.y
                d = math.hypot(dx, dy) or 1.0
                s = min(8.0, d / 3.0)
                self.cmd_v = (dx / d * s, dy / d * s)
                self.target_alt = float(p.get("alt", self.target_alt))
        elif k == "hold":
            if self.armed:
                self.mode, self.cmd_v = "GUIDED", (0.0, 0.0)
        elif k == "rtl":
            if self.armed:
                self.mode = "RTL"
        elif k == "land":
            if self.armed:
                self.mode = "LAND"

    def step(self, dt: float):
        if not self.alive:
            return
        cvx, cvy, tz = self.cmd_v[0], self.cmd_v[1], self.target_alt
        if self.mode == "RTL":
            dx, dy = self.home[0] - self.x, self.home[1] - self.y
            d = math.hypot(dx, dy)
            if d > 3.0:   # ArduPilot-like: climb to RTL_ALT if lower, fly home, land
                s = min(10.0, d)
                cvx, cvy, tz = dx / d * s, dy / d * s, max(self.rtl_alt, self.alt)
            else:
                cvx, cvy, tz = 0.0, 0.0, 0.0
        elif self.mode == "LAND":
            cvx, cvy, tz = 0.0, 0.0, 0.0
        elif not self.armed:
            cvx, cvy, tz = 0.0, 0.0, 0.0
        a = min(1.0, dt / self.tau)
        self.vx += (cvx - self.vx) * a
        self.vy += (cvy - self.vy) * a
        self.x += self.vx * dt
        self.y += self.vy * dt
        dz = tz - self.alt
        self.alt += max(-self.climb_rate * dt, min(self.climb_rate * dt, dz))
        if self.alt <= 0.05 and self.mode in ("LAND", "RTL") and tz <= 0.0:
            self.alt, self.armed, self.mode, self.vx, self.vy = 0.0, False, "STABILIZE", 0.0, 0.0
            self.target_alt = 0.0
        if self.alt > 0.5:
            speed = math.hypot(self.vx, self.vy)
            self.battery -= self.drain_factor * (speed * dt * self.pct_per_m + dt * self.pct_per_s_hover)
            self.battery = max(0.0, self.battery)


# ---------------------------------------------------------------- network
@dataclass
class NetCfg:
    range_m: float = 3500.0
    loss: float = 0.0
    latency_s: float = 0.05
    operator_ids: Optional[Set[int]] = None   # drones the GCS can reach (None = all)


@dataclass(order=True)
class _Delivery:
    at: float
    n: int
    dst: int = field(compare=False)
    pkt: dict = field(compare=False)


@dataclass
class Victim:
    x: float
    y: float
    found_by: Optional[int] = None


@dataclass
class Quarry:
    x: float
    y: float
    vx: float
    vy: float
    start: float = 0.0
    stop: float = 1e18

    def at(self, t):
        if t < self.start:
            return None
        tt = min(t, self.stop) - self.start
        return self.x + self.vx * tt, self.y + self.vy * tt


class SwarmSim:
    def __init__(self, fleet: Fleet, seed: int = 0, net: Optional[NetCfg] = None, dt: float = 0.1):
        self.fleet = fleet
        self.cfg = fleet.swarm
        self.rnd = random.Random(seed)
        self.net = net or NetCfg(range_m=self.cfg.radio_range_m)
        self.dt = dt
        self.t = 0.0
        self.brains: Dict[int, DroneBrain] = {}
        self.fsms: Dict[int, VehicleFSM] = {}
        self.veh: Dict[int, SimVehicle] = {}
        e = self.cfg.energy
        for d in fleet.drones:
            hx, hy = fleet.home_enu(d.id)
            self.brains[d.id] = DroneBrain(fleet, d.id)
            self.fsms[d.id] = VehicleFSM(FsmCfg(
                critical_pct=e.critical_pct, fence_radius_m=self.cfg.geofence.radius_m,
                fence_max_alt_m=self.cfg.geofence.max_alt_m,
                brain_stale_s=self.cfg.brain_stale_s, brain_dead_s=self.cfg.brain_dead_s))
            self.veh[d.id] = SimVehicle(hx, hy, (hx, hy), pct_per_m=e.pct_per_m,
                                        pct_per_s_hover=e.pct_per_s_hover,
                                        rtl_alt=15.0 + 3.0 * d.id)
        self._q: List[_Delivery] = []
        self._n = 0
        self.partitions: List[Tuple[float, float, Set[int]]] = []   # (t0, t1, group A)
        self.scheduled: List[Tuple[float, Callable[["SwarmSim"], None]]] = []
        self.victims: List[Victim] = []
        self.quarry: Optional[Quarry] = None
        self.brain_alive: Dict[int, bool] = {i: True for i in self.brains}
        # metrics
        self.min_sep = float("inf")
        self.min_sep_pair = None
        self.events: List[Tuple[float, int, str, str, str]] = []
        self.logs: List[Tuple[float, str]] = []
        self.suggestions: List[Tuple[float, int, str]] = []
        self.assign_log: List[Tuple[float, int, str]] = []
        self.packets_sent = 0
        self.packets_delivered = 0
        self.bytes_sent = 0
        self.conflict_samples = 0
        self.conflict_log: List[Tuple[float, str, List[int]]] = []
        self.max_conflict = 0
        self._conflict_open: Dict[str, float] = {}
        self.conflict_episodes: List[Tuple[str, float, float]] = []   # (item, start, duration)
        self.los_samples = 0           # loss of separation: too close horizontally AND vertically
        self.los_log: List[Tuple[float, int, int, float, float]] = []
        self.track: Dict[int, List[Tuple[float, float, float, float]]] = {i: [] for i in self.brains}
        self.auto_confirm = False
        self._next_sense = 0.0
        self.building_hits = 0
        self.building_log: List[Tuple[float, int, float, float]] = []
        self._truth_grid = None
        if fleet.area:
            from ..area import height_grid
            self._truth_grid = height_grid(fleet.area, cell=5.0, dilate=False)
        self.recorder = None          # optional swarm_common.sim.recorder.Recorder

    # ------------------------------------------------------------- scripting
    def at(self, t: float, fn: Callable[["SwarmSim"], None]):
        self.scheduled.append((t, fn))
        self.scheduled.sort(key=lambda a: a[0])

    def operator_task(self, task_id: str, x: float, y: float, params: Optional[dict] = None,
                      to: Optional[Set[int]] = None):
        targets = to if to is not None else (self.net.operator_ids or set(self.brains))
        for i in sorted(targets):
            if self.brain_alive.get(i) and self.veh[i].alive:
                self.brains[i].on_operator_task(task_id, x, y, self.t, params=params)

    def operator_command(self, drone_id: int, cmd: str):
        v = self.veh[drone_id]
        acts = self.fsms[drone_id].on_operator(cmd, self.t, self._obs(drone_id))
        for a in acts:
            v.apply(a)

    def kill(self, drone_id: int, vehicle_too: bool = True):
        """Brain crash (vehicle_too=False) or whole drone lost (True)."""
        self.brain_alive[drone_id] = False
        if vehicle_too:
            self.veh[drone_id].alive = False

    def partition(self, t0: float, t1: float, group: Set[int]):
        self.partitions.append((t0, t1, set(group)))

    # ------------------------------------------------------------------ loop
    def _obs(self, i) -> VehicleObs:
        v = self.veh[i]
        return VehicleObs(self.t, v.x, v.y, v.alt, v.battery, v.armed, v.mode)

    def _link_ok(self, a: int, b: int) -> bool:
        va, vb = self.veh[a], self.veh[b]
        if not (va.alive and vb.alive):
            return False
        if math.hypot(va.x - vb.x, va.y - vb.y) > self.net.range_m:
            return False
        for t0, t1, grp in self.partitions:
            if t0 <= self.t < t1 and ((a in grp) != (b in grp)):
                return False
        return self.rnd.random() >= self.net.loss

    def run(self, duration_s: float, every: Optional[Callable[["SwarmSim"], None]] = None):
        end = self.t + duration_s
        while self.t < end - 1e-9:
            self.step()
            if every:
                every(self)

    def step(self):
        dt, now = self.dt, self.t
        while self.scheduled and self.scheduled[0][0] <= now:
            _, fn = self.scheduled.pop(0)
            fn(self)
        # deliver packets due now
        while self._q and self._q[0].at <= now:
            d = heapq.heappop(self._q)
            if self.brain_alive.get(d.dst) and self.veh[d.dst].alive:
                self.brains[d.dst].on_packet(d.pkt, now)
                self.packets_delivered += 1
        sense = now >= self._next_sense
        if sense:
            self._next_sense = now + 1.0
        for i, brain in self.brains.items():
            v = self.veh[i]
            if not v.alive:
                continue
            fsm = self.fsms[i]
            if self.brain_alive[i]:
                brain.on_vehicle(OwnState(now, v.x, v.y, v.alt, v.vx, v.vy, v.battery, v.armed,
                                          fsm.state, fsm.latch or ""))
                if sense:
                    self._sense(i)
                out = brain.tick(now)
                if out.setpoint is not None:
                    fsm.on_setpoint(out.setpoint, now)
                for p in out.packets:
                    self._broadcast(i, p)
                for a in out.assignments:
                    self.assign_log.append((now, i, a.item_id))
                for (tid, ev, det) in out.events:
                    self.events.append((now, i, tid, ev, det))
                for s in out.suggestions:
                    self.suggestions.append((now, i, s.id))
                    if self.auto_confirm:
                        self.at(now + 5.0, lambda sim, tid=s.id, x=s.x, y=s.y:
                                sim.operator_task(tid, x, y))
                for line in out.logs:
                    self.logs.append((now, line))
            for a in fsm.tick(self._obs(i), now):
                v.apply(a)
            for line in fsm.events:
                self.logs.append((now, f"D{i} FSM: {line}"))
            fsm.events.clear()
        for v in self.veh.values():
            v.step(dt)
        self._metrics()
        if self.recorder is not None:
            self.recorder.on_step(self, now)
        self.t = round(now + dt, 6)

    def _broadcast(self, src: int, pkt: dict):
        if self.recorder is not None:
            self.recorder.on_packet(self.t, src, pkt)
        self.packets_sent += 1
        self.bytes_sent += _approx_size(pkt)
        for dst in self.brains:
            if dst != src and self._link_ok(src, dst):
                self._n += 1
                heapq.heappush(self._q, _Delivery(self.t + self.net.latency_s, self._n, dst, pkt))

    def _sense(self, i: int):
        v = self.veh[i]
        if v.alt < 10.0:
            return
        r = footprint_radius(v.alt, self.cfg.perception)
        for vic in self.victims:
            if math.hypot(vic.x - v.x, vic.y - v.y) <= r and self.rnd.random() < 0.6:
                vic.found_by = vic.found_by or i
                self.brains[i].on_detection(PERSON, vic.x + self.rnd.gauss(0, 3),
                                            vic.y + self.rnd.gauss(0, 3), 0.8, self.t)
        if self.quarry is not None:
            q = self.quarry.at(self.t)
            if q and math.hypot(q[0] - v.x, q[1] - v.y) <= max(r, 400.0):
                self.brains[i].on_detection(TARGET, q[0] + self.rnd.gauss(0, 2),
                                            q[1] + self.rnd.gauss(0, 2), 0.9, self.t,
                                            self.quarry.vx, self.quarry.vy)

    def _metrics(self):
        ids = [i for i, v in self.veh.items() if v.alive and v.alt > 2.0]
        if self._truth_grid is not None:
            for i in ids:
                v = self.veh[i]
                roof = self._truth_grid.height_at(v.x, v.y)
                if roof > 0 and v.alt < roof:
                    self.building_hits += 1
                    if len(self.building_log) < 30:
                        self.building_log.append((round(self.t, 1), i, round(v.alt, 1), roof))
        for a_i, a in enumerate(ids):
            va = self.veh[a]
            self.track[a].append((self.t, va.x, va.y, va.alt))
            for b in ids[a_i + 1:]:
                vb = self.veh[b]
                dh = math.hypot(va.x - vb.x, va.y - vb.y)
                dv = abs(va.alt - vb.alt)
                d = math.sqrt(dh * dh + dv * dv)
                if d < self.min_sep:
                    self.min_sep, self.min_sep_pair = d, (a, b, round(self.t, 1))
                m = self.cfg.motion
                if dh < 2 * m.safety_radius_m and dv < 0.8 * m.layer_spacing_m:
                    self.los_samples += 1
                    if len(self.los_log) < 50:
                        self.los_log.append((round(self.t, 1), a, b, round(dh, 1), round(dv, 1)))
        # allocation conflicts: two live drones EXECUTING the same work item
        holders: Dict[str, int] = {}
        for i, b in self.brains.items():
            if self.brain_alive[i] and self.veh[i].alive and b.current_item():
                holders[b.current_item()] = holders.get(b.current_item(), 0) + 1
        for item, n in holders.items():
            if n > 1:
                self._conflict_open.setdefault(item, self.t)
        for item in list(self._conflict_open):
            if holders.get(item, 0) <= 1:
                t0 = self._conflict_open.pop(item)
                self.conflict_episodes.append((item, t0, round(self.t - t0, 1)))
        worst = max(holders.values(), default=0)
        if worst > 1:
            self.conflict_samples += 1
            if len(self.conflict_log) < 50:
                item, n = next((k, v) for k, v in holders.items() if v > 1)
                self.conflict_log.append((round(self.t, 1), item, n))
        self.max_conflict = max(self.max_conflict, worst)

    # --------------------------------------------------------------- queries
    def longest_conflict(self, after: float = -1.0) -> float:
        """Longest continuous period two live drones executed the same item."""
        eps = [d for (_, t0, d) in self.conflict_episodes if t0 > after]
        eps += [self.t - t0 for t0 in self._conflict_open.values() if t0 > after]
        return max(eps, default=0.0)

    def holders(self) -> Dict[str, List[int]]:
        out: Dict[str, List[int]] = {}
        for i, b in self.brains.items():
            if self.brain_alive[i] and self.veh[i].alive and b.current_item():
                out.setdefault(b.current_item(), []).append(i)
        return out

    def task_status(self, task_id: str) -> Dict[int, str]:
        return {i: (b.registry.get(task_id).status if b.registry.get(task_id) else "-")
                for i, b in self.brains.items() if self.brain_alive[i] and self.veh[i].alive}

    def event_names(self, task_id: str) -> List[str]:
        return [e[3] for e in self.events if e[2] == task_id]


def _approx_size(obj) -> int:
    import json
    try:
        return len(json.dumps(obj, separators=(",", ":")))
    except (TypeError, ValueError):
        return 0
