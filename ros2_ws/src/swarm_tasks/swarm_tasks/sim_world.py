"""Simulation prop: the world the drones look at, without rendering it.

For flying the swarm on real ArduPilot (SITL) with no Gazebo: holds the scene
(people, parked cars, flood water; the moving car comes from target_mover) and,
for every drone, turns its real pose (from its autopilot, via vehicle_state)
into the detections its camera + YOLO would produce -> /swarm/<D>/detections,
the same topic the real perception node publishes. The brains cannot tell the
difference; they project and fuse these exactly as on hardware.

Also publishes the scene on /swarm/sim/scene (JSON) so the GCS can draw the
ground truth (people, cars, flood). Never used on hardware.
"""
import json
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

from swarm_common.config import load_fleet
from swarm_common.simcam import SimCamera, make_scene
from swarm_interfaces.msg import Detection, DetectionArray, TargetTrack, VehicleState


class SimWorld(Node):
    def __init__(self):
        super().__init__('sim_world')
        self.declare_parameter('fleet_file', '')
        self.declare_parameter('scene_file', '')
        self.declare_parameter('seed', 1)
        self.declare_parameter('people', 10)
        self.declare_parameter('cars', 14)
        self.declare_parameter('flood', False)
        self.declare_parameter('radius', 650.0)
        self.declare_parameter('camera_hz', 2.0)
        self.declare_parameter('view_hz', 1.0)          # annotated camera views for the GCS (0 = off)
        self.declare_parameter('only_labels', [''])     # Gazebo: drones without a rendered camera
        fleet = load_fleet(self.get_parameter('fleet_file').value or None)
        self.origin = fleet.swarm.origin
        only = [x for x in self.get_parameter('only_labels').value if x]
        self.labels = [d.label for d in fleet.drones if not only or d.label in only]
        pads = [fleet.home_enu(d.id) for d in fleet.drones]
        self.n_drones = len(pads)
        cx = sum(p[0] for p in pads) / len(pads)
        cy = sum(p[1] for p in pads) / len(pads)
        flood = bool(self.get_parameter('flood').value)
        path = self.get_parameter('scene_file').value
        ff = self.get_parameter('fleet_file').value or os.environ.get('SWARM_FLEET', '')
        if not path and ff and fleet.swarm.area_file:
            base = os.path.dirname(os.path.abspath(ff))
            path = os.path.join(base, 'scene_flood.json' if flood else 'scene.json')
        gz = os.environ.get('SWARM_GZ_INFO', '')
        gzi = json.load(open(gz)) if gz and os.path.isfile(gz) else {}
        if gzi.get('survivors') is not None and (not flood or gzi.get('flood_m')):
            # same people and cars as the Gazebo world, so simulated and rendered cameras agree
            fl = []
            if gzi.get('flood_m') and fleet.area and fleet.area.get('buildings'):
                xs = [p[0] for b in fleet.area['buildings'] for p in b['poly']]
                ys = [p[1] for b in fleet.area['buildings'] for p in b['poly']]
                fl = [[[min(xs) - 100, min(ys) - 100], [max(xs) + 100, min(ys) - 100],
                       [max(xs) + 100, max(ys) + 100], [min(xs) - 100, max(ys) + 100]]]
            self.scene = {'people': gzi.get('survivors', []), 'cars': gzi.get('cars', []), 'flood': fl}
            self.get_logger().info(f'scene from the Gazebo world ({gz})')
        elif path and os.path.isfile(path):
            self.scene = json.load(open(path))
            self.get_logger().info(f'scene from {path}')
        else:
            self.scene = make_scene(fleet.area or {}, seed=int(self.get_parameter('seed').value),
                                    people=int(self.get_parameter('people').value),
                                    cars=int(self.get_parameter('cars').value), flood=flood,
                                    centre=(cx, cy), radius=float(self.get_parameter('radius').value),
                                    avoid=[(px, py) for px, py in pads])
            if path:
                try:
                    json.dump(self.scene, open(path, 'w'), indent=1)
                except OSError:
                    pass
        self.scene['pads'] = [[round(p[0], 1), round(p[1], 1)] for p in pads]
        self.cam = {lab: SimCamera(fleet.swarm.perception, self.scene, seed=i + 1)
                    for i, lab in enumerate(self.labels)}
        self.vs = {}
        self.mover = None
        self.views, self.view_pubs, self._last_dets = None, {}, {}
        if float(self.get_parameter('view_hz').value) > 0:
            try:
                from swarm_common.annotate import SimViewRenderer
                import cv2  # noqa: F401
                self.views = SimViewRenderer(fleet.swarm.perception, fleet.area, self.scene)
                self.view_pubs = {lab: self.create_publisher(CompressedImage, f'/swarm/{lab}/camera/annotated', 2)
                                  for lab in self.labels}
                self.create_timer(1.0 / float(self.get_parameter('view_hz').value), self.publish_views)
            except ImportError:
                self.get_logger().warn('OpenCV not available: no simulated camera views')
        self.pubs = {lab: self.create_publisher(DetectionArray, f'/swarm/{lab}/detections', 10)
                     for lab in self.labels}
        for lab in self.labels:
            self.create_subscription(VehicleState, f'/swarm/{lab}/vehicle_state',
                                     lambda m, lab=lab: self.vs.__setitem__(lab, m), 10)
        self.create_subscription(TargetTrack, '/swarm/target_track', self.on_target, 10)
        latched = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.scene_pub = self.create_publisher(String, '/swarm/sim/scene', latched)
        self.create_timer(1.0 / float(self.get_parameter('camera_hz').value), self.frame)
        self.create_timer(3.0, self.publish_scene)
        self.publish_scene()
        self.get_logger().info(
            f"simulated cameras for {len(self.labels)} drones: {len(self.scene['people'])} people, "
            f"{len(self.scene['cars'])} parked cars, {len(self.scene['flood'])} flood zones")

    def on_target(self, m: TargetTrack):
        self.mover = (self.get_clock().now().nanoseconds * 1e-9, self.origin.to_enu(m.lat, m.lon))

    def publish_scene(self):
        sc = dict(self.scene)
        now = self.get_clock().now().nanoseconds * 1e-9
        sc['mover'] = list(self.mover[1]) if self.mover and now - self.mover[0] < 3.0 else None
        self.scene_pub.publish(String(data=json.dumps(sc)))

    def frame(self):
        now = self.get_clock().now()
        movers = [self.mover[1]] if self.mover and now.nanoseconds * 1e-9 - self.mover[0] < 3.0 else []
        for lab, m in self.vs.items():
            if not m.connected:
                continue
            out = DetectionArray()
            out.header.stamp = now.to_msg()
            out.header.frame_id = lab
            dets = self.cam[lab].detect(m.x, m.y, m.alt, m.roll, m.pitch, m.yaw_enu, movers)
            self._last_dets[lab] = (dets, movers)
            for d in dets:
                det = Detection()
                det.class_name, det.confidence = d['class'], float(d['conf'])
                det.bbox_x, det.bbox_y, det.bbox_w, det.bbox_h = d['u0'], d['v0'], d['w'], d['h']
                out.detections.append(det)
            out.count = len(out.detections)
            self.pubs[lab].publish(out)

    def publish_views(self):
        from swarm_common.annotate import to_jpeg
        for lab, m in self.vs.items():
            if not m.connected or m.alt < 2.0 or lab not in self.view_pubs:
                continue
            dets, movers = self._last_dets.get(lab, ([], []))
            img = self.views.render((m.x, m.y, m.alt, m.roll, m.pitch, m.yaw_enu), dets,
                                    f'{lab}  alt {m.alt:.0f} m', movers)
            msg = CompressedImage()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = lab
            msg.format = 'jpeg'
            msg.data = to_jpeg(img)
            self.view_pubs[lab].publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SimWorld()
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
