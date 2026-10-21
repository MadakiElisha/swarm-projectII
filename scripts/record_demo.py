#!/usr/bin/env python3
"""Record missions for the GCS replay mode (no ROS needed).

    python3 scripts/record_demo.py                       # -> gcs/demos/showcase.json
    python3 scripts/record_demo.py --mission flood       # -> gcs/demos/flood.json
    python3 scripts/record_demo.py --mission patrol      # -> gcs/demos/patrol.json
    python3 scripts/record_demo.py --loss 0.2 --out /tmp/x.json
    python3 scripts/record_demo.py --mission patrol --fleet areas/eko/fleet.yaml   # among real buildings

Open one with gcs/index.html?replay=demos/<name>.json

showcase:
7 drones launch together from one staging site (Lagos lagoon shore) and:
  1. SEARCH a 1.2 x 0.9 km area; sightings are fused across drones, the
     simulated operator confirms each suggestion, RESCUE tasks are allocated
  2. form a 5-slot PERIMETER by consensus
  3. lose a ring drone mid-hold: survivors report DEGRADED, a spare takes the slot
  4. INTERCEPT a moving target, ring centred on the fused track
Every decision is made by the drones' own brains (CBBA over a lossy radio).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ros2_ws", "src", "swarm_common"))

from swarm_common.config import DroneSpec, Fleet, SwarmCfg, load_fleet  # noqa: E402
from swarm_common.geo import Origin  # noqa: E402
from swarm_common.sim.core import NetCfg, Quarry, SwarmSim, Victim  # noqa: E402
from swarm_common.sim.recorder import Recorder  # noqa: E402


def staging_fleet(n=7, origin=Origin(6.4500, 3.4030)):
    """n drones on one launch pad grid, 15 m apart (take off together)."""
    sw = SwarmCfg(origin=origin)
    drones = []
    for i in range(n):
        x, y = (i % 4) * 15.0, (i // 4) * 15.0
        lat, lon = origin.to_latlon(x, y)
        drones.append(DroneSpec(id=i + 1, home_lat=lat, home_lon=lon))
    return Fleet(swarm=sw, drones=drones)


class Mission:
    """Mission geometry is written around a local centre (650, 900); with an OSM
    area fleet everything is shifted onto the area's centre, so the same missions
    fly among real buildings."""
    def __init__(self, a):
        if a.fleet:
            self.fleet = load_fleet(a.fleet)
            self.dx, self.dy = -650.0, -900.0
        else:
            self.fleet, self.dx, self.dy = staging_fleet(), 0.0, 0.0
        self.sim = SwarmSim(self.fleet, seed=a.seed, net=NetCfg(loss=a.loss, operator_ids={1, 2}))

    def p(self, x, y):
        return x + self.dx, y + self.dy

    def rect(self, x0, y0, x1, y1):
        return (*self.p(x0, y0), *self.p(x1, y1))

    def task(self, t, tid, x, y, params):
        self.sim.at(t, lambda s: s.operator_task(tid, *self.p(x, y), params=params))


def flood(a):
    """FLOOD recon: map what is under water, find people stranded in it."""
    m = Mission(a)
    sim = m.sim
    sim.auto_confirm = True
    rec = Recorder(sim, name="flood recon")
    sim.flood_zones = [m.rect(80, 450, 700, 900), m.rect(850, 1000, 1250, 1400)]
    sim.victims = [Victim(*m.p(400, 700)), Victim(*m.p(1000, 1200)), Victim(*m.p(1100, 500))]  # 2 stranded
    m.task(3, "FLOOD-1", 650, 900, {"area": list(m.rect(0, 300, 1300, 1500)), "desc": "flood recon"})
    sim.run(800)
    rep = sim.brains[1].flood_report("FLOOD-1")
    story = [[3, "FLOOD-1: operator marks the district; the swarm splits the survey with no leader"],
             [60, "Blue = water seen by any drone's camera, merged by gossip (every drone holds the same map)"],
             [300, "People seen in flood water become RESCUE tasks; the operator confirms, a drone goes"]]
    return sim, rec, story, f"flood map: {rep and round(rep['flooded_m2'] / 1e4, 1)} ha, " \
                            f"{rep and rep['stranded']} stranded"


def patrol(a):
    """PATROL a perimeter; a car drives in; the nearest patrollers intercept it."""
    m = Mission(a)
    sim = m.sim
    sim.realistic_detector = True
    rec = Recorder(sim, name="perimeter patrol")
    sim.decoys = [m.p(620, 880), m.p(700, 960), m.p(560, 1010)]       # parked inside: ignored
    sim.quarry = Quarry(*m.p(1150, 1000), -2.8, 0.5, start=250.0, stop=600.0)
    m.task(3, "PATROL-1", 650, 950, {"radius": 260.0, "desc": "guard the depot"})
    sim.run(620)
    story = [[3, "PATROL-1: a standing patrol ring, one drone kept in reserve"],
             [120, "Parked cars and people standing still inside the perimeter never raise an alarm"],
             [250, "A car drives in from the east"],
             [330, "INTRUDER: the nearest drones leave the patrol to intercept; the ring keeps flying"]]
    return sim, rec, story, ""


def showcase(a):
    """SEARCH + RESCUE, PERIMETER with a drone lost mid-ring, then INTERCEPT."""
    m = Mission(a)
    sim = m.sim
    sim.auto_confirm = True
    rec = Recorder(sim, name="showcase")
    sim.victims = [Victim(*m.p(500, 900)), Victim(*m.p(1050, 450)), Victim(*m.p(250, 1300))]
    m.task(3, "SEARCH-1", 650, 900, {"area": list(m.rect(0, 300, 1300, 1500)), "desc": "flood zone sweep"})
    m.task(380, "SWARM-1", 900, 1000, {"radius": 220.0, "hold_s": 150.0})
    state = {}

    def chaos(s):
        ev = s.event_names("SWARM-1")
        if "killed" not in state and "PERIMETER_FORMED" in ev:
            state.setdefault("formed", s.t)
            if s.t - state["formed"] > 35:
                holders = sorted(i for k, v in s.holders().items() if k.startswith("SWARM-1/")
                                 for i in v)
                if holders:
                    state["killed"] = holders[len(holders) // 2]
                    s.kill(state["killed"])
                    print(f"t={s.t:.0f}s: killed D{state['killed']} mid-ring")
        if "intercept" not in state and "RELEASED" in ev:
            state["intercept"] = s.t
            s.quarry = Quarry(*m.p(300, 1100), 3.5, -1.2, start=s.t, stop=s.t + 400)
            s.operator_task("INTERCEPT-1", *m.p(300, 1100), params={"radius": 180.0, "hold_s": 120.0})
            print(f"t={s.t:.0f}s: INTERCEPT issued")
    sim.run(1000, chaos)
    story = [
        [3, "SEARCH-1: operator marks the flood zone (heard by D1, D2 only - gossip spreads it)"],
        [380, "SWARM-1: operator asks for a perimeter; slots allocated by CBBA consensus"],
        [state.get("formed", 0) + 35, f"D{state.get('killed', '?')} lost mid-ring - no leader to fail"],
        [state.get("intercept", 0), "INTERCEPT-1: ring follows the track fused from every drone's sightings"],
    ]
    return sim, rec, story, f"victims found: {[v.found_by for v in sim.victims]}  " \
                            f"longest double-execution {sim.longest_conflict():.1f} s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mission", choices=["showcase", "flood", "patrol"], default="showcase")
    ap.add_argument("--fleet", help="fly in an OSM area, e.g. areas/eko/fleet.yaml (scripts/make_area.py)")
    ap.add_argument("--out")
    ap.add_argument("--loss", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    a.out = a.out or os.path.join(HERE, "..", "gcs", "demos", f"{a.mission}.json")
    sim, rec, story, note = {"showcase": showcase, "flood": flood, "patrol": patrol}[a.mission](a)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    rec.save(a.out, {"story": story})
    print("events:", sorted({(round(e[0]), e[2], e[3]) for e in sim.events})[:20])
    print(f"{note}  min separation {sim.min_sep:.1f} m (loss-of-separation samples {sim.los_samples}, "
          f"building hits {getattr(sim, 'building_hits', 0)})")
    print(f"{len(rec.rows)} rows -> {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
