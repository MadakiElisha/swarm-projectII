#!/usr/bin/env python3
"""Acceptance test against a RUNNING ROS swarm (sim backend or SITL).

    ros2 launch swarm_bringup swarm_sim.launch.py        # or swarm_sitl.launch.py
    python3 scripts/ros_acceptance.py [--quick] [--csv reports/run.csv]

Criteria (all observed from the outside, like an operator would):
  A1 telemetry from every drone in fleet.yaml
  A2 every drone hears at least one neighbour (measured radio links)
  A3 operator GOTO sent to ONE drone -> exactly one drone executes it
  A4 SWARM converge -> PERIMETER_FORMED with every slot filled
  A5 operator RTL on a ring drone sticks (vehicle FSM latched, drone lands)
  A6 the remaining drones notice the loss (PERIMETER_DEGRADED)
Exit code 0 only if every criterion passes.
"""
import argparse
import csv
import os
import sys
import time

import rclpy
from rclpy.node import Node

from swarm_common.config import load_fleet
from swarm_interfaces.msg import (DroneCommand, DroneTelemetry, MissionEvent, NeighborReport,
                                  TaskAssignment, TaskRequest, VehicleState)


class Watcher(Node):
    def __init__(self, fleet, csv_path=None):
        super().__init__('swarm_acceptance')
        self.fleet = fleet
        self.telem, self.nbrs, self.vs = {}, {}, {}
        self.assign = []          # (t, label, task_id, item_id)
        self.events = []          # (t, task_id, event, reporter)
        self.t0 = time.time()
        self.csv = None
        if csv_path:
            os.makedirs(os.path.dirname(csv_path) or '.', exist_ok=True)
            self.csv = csv.writer(open(csv_path, 'w', newline=''))
            self.csv.writerow(['t', 'kind', 'label', 'alt', 'batt', 'phase', 'task', 'event'])
        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telem, 50)
        self.create_subscription(NeighborReport, '/swarm/neighbors', self.on_nbr, 50)
        self.create_subscription(TaskAssignment, '/swarm/task_assignments', self.on_asg, 50)
        self.create_subscription(MissionEvent, '/swarm/mission_event', self.on_evt, 50)
        for d in fleet.drones:
            self.create_subscription(VehicleState, f'/swarm/{d.label}/vehicle_state',
                                     lambda m: self.vs.__setitem__(m.label, m), 10)
        self.req = self.create_publisher(TaskRequest, '/swarm/task_requests', 10)
        self.cmd = self.create_publisher(DroneCommand, '/swarm/commands', 10)

    def _row(self, *a):
        if self.csv:
            self.csv.writerow([f'{time.time() - self.t0:.2f}'] + list(a) + [''] * (7 - len(a)))

    def on_telem(self, m):
        self.telem[m.label] = m
        self._row('telem', m.label, f'{m.alt:.1f}', f'{m.battery_pct:.0f}')

    def on_nbr(self, m):
        self.nbrs[m.label] = m
        self._row('phase', m.label, '', '', m.phase, m.current_task)

    def on_asg(self, m):
        self.assign.append((time.time(), m.assigned_to, m.task_id, m.item_id))

    def on_evt(self, m):
        self.events.append((time.time(), m.task_id, m.event, m.reporter))
        self._row('event', m.reporter, '', '', '', m.task_id, m.event)

    # ---------------------------------------------------------------- helpers
    def spin_until(self, cond, timeout):
        t_end = time.time() + timeout
        while time.time() < t_end:
            rclpy.spin_once(self, timeout_sec=0.2)
            if cond():
                return True
        return False

    def task(self, tid, x, y, desc=''):
        lat, lon = self.fleet.swarm.origin.to_latlon(x, y)
        m = TaskRequest(task_id=tid, lat=lat, lon=lon, description=desc)
        for _ in range(3):              # publish a few times: best-effort discovery
            self.req.publish(m)
            self.spin_until(lambda: False, 0.3)

    def executors(self, tid):
        """Drones whose LATEST assignment is (a part of) task tid."""
        last = {}
        for (_, lab, task_id, item) in self.assign:
            last[lab] = task_id
        return sorted(lab for lab, t in last.items() if t == tid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fleet', default=None)
    ap.add_argument('--csv', default=None)
    ap.add_argument('--formation-timeout', type=float, default=420.0)
    ap.add_argument('--quick', action='store_true', help='only A1-A3')
    a = ap.parse_args()
    fleet = load_fleet(a.fleet)
    n = len(fleet.drones)
    rclpy.init()
    w = Watcher(fleet, a.csv)
    results = {}

    def check(name, ok, detail=''):
        results[name] = ok
        print(f"{'PASS' if ok else 'FAIL'}: {name} {detail}", flush=True)

    labels = {d.label for d in fleet.drones}
    ok = w.spin_until(lambda: labels <= set(w.telem), 30)
    check('A1 telemetry from every drone', ok, f'({len(w.telem)}/{n})')
    ok = w.spin_until(lambda: labels <= set(w.nbrs) and all(w.nbrs[lb].neighbors for lb in labels), 30)
    check('A2 every drone hears a neighbour', ok,
          str({lb: list(r.neighbors) for lb, r in w.nbrs.items()}))

    # A3: operator reaches the swarm, gossip spreads it, exactly one drone takes it
    hx, hy = fleet.home_enu(fleet.drones[n // 2].id)
    w.task('T-ACC', hx + 250.0, hy + 150.0)
    w.spin_until(lambda: w.executors('T-ACC'), 30)
    w.spin_until(lambda: False, 8.0)                  # let consensus settle
    ex = w.executors('T-ACC')
    check('A3 exactly one drone executes a GOTO', len(ex) == 1, f'executors={ex}')

    if not a.quick:
        cx = sum(fleet.home_enu(d.id)[0] for d in fleet.drones) / n
        cy = sum(fleet.home_enu(d.id)[1] for d in fleet.drones) / n
        w.task('SWARM-ACC', cx, cy, 'acceptance ring')
        formed = w.spin_until(lambda: any(e[1] == 'SWARM-ACC' and e[2] == 'PERIMETER_FORMED'
                                          for e in w.events), a.formation_timeout)
        ring = w.executors('SWARM-ACC')
        check('A4 PERIMETER_FORMED', formed, f'ring={ring}')
        if formed and ring:
            victim = ring[0]
            t_cmd = time.time()
            w.cmd.publish(DroneCommand(label=victim, command='RTL'))
            latched = w.spin_until(lambda: victim in w.vs and w.vs[victim].latch == 'operator RTL', 10)
            stuck = latched and w.spin_until(
                lambda: w.vs[victim].fsm_state != 'RTL' and w.vs[victim].alt > 1.0, 20) is False
            check('A5 operator RTL sticks', latched and stuck,
                  f'{victim}: fsm={getattr(w.vs.get(victim), "fsm_state", "?")} '
                  f'latch={getattr(w.vs.get(victim), "latch", "?")!r}')
            deg = w.spin_until(lambda: any(e[1] == 'SWARM-ACC' and e[2] == 'PERIMETER_DEGRADED'
                                           and e[0] > t_cmd for e in w.events), 30)
            check('A6 swarm notices the loss (DEGRADED)', deg)
        else:
            check('A5 operator RTL sticks', False, '(no ring)')
            check('A6 swarm notices the loss (DEGRADED)', False, '(no ring)')

    passed = sum(results.values())
    print(f'=== ACCEPTANCE: {passed}/{len(results)} passed ===')
    w.destroy_node()
    rclpy.shutdown()
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
