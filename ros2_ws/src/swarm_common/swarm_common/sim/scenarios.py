"""Scenario library: each returns a ScenarioResult with pass/fail checks.

Used by the pytest suite (CI) and by `python -m swarm_common.sim`.
"""
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from ..config import load_fleet, reference_fleet_file, synthetic_fleet, SwarmCfg
from ..tasks import DONE, MERGED
from .core import NetCfg, Quarry, SwarmSim, Victim

REF = reference_fleet_file()     # scenarios are written for the repo fleet, whatever $SWARM_FLEET says


@dataclass
class ScenarioResult:
    name: str
    sim: SwarmSim
    checks: Dict[str, bool] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(self.checks.values())

    def summary(self) -> str:
        s = self.sim
        lines = [f"== {self.name}: {'PASS' if self.passed else 'FAIL'}"]
        for k, v in self.checks.items():
            lines.append(f"   [{'x' if v else ' '}] {k}")
        lines.append(f"   min 3D separation: {s.min_sep:.1f} m  loss-of-separation samples: "
                     f"{s.los_samples}  longest double-execution: {s.longest_conflict():.1f} s  "
                     f"packets: {s.packets_sent} sent / {s.packets_delivered} delivered  "
                     f"({s.bytes_sent / max(1.0, s.t) / max(1, len(s.brains)) / 1024:.1f} KiB/s per drone)")
        lines += [f"   note: {n}" for n in self.notes]
        return "\n".join(lines)


# Asynchronous messaging means two drones can BOTH believe they hold an item
# for the instant an outbid message is in flight. What must never happen is
# sustained double execution. 3 s ~ a few gossip rounds at 10% loss.
MAX_CONFLICT_S = 3.0


def _all_agree(sim: SwarmSim, task_id: str, status: str) -> bool:
    st = sim.task_status(task_id)
    return bool(st) and all(v == status for v in st.values())


# --------------------------------------------------------------------------
def single_dispatch(seed=1, loss=0.0) -> ScenarioResult:
    """Operator reaches ONE drone; gossip spreads the task; nearest feasible drone flies it."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.at(2, lambda s: s.operator_task("T1", 1500, 800, to={1}))
    sim.run(220)
    r = ScenarioResult("single_dispatch", sim)
    flew = {i for (t, i, item) in sim.assign_log if item == "T1"}
    r.checks["task reached every drone via gossip"] = all(v != "-" for v in sim.task_status("T1").values())
    r.checks["exactly one drone executed T1"] = len(flew) == 1
    r.checks["nearest drone (D3) won"] = flew == {3}
    r.checks["all drones agree T1 is DONE"] = _all_agree(sim, "T1", DONE)
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def perimeter(seed=2, loss=0.1) -> ScenarioResult:
    """SWARM converge: 5 slots allocated by consensus, ring forms, holds, releases."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.at(2, lambda s: s.operator_task("SWARM-1", 1200, 1300, to={1}))
    sim.run(650)
    r = ScenarioResult("perimeter", sim)
    ev = sim.event_names("SWARM-1")
    r.checks["PERIMETER_FORMED declared"] = "PERIMETER_FORMED" in ev
    r.checks["RELEASED after hold"] = "RELEASED" in ev
    r.checks["no slot held by two drones (sustained)"] = sim.longest_conflict() <= MAX_CONFLICT_S
    r.checks["no loss of separation"] = sim.los_samples == 0
    r.checks["all drones back on the ground"] = all(v.alt < 0.5 for v in sim.veh.values())
    return r


def intercept(seed=3, loss=0.1) -> ScenarioResult:
    """INTERCEPT: ring centre follows a FUSED track built from every drone's sightings."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.quarry = Quarry(1000, 900, 3.0, 1.5, start=0.0, stop=400.0)
    sim.at(2, lambda s: s.operator_task("INTERCEPT-1", 1000, 900, to={2}))
    errs = []

    def watch(s):
        if 250 <= s.t <= 380 and abs(s.t % 5) < 1e-6:
            q = s.quarry.at(s.t)
            on = [i for i, b in s.brains.items() if b.phase == "ON_STATION"]
            if on and q:
                cx = sum(s.veh[i].x for i in on) / len(on)
                cy = sum(s.veh[i].y for i in on) / len(on)
                errs.append(math.hypot(cx - q[0], cy - q[1]))
    sim.run(420, watch)
    r = ScenarioResult("intercept", sim)
    r.checks["PERIMETER_FORMED around moving target"] = "PERIMETER_FORMED" in sim.event_names("INTERCEPT-1")
    mean_err = sum(errs) / len(errs) if errs else 1e9
    r.notes.append(f"mean ring-centre error vs quarry: {mean_err:.0f} m (ring radius 300 m)")
    r.checks["ring stays centred on quarry (< 150 m)"] = mean_err < 150.0
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def search_and_rescue(seed=4, loss=0.15) -> ScenarioResult:
    """SEARCH an area: decentralized coverage -> fused sightings -> HITL -> rescue."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.auto_confirm = True                     # simulated operator clicks "confirm"
    sim.victims = [Victim(900, 1300), Victim(1500, 700), Victim(500, 1500)]
    area = [300.0, 500.0, 1700.0, 1600.0]      # 1.4 km x 1.1 km
    sim.at(2, lambda s: s.operator_task("SEARCH-1", 1100, 1200, params={"area": area}, to={1, 2}))
    sim.run(900)
    r = ScenarioResult("search_and_rescue", sim)
    b = sim.brains[1]
    grid = b.grids.get("SEARCH-1")
    frac = grid.fraction() if grid else 0.0
    r.notes.append(f"area covered: {frac * 100:.0f}%")
    rescues = [t for t in b.registry.tasks.values() if t.kind == "RESCUE" and t.status != MERGED]
    done = [t for t in rescues if t.status == DONE]
    r.notes.append(f"rescue tasks: {len(rescues)} distinct, {len(done)} done; "
                   f"suggestions raised: {len(set(x[2] for x in sim.suggestions))}")
    r.checks["area >= 95% covered"] = frac >= 0.95
    r.checks["every victim found"] = all(v.found_by for v in sim.victims)
    r.checks["one rescue task per victim (dedup across drones)"] = len(rescues) == len(sim.victims)
    r.checks["all rescues completed"] = len(done) == len(sim.victims)
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def battery_handover(seed=5) -> ScenarioResult:
    """Holder's battery drains faster than modelled -> it relinquishes -> another drone takes over."""
    sim = SwarmSim(load_fleet(REF), seed=seed)
    sim.at(2, lambda s: s.operator_task("T9", 1300, 1250, params={"hold_s": 900.0}, to={1}))
    sim.run(30)
    first = sim.holders().get("T9", [None])[0]
    if first:
        sim.veh[first].drain_factor = 6.0
    sim.run(600)
    r = ScenarioResult("battery_handover", sim)
    flew = []
    for (_, i, item) in sim.assign_log:
        if item == "T9" and (not flew or flew[-1] != i):
            flew.append(i)
    r.notes.append(f"T9 executed by, in order: {flew}")
    r.checks["first holder relinquished"] = len(flew) >= 2 and flew[0] == first
    r.checks["another drone took over"] = len(flew) >= 2 and flew[1] != first
    r.checks["first holder got home without a hard failsafe"] = (
        sim.veh[first].alt < 0.5 and sim.veh[first].battery > sim.cfg.energy.critical_pct)
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def drone_loss(seed=6, loss=0.1) -> ScenarioResult:
    """7 drones, 5-slot ring. Kill a slot holder: DEGRADED, a spare fills it, FORMED again."""
    fleet = synthetic_fleet(7, spacing_m=200.0)
    sim = SwarmSim(fleet, seed=seed, net=NetCfg(loss=loss))
    sim.at(2, lambda s: s.operator_task("SWARM-7", 600, 900, to={1}))
    state = {}

    def killer(s):
        if "killed" not in state and "PERIMETER_FORMED" in s.event_names("SWARM-7") and s.t > 60:
            victim = sorted(i for items in [s.holders()] for k, v in items.items() for i in v)[0]
            state["killed"] = (victim, s.t)
            s.kill(victim)
    sim.run(500, killer)
    r = ScenarioResult("drone_loss", sim)
    ev = sim.event_names("SWARM-7")
    r.notes.append(f"events: {ev}; killed: {state.get('killed')}")
    r.checks["ring formed initially"] = "PERIMETER_FORMED" in ev
    r.checks["loss detected (DEGRADED)"] = "PERIMETER_DEGRADED" in ev
    i_deg = ev.index("PERIMETER_DEGRADED") if "PERIMETER_DEGRADED" in ev else len(ev)
    r.checks["spare filled the slot (FORMED again)"] = "PERIMETER_FORMED" in ev[i_deg:]
    r.checks["no sustained double execution among the living"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def partition_heal(seed=7) -> ScenarioResult:
    """Network splits into {1,2} | {3,4,5}. The operator reaches one drone on each side.

    Each side must keep working on its own (no single point of failure). The
    same task given to both sides gets one executor PER SIDE - unavoidable
    without communication. A second task, long enough to still be running at
    heal time, must end with exactly one executor once CBBA reconciles.
    """
    sim = SwarmSim(load_fleet(REF), seed=seed)
    sim.partition(0, 60, {1, 2})
    for side in ({1}, {5}):
        sim.at(5, lambda s, side=side: s.operator_task(
            "T5", 1400, 1400, to=side, params={"hold_s": 300.0}))
    sim.at(10, lambda s: s.operator_task("T6", 200, 1500, to={1}))     # side A only
    snap = {}
    sim.at(45, lambda s: snap.setdefault("during", {k: list(v) for k, v in s.holders().items()}))
    sim.at(80, lambda s: snap.setdefault("after", {k: list(v) for k, v in s.holders().items()}))
    sim.at(80, lambda s: snap.setdefault("t6", s.task_status("T6")))
    sim.run(200)
    r = ScenarioResult("partition_heal", sim)
    r.notes.append(f"holders during partition {snap.get('during')}, 20 s after heal {snap.get('after')}")
    r.checks["both sides acted while split (no single point of failure)"] = \
        len(snap.get("during", {}).get("T5", [])) == 2
    r.checks["exactly one executor of T5 after heal"] = len(snap.get("after", {}).get("T5", [])) == 1
    r.checks["task known only to side A reached side B after heal"] = \
        all(v != "-" for v in snap.get("t6", {}).values())
    r.checks["no conflicts once reconciled"] = sim.longest_conflict(after=70.0) <= MAX_CONFLICT_S
    r.checks["no loss of separation"] = sim.los_samples == 0
    return r


def dense_crossing(seed=8, n=10) -> ScenarioResult:
    """n drones on ONE altitude layer swap sides through the same point: ORCA only."""
    sw = SwarmCfg()
    sw.motion.layers = 1
    fleet = synthetic_fleet(n, spacing_m=60.0, swarm=sw)
    sim = SwarmSim(fleet, seed=seed)
    cx = 30.0 * (n - 1)
    for d in fleet.drones:
        hx, hy = fleet.home_enu(d.id)
        tx, ty = 2 * cx - hx, 900.0 if d.id % 2 else -900.0
        sim.at(1, lambda s, i=d.id, tx=tx, ty=ty: s.operator_task(
            f"X{i}", tx, ty, to={i}, params={"hold_s": 5.0}))
    # make each drone prefer its own task: others see it only via gossip; CBBA
    # may swap tasks, which is fine - what we test is separation.
    sim.run(300)
    r = ScenarioResult("dense_crossing", sim)
    r.checks[f"min separation >= {2 * sw.motion.safety_radius_m:.0f} m on a single layer"] = \
        sim.min_sep >= 2 * sw.motion.safety_radius_m - 0.5
    r.checks["no loss of separation"] = sim.los_samples == 0
    done = sum(1 for d in fleet.drones if sim.brains[1].registry.get(f"X{d.id}") and
               sim.brains[1].registry.get(f"X{d.id}").status == DONE)
    r.notes.append(f"{done}/{n} crossing tasks completed")
    r.checks["all crossing tasks completed"] = done == n
    return r


def operator_rtl_sticks(seed=9) -> ScenarioResult:
    """Regression for the old bug: an operator RTL during a ring mission must stick."""
    sim = SwarmSim(load_fleet(REF), seed=seed)
    sim.at(2, lambda s: s.operator_task("SWARM-2", 1200, 1300, to={1}))
    sim.run(120)
    target = sim.holders()
    victim = sorted(v[0] for v in target.values())[0] if target else 1
    sim.operator_command(victim, "RTL")
    sim.run(200)
    r = ScenarioResult("operator_rtl_sticks", sim)
    v = sim.veh[victim]
    r.checks["drone went home and landed"] = v.alt < 0.5 and math.hypot(v.x - v.home[0], v.y - v.home[1]) < 20
    r.checks["mission layer stayed locked out"] = sim.fsms[victim].latch == "operator RTL"
    r.checks["its slot was re-allocated or ring degraded honestly"] = (
        "PERIMETER_DEGRADED" in sim.event_names("SWARM-2") or
        "PERIMETER_FORMED" not in sim.event_names("SWARM-2"))
    return r


def miscalibrated_batteries(seed=10) -> ScenarioResult:
    """Every battery drains 4x faster than fleet.yaml's model (like stock ArduPilot SITL).

    Drones must learn their real drain in flight, stop bidding on work they
    can no longer afford, and get home on their own decision - never via
    the vehicle's critical-battery failsafe.
    """
    sim = SwarmSim(load_fleet(REF), seed=seed)
    for v in sim.veh.values():
        v.drain_factor = 4.0
    sim.at(2, lambda s: s.operator_task("SWARM-9", 1200, 1300, to={1}))
    sim.run(900)
    r = ScenarioResult("miscalibrated_batteries", sim)
    scales = {i: round(b.energy.scale, 1) for i, b in sim.brains.items()}
    r.notes.append(f"learned drain scale per drone: {scales}")
    crit = [i for i, f in sim.fsms.items() if f.latch == "critical battery"]
    crit += [i for (_, line) in sim.logs for i in [line.split()[0]] if "critical battery" in line]
    r.checks["every drone learned its real drain (scale 3-5x)"] = \
        all(3.0 <= k <= 5.5 for k in scales.values())
    r.checks["no critical-battery failsafe needed"] = not crit
    r.checks["every drone landed on its own"] = all(v.alt < 0.5 for v in sim.veh.values())
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    if crit:
        r.notes.append(f"failsafes: {sorted(set(crit))}")
    return r


def city_ops(seed=11, loss=0.1) -> ScenarioResult:
    """Downtown with 60-110 m towers above the 30-54 m flight layers.

    Drones must plan around towers for dispatches and a perimeter whose slots
    fall between buildings, never entering a building footprint below its roof.
    """
    from ..area import synthetic_city
    from ..config import DroneSpec, Fleet
    area = synthetic_city(blocks=6, seed=seed)
    sw = SwarmCfg()
    lx, ly = area["launch"]
    drones = []
    for i in range(5):
        lat, lon = sw.origin.to_latlon(lx + (i % 3) * 12 - 12, ly + (i // 3) * 12 - 6)
        drones.append(DroneSpec(id=i + 1, home_lat=lat, home_lon=lon))
    fleet = Fleet(swarm=sw, drones=drones, area=area)
    sim = SwarmSim(fleet, seed=seed, net=NetCfg(loss=loss))
    sim.at(2, lambda s: s.operator_task("T-NE", 380, 400, to={1}))
    sim.at(2, lambda s: s.operator_task("T-SW", -420, -380, to={1}))
    sim.at(150, lambda s: s.operator_task("SWARM-C", 160, -170, params={"radius": 180.0, "hold_s": 60.0},
                                          to={2}))
    sim.run(560)
    r = ScenarioResult("city_ops", sim)
    r.notes.append(f"towers up to {area['max_h']:.0f} m; building strikes {sim.building_hits} "
                   f"{sim.building_log[:3]}")
    r.checks["no drone ever entered a building"] = sim.building_hits == 0
    r.checks["both dispatches completed"] = all(sim.brains[1].registry.get(t) and
                                                sim.brains[1].registry.get(t).status == DONE
                                                for t in ("T-NE", "T-SW"))
    r.checks["perimeter formed among the towers"] = "PERIMETER_FORMED" in sim.event_names("SWARM-C")
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def intercept_with_decoys(seed=12, loss=0.1) -> ScenarioResult:
    """Pursuit with a realistic detector: the target is just "vehicle" (no velocity),
    and 8 parked cars nearby are also "vehicle". The gated tracker must follow
    the moving one."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.realistic_detector = True
    sim.quarry = Quarry(1000, 900, 3.0, 1.5, start=0.0, stop=400.0)
    sim.decoys = [(1000 + 60 * k, 840 + 25 * (k % 3)) for k in range(8)]   # along the target's road
    sim.at(2, lambda s: s.operator_task("INTERCEPT-2", 1000, 900, to={2}))
    errs = []

    def watch(s):
        if 250 <= s.t <= 380 and abs(s.t % 5) < 1e-6:
            q = s.quarry.at(s.t)
            tr = s.brains[2]._tracks.get("INTERCEPT-2")
            if tr is not None and q:
                errs.append(math.hypot(tr.x - q[0], tr.y - q[1]))
    sim.run(420, watch)
    r = ScenarioResult("intercept_with_decoys", sim)
    mean_err = sum(errs) / len(errs) if errs else 1e9
    r.notes.append(f"mean track error vs true target: {mean_err:.0f} m over {len(errs)} samples "
                   f"(8 decoy cars within 500 m)")
    r.checks["track follows the moving car, not the parked ones (< 40 m)"] = mean_err < 40.0
    r.checks["PERIMETER_FORMED around the moving target"] = "PERIMETER_FORMED" in sim.event_names("INTERCEPT-2")
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def flood_recon(seed=21, loss=0.15) -> ScenarioResult:
    """FLOOD recon: survey a district, map what is under water, find stranded people."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.auto_confirm = True
    zones = [(500.0, 600.0, 1100.0, 1000.0), (1200.0, 1200.0, 1600.0, 1500.0)]
    sim.flood_zones = zones
    sim.victims = [Victim(800, 800), Victim(1400, 1350), Victim(400, 1450)]   # 2 stranded, 1 dry
    area = [300.0, 500.0, 1700.0, 1600.0]
    sim.at(2, lambda s: s.operator_task("FLOOD-1", 1000, 1050, params={"area": area}, to={1}))
    sim.run(900)
    r = ScenarioResult("flood_recon", sim)
    reps = [b.flood_report("FLOOD-1") for b in sim.brains.values()]
    rep = reps[0]
    truth = sum((x1 - x0) * (y1 - y0) for (x0, y0, x1, y1) in zones)
    err = abs(rep["flooded_m2"] - truth) / truth if rep else 1.0
    if rep:
        r.notes.append(f"flood map: {rep['flooded_m2'] / 1e4:.1f} ha mapped vs {truth / 1e4:.1f} ha true "
                       f"({err * 100:.0f}% error), {rep['stranded']} stranded people")
    r.checks["FLOOD_MAP reported"] = "FLOOD_MAP" in sim.event_names("FLOOD-1")
    r.checks["flooded area within 20% of truth"] = err <= 0.20
    r.checks["every drone holds the same flood map"] = len({tuple(map(tuple, x["cells"])) for x in reps if x}) == 1
    r.checks["every person found"] = all(v.found_by for v in sim.victims)
    r.checks["stranded people identified (2)"] = rep is not None and rep["stranded"] == 2
    r.checks["no sustained double execution"] = sim.longest_conflict() <= MAX_CONFLICT_S
    return r


def patrol_intruder(seed=22, loss=0.1) -> ScenarioResult:
    """Perimeter surveillance: a standing patrol ring; parked cars and a guard inside are
    ignored; a car that drives in is detected and intercepted automatically; the patrol
    keeps going."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.realistic_detector = True
    sim.decoys = [(1150, 1250), (1260, 1330), (1190, 1380)]           # parked inside the perimeter
    sim.quarry = Quarry(1700, 1300, -3.0, 0.4, start=260.0, stop=520.0)   # drives in from the east
    sim.at(2, lambda s: s.operator_task("PATROL-1", 1200, 1300, params={"radius": 250.0}, to={1}))
    errs, ring_ok = [], []

    def watch(s):
        if s.t >= 330 and abs(s.t % 5) < 1e-6:
            q = s.quarry.at(s.t)
            ints = [t for t in s.brains[1].registry.tasks.values()
                    if t.kind == "INTERCEPT" and not t.terminal]
            if q and ints:
                tr = s.brains[1]._tracks.get(sorted(ints, key=lambda t: t.def_key())[0].id)
                if tr is not None:
                    errs.append(math.hypot(tr.x - q[0], tr.y - q[1]))
            ring_ok.append(any(e.task.startswith("PATROL-1/") for e in s.brains[1].roster.entries.values()))
    sim.run(560, watch)
    r = ScenarioResult("patrol_intruder", sim)
    b = sim.brains[1]
    ints = [t for t in b.registry.tasks.values() if t.kind == "INTERCEPT" and t.status != MERGED]
    first_intr = min((e[0] for e in sim.events if e[2] == "PATROL-1" and e[3] == "INTRUDER"), default=None)
    mean_err = sum(errs) / len(errs) if errs else 1e9
    r.notes.append(f"intercepts spawned: {len(ints)}; track error {mean_err:.0f} m; first INTRUDER at "
                   f"{first_intr if first_intr is not None else '-'} s")
    r.checks["PATROL ring formed"] = "PERIMETER_FORMED" in sim.event_names("PATROL-1")
    r.checks["no intruder alarm before the car arrives"] = not any(
        t.created_t < 260 for t in b.registry.tasks.values() if t.kind == "INTERCEPT")
    r.checks["INTRUDER raised"] = "INTRUDER" in sim.event_names("PATROL-1")
    r.checks["exactly one intercept (dedup across drones)"] = len(ints) == 1
    r.checks["intercept ring formed on the intruder"] = bool(ints) and \
        "PERIMETER_FORMED" in sim.event_names(ints[0].id)
    r.checks["track follows the intruder (< 40 m)"] = mean_err < 40.0
    r.checks["patrol still manned"] = bool(ring_ok) and all(ring_ok[-10:])
    r.checks["no loss of separation"] = sim.los_samples == 0
    return r


def intercept_chase(seed=31, loss=0.1) -> ScenarioResult:
    """The exhibition case: a car is ALREADY driving; the operator clicks where they see it.
    Drones scramble from their pads, hunt for it (cameras only see their own footprint),
    lock on to the moving one (parked cars nearby), then follow it: the ring moves with it."""
    sim = SwarmSim(load_fleet(REF), seed=seed, net=NetCfg(loss=loss))
    sim.realistic_detector = True
    sim.camera_only = True
    sim.quarry = Quarry(700, 600, 6.0, 2.5, start=0.0, stop=900.0)
    t_click = 60.0
    q0 = sim.quarry.at(t_click)
    sim.decoys = [(q0[0] + 40 + 70 * k, q0[1] + 30 + 20 * (k % 2)) for k in range(5)]
    # the operator clicks on the car and drags along its direction of travel (GCS: second click)
    hd = math.degrees(math.atan2(sim.quarry.vx, sim.quarry.vy))
    sim.at(t_click, lambda s: s.operator_task("INTERCEPT-9", q0[0], q0[1], to={1, 2},
                                              params={"heading_deg": hd}))
    st = {"near": None, "lock": None}
    errs = []

    def watch(s):
        q = s.quarry.at(s.t)
        if q is None:
            return
        if st["near"] is None and any(v.alive and v.alt > 5 and math.hypot(v.x - q[0], v.y - q[1]) < 60
                                      for v in s.veh.values()):
            st["near"] = s.t
        tk = s.brains[1]._trackers.get("INTERCEPT-9")
        if st["lock"] is None and tk is not None and tk.locked is not None:
            st["lock"] = s.t
        if s.t >= 400 and abs(s.t % 5) < 1e-6:
            tr = s.brains[1]._tracks.get("INTERCEPT-9")
            if tr is not None and tk is not None and tk.locked is not None:
                errs.append(math.hypot(tr.x - q[0], tr.y - q[1]))
            else:
                errs.append(999.0)
    sim.run(720, watch)
    r = ScenarioResult("intercept_chase", sim)
    mean_err = sum(errs) / len(errs) if errs else 1e9
    r.notes.append(f"first drone within 60 m of the car {st['near'] and st['near'] - t_click:.0f} s after the "
                   f"click; locked {st['lock'] and st['lock'] - t_click:.0f} s after; follow error {mean_err:.0f} m")
    r.checks["a drone reaches the car within 120 s of the click"] = st["near"] is not None and \
        st["near"] - t_click <= 120
    r.checks["locked on to the moving car"] = st["lock"] is not None
    r.checks["keeps following it (mean error < 40 m over 5 min)"] = mean_err < 40.0
    r.checks["ring formed around the moving car"] = "PERIMETER_FORMED" in sim.event_names("INTERCEPT-9")
    r.checks["no loss of separation"] = sim.los_samples == 0
    return r


def chase_among_towers(seed=33, loss=0.1) -> ScenarioResult:
    """A car driving down a street between 60-110 m towers. Chasing it, drones switch between
    search height (wide view) and ring height again and again, right next to and over roofs:
    nobody may descend onto a roof or fly into a wall (the Gazebo crash this guards against)."""
    from ..area import synthetic_city
    from ..config import DroneSpec, Fleet
    area = synthetic_city(blocks=6, seed=11)
    sw = SwarmCfg()
    lx, ly = area["launch"]
    drones = []
    for i in range(4):
        lat, lon = sw.origin.to_latlon(lx + (i % 2) * 15 - 8, ly + (i // 2) * 15 - 8)
        drones.append(DroneSpec(id=i + 1, home_lat=lat, home_lon=lon))
    sim = SwarmSim(Fleet(swarm=sw, drones=drones, area=area), seed=seed, net=NetCfg(loss=loss))
    sim.realistic_detector = True
    sim.camera_only = True
    sim.quarry = Quarry(-440, 135, 5.0, 0.0, start=0.0, stop=900.0)       # east along y=135
    q0 = sim.quarry.at(20.0)
    sim.at(20.0, lambda s: s.operator_task("INTERCEPT-T", q0[0], q0[1], to={1, 2}, params={"heading_deg": 90.0}))
    sim.run(420)
    r = ScenarioResult("chase_among_towers", sim)
    r.notes.append(f"towers up to {area['max_h']:.0f} m; building strikes {sim.building_hits} "
                   f"{sim.building_log[:3]}")
    r.checks["no drone ever entered a building"] = sim.building_hits == 0
    r.checks["ring formed around the car"] = "PERIMETER_FORMED" in sim.event_names("INTERCEPT-T")
    r.checks["no loss of separation"] = sim.los_samples == 0
    return r


def exhibition_round(seed=41, loss=0.1) -> ScenarioResult:
    """One round of scripts/demo.py: 5 drones patrol (wide view, no reserve); a car drives in
    from outside and stops inside; the patrol's cameras raise it; two drones break off, one
    holds over the stopped car, three keep patrolling; called off, all land on their pads."""
    from ..area import synthetic_city
    from ..config import DroneSpec, Fleet
    area = synthetic_city(blocks=6, seed=11)
    sw = SwarmCfg()
    lx, ly = area["launch"]
    drones = []
    for i in range(5):
        lat, lon = sw.origin.to_latlon(lx + (i % 3) * 15 - 15, ly + (i // 3) * 15 - 8)
        drones.append(DroneSpec(id=i + 1, home_lat=lat, home_lon=lon))
    sim = SwarmSim(Fleet(swarm=sw, drones=drones, area=area), seed=seed, net=NetCfg(loss=loss))
    sim.realistic_detector = True
    sim.camera_only = True
    c = (135.0, 135.0)
    sim.decoys = [(150, 120), (100, 150)]                       # parked inside: not intruders
    t_car = 120.0
    sim.quarry = Quarry(-300, 135, 6.0, 0.0, start=t_car, stop=t_car + 430 / 6.0)   # stops at (130, 135)
    sim.at(2, lambda s: s.operator_task("PATROL-X", c[0], c[1], params={
        "radius": 90.0, "reserve": 0, "responders": 2, "intercept_hold_s": 1800.0, "wide_view": True}, to={1}))
    st = {"split": None, "over": []}

    def watch(s):
        q = s.quarry.at(s.t)
        roles = [s.brains[i].current_item() or "" for i in s.brains]
        if st["split"] is None and sum(r.startswith("INTERCEPT-") for r in roles) == 2:
            st["split"] = (s.t, sum(r.startswith("PATROL-X") for r in roles))
        if q and s.t > t_car + 430 / 6.0 + 15 and s.t < 300 and abs(s.t % 5) < 1e-6:
            st["over"].append(min(math.hypot(v.x - q[0], v.y - q[1]) for v in s.veh.values()))
        if abs(s.t - 300.0) < 1e-6:
            for t in list(s.brains[1].registry.tasks.values()):
                if not t.terminal:
                    s.operator_task("CANCEL-" + t.id, 0.0, 0.0, to={1})
    sim.run(560, watch)
    r = ScenarioResult("exhibition_round", sim)
    ints = [e for e in sim.events if e[2] == "PATROL-X" and e[3] == "INTRUDER"]
    r.notes.append(f"intruder raised at {ints[0][0] - t_car:.0f} s after the car set off" if ints else "no intruder")
    r.notes.append(f"split {st['split']}; nearest drone over the stopped car: "
                   f"{max(st['over']) if st['over'] else -1:.0f} m (worst sample)")
    r.checks["patrol formed"] = "PERIMETER_FORMED" in sim.event_names("PATROL-X")
    r.checks["the cameras raised the intruder (no help)"] = bool(ints) and ints[0][0] > t_car
    r.checks["two break off, three keep patrolling"] = st["split"] is not None and st["split"][1] == 3
    r.checks["a drone holds over the stopped car (< 25 m)"] = bool(st["over"]) and max(st["over"]) < 25.0
    r.checks["all back on their pads after the call-off"] = all(v.alt < 0.5 for v in sim.veh.values())
    r.checks["no drone ever entered a building"] = sim.building_hits == 0
    r.checks["no loss of separation"] = sim.los_samples == 0
    return r


ALL: Dict[str, Callable[..., ScenarioResult]] = {
    "intercept_chase": intercept_chase,
    "exhibition_round": exhibition_round,
    "chase_among_towers": chase_among_towers,
    "flood_recon": flood_recon,
    "patrol_intruder": patrol_intruder,
    "intercept_with_decoys": intercept_with_decoys,
    "city_ops": city_ops,
    "miscalibrated_batteries": miscalibrated_batteries,
    "single_dispatch": single_dispatch,
    "perimeter": perimeter,
    "intercept": intercept,
    "search_and_rescue": search_and_rescue,
    "battery_handover": battery_handover,
    "drone_loss": drone_loss,
    "partition_heal": partition_heal,
    "dense_crossing": dense_crossing,
    "operator_rtl_sticks": operator_rtl_sticks,
}
