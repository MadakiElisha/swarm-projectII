"""Record a simulator run for the web GCS replay mode.

The recording carries what the GCS would see live, plus what each drone
believes: per-drone CBBA winner tables (so the GCS can show consensus
forming), phases, learned battery drain, measured links, the task
registry, coverage, sightings and radio activity.

Format (compact JSON, version 1):
  {"v": 1, "meta": {...}, "rows": [[t, kind, payload], ...]}   sorted by t
  kinds: v vehicle · b brain · T tasks · c coverage · o observation ·
         p radio pulse · e mission event · a assignment · s suggestion · q quarry truth
"""
import json
import math
from typing import Optional, Dict, List

from ..vehicle_fsm import ESTOP, GROUND, GUIDED, HOLD, LAND, RTL, TAKEOFF

G = 9.81
DRAG_TILT = 0.02        # forward tilt per (m/s)^2 needed to hold cruise against drag
FSM_STATES = [GROUND, TAKEOFF, GUIDED, HOLD, RTL, LAND, ESTOP]


class Recorder:
    def __init__(self, sim, vehicle_hz: float = 4.0, brain_hz: float = 1.0, name: str = "run"):
        self.sim = sim
        self.name = name
        self.dv = 1.0 / vehicle_hz
        self.db = 1.0 / brain_hz
        self.rows: List[list] = []
        self._next_v = 0.0
        self._next_b = 0.0
        self._next_q = 0.0
        self._acc: Dict[int, tuple] = {}
        self._prev_v: Dict[int, tuple] = {}
        self._yaw: Dict[int, float] = {}
        self._dead = set()
        self._last_tasks = None
        self._last_cov: Dict[str, str] = {}
        self._seen_obs = set()
        self._last_pulse: Dict[tuple, float] = {}
        self._n_events = self._n_assign = self._n_sugg = 0
        sim.recorder = self

    # ------------------------------------------------------------- hooks
    def on_packet(self, t, src, pkt):
        k = pkt.get("k")
        key = (src, k)
        # beacons are 5 Hz; one pulse per second per drone is plenty for display
        if k == "B" and t - self._last_pulse.get(key, -9) < 1.0:
            return
        self._last_pulse[key] = t
        self.rows.append([round(t, 2), "p", [src, k]])

    def on_step(self, sim, now):
        dt = sim.dt
        for i, v in sim.veh.items():          # attitude from acceleration (multirotor tilt)
            pv = self._prev_v.get(i, (v.vx, v.vy))
            ax, ay = (v.vx - pv[0]) / dt, (v.vy - pv[1]) / dt
            sa = self._acc.get(i, (0.0, 0.0))
            self._acc[i] = (0.85 * sa[0] + 0.15 * ax, 0.85 * sa[1] + 0.15 * ay)
            self._prev_v[i] = (v.vx, v.vy)
        if now >= self._next_v:
            self._next_v = now + self.dv
            for i, v in sim.veh.items():
                if i in self._dead:
                    continue
                self.rows.append([round(now, 2), "v", self._vehicle(i, v, sim)])
                if not v.alive:
                    self._dead.add(i)       # one final row marks the loss
        if now >= self._next_b:
            self._next_b = now + self.db
            for i, b in sim.brains.items():
                if not (sim.brain_alive[i] and sim.veh[i].alive):
                    continue
                nb = b.neighbors
                ids = nb.neighbors(now)
                self.rows.append([round(now, 2), "b", {
                    "i": i, "ph": b.phase, "tk": b.current_item(),
                    "sc": round(b.energy.scale, 2),
                    "nb": [[j, round(nb.quality(j, now), 2)] for j in ids],
                    "z": {j: w for j, w in b.cbba.z.items() if w},
                    "y": {j: round(y, 1) for j, y in b.cbba.y.items() if y > 0},
                }])
            self._tasks(sim, now)
            self._coverage(sim, now)
        self._observations(sim, now)
        self._logs(sim, now)
        if sim.quarry is not None and now >= self._next_q:
            self._next_q = now + 0.5
            q = sim.quarry.at(now)
            if q:
                self.rows.append([round(now, 2), "q", [round(q[0], 1), round(q[1], 1),
                                                       sim.quarry.vx, sim.quarry.vy]])

    # ----------------------------------------------------------- helpers
    def _vehicle(self, i, v, sim):
        speed = math.hypot(v.vx, v.vy)
        if speed > 0.7:
            self._yaw[i] = math.atan2(v.vy, v.vx)
        yaw = self._yaw.get(i, 0.0)
        ax, ay = self._acc.get(i, (0.0, 0.0))
        fx, fy = math.cos(yaw), math.sin(yaw)
        fwd = ax * fx + ay * fy + DRAG_TILT * speed * speed
        lat_acc = -ax * fy + ay * fx
        airborne = v.alt > 0.5
        pitch = math.atan(fwd / G) if airborne else 0.0          # FLU: + = nose down
        roll = -math.atan(lat_acc / G) if airborne else 0.0
        lat, lon = sim.cfg.origin.to_latlon(v.x, v.y)
        f = sim.fsms[i]
        return [i, round(lat, 7), round(lon, 7), round(v.alt, 1), round(v.vx, 2), round(v.vy, 2),
                round(v.battery, 1), round(roll, 3), round(pitch, 3), round(yaw, 3),
                FSM_STATES.index(f.state) if f.state in FSM_STATES else 0, f.latch or "",
                1 if v.alive else 0]

    def _tasks(self, sim, now):
        merged = {}
        for i, b in sim.brains.items():
            if not (sim.brain_alive[i] and sim.veh[i].alive):
                continue
            for t in b.registry.tasks.values():
                cur = merged.get(t.id)
                if cur is None or _rank(t.status) > _rank(cur.status):
                    merged[t.id] = t
        snap = []
        for t in sorted(merged.values(), key=lambda t: t.id):
            d = {"id": t.id, "k": t.kind, "x": round(t.x, 1), "y": round(t.y, 1), "st": t.status,
                 "ct": round(t.created_t, 2)}
            p = t.params
            for key, short in (("n_slots", "n"), ("radius", "r"), ("area", "ar"), ("desc", "d")):
                if key in p:
                    d[short] = [round(a, 1) for a in p[key]] if key == "area" else p[key]
            snap.append(d)
        if snap != self._last_tasks:
            self._last_tasks = snap
            self.rows.append([round(now, 2), "T", snap])

    def _coverage(self, sim, now):
        for attr, water in (("grids", 0), ("flood", 1)):      # searched cells, cells under water
            union: Dict[str, int] = {}
            grids = {}
            for i, b in sim.brains.items():
                if not (sim.brain_alive[i] and sim.veh[i].alive):
                    continue
                for tid, g in getattr(b, attr, {}).items():
                    union[tid] = union.get(tid, 0) | g._bits
                    grids[tid] = g
            for tid, bits in union.items():
                h = format(bits, "x")
                key = tid + ("#water" if water else "")
                if self._last_cov.get(key) != h:
                    self._last_cov[key] = h
                    g = grids[tid]
                    row = {"id": tid, "x0": g.x0, "y0": g.y0, "cell": g.cell, "nx": g.nx, "ny": g.ny,
                           "bits": h}
                    if water:
                        row["water"] = 1
                    self.rows.append([round(now, 2), "c", row])

    def _observations(self, sim, now):
        for i, b in sim.brains.items():
            for oid, o in b.world.obs.items():
                if o.observer == i and oid not in self._seen_obs:
                    self._seen_obs.add(oid)
                    self.rows.append([round(o.t, 2), "o", [o.cls, round(o.x, 1), round(o.y, 1), i]])

    def _logs(self, sim, now):
        for (t, i, tid, ev, det) in sim.events[self._n_events:]:
            self.rows.append([round(t, 2), "e", [tid, ev, det, i]])
        self._n_events = len(sim.events)
        for (t, i, item) in sim.assign_log[self._n_assign:]:
            self.rows.append([round(t, 2), "a", [i, item]])
        self._n_assign = len(sim.assign_log)
        for (t, i, tid) in sim.suggestions[self._n_sugg:]:
            self.rows.append([round(t, 2), "s", [tid, i]])
        self._n_sugg = len(sim.suggestions)

    # -------------------------------------------------------------- output
    def meta(self, extra=None):
        f = self.sim.fleet
        sw = f.swarm
        m = {
            "name": self.name,
            "origin": [sw.origin.lat, sw.origin.lon],
            "drones": [{"id": d.id, "label": d.label, "home": [d.home_lat, d.home_lon]}
                       for d in f.drones],
            "cfg": fleet_json(f)["swarm"],
            "area": area_for_gcs(getattr(f, "area", None)),
            "victims": [[v.x, v.y] for v in self.sim.victims],
            "world": {"people": [[v.x, v.y] for v in self.sim.victims],
                      "cars": [list(c) for c in getattr(self.sim, "decoys", [])],
                      "flood": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
                                for (x0, y0, x1, y1) in getattr(self.sim, "flood_zones", [])]},
            "duration": round(self.sim.t, 1),
            "fsm_states": FSM_STATES,
        }
        m.update(extra or {})
        return m

    def save(self, path, extra_meta=None):
        self.rows.sort(key=lambda r: r[0])
        with open(path, "w") as fh:
            json.dump({"v": 1, "meta": self.meta(extra_meta), "rows": self.rows}, fh,
                      separators=(",", ":"))


def _rank(st):
    from ..tasks import STATUS_RANK
    return STATUS_RANK.get(st, -1)


def area_for_gcs(area) -> Optional[dict]:
    """Compact building/water/road geometry (ENU metres, 0.1 m) for the 3D GCS: the
    exact footprints the drones plan around, drawn without any map token."""
    if not area:
        return None

    def flat(pts):
        return [round(float(v), 1) for p in pts for v in p[:2]]
    return {
        "name": area.get("name", ""),
        "max_h": area.get("max_h", 0.0),
        "b": [[round(float(b.get("h", 0.0)), 1), round(float(b.get("base", 0.0)), 1), flat(b["poly"])]
              for b in area.get("buildings", []) if len(b.get("poly", [])) >= 3],
        "w": [flat(w["poly"]) for w in area.get("water", []) if len(w.get("poly", [])) >= 3],
        "r": [[float(r.get("w", 6)), flat(r["line"])] for r in area.get("roads", []) if len(r.get("line", [])) >= 2],
    }


def fleet_json(fleet) -> dict:
    """The subset of fleet.yaml the GCS needs (served as gcs/fleet.json)."""
    sw = fleet.swarm
    out = {
        "origin": [sw.origin.lat, sw.origin.lon],
        "drones": [{"id": d.id, "label": d.label, "home": [d.home_lat, d.home_lon]}
                   for d in fleet.drones],
        "swarm": {
            "radio_range_m": sw.radio_range_m,
            "energy": vars(sw.energy),
            "motion": vars(sw.motion),
            "formation": vars(sw.formation),
            "perception": vars(sw.perception),
            "coverage": vars(sw.coverage),
            "geofence": vars(sw.geofence),
        },
    }
    a = area_for_gcs(getattr(fleet, "area", None))
    if a:
        out["area"] = a
    return out
