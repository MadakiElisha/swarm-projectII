"""mesh_observer: GCS-side VISUALISATION of the real radio mesh.

Merges every drone's own NeighborReport (links measured from packet
receipt, not guessed from GPS distance) into one MeshTopology for the GCS.
Nothing in the swarm depends on this node; kill it and the drones carry on.
"""
import math
import time

import rclpy
from rclpy.node import Node

from swarm_common.geo import haversine_m
from swarm_interfaces.msg import DroneTelemetry, MeshEdge, MeshTopology, NeighborReport

REPORT_FRESH_S = 3.0


class MeshObserver(Node):
    def __init__(self):
        super().__init__('mesh_observer')
        self.reports = {}        # label -> (NeighborReport, t)
        self.pos = {}            # label -> (lat, lon)
        self.create_subscription(NeighborReport, '/swarm/neighbors', self.on_report, 10)
        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telem, 10)
        self.pub = self.create_publisher(MeshTopology, '/swarm/mesh_topology', 10)
        self.create_timer(1.0, self.publish)
        self.get_logger().info('mesh observer (display only) listening on /swarm/neighbors')

    def on_report(self, m):
        self.reports[m.label] = (m, time.time())

    def on_telem(self, m):
        self.pos[m.label] = (m.lat, m.lon)

    def publish(self):
        now = time.time()
        fresh = {k: r for k, (r, t) in self.reports.items() if now - t <= REPORT_FRESH_S}
        q = {}
        for a, r in fresh.items():
            for b, lq in zip(r.neighbors, r.link_quality):
                key = tuple(sorted((a, b)))
                q.setdefault(key, []).append(float(lq))
        topo = MeshTopology()
        topo.header.stamp = self.get_clock().now().to_msg()
        topo.active_drones = sorted(fresh)
        for (a, b), lqs in sorted(q.items()):
            e = MeshEdge(a=a, b=b)
            e.link_quality = min(lqs) if len(lqs) == 2 else 0.5 * lqs[0]   # one-way = degraded
            if a in self.pos and b in self.pos:
                e.distance_km = haversine_m(*self.pos[a], *self.pos[b]) / 1000.0
            else:
                e.distance_km = math.nan
            topo.edges.append(e)
        self.pub.publish(topo)


def main(args=None):
    rclpy.init(args=args)
    node = MeshObserver()
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
