"""Mesh Builder node: builds the live mesh graph from telemetry.

Thin ROS shell over the tested swarm_common.mesh_core logic.
Publishes a typed MeshTopology instead of a JSON string.
"""
import time

import rclpy
from rclpy.node import Node

from swarm_interfaces.msg import DroneTelemetry, MeshTopology, MeshEdge
from swarm_common.mesh_core import build_mesh_graph
from swarm_common.config import STALE_TELEMETRY_AFTER_SEC


class MeshBuilder(Node):
    def __init__(self):
        super().__init__('mesh_builder')
        self.drone_states = {}  # label -> (lat, lon, battery, last_seen)

        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telemetry, 10)
        self.publisher_ = self.create_publisher(MeshTopology, '/swarm/mesh_topology', 10)
        self.timer = self.create_timer(1.0, self.publish_topology)
        self.get_logger().info('Mesh builder started, listening on /swarm/telemetry')

    def on_telemetry(self, msg: DroneTelemetry):
        # Typed message guarantees structure; we trust the fields.
        self.drone_states[msg.label] = (msg.lat, msg.lon, msg.battery_pct, time.time())

    def publish_topology(self):
        now = time.time()
        active = {
            label: (lat, lon)
            for label, (lat, lon, batt, seen) in self.drone_states.items()
            if now - seen <= STALE_TELEMETRY_AFTER_SEC
        }
        G = build_mesh_graph(active)

        topo = MeshTopology()
        topo.header.stamp = self.get_clock().now().to_msg()
        topo.active_drones = list(G.nodes())
        topo.edges = [
            MeshEdge(a=a, b=b, distance_km=round(d['weight'], 2))
            for a, b, d in G.edges(data=True)
        ]
        self.publisher_.publish(topo)

        if topo.active_drones:
            self.get_logger().info(
                f"Mesh: {len(topo.active_drones)} active drones, {len(topo.edges)} links"
            )


def main(args=None):
    rclpy.init(args=args)
    node = MeshBuilder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
