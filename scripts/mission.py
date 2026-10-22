#!/usr/bin/env python3
"""Operator commands from the terminal (same messages the web GCS sends).

Positions are metres east,north of the area origin ("0,0" = centre of the map),
or lat,lon with --ll. The swarm decides who does what; this only asks.

    scripts/mission.py search  --at 0,0 --size 600x400        # SAR: survey + rescue suggestions
    scripts/mission.py flood   --at 0,0 --size 600x400        # flood recon + flood map
    scripts/mission.py perimeter --at 150,-100 [--radius 120]  # ring, holds, releases
    scripts/mission.py patrol  --at 0,0 --radius 200          # standing patrol ring
    scripts/mission.py intruder --at 400,0 [--to 0,0]         # SIM: a car drives into the patrol area
    scripts/mission.py intercept [--at x,y]                   # SIM car starts there; swarm pursues it
    scripts/mission.py goto    --at 200,50                    # one drone goes there
    scripts/mission.py confirm RESCUE-3-1                     # confirm a perception suggestion
    scripts/mission.py cancel  PATROL-1234
    scripts/mission.py rtl D2 | land ALL | resume ALL | estop ALL

Without --at, intercept/intruder use the moving car from the Gazebo world (world.json).
"""
import argparse
import json
import os
import sys
import time

import rclpy
from rclpy.node import Node

from swarm_common.config import load_fleet
from swarm_interfaces.msg import DroneCommand, TaskRequest


def _xy(s):
    a, b = (float(v) for v in s.split(","))
    return a, b


def main():
    ap = argparse.ArgumentParser(description="send operator commands to the swarm",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("what", choices=["search", "flood", "perimeter", "patrol", "intercept", "intruder",
                                     "goto", "confirm", "cancel", "rtl", "land", "resume", "estop"])
    ap.add_argument("arg", nargs="?", default=None, help="task id (confirm/cancel) or D<n>/ALL (rtl/land/...)")
    ap.add_argument("--at", default=None, help="x,y metres from the origin (or lat,lon with --ll)")
    ap.add_argument("--ll", action="store_true")
    ap.add_argument("--size", default="600x400", help="search/flood area WxH metres")
    ap.add_argument("--radius", type=float, default=None)
    ap.add_argument("--to", default="0,0", help="intruder: x,y it drives towards (along streets)")
    ap.add_argument("--fleet", default=None)
    a = ap.parse_args()

    fleet = load_fleet(a.fleet)
    o = fleet.swarm.origin

    def to_ll(xy):
        return xy if a.ll else o.to_latlon(*xy)

    def car_start():
        info = os.environ.get("SWARM_GZ_INFO", "")
        if info and os.path.isfile(info):
            t = json.load(open(info)).get("target")
            if t:
                return tuple(t)
        sys.exit("give --at x,y (no Gazebo world.json with a target car found; source sim/gz/<area>/env.sh)")

    rclpy.init()
    node = Node("swarm_operator_cli")
    req = node.create_publisher(TaskRequest, "/swarm/task_requests", 10)
    sim = node.create_publisher(TaskRequest, "/swarm/sim/start_target", 10)
    cmd = node.create_publisher(DroneCommand, "/swarm/commands", 10)

    n = int(time.time()) % 100000
    at = _xy(a.at) if a.at else None
    msgs = []
    if a.what in ("rtl", "land", "resume", "estop"):
        m = DroneCommand()
        m.label, m.command = (a.arg or "ALL").upper(), a.what.upper()
        msgs.append((cmd, m, f"{m.command} -> {m.label}"))
    elif a.what in ("confirm", "cancel"):
        if not a.arg:
            sys.exit("give the task id")
        m = TaskRequest()
        m.task_id = a.arg if a.what == "confirm" else "CANCEL-" + a.arg
        m.lat, m.lon = o.lat, o.lon
        msgs.append((req, m, m.task_id))
    else:
        if a.what in ("intercept", "intruder") and at is None:
            at = car_start()
        if at is None:
            at = (0.0, 0.0)
        lat, lon = to_ll(at)
        m = TaskRequest()
        m.lat, m.lon = lat, lon
        if a.what in ("search", "flood"):
            w, h = (float(v) for v in a.size.lower().split("x"))
            cx, cy = at if not a.ll else o.to_enu(*at)
            la0, lo0 = o.to_latlon(cx - w / 2, cy - h / 2)
            la1, lo1 = o.to_latlon(cx + w / 2, cy + h / 2)
            m.task_id = f"{a.what.upper()}-{n}"
            m.description = f"area={la0:.6f},{lo0:.6f},{la1:.6f},{lo1:.6f}"
        elif a.what == "perimeter":
            m.task_id = f"SWARM-{n}"
            m.description = f"radius={a.radius:.0f}" if a.radius else "operator"
        elif a.what == "patrol":
            m.task_id = f"PATROL-{n}"
            m.description = f"radius={a.radius or 200:.0f}"
        elif a.what == "intercept":
            m.task_id = f"INTERCEPT-{n}"
            m.description = "operator: pursue this vehicle"
        elif a.what == "intruder":
            m.task_id = f"SIM-INTRUDER-{n}"
            m.description = f"toward={a.to}"
            msgs.append((sim, m, f"simulated intruder car starts at {at[0]:.0f},{at[1]:.0f}"))
            m = None
        elif a.what == "goto":
            m.task_id = f"T{n}"
            m.description = "operator goto"
        if m is not None:
            msgs.append((req, m, f"{m.task_id} at {at[0]:.0f},{at[1]:.0f}" +
                         (f"  ({m.description})" if m.description else "")))
    for pub, m, text in msgs:
        t_end = time.time() + 8.0                 # wait for discovery: someone must be listening
        while pub.get_subscription_count() == 0 and time.time() < t_end:
            rclpy.spin_once(node, timeout_sec=0.2)
        if pub.get_subscription_count() == 0:
            print(f"warning: nobody is subscribed to {pub.topic_name} - is the swarm launch running?")
        time.sleep(0.5)
        for _ in range(3):                        # best effort: brains dedupe by id
            pub.publish(m)
            time.sleep(0.2)
        print("sent:", text)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
