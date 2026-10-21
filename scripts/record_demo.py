#!/usr/bin/env python3
"""Record the showcase mission for the GCS replay mode (no ROS needed).

    python3 scripts/record_demo.py                 # -> gcs/demos/showcase.json
    python3 scripts/record_demo.py --loss 0.2 --out /tmp/x.json

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

from swarm_common.config import DroneSpec, Fleet, SwarmCfg  # noqa: E402
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "gcs", "demos", "showcase.json"))
    ap.add_argument("--loss", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()

    fleet = staging_fleet()
    sim = SwarmSim(fleet, seed=a.seed, net=NetCfg(loss=a.loss, operator_ids={1, 2}))
    sim.auto_confirm = True
    rec = Recorder(sim, name="showcase")
    sim.victims = [Victim(500, 900), Victim(1050, 450), Victim(250, 1300)]
    area = [0.0, 300.0, 1300.0, 1500.0]
    search = {"area": area, "desc": "flood zone sweep"}
    ring = {"radius": 220.0, "hold_s": 150.0}
    sim.at(3, lambda s: s.operator_task("SEARCH-1", 650, 900, params=search))
    sim.at(380, lambda s: s.operator_task("SWARM-1", 900, 1000, params=ring))
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
            s.quarry = Quarry(300, 1100, 3.5, -1.2, start=s.t, stop=s.t + 400)
            s.operator_task("INTERCEPT-1", 300, 1100, params={"radius": 180.0, "hold_s": 120.0})
            print(f"t={s.t:.0f}s: INTERCEPT issued")
    sim.run(1000, chaos)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    rec.save(a.out, {"story": [
        [3, "SEARCH-1: operator marks the flood zone (heard by D1, D2 only - gossip spreads it)"],
        [380, "SWARM-1: operator asks for a perimeter; slots allocated by CBBA consensus"],
        [state.get("formed", 0) + 35, f"D{state.get('killed', '?')} lost mid-ring - no leader to fail"],
        [state.get("intercept", 0), "INTERCEPT-1: ring follows the track fused from every drone's sightings"],
    ]})
    ev = sorted({(round(e[0]), e[2], e[3]) for e in sim.events})
    print("events:", ev[:20])
    print(f"victims found: {[v.found_by for v in sim.victims]}  min separation {sim.min_sep:.1f} m  "
          f"longest double-execution {sim.longest_conflict():.1f} s")
    print(f"{len(rec.rows)} rows -> {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
