"""Scenario library: each returns a ScenarioResult with pass/fail checks.

Used by the pytest suite (CI) and by `python -m swarm_common.sim`.
"""
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from ..config import load_fleet, synthetic_fleet, SwarmCfg
from ..tasks import DONE, MERGED
from .core import NetCfg, Quarry, SwarmSim, Victim


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
    sim = SwarmSim(load_fleet(), seed=seed, net=NetCfg(loss=loss))
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
    sim = SwarmSim(load_fleet(), seed=seed, net=NetCfg(loss=loss))
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
    sim = SwarmSim(load_fleet(), seed=seed, net=NetCfg(loss=loss))
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
    sim = SwarmSim(load_fleet(), seed=seed, net=NetCfg(loss=loss))
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
    sim = SwarmSim(load_fleet(), seed=seed)
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
    sim = SwarmSim(load_fleet(), seed=seed)
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
    sim = SwarmSim(load_fleet(), seed=seed)
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
    sim = SwarmSim(load_fleet(), seed=seed)
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


ALL: Dict[str, Callable[..., ScenarioResult]] = {
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
