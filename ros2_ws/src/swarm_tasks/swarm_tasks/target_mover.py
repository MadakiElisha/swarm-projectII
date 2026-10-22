"""Simulation prop: the vehicle the swarm has to find and follow.

Starts driving when
  * an INTERCEPT-<n> task request arrives (the car starts where the operator clicked), or
  * a request arrives on /swarm/sim/start_target (an "intruder" for PATROL tests;
    the drones do not listen to that topic).
With an OSM area it drives along real streets (road graph); otherwise straight.
Publishes ground truth on /swarm/target_track; in Gazebo gz_quarry moves the car
model so the drones' cameras see it. Never used on hardware.
"""
import math
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
        self.declare_parameter('duration', 240.0)
        self.declare_parameter('seed', 7)
        fleet = load_fleet()
        self.origin = fleet.swarm.origin
        roads = (fleet.area or {}).get('roads') or []
        self.graph = RoadGraph(roads) if roads else None
        self.pub = self.create_publisher(TargetTrack, '/swarm/target_track', 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_request, 10)
        self.create_subscription(TaskRequest, '/swarm/sim/start_target', self.on_start, 10)
        self.thread = None
        self.stop_flag = threading.Event()
        self.get_logger().info('target mover ready ('
                               + (f'{len(self.graph.nodes)} road nodes' if self.graph else 'no roads')
                               + ') - starts on INTERCEPT- requests or /swarm/sim/start_target')

    def on_request(self, msg):
        if msg.task_id.startswith('INTERCEPT-'):
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
