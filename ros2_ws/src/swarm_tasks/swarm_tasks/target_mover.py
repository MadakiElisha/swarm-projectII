"""Simulation prop: the vehicle the swarm has to find and follow.

Starts driving when
  * an INTERCEPT-<n> task request arrives (the car starts where the operator clicked), or
  * a request arrives on /swarm/sim/start_target (an "intruder" for PATROL tests;
    the drones do not listen to that topic).
With an OSM area it drives along real streets (road graph); otherwise straight.
Publishes ground truth on /swarm/target_track; in Gazebo gz_quarry moves the car
model so the drones' cameras see it. Never used on hardware.
"""
import json
import math
import os
import random
import threading
import time

import rclpy
from rclpy.node import Node

from swarm_common.config import load_fleet
from swarm_common.roads import RoadGraph, along
from swarm_interfaces.msg import TargetTrack, TaskRequest


class TargetMover(Node):
    def __init__(self):
        super().__init__('target_mover')
        self.declare_parameter('speed', 6.0)
        self.declare_parameter('bearing', 75.0)       # straight-line fallback (no roads)
        self.declare_parameter('duration', 3600.0)
        self.declare_parameter('seed', 7)
        # the exhibition: the car is already driving when the scene starts (x,y metres from the
        # origin, or "" = do not start until an INTERCEPT request / /swarm/sim/start_target)
        self.declare_parameter('autostart', '')
        fleet = load_fleet()
        self.origin = fleet.swarm.origin
        roads = (fleet.area or {}).get('roads') or []
        self.graph = RoadGraph(roads) if roads else None
        self.pub = self.create_publisher(TargetTrack, '/swarm/target_track', 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_request, 10)
        self.create_subscription(TaskRequest, '/swarm/sim/start_target', self.on_start, 10)
        self.thread = None
        self.stop_flag = threading.Event()
        auto = str(self.get_parameter('autostart').value or '')
        if auto == 'auto':
            auto = self._auto_start(fleet)
        if auto:
            try:
                ax, ay = (float(v) for v in auto.split(','))
                la, lo = self.origin.to_latlon(ax, ay)
                self.start(la, lo, 'already driving when the scene starts')
            except ValueError:
                self.get_logger().error(f'bad autostart {auto!r} (want x,y)')
        self.get_logger().info('target mover ready ('
                               + (f'{len(self.graph.nodes)} road nodes' if self.graph else 'no roads')
                               + ') - starts on INTERCEPT- requests or /swarm/sim/start_target')

    def _auto_start(self, fleet):
        """Where the car is when the scene starts: the Gazebo world's car if there is one,
        else a street ~350 m from the launch site."""
        info = os.environ.get('SWARM_GZ_INFO', '')
        if info and os.path.isfile(info):
            t = json.load(open(info)).get('target')
            if t:
                return f'{t[0]},{t[1]}'
        pads = [fleet.home_enu(d.id) for d in fleet.drones]
        px = sum(p[0] for p in pads) / len(pads) + 350.0
        py = sum(p[1] for p in pads) / len(pads) + 120.0
        if self.graph:
            px, py = self.graph.nodes[self.graph.nearest((px, py))]
        return f'{px:.1f},{py:.1f}'

    def on_request(self, msg):
        # the operator clicked on the car: if it is already driving, leave it alone
        if msg.task_id.startswith('INTERCEPT-') and not (self.thread and self.thread.is_alive()):
            self.start(msg.lat, msg.lon, msg.task_id)

    def on_start(self, msg):
        toward = None
        if 'toward=' in (msg.description or ''):      # an intruder heading for a place
            try:
                a, b = (float(v) for v in msg.description.split('toward=', 1)[1].split()[0].split(','))
                toward = (a, b)
            except ValueError:
                pass
        self.start(msg.lat, msg.lon, msg.task_id or 'intruder', toward)

    def start(self, lat, lon, why, toward=None):
        self.stop_flag.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.stop_flag = threading.Event()
        self.thread = threading.Thread(target=self.run, args=(lat, lon, toward), daemon=True)
        self.thread.start()
        self.get_logger().warn(f'TARGET DRIVING ({why}) from {lat:.5f},{lon:.5f}')

    def run(self, lat0, lon0, toward=None):
        speed = float(self.get_parameter('speed').value)
        duration = float(self.get_parameter('duration').value)
        x0, y0 = self.origin.to_enu(lat0, lon0)
        if self.graph:
            rnd = random.Random(int(self.get_parameter('seed').value))
            if toward is not None:        # drive to the place along streets, then wander on
                path = [(x0, y0)] + self.graph.shortest((x0, y0), toward)
                path += self.graph.drive(path[-1], speed * duration, rnd)[1:]
            else:
                path = [(x0, y0)] + self.graph.drive((x0, y0), speed * duration + 50, rnd)
        elif toward is not None:
            path = [(x0, y0), toward]
        else:
            b = math.radians(float(self.get_parameter('bearing').value))
            d = speed * duration
            path = [(x0, y0), (x0 + d * math.sin(b), y0 + d * math.cos(b))]
        t0 = time.time()
        while not self.stop_flag.is_set() and time.time() - t0 < duration:
            s = speed * (time.time() - t0)
            (x, y), hdg = along(path, s)
            lat, lon = self.origin.to_latlon(x, y)
            m = TargetTrack()
            m.header.stamp = self.get_clock().now().to_msg()
            m.lat, m.lon = lat, lon
            m.vel_e, m.vel_n = speed * math.cos(hdg), speed * math.sin(hdg)
            m.source = 'auto_mover'
            self.pub.publish(m)
            time.sleep(0.25)
        self.get_logger().info('target stopped')


def main(args=None):
    rclpy.init(args=args)
    node = TargetMover()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
