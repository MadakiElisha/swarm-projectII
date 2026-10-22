"""drone_brain: one per drone, runs swarm_common.brain.DroneBrain.

The brain only ever talks to:
  * its OWN vehicle_manager   (/swarm/<label>/vehicle_state, /swarm/<label>/setpoint)
  * the radio                 (/swarm/radio, SwarmPacket - shared broadcast medium)
  * its OWN camera pipeline   (/swarm/<label>/detections)
  * the operator uplink       (/swarm/task_requests, if the GCS can reach it)

and publishes GCS-facing status (assignments, mission events, suggestions,
neighbour reports). There is no node in the system that every drone needs.

link_emulation (simulation only): on one computer every drone hears every
packet, so the brain itself drops packets from senders beyond radio range
and adds random loss. On real radios leave it off.
"""
import json
import math
import random

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from swarm_common.brain import DroneBrain, OwnState, PERSON, TARGET
from swarm_common.config import load_fleet
from swarm_common.perception import footprint_radius, project_bbox
from swarm_interfaces.msg import (DetectionArray, MissionEvent, NeighborReport, SwarmPacket,
                                  TargetTrack, TaskAssignment, TaskRequest, VehicleState)
from swarm_interfaces.msg import Setpoint as SetpointMsg

RADIO_QOS = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                       history=HistoryPolicy.KEEP_LAST, depth=200)
TARGET_SENSOR_RANGE_M = 400.0


class DroneBrainNode(Node):
    def __init__(self):
        super().__init__('drone_brain')
        self.declare_parameter('drone_id', 1)
        self.declare_parameter('fleet_file', '')
        self.declare_parameter('tick_hz', 10.0)
        self.declare_parameter('link_emulation', False)
        self.declare_parameter('emu_loss', 0.0)
        self.declare_parameter('emu_range_m', 0.0)          # 0 -> fleet radio_range_m
        self.declare_parameter('simulate_target_sensor', False)
        self.declare_parameter('seed', 0)

        self.id = int(self.get_parameter('drone_id').value)
        self.fleet = load_fleet(self.get_parameter('fleet_file').value or None)
        self.brain = DroneBrain(self.fleet, self.id)
        self.label = self.brain.label
        self.origin = self.fleet.swarm.origin
        self.emulate = bool(self.get_parameter('link_emulation').value)
        self.loss = float(self.get_parameter('emu_loss').value)
        self.range = float(self.get_parameter('emu_range_m').value) or self.fleet.swarm.radio_range_m
        self.sim_target = bool(self.get_parameter('simulate_target_sensor').value)
        self.rnd = random.Random(int(self.get_parameter('seed').value) * 1000 + self.id)
        self.vs = None

        L = self.label
        self.radio_pub = self.create_publisher(SwarmPacket, '/swarm/radio', RADIO_QOS)
        self.sp_pub = self.create_publisher(SetpointMsg, f'/swarm/{L}/setpoint', 10)
        self.asg_pub = self.create_publisher(TaskAssignment, '/swarm/task_assignments', 10)
        self.evt_pub = self.create_publisher(MissionEvent, '/swarm/mission_event', 10)
        self.sug_pub = self.create_publisher(TaskRequest, '/swarm/task_suggestions', 10)
        self.nbr_pub = self.create_publisher(NeighborReport, '/swarm/neighbors', 10)

        self.create_subscription(SwarmPacket, '/swarm/radio', self.on_radio, RADIO_QOS)
        self.create_subscription(VehicleState, f'/swarm/{L}/vehicle_state', self.on_vehicle, 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_task_request, 10)
        self.create_subscription(DetectionArray, f'/swarm/{L}/detections', self.on_detections, 10)
        if self.sim_target:
            self.create_subscription(TargetTrack, '/swarm/target_track', self.on_target_truth, 10)
        self.create_timer(1.0 / float(self.get_parameter('tick_hz').value), self.tick)
        self.create_timer(1.0, self.publish_neighbors)
        self.get_logger().info(f'{L}: brain online (link emulation: {self.emulate}, '
                               f'loss={self.loss:.0%}, range={self.range:.0f} m)')

    # ------------------------------------------------------------- inputs
    def on_radio(self, m: SwarmPacket):
        if m.src == self.id or self._now() == 0.0:
            return
        if self.emulate:
            if self.vs is None:
                return
            if math.hypot(m.sender_x - self.vs.x, m.sender_y - self.vs.y) > self.range:
                return
            if self.rnd.random() < self.loss:
                return
        try:
            pkt = json.loads(m.payload)
        except (ValueError, TypeError):
            self.get_logger().warn(f'{self.label}: undecodable packet from {m.src}')
            return
        self.brain.on_packet(pkt, self._now())

    def on_vehicle(self, m: VehicleState):
        if self._now() == 0.0:          # on Gazebo's clock and it hasn't started yet
            return
        self.vs = m
        if not m.connected:
            return
        self.brain.on_vehicle(OwnState(self._now(), m.x, m.y, m.alt, m.vx, m.vy, m.battery_pct,
                                       m.armed, m.fsm_state, m.latch, m.wind_speed))

    def on_task_request(self, m: TaskRequest):
        if self._now() == 0.0:          # on Gazebo's clock and it hasn't started yet
            return
        x, y = self.origin.to_enu(m.lat, m.lon)
        params = {}
        desc = m.description or ''
        if 'area=' in desc:                     # SEARCH: area=lat0,lon0,lat1,lon1
            try:
                a = [float(v) for v in desc.split('area=', 1)[1].split()[0].split(',')]
                x0, y0 = self.origin.to_enu(a[0], a[1])
                x1, y1 = self.origin.to_enu(a[2], a[3])
                params['area'] = [x0, y0, x1, y1]
            except (ValueError, IndexError):
                self.get_logger().warn(f'{self.label}: bad search area in {desc!r}')
                return
        for key, name in (('heading=', 'heading_deg'), ('speed=', 'speed')):   # INTERCEPT: where it's going
            if key in desc:
                try:
                    params[name] = float(desc.split(key, 1)[1].split()[0].split(',')[0])
                except (ValueError, IndexError):
                    pass
        if 'radius=' in desc:                   # PATROL / SWARM: radius=<metres>
            try:
                params['radius'] = float(desc.split('radius=', 1)[1].split()[0].split(',')[0])
            except (ValueError, IndexError):
                self.get_logger().warn(f'{self.label}: bad radius in {desc!r}')
        res = self.brain.on_operator_task(m.task_id, x, y, self._now(), desc, params)
        self.get_logger().info(f'{self.label}: operator {m.task_id} -> {res}')

    def on_detections(self, m: DetectionArray):
        if self._now() == 0.0:          # on Gazebo's clock and it hasn't started yet
            return
        vs = self.vs
        if vs is None or vs.alt < 3.0:
            return
        cfg = self.fleet.swarm.perception
        now = self._now()
        for d in m.detections:
            u = d.bbox_x + d.bbox_w / 2.0
            v = d.bbox_y + d.bbox_h / 2.0
            g = project_bbox(u, v, vs.x, vs.y, vs.alt, vs.roll, vs.pitch, vs.yaw_enu, cfg)
            if g is None:
                continue
            if d.class_name == 'water':           # flood recon: a patch of the image is water
                half = 0.5 * max(d.bbox_w, d.bbox_h) * 2.0 * footprint_radius(vs.alt, cfg)
                self.brain.on_water(g[0], g[1], half)
                continue
            cls = PERSON if d.class_name == 'person' else d.class_name
            self.brain.on_detection(cls, g[0], g[1], float(d.confidence), now)

    def on_target_truth(self, m: TargetTrack):
        """Simulation only: 'see' the scripted quarry when it is within sensor range."""
        vs = self.vs
        if vs is None or vs.alt < 5.0:
            return
        x, y = self.origin.to_enu(m.lat, m.lon)
        r = max(TARGET_SENSOR_RANGE_M, footprint_radius(vs.alt, self.fleet.swarm.perception))
        if math.hypot(x - vs.x, y - vs.y) <= r:
            self.brain.on_detection(TARGET, x, y, 0.9, self._now(), m.vel_e, m.vel_n)

    # --------------------------------------------------------------- tick
    def tick(self):
        now = self._now()
        out = self.brain.tick(now)
        stamp = self.get_clock().now().to_msg()
        for p in out.packets:
            msg = SwarmPacket()
            msg.header.stamp = stamp
            msg.src, msg.seq, msg.kind = self.id, int(p['seq']), p['k']
            msg.sender_x, msg.sender_y = float(p['p'][0]), float(p['p'][1])
            msg.payload = json.dumps(p, separators=(',', ':'))
            self.radio_pub.publish(msg)
        if out.setpoint is not None:
            sp = out.setpoint
            m = SetpointMsg()
            m.header.stamp = stamp
            m.drone_id, m.kind = self.id, sp.kind
            m.vx, m.vy, m.vz, m.x, m.y, m.alt = sp.vx, sp.vy, sp.vz, sp.x, sp.y, sp.alt
            self.sp_pub.publish(m)
        for a in out.assignments:
            m = TaskAssignment()
            m.header.stamp = stamp
            m.task_id, m.item_id, m.assigned_to, m.kind = a.parent, a.item_id, self.label, a.kind
            if a.item_id:
                m.lat, m.lon = self.origin.to_latlon(a.x, a.y)
            m.orbit_radius = float(a.radius)
            self.asg_pub.publish(m)
        for (tid, ev, det) in out.events:
            m = MissionEvent()
            m.header.stamp = stamp
            m.task_id, m.event, m.detail, m.reporter = tid, ev, det, self.label
            self.evt_pub.publish(m)
        for t in out.suggestions:
            m = TaskRequest()
            m.header.stamp = stamp
            m.task_id = t.id
            m.lat, m.lon = self.origin.to_latlon(t.x, t.y)
            m.description = t.params.get('desc', 'perception suggestion')
            self.sug_pub.publish(m)
        for line in out.logs:
            self.get_logger().info(line)

    def publish_neighbors(self):
        now = self._now()
        nb = self.brain.neighbors
        ids = nb.neighbors(now)
        m = NeighborReport()
        m.header.stamp = self.get_clock().now().to_msg()
        m.drone_id, m.label = self.id, self.label
        m.neighbors = [f'D{i}' for i in ids]
        m.link_quality = [float(nb.quality(i, now)) for i in ids]
        m.phase, m.current_task = self.brain.phase, self.brain.current_item()
        self.nbr_pub.publish(m)

    def _now(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9


def main(args=None):
    rclpy.init(args=args)
    node = DroneBrainNode()
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
