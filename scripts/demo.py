#!/usr/bin/env python3
"""Exhibition director: runs the swarm story in rounds, one key press per round.

    1/5 LAUNCH       the swarm takes off from its pads and forms a patrol ring
    2/5 INTRUSION    a car drives into the patrolled area from outside
    3/5 ACQUISITION  a drone's camera sees it moving -> TARGET IDENTIFIED
    4/5 TRACKING     two drones break off to follow it, the other three keep patrolling;
                     the car stops and the two hold over it (one overhead, one circling)
    5/5 RESET        tasks called off, every drone flies home and lands on its pad,
                     simulated batteries swapped, the car goes back outside

It only does what an operator does (the same task requests and commands as the GCS and
scripts/mission.py) plus two simulator props: the car (target_mover) and the simulated
battery swap. The swarm decides who goes where. It refuses to run against real drones.

If a stage doesn't happen in time (the cameras miss the car, say) it nudges it the way an
operator would - it hands the car's position to the swarm - and says so on screen. Every
stage has a time limit, so a round always ends on the pads.

    scripts/demo.py                    # 5 drones, patrol placed automatically near the pads
    scripts/demo.py --radius 120 --centre 300,150 --hold 40

Or the structure-inspection mission (precision approach + standoff, no contact):

    1/5 LAUNCH       takes off; two drones take high overwatch
    2/5 APPROACH     three drones make a fast precision run to a chosen building
    3/5 STANDOFF     each arrests ~18 m off the walls - a cordon clear of the structure (no contact)
    4/5 INSPECT      hold the standoff, cameras on the façades
    5/5 RESET        home and land

    scripts/demo.py --mission inspect [--structure x,y] [--inspect-hold 45]

Keys (then Enter): Enter = start the next round, r = reset now, q = quit after this round.
"""
import argparse
import json
import math
import os
import queue
import shutil
import subprocess
import sys
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from swarm_common.config import load_fleet
from swarm_common.roads import RoadGraph
from swarm_interfaces.msg import DroneCommand, MissionEvent, NeighborReport, TargetTrack, TaskRequest, VehicleState

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
C = {"b": "\033[1m", "y": "\033[1;33m", "g": "\033[1;32m", "r": "\033[1;31m", "c": "\033[1;36m",
     "d": "\033[2m", "0": "\033[0m"}
STAGES = {0: "READY", 1: "LAUNCH", 2: "INTRUSION", 3: "ACQUISITION", 4: "TRACKING", 5: "RESET"}
STAGE_NAMES = {
    "patrol": {0: "READY", 1: "LAUNCH", 2: "INTRUSION", 3: "ACQUISITION", 4: "TRACKING", 5: "RESET"},
    "inspect": {0: "READY", 1: "LAUNCH", 2: "APPROACH", 3: "STANDOFF", 4: "INSPECT", 5: "RESET"},
}


def say(txt, col="0"):
    print(f"{C['d']}{time.strftime('%H:%M:%S')}{C['0']}  {C[col]}{txt}{C['0']}", flush=True)


def banner(txt, col="y"):
    w = max(46, len(txt) + 8)
    print(f"\n{C[col]}{'=' * w}\n{txt.center(w)}\n{'=' * w}{C['0']}\n", flush=True)


class Director(Node):
    def __init__(self, a):
        # in Gazebo the stage timers run on Gazebo's clock (like the drones): a PC that can't keep
        # Gazebo at real time slows the show down instead of cutting stages short
        gz = os.environ.get("SWARM_MODE") == "gazebo" and not a.wall_clock
        super().__init__("demo_director", parameter_overrides=[Parameter("use_sim_time", value=gz)])
        self.a = a
        self.fleet = load_fleet(a.fleet)
        self.o = self.fleet.swarm.origin
        self.labels = [d.label for d in self.fleet.drones]
        self.vs, self.nb, self.events, self.car = {}, {}, [], None
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.stage_pub = self.create_publisher(String, "/swarm/demo/stage", latched)
        self.req = self.create_publisher(TaskRequest, "/swarm/task_requests", 10)
        self.sim = self.create_publisher(TaskRequest, "/swarm/sim/start_target", 10)
        self.cmd = self.create_publisher(DroneCommand, "/swarm/commands", 10)
        for lb in self.labels:
            self.create_subscription(VehicleState, f"/swarm/{lb}/vehicle_state",
                                     lambda m, lb=lb: self.vs.__setitem__(lb, (self.now(), m)), 10)
        self.create_subscription(NeighborReport, "/swarm/neighbors",
                                 lambda m: self.nb.__setitem__(m.label, (self.now(), m)), 50)
        self.create_subscription(MissionEvent, "/swarm/mission_event",
                                 lambda m: self.events.append((self.now(), m)), 100)
        self.create_subscription(TargetTrack, "/swarm/target_track", self._on_car, 10)
        self.round = 0
        self.keys = queue.Queue()
        self.reset_now = False
        self.quit = False
        self.gz_ok = None
        if self.a.mission == "inspect":
            self.struct = self._pick_structure()
            self.plan = {"pads": self.struct["pads"], "starts": [], "centre": (self.struct["cx"], self.struct["cy"]),
                         "radius": self.struct["R"]}
        else:
            self.plan = self._plan()

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def wait_clock(self):
        t_end = time.time() + 15.0
        while self.now() == 0.0:                 # Gazebo's clock not running yet
            rclpy.spin_once(self, timeout_sec=0.2)
            if time.time() > t_end:
                say("no Gazebo clock on /clock - timing the stages by the wall clock", "r")
                self.set_parameters([Parameter("use_sim_time", value=False)])
                break

    # ------------------------------------------------------------ inputs
    def _on_car(self, m):
        x, y = self.o.to_enu(m.lat, m.lon)
        self.car = (self.now(), x, y, m.vel_e, m.vel_n)

    def spin_for(self, s):
        end = self.now() + s
        while self.now() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
            self._poll_keys()

    def wait(self, cond, timeout, every=None):
        """Spin until cond() is truthy (returns it) or timeout (returns None). 'r' aborts."""
        end, nxt = self.now() + timeout, 0.0
        while self.now() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
            self._poll_keys()
            if self.reset_now:
                return None
            v = cond()
            if v:
                return v
            if every and self.now() >= nxt:
                nxt = self.now() + 10.0
                every()
        return None

    def _poll_keys(self):
        while not self.keys.empty():
            k = self.keys.get()
            if k == "r":
                if not self.reset_now:
                    say("reset requested", "r")
                self.reset_now = True
            elif k == "q":
                self.quit = True
                say("will stop after this round", "r")

    # ------------------------------------------------------------ outputs
    def stage(self, n, title, detail="", **extra):
        names = STAGE_NAMES[self.a.mission]
        msg = {"round": self.round, "stage": n, "name": names[n], "names": [names[k] for k in range(1, 6)],
               "title": title, "detail": detail, "t": time.time()}
        msg.update(extra)
        self.stage_pub.publish(String(data=json.dumps(msg)))
        if n:
            banner(f"{n}/5  {names[n]}  -  {title}", "c")
        if detail:
            say(detail)

    def task(self, tid, x, y, desc=""):
        m = TaskRequest()
        m.task_id, m.description = tid, desc
        m.lat, m.lon = self.o.to_latlon(x, y)
        self.req.publish(m)

    def cancel(self, tid):
        m = TaskRequest()
        m.task_id = "CANCEL-" + tid
        m.lat, m.lon = self.o.lat, self.o.lon
        self.req.publish(m)

    def command(self, label, c):
        m = DroneCommand()
        m.label, m.command = label, c
        self.cmd.publish(m)

    def car_cmd(self, x, y, desc):
        m = TaskRequest()
        m.task_id = f"DEMO-CAR-{self.round}"
        m.lat, m.lon = self.o.to_latlon(x, y)
        m.description = desc
        for _ in range(3):                   # best effort topic: say it a few times
            self.sim.publish(m)
            self.spin_for(0.2)

    def gz_view(self, *args):
        """Point the Gazebo window (only if Gazebo's GUI is up)."""
        if os.environ.get("SWARM_MODE") != "gazebo" or not shutil.which("gz"):
            return
        if self.gz_ok is None or (self.gz_ok is False and self.round <= 1):
            try:
                out = subprocess.run(["gz", "service", "-l"], capture_output=True, text=True, timeout=8).stdout
                self.gz_ok = "/gui/follow" in out
            except (OSError, subprocess.TimeoutExpired):
                self.gz_ok = False
        if self.gz_ok:
            subprocess.Popen([os.path.join(ROOT, "scripts", "gz", "view.sh"), *args],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ------------------------------------------------------------ geometry
    def _plan(self):
        """Patrol centre near the pads; car routes that start outside and end at the centre."""
        pads = [self.fleet.home_enu(d.id) for d in self.fleet.drones]
        px, py = sum(p[0] for p in pads) / len(pads), sum(p[1] for p in pads) / len(pads)
        R = self.a.radius
        roads = (self.fleet.area or {}).get("roads") or []
        g = RoadGraph(roads) if roads else None
        if self.a.centre:
            cx, cy = (float(v) for v in self.a.centre.split(","))
            if g:
                cx, cy = g.nodes[g.nearest((cx, cy))]
            cands = [(cx, cy)]
        elif g:
            cands = sorted((n for n in g.nodes if R + 50 <= math.hypot(n[0] - px, n[1] - py) <= R + 220),
                           key=lambda n: abs(math.hypot(n[0] - px, n[1] - py) - (R + 90)))[:25]
        else:
            cands = [(px + R + 90, py)]
        best = None
        for c in cands:
            routes = []
            if g:
                for n in g.nodes:
                    d = math.hypot(n[0] - c[0], n[1] - c[1])
                    if not (R * 1.2 + 150 <= d <= R * 1.2 + 380):
                        continue
                    path = [n] + g.shortest(n, c)
                    if len(path) < 2 or math.hypot(path[-1][0] - c[0], path[-1][1] - c[1]) > 5:
                        continue
                    ln = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
                    near_pads = min(math.hypot(p[0] - px, p[1] - py) for p in path)
                    if ln <= 2.2 * d and near_pads > 60:
                        routes.append((ln, n))
            else:
                for k in range(6):
                    b = math.radians(30 + 60 * k)
                    n = (c[0] + (R * 1.2 + 250) * math.cos(b), c[1] + (R * 1.2 + 250) * math.sin(b))
                    if math.hypot(n[0] - px, n[1] - py) > R + 150:
                        routes.append((R * 1.2 + 250, n))
            # spread the starts around the circle: every round comes from a different side
            routes.sort()
            picked = []
            for ln, n in routes:
                ang = math.atan2(n[1] - c[1], n[0] - c[0])
                if all(abs(math.atan2(math.sin(ang - q), math.cos(ang - q))) > 0.8 for q in
                       (math.atan2(p[1] - c[1], p[0] - c[0]) for p in picked)):
                    picked.append(n)
            if picked and (best is None or len(picked) > len(best[1])):
                best = (c, picked)
        if best is None:
            sys.exit("could not place a patrol and car routes in this area (give --centre x,y)")
        c, starts = best
        return {"centre": c, "radius": R, "starts": starts[:6], "pads": (px, py)}

    # ------------------------------------------------------------ helpers
    def fresh(self, lb, s=3.0):
        v = self.vs.get(lb)
        return v[1] if v and self.now() - v[0] <= s else None

    def on_ground(self, lb):
        m = self.fresh(lb)
        return m is not None and m.connected and m.alt < 1.0 and not m.armed

    def holders(self, prefix):
        out = []
        for lb, (t, m) in sorted(self.nb.items()):
            if self.now() - t <= 4.0 and m.current_task.startswith(prefix):
                out.append(lb)
        return out

    def event(self, task_prefix, ev, since):
        for t, m in self.events:
            if t >= since and m.task_id.startswith(task_prefix) and m.event == ev:
                return m
        return None

    def car_xy(self):
        if self.car and self.now() - self.car[0] <= 3.0:
            return self.car[1], self.car[2]
        return None

    def car_speed(self):
        return math.hypot(self.car[3], self.car[4]) if self.car and self.now() - self.car[0] <= 3.0 else None

    def battery_swap(self):
        """Simulated battery swap on the pad: MAV_CMD_BATTERY_RESET on each SITL's spare port."""
        try:
            from pymavlink import mavutil
        except ImportError:
            say("pymavlink missing: batteries not swapped", "r")
            return
        done = []
        for d in self.fleet.drones:
            url = d.mavlink_url or ""
            try:
                port = int(url.rsplit(":", 1)[1]) + 2          # SITL: serial1 = serial0 + 2
            except (IndexError, ValueError):
                continue
            try:
                c = mavutil.mavlink_connection(f"tcp:127.0.0.1:{port}", source_system=250, autoreconnect=False)
                if c.wait_heartbeat(timeout=5) is None:
                    raise RuntimeError("no heartbeat")
                c.mav.command_long_send(c.target_system, c.target_component,
                                        mavutil.mavlink.MAV_CMD_BATTERY_RESET, 0, 0xFF, 100, 0, 0, 0, 0, 0)
                ack = c.recv_match(type="COMMAND_ACK", blocking=True, timeout=3)
                c.close()
                done.append(d.label if ack is None or ack.result == 0 else f"{d.label}(refused)")
            except Exception as e:      # noqa: BLE001 - a prop: never stop the show for it
                done.append(f"{d.label}(no: {e})")
        say("batteries swapped: " + ", ".join(done), "g")

    # ------------------------------------------------------------ the show
    def ready(self):
        def missing():
            out = []
            for lb in self.labels:
                m = self.fresh(lb)
                if m is None or not m.connected:
                    out.append(f"{lb}: no link")
                elif m.armed or m.alt > 1.0:
                    out.append(f"{lb}: in the air ({m.fsm_state})")
                elif m.battery_pct < 60:
                    out.append(f"{lb}: battery {m.battery_pct:.0f}%")
                elif lb not in self.nb or self.now() - self.nb[lb][0] > 5:
                    out.append(f"{lb}: brain silent")
            return out
        say("waiting for all drones on their pads, linked, brains running ...")
        ok = self.wait(lambda: not missing(), 600, every=lambda: say("  waiting: " + "; ".join(missing()), "d"))
        if ok is None and not self.reset_now:
            say("not all drones ready: " + "; ".join(missing()), "r")
        return ok is not None

    def run_round(self):
        self.round += 1
        self.reset_now = False
        P = self.plan
        cx, cy = P["centre"]
        sx, sy = P["starts"][(self.round - 1) % len(P["starts"])]
        t_round = self.now()
        pid = f"PATROL-D{self.round}{int(time.time()) % 1000:03d}"
        iid = None

        # 1 LAUNCH
        self.stage(1, "the swarm takes off and starts patrolling",
                   f"patrol ring {P['radius']:.0f} m around ({cx:.0f}, {cy:.0f}); no drone is told which slot to take",
                   centre=[cx, cy], radius=P["radius"])
        self.gz_view("site")
        self.task(pid, cx, cy, f"radius={P['radius']:.0f} reserve=0 responders=2 intercept_hold=1800 wide=1")
        formed = self.wait(lambda: self.event(pid, "PERIMETER_FORMED", t_round), self.a.stage_timeout)
        if formed:
            say(f"patrol formed: {', '.join(self.holders(pid))} on station", "g")
            self.gz_view("follow", self.holders(pid)[0] if self.holders(pid) else self.labels[0])
        elif not self.reset_now:
            say("patrol not fully formed in time - carrying on", "r")
        self.spin_for(8)

        # 2 INTRUSION
        if not self.reset_now:
            self.stage(2, "an unknown car drives into the patrolled area",
                       f"from ({sx:.0f}, {sy:.0f}) along the streets - the drones are not told", car=[sx, sy])
            t_int = self.now()
            self.car_cmd(sx, sy, f"toward={cx:.1f},{cy:.1f} stop")
            self.gz_view("follow", "quarry")

        # 3 ACQUISITION
        if not self.reset_now:
            ev = self.wait(lambda: self.event(pid, "INTRUDER", t_int), self.a.detect_timeout)
            if ev:
                # several drones may raise it at once; duplicates merge - follow them all by prefix
                iid = f"INTERCEPT-{pid[len('PATROL-'):]}-"
                banner(f"TARGET IDENTIFIED  by {ev.reporter}'s camera", "y")
                self.stage(3, f"TARGET IDENTIFIED by {ev.reporter}'s camera", ev.detail,
                           banner="TARGET IDENTIFIED", focus=ev.reporter, intercept=iid)
            elif not self.reset_now:
                xy = self.car_xy()
                if xy:
                    vx, vy = self.car[3], self.car[4]
                    hd = math.degrees(math.atan2(vx, vy)) % 360 if math.hypot(vx, vy) > 0.5 else None
                    iid = f"INTERCEPT-D{self.round}{int(time.time()) % 1000:03d}"
                    self.task(iid, xy[0], xy[1], "operator: pursue this vehicle slots=2 radius=60"
                              + (f" heading={hd:.0f}" if hd is not None else ""))
                    banner("TARGET IDENTIFIED  (handed over by the operator)", "y")
                    self.stage(3, "TARGET IDENTIFIED (operator handed it over)",
                               "the cameras missed it in time: the operator points it out, the swarm takes over",
                               banner="TARGET IDENTIFIED", intercept=iid)
                else:
                    say("no car on /swarm/target_track (is target_mover running?)", "r")

        # 4 TRACKING & SPLIT
        if iid and not self.reset_now:
            t4 = self.now()
            got = self.wait(lambda: self.holders(iid) if len(self.holders(iid)) >= 2 else None, 60)
            chasers = self.holders(iid)
            patrol = self.holders(pid)
            self.stage(4, f"{' and '.join(chasers) or 'two drones'} break off to follow it, "
                          f"{', '.join(patrol) or 'the rest'} keep patrolling",
                       "one flies over the car, one circles it; the patrol ring closes up",
                       chasers=chasers, patrol=patrol, focus=chasers[0] if chasers else None, intercept=iid)
            if chasers:
                self.gz_view("follow", chasers[0])
            if got is None and not self.reset_now:
                say("responders slow to claim - carrying on", "r")
            self.wait(lambda: self.event(iid, "PERIMETER_FORMED", t4), self.a.stage_timeout)
            stopped = self.wait(lambda: (self.car_speed() is not None and self.car_speed() < 0.05) or None,
                                self.a.stage_timeout)
            if stopped:
                self.stage(4, "the car has stopped - the drones hold over it",
                           f"holding {self.a.hold:.0f} s", chasers=self.holders(iid),
                           patrol=self.holders(pid), focus=chasers[0] if chasers else None, intercept=iid)
            self.spin_for(min(self.a.hold, 12))
            caught = self._caught(iid)
            self.spin_for(max(0.0, self.a.hold - 12))
            caught = self._caught(iid) or caught
            if caught:
                lb, d = caught
                banner(f"TARGET CAUGHT  -  {lb} overhead ({d:.0f} m)", "g")
                self.stage(4, f"TARGET CAUGHT - {lb} is overhead ({d:.0f} m)", "position, track and video recorded",
                           banner="TARGET CAUGHT", focus=lb, intercept=iid)
            elif not self.reset_now:
                say("no drone right over the car at the end of the hold", "r")

        # 5 RESET
        self.reset(pid, iid)

    def _caught(self, iid):
        xy = self.car_xy()
        if not xy:
            return None
        best = None
        for lb in self.holders(iid):
            m = self.fresh(lb)
            if m is not None:
                d = math.hypot(m.x - xy[0], m.y - xy[1])
                if best is None or d < best[1]:
                    best = (lb, d)
        return best if best and best[1] <= 25.0 else None

    def reset(self, pid, iid):
        cancel = [pid] + ([iid] if iid and not iid.endswith("-") else [])
        for t, m in list(self.events):          # every intercept this round spawned (merged twins too)
            if iid and m.task_id.startswith(iid):
                cancel.append(m.task_id)
            if m.event == "INTRUDER" and "-> " in m.detail and m.task_id == pid:
                cancel.append(m.detail.split("-> ")[-1].strip())
        self._finish(cancel, car=True)

    def _finish(self, task_ids, car=True):
        self.reset_now = False
        self.stage(5, "mission over - every drone flies home and lands on its pad",
                   "tasks called off; each drone plans its own way back around the buildings")
        self.gz_view("site")
        for _ in range(2):
            for tid in task_ids:
                self.cancel(tid)
            self.spin_for(1.0)
        landed = self.wait(lambda: all(self.on_ground(lb) for lb in self.labels), self.a.land_timeout)
        if not landed:
            up = [lb for lb in self.labels if not self.on_ground(lb)]
            say(f"still flying after {self.a.land_timeout:.0f} s: {', '.join(up)} - sending them home (RTL)", "r")
            for lb in up:
                self.command(lb, "RTL")
            self.wait(lambda: all(self.on_ground(lb) for lb in self.labels), 240)
            self.spin_for(3)
            self.command("ALL", "RESUME")
        if car:
            # the car goes back outside for the next round, parked (parked cars are not intruders)
            nx, ny = self.plan["starts"][self.round % len(self.plan["starts"])]
            self.car_cmd(nx, ny, "park")
            self.spin_for(2)
        self.battery_swap()
        self.stage(0, f"round {self.round} done", "ready for the next round")
        say(f"round {self.round} finished in {self._fmt(time.time() - self._t_start)}", "g")

    # ------------------------------------------------- structure inspection
    def _pick_structure(self):
        """A building to inspect: tall enough to be worth it, a few hundred metres off the pads."""
        pads = [self.fleet.home_enu(d.id) for d in self.fleet.drones]
        px, py = sum(p[0] for p in pads) / len(pads), sum(p[1] for p in pads) / len(pads)
        blds = (self.fleet.area or {}).get("buildings") or []
        if not blds:
            sys.exit("the inspect mission needs an area with buildings (OSM or --synthetic)")

        def info(b):
            xs = [p[0] for p in b["poly"]]
            ys = [p[1] for p in b["poly"]]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
            return cx, cy, half, float(b.get("h", 10.0))
        if self.a.structure:
            tx, ty = (float(v) for v in self.a.structure.split(","))
            cx, cy, half, h = min((info(b) for b in blds), key=lambda t: math.hypot(t[0] - tx, t[1] - ty))
        else:
            cand = []
            for b in blds:
                cx, cy, half, h = info(b)
                d = math.hypot(cx - px, cy - py)
                if h >= 25.0 and 120.0 <= d <= 360.0:
                    cand.append((abs(d - 220.0), cx, cy, half, h))
            if not cand:
                sys.exit("no suitable building 120-360 m from the pads; pass --structure x,y")
            _, cx, cy, half, h = min(cand)
        standoff = 18.0
        return {"cx": cx, "cy": cy, "half": half, "h": h, "pads": (px, py), "standoff": standoff,
                "R": half + standoff, "alt": min(45.0, max(20.0, h - 12.0))}

    def run_inspect_round(self):
        self.round += 1
        self.reset_now = False
        S = self.struct
        cx, cy = S["cx"], S["cy"]
        t0 = self.now()
        ins = f"SWARM-INS-D{self.round}{int(time.time()) % 1000:03d}"
        ovw = f"SWARM-OVW-D{self.round}{int(time.time()) % 1000:03d}"

        # 1 LAUNCH - two drones take high overwatch first (so the groups never climb out together)
        self.stage(1, "the swarm takes off; two drones take high overwatch",
                   f"a {S['h']:.0f} m structure at ({cx:.0f}, {cy:.0f}); two cover it from above",
                   centre=[cx, cy], radius=S["R"])
        self.gz_view("site")
        self.task(ovw, cx, cy, f"radius={max(140.0, S['R'] * 3):.0f} slots=2 alt=95 static=1 hold=900")
        if self.wait(lambda: self.event(ovw, "PERIMETER_FORMED", t0), self.a.stage_timeout):
            say(f"overwatch up: {', '.join(self.holders(ovw))}", "g")
        self.spin_for(6)

        # 2 APPROACH - three drones make the precision run in
        formed = None
        if not self.reset_now:
            self.stage(2, "three drones make a precision approach to the structure",
                       f"fast run in; each arrests ~{S['standoff']:.0f} m off the walls - clear, no contact",
                       centre=[cx, cy])
            self.task(ins, cx, cy,
                      f"radius={S['R']:.0f} slots=3 alt={S['alt']:.0f} fast=1 static=1 hold={self.a.inspect_hold + 40:.0f}")
            formed = self.wait(lambda: self.event(ins, "PERIMETER_FORMED", t0), self.a.stage_timeout)
            hs = self.holders(ins)
            self.gz_view("follow", hs[0] if hs else self.labels[0])

        # 3 STANDOFF
        if formed and not self.reset_now:
            hs = self.holders(ins)
            banner(f"STANDOFF ESTABLISHED  -  {len(hs)} drones on the structure", "g")
            self.stage(3, f"standoff established - {len(hs)} drones on the structure, clear of the walls",
                       "cameras on the façades; two drones hold high cover",
                       banner="STANDOFF ESTABLISHED", centre=[cx, cy], focus=hs[0] if hs else None)
        elif not self.reset_now:
            say("cordon not fully formed in time - carrying on", "r")

        # 4 INSPECT
        if not self.reset_now:
            self.stage(4, "inspecting the structure", f"holding {self.a.inspect_hold:.0f} s",
                       centre=[cx, cy], focus=(self.holders(ins)[0] if self.holders(ins) else None))
            self.spin_for(self.a.inspect_hold)
            say(f"inspection complete: cordon held by {', '.join(self.holders(ins)) or '-'}", "g")

        # 5 RESET
        self._finish([ins, ovw], car=False)

    @staticmethod
    def _fmt(s):
        return f"{int(s // 60)}:{int(s % 60):02d}"

    def show(self):
        P = self.plan
        self.wait_clock()
        if self.a.mission == "inspect":
            S = self.struct
            say(f"inspect target: a {S['h']:.0f} m structure at ({S['cx']:.0f}, {S['cy']:.0f}); "
                f"cordon {S['R']:.0f} m radius (~{S['standoff']:.0f} m standoff); pads at "
                f"({P['pads'][0]:.0f}, {P['pads'][1]:.0f})")
        else:
            say(f"patrol centre ({P['centre'][0]:.0f}, {P['centre'][1]:.0f}) radius {P['radius']:.0f} m; "
                f"{len(P['starts'])} car routes; pads at ({P['pads'][0]:.0f}, {P['pads'][1]:.0f})")
            self.spin_for(2)
            sx, sy = P["starts"][0]
            self.car_cmd(sx, sy, "park")
        threading.Thread(target=self._stdin, daemon=True).start()
        while not self.quit and (self.a.rounds == 0 or self.round < self.a.rounds):
            self.stage(0, "ready", "press Enter to start")
            if not self.ready():
                if self.reset_now:
                    self.reset_now = False
                    continue
            if not self.a.no_key:
                print(f"\n{C['b']}>>> press Enter to start round {self.round + 1}   (q + Enter = quit){C['0']}",
                      flush=True)
                while True:
                    self.spin_for(0.2)
                    if self.quit or self._go:
                        break
                self._go = False
                if self.quit:
                    break
            self._t_start = time.time()
            if self.a.mission == "inspect":
                self.run_inspect_round()
            else:
                self.run_round()
        self.stage(0, "show over", "")
        say("bye")

    _go = False

    def _stdin(self):
        for line in sys.stdin:
            k = line.strip().lower()
            if k in ("q", "quit"):
                self.keys.put("q")
            elif k in ("r", "reset"):
                self.keys.put("r")
            else:
                self._go = True


def main():
    ap = argparse.ArgumentParser(description="exhibition director", epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fleet", default=None)
    ap.add_argument("--mission", choices=["patrol", "inspect"], default="patrol",
                    help="patrol: launch->intrusion->track->home; inspect: precision standoff on a structure")
    ap.add_argument("--radius", type=float, default=90.0, help="patrol ring radius (m)")
    ap.add_argument("--centre", default=None, help="patrol centre x,y (default: a street near the pads)")
    ap.add_argument("--structure", default=None, help="inspect: building to approach, x,y (default: auto)")
    ap.add_argument("--inspect-hold", type=float, default=45.0, help="inspect: seconds to hold the standoff")
    ap.add_argument("--hold", type=float, default=30.0, help="seconds to hold over the stopped car")
    ap.add_argument("--rounds", type=int, default=0, help="0 = until you quit")
    ap.add_argument("--no-key", action="store_true", help="start rounds without waiting for Enter")
    ap.add_argument("--stage-timeout", type=float, default=180.0)
    ap.add_argument("--detect-timeout", type=float, default=150.0)
    ap.add_argument("--land-timeout", type=float, default=240.0)
    ap.add_argument("--wall-clock", action="store_true", help="Gazebo: time stages by the wall clock")
    a = ap.parse_args()
    fleet = load_fleet(a.fleet)
    real = [d.label for d in fleet.drones
            if d.mavlink_url and not any(h in d.mavlink_url for h in ("127.0.0.1", "localhost"))]
    if real:
        sys.exit(f"demo director: {', '.join(real)} are not local simulators - it only runs in simulation")
    rclpy.init()
    d = Director(a)
    try:
        d.show()
    except KeyboardInterrupt:
        say("interrupted: calling the swarm home", "r")
        d.command("ALL", "RTL")
        d.spin_for(1)
    finally:
        d.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
