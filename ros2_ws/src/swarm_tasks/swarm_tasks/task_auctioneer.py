"""Task Auctioneer node: assigns tasks via auction.

Thin ROS shell over the tested swarm_common.auction_core logic.
Production hardening included:
  1. drone_states pruning (stale drones are dropped).
  2. busy_drones timeout (a lost task_complete can't lock a drone forever).
  3. Idempotent auctions: an already-assigned task is stored; duplicate
     requests re-publish the stored result instead of re-auctioning,
     which makes retries safe over lossy links.
  4. Relinquish handling: a tired drone's relinquish reopens the task,
     excludes that drone (busy cooldown), and re-auctions immediately -
     the swarm covers for its members.
"""
import time

import networkx as nx
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
LATCH = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)


from swarm_interfaces.msg import (
    DroneTelemetry, MeshTopology, TaskRequest, TaskAssignment, TaskComplete,
    TaskRelinquish,
)
from swarm_common.auction_core import calculate_bid
from swarm_common.config import GROUND_STATION_LABEL, STALE_TELEMETRY_AFTER_SEC

BUSY_TIMEOUT_SEC = 120.0


class TaskAuctioneer(Node):
    def __init__(self):
        super().__init__('task_auctioneer')
        self.drone_states = {}
        self.current_topology = MeshTopology()
        self.busy_drones = {}
        self.auction_results = {}  # task_id -> TaskAssignment (assigned only)
        self.task_coords = {}      # task_id -> (lat, lon)
        self.suggestions = {}      # task_id -> first-seen (awaiting human confirmation)

        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telemetry, 10)
        self.create_subscription(MeshTopology, '/swarm/mesh_topology', self.on_topology, 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_task_request, 10)
        self.create_subscription(TaskComplete, '/swarm/task_complete', self.on_task_complete, 10)
        self.create_subscription(TaskRelinquish, '/swarm/task_relinquish', self.on_relinquish, 10)
        self.publisher_ = self.create_publisher(TaskAssignment, '/swarm/task_assignments', LATCH)
        self.create_timer(2.0, self.housekeeping)
        self.get_logger().info('Task auctioneer started, waiting for task requests...')

    def housekeeping(self):
        now = time.time()
        stale = [l for l, s in self.drone_states.items() if now - s[3] > STALE_TELEMETRY_AFTER_SEC]
        for label in stale:
            del self.drone_states[label]
            self.get_logger().info(f'Pruned stale drone {label} from auctioneer state')
        expired = [l for l, t in self.busy_drones.items() if now - t > BUSY_TIMEOUT_SEC]
        for label in expired:
            del self.busy_drones[label]
            self.get_logger().warning(f'Released {label} from busy after {BUSY_TIMEOUT_SEC}s timeout')
        # swarm covers for members that can no longer speak for themselves
        for task_id, res in list(self.auction_results.items()):
            label = res.assigned_to
            st = self.drone_states.get(label)
            if st is None:
                continue
            _lat, _lon, batt, _seen = st
            if batt < 10.0:
                self.get_logger().warn(
                    f'{label} battery empty ({batt:.0f}%) while holding {task_id} - swarm covers')
                self.busy_drones[label] = time.time()
                del self.auction_results[task_id]
                coords = self.task_coords.get(task_id)
                if coords:
                    self._run_auction(task_id, coords[0], coords[1])

    def on_telemetry(self, msg: DroneTelemetry):
        self.drone_states[msg.label] = (msg.lat, msg.lon, msg.battery_pct, time.time())

    def on_topology(self, msg: MeshTopology):
        self.current_topology = msg

    def on_task_complete(self, msg: TaskComplete):
        label = msg.drone_label
        if label in self.busy_drones:
            del self.busy_drones[label]
            self.get_logger().info(f'{label} reported task complete - now available again')
        else:
            self.get_logger().warning(f'Got task_complete for {label}, but it was not marked busy')

    def on_relinquish(self, msg):
        label, task_id = msg.label, msg.task_id
        self.get_logger().warn(f'{label} relinquished {task_id} ({msg.reason})')
        # the tired drone is going home: exclude it from re-bidding for a while
        self.busy_drones[label] = time.time()
        # reopen the task and re-auction immediately
        self.auction_results.pop(task_id, None)
        coords = self.task_coords.get(task_id)
        if coords is None:
            self.get_logger().warning(f'relinquish for unknown task {task_id}')
            return
        self.get_logger().info(f'Re-auctioning {task_id} (swarm covers for {label})')
        self._run_auction(task_id, coords[0], coords[1])

    def build_graph(self) -> nx.Graph:
        G = nx.Graph()
        for label in self.current_topology.active_drones:
            G.add_node(label)
        for e in self.current_topology.edges:
            G.add_edge(e.a, e.b, weight=e.distance_km)
        return G

    def on_task_request(self, msg: TaskRequest):
        task_id, task_lat, task_lon = msg.task_id, msg.lat, msg.lon
        self.task_coords[task_id] = (task_lat, task_lon)

        # Idempotency: duplicate request for an already-assigned task
        # re-publishes the stored result (safe retries, lost-ack recovery).
        if task_id in self.auction_results:
            self.get_logger().info(f'{task_id}: already assigned - re-publishing stored result')
            self.publisher_.publish(self.auction_results[task_id])
            return

        # M3.5a HITL: perception-sourced tasks need a human confirmation.
        # First sighting is held as a suggestion; the repeated request
        # (operator clicking the pulsing star in the GCS) releases it.
        if task_id.startswith('RESCUE-') and task_id not in self.suggestions:
            self.suggestions[task_id] = time.time()
            self.get_logger().warn(
                f'{task_id}: SUGGESTED by perception - awaiting human confirmation')
            return
        if task_id in self.suggestions:
            del self.suggestions[task_id]
            self.get_logger().info(f'{task_id}: human confirmed - auctioning')

        self._run_auction(task_id, task_lat, task_lon)

    def _run_auction(self, task_id, task_lat, task_lon):
        self.get_logger().info(f'Auction started for {task_id}')

        if not self.drone_states:
            self.get_logger().warning(
                'Auction has ZERO known drones - never received /swarm/telemetry'
            )

        bids = {}
        for label, (lat, lon, batt, _seen) in self.drone_states.items():
            is_busy = label in self.busy_drones
            self.get_logger().info(
                f'  Candidate {label}: lat={lat}, lon={lon}, battery={batt}%, busy={is_busy}'
            )
            try:
                bid = calculate_bid(lat, lon, batt, task_lat, task_lon, is_busy=is_busy)
            except ValueError as e:
                self.get_logger().error(f'  {label}: EXCEPTION - {e}')
                continue
            if bid is None:
                self.get_logger().info(f'  {label}: REJECTED (busy or insufficient battery margin)')
            else:
                self.get_logger().info(f'  {label}: bid = {bid:.3f}')
                bids[label] = bid

        result = TaskAssignment()
        result.header.stamp = self.get_clock().now().to_msg()
        result.task_id = task_id
        result.assigned_to = ''
        result.path = []

        if bids:
            G = self.build_graph()
            for candidate in sorted(bids, key=bids.get):
                if candidate == GROUND_STATION_LABEL:
                    path = [candidate]
                elif candidate in G and GROUND_STATION_LABEL in G and \
                        nx.has_path(G, candidate, GROUND_STATION_LABEL):
                    path = nx.shortest_path(G, candidate, GROUND_STATION_LABEL, weight='weight')
                else:
                    self.get_logger().info(
                        f'{candidate} had bid {bids[candidate]:.2f} but is unreachable '
                        f'from ground station - trying next best bid'
                    )
                    continue
                result.assigned_to = candidate
                result.path = path
                self.busy_drones[candidate] = time.time()
                break

        if result.assigned_to:
            self.auction_results[task_id] = result  # store for idempotent re-ack

        self.publisher_.publish(result)
        if result.assigned_to:
            self.get_logger().info(
                f"{task_id} -> {result.assigned_to} (path: {' -> '.join(result.path)})"
            )
        else:
            self.get_logger().info(f'{task_id} -> UNASSIGNED')


def main(args=None):
    rclpy.init(args=args)
    node = TaskAuctioneer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
