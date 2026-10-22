#!/usr/bin/env python3
"""Live status board for a running swarm (any backend). Ctrl-C to quit.

    scripts/swarm_status.py            # refreshes every second

Per drone: link to its autopilot, armed, autopilot mode, safety-FSM state (and why
it is locked), altitude, battery, the work item it executes, neighbours it hears,
and what its camera detected in the last 10 s. Below: the latest mission events.
"""
import os
import time
from collections import deque

import rclpy
from rclpy.node import Node

from swarm_common.config import load_fleet
from swarm_interfaces.msg import DetectionArray, MissionEvent, NeighborReport, TaskAssignment, VehicleState

G, Y, R, D, B, X = "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


class Board(Node):
    def __init__(self, fleet):
        super().__init__("swarm_status_board")
        self.labels = [d.label for d in fleet.drones]
        self.vs, self.task, self.nbrs = {}, {}, {}
        self.dets = {lab: deque() for lab in self.labels}
        self.events = deque(maxlen=12)
        self._seen_ev = set()
        for lab in self.labels:
            self.create_subscription(VehicleState, f"/swarm/{lab}/vehicle_state",
                                     lambda m, lab=lab: self.vs.__setitem__(lab, (time.time(), m)), 10)
            self.create_subscription(DetectionArray, f"/swarm/{lab}/detections",
                                     lambda m, lab=lab: self.on_det(lab, m), 10)
        self.create_subscription(TaskAssignment, "/swarm/task_assignments", self.on_task, 50)
        self.create_subscription(MissionEvent, "/swarm/mission_event", self.on_event, 50)
        self.create_subscription(NeighborReport, "/swarm/neighbors", self.on_nbr, 50)
        self.create_timer(1.0, self.draw)

    def on_det(self, lab, m):
        now = time.time()
        for d in m.detections:
            self.dets[lab].append((now, d.class_name))

    def on_task(self, m):
        self.task[m.assigned_to] = m.item_id or "-"

    def on_nbr(self, m):
        self.nbrs[m.label] = (time.time(), len(m.neighbors), m.phase, m.current_task)

    def on_event(self, m):
        key = (m.task_id, m.event)
        if key in self._seen_ev:
            return
        self._seen_ev.add(key)
        self.events.append(f"{time.strftime('%H:%M:%S')}  {m.task_id:22s} {m.event:20s} {m.detail}")

    def draw(self):
        now = time.time()
        out = ["\033[H\033[2J" + B + "SWARM STATUS" + X + D + "   (Ctrl-C to quit)" + X, "",
               B + f"{'drone':6s}{'link':6s}{'armed':7s}{'mode':10s}{'FSM':9s}{'lock':16s}"
               f"{'alt m':>7s}{'batt%':>7s}  {'phase':11s}{'executing':24s}{'hears':>6s}  seen (10 s)" + X]
        for lab in self.labels:
            dq = self.dets[lab]
            while dq and now - dq[0][0] > 10:
                dq.popleft()
            seen = {}
            for _, c in dq:
                seen[c] = seen.get(c, 0) + 1
            seen_s = " ".join(f"{c}:{n}" for c, n in sorted(seen.items())) or D + "-" + X
            t, m = self.vs.get(lab, (0, None))
            nb = self.nbrs.get(lab)
            fresh = nb and now - nb[0] < 5
            hears = str(nb[1]) if fresh else "?"
            phase = nb[2] if fresh else "?"
            doing = (nb[3] if fresh and nb[3] else self.task.get(lab, "-")) or "-"
            if m is None or now - t > 3:
                out.append(f"{lab:6s}{R}{'none':6s}{X}  no vehicle_state - is the launch running?")
                continue
            link = (G + "ok  " if m.connected else R + "DOWN") + X
            fsm_c = G if m.fsm_state in ("GUIDED", "HOLD") else Y if m.fsm_state in ("TAKEOFF", "GROUND") else R
            out.append(f"{lab:6s}{link}  {('yes' if m.armed else 'no'):7s}{m.mode[:9]:10s}{fsm_c}{m.fsm_state:9s}{X}"
                       f"{(m.latch or '-')[:15]:16s}{m.alt:7.1f}{m.battery_pct:7.0f}  "
                       f"{phase[:10]:11s}{doing[:23]:24s}{hears:>6s}  {seen_s}")
        out += ["", B + "mission events" + X] + (list(self.events) or [D + "  (none yet)" + X])
        print("\n".join(out), flush=True)


def main():
    rclpy.init()
    node = Board(load_fleet(os.environ.get("SWARM_FLEET") or None))
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
