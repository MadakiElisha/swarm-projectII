#!/usr/bin/env python3
"""Print fleet.yaml as shell-friendly lines: <id> <label> <home_lat> <home_lon> <mavlink_url>"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ros2_ws", "src", "swarm_common"))
from swarm_common.config import load_fleet  # noqa: E402

fleet = load_fleet(sys.argv[1] if len(sys.argv) > 1 else None)
for d in fleet.drones:
    print(d.id, d.label, d.home_lat, d.home_lon, d.mavlink_url or "-")
