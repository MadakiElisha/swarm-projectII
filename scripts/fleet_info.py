#!/usr/bin/env python3
"""Print fleet.yaml as shell lines (<id> <label> <lat> <lon> <url>), or --json for the web GCS."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ros2_ws", "src", "swarm_common"))
from swarm_common.config import load_fleet  # noqa: E402

args = [a for a in sys.argv[1:] if a != "--json"]
fleet = load_fleet(args[0] if args else None)
if "--json" in sys.argv:            # what the web GCS needs (gcs/fleet.json)
    import json
    from swarm_common.sim.recorder import fleet_json
    print(json.dumps(fleet_json(fleet), indent=1))
else:
    for d in fleet.drones:
        print(d.id, d.label, d.home_lat, d.home_lon, d.mavlink_url or "-")
