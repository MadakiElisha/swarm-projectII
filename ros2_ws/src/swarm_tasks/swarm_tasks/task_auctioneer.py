"""Task Auctioneer node: assigns tasks via contract-net auction.

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
  5. Mission-state aggregation (leader only): per-drone MissionStatus
     reports are folded into exactly one PERIMETER_FORMED /
     PERIMETER_DEGRADED / RELEASED event per task.

BEHAVIOR IS FROZEN: consolidation pass 2/3 is a readability rewrite.
All timings, thresholds, log lines, attribute and method names are
unchanged (replicated auctioneers subclass this class); the regression
gate (C1-C6) is the equivalence proof.
"""
import math
import time

import networkx as nx
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy

from swarm_interfaces.msg import (
    DroneTelemetry, MeshTopology, TaskRequest, TaskAssignment, TaskComplete,
    TaskRelinquish, MissionEvent, MissionStatus,
)
from swarm_common.auction_core import calculate_bid
from swarm_common.config import GROUND_STATION_LABEL, STALE_TELEMETRY_AFTER_SEC

# Latched QoS: late joiners must still see stored assignments.
LATCH = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)

# --- hardening thresholds (frozen) ---
BUSY_TIMEOUT_SEC = 120.0        # a lost task_complete can't lock a drone forever
EMPTY_BATTERY_PCT = 10.0        # below this the swarm covers for the holder
STATUS_FRESH_SEC = 10.0         # ON_STATION reports older than this don't count

# --- formation geometry & timing (frozen) ---
RING_RADIUS_M = 300.0           # pentagon slot radius in metres
MAX_FORMATION_WINNERS = 5       # top-N bidders form the ring
LIFT_LEAD_SEC = 15.0            # execute_at = now + this (T0: synchronized lift)
ARRIVE_WINDOW_SEC = 60.0        # arrive_by = now + this (T1: on station)


class TaskAuctioneer(Node):
    def __init__(self):
        super().__init__('task_auctioneer')
        # --- live world state ---
        self.drone_states = {}          # label -> (lat, lon, battery, seen_at)
        self.current_topology = MeshTopology()
        # --- task bookkeeping ---
        self.busy_drones = {}           # label -> busy-since timestamp
        self.auction_results = {}       # task_id -> TaskAssignment (assigned only)
        self.task_coords = {}           # task_id -> (lat, lon)
        self.suggestions = {}           # task_id -> first-seen (awaiting human confirmation)
        self._swarm_seen = set()        # SWARM/INTERCEPT ids already accepted
        # --- mission-state aggregation ---
        self.winners = {}               # task_id -> [labels] in the ring
        self.station = {}               # (task_id, label) -> (phase, seen_at)
        self.formed_state = {}          # task_id -> bool (ring currently formed)
        # --- IO ---
        self.event_pub = self.create_publisher(MissionEvent, '/swarm/mission_event', 10)
        self.create_subscription(MissionStatus, '/swarm/mission_status', self.on_status, 10)
        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telemetry, 10)
        self.create_subscription(MeshTopology, '/swarm/mesh_topology', self.on_topology, 10)
        self.create_subscription(TaskRequest, '/swarm/task_requests', self.on_task_request, 10)
        self.create_subscription(TaskComplete, '/swarm/task_complete', self.on_task_complete, 10)
        self.create_subscription(TaskRelinquish, '/swarm/task_relinquish', self.on_relinquish, 10)
        self.publisher_ = self.create_publisher(TaskAssignment, '/swarm/task_assignments', LATCH)
        self.create_timer(2.0, self.housekeeping)
        self.get_logger().info('Task auctioneer started, waiting for task requests...')

    # ------------------------------------------------------------------
    # housekeeping: pruning, busy expiry, swarm-covers-for-members
    # ------------------------------------------------------------------
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
            if batt < EMPTY_BATTERY_PCT:
                self.get_logger().warn(
                    f'{label} battery empty ({batt:.0f}%) while holding {task_id} - swarm covers')
                self.busy_drones[label] = time.time()
                del self.auction_results[task_id]
                coords = self.task_coords.get(task_id)
                if coords:
                    self._run_auction(task_id, coords[0], coords[1])

    # ------------------------------------------------------------------
    # inbound: world state
    # ------------------------------------------------------------------
    def on_telemetry(self, msg: DroneTelemetry):
        self.drone_states[msg.label] = (msg.lat, msg.lon, msg.battery_pct, time.time())

    def on_topology(self, msg: MeshTopology):
        self.current_topology = msg

    def build_graph(self) -> nx.Graph:
        G = nx.Graph()
        for label in self.current_topology.active_drones:
            G.add_node(label)
        for e in self.current_topology.edges:
            G.add_edge(e.a, e.b, weight=e.distance_km)
        return G

    # ------------------------------------------------------------------
    # inbound: task lifecycle (complete / relinquish / request)
    # ------------------------------------------------------------------
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

    def on_task_request(self, msg: TaskRequest):
        task_id, task_lat, task_lon = msg.task_id, msg.lat, msg.lon
        self.task_coords[task_id] = (task_lat, task_lon)

        # Idempotency: duplicate request for an already-assigned task
        # re-publishes the stored result (safe retries, lost-ack recovery).
        if task_id in self.auction_results:
            self.get_logger().info(f'{task_id}: already assigned - re-publishing stored result')
            self.publisher_.publish(self.auction_results[task_id])
            return

        if task_id.startswith(('SWARM-', 'INTERCEPT-')):
            if task_id in self._swarm_seen:
                self.get_logger().info(f'{task_id}: duplicate request ignored')
                return
            self._swarm_seen.add(task_id)

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

    # ------------------------------------------------------------------
    # the auction itself
    # ------------------------------------------------------------------
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

        # M3.6a: Multi-winner SWARM/INTERCEPT tasks
        if task_id.startswith(('SWARM-', 'INTERCEPT-')) and len(bids) > 1:
            self.get_logger().info(f'{task_id}: SWARM task - assigning top {min(MAX_FORMATION_WINNERS, len(bids))} bidders to formation')
            winners = sorted(bids, key=bids.get)[:MAX_FORMATION_WINNERS]
            self.winners[task_id] = winners
            N = len(winners)
            for i, winner in enumerate(winners):
                # Pentagon ring offsets (meters)
                angle = (2 * math.pi * i) / N
                ox, oy = RING_RADIUS_M * math.cos(angle), RING_RADIUS_M * math.sin(angle)

                res = TaskAssignment()
                res.header.stamp = self.get_clock().now().to_msg()
                res.task_id = task_id
                res.assigned_to = winner
                res.path = [winner]
                res.execute_at = time.time() + LIFT_LEAD_SEC    # T0: takeoff in 15s
                res.arrive_by = time.time() + ARRIVE_WINDOW_SEC  # T1: arrive in 60s
                res.offset_x = ox
                res.offset_y = oy
                res.orbit_radius = RING_RADIUS_M
                self.busy_drones[winner] = time.time()
                self.publisher_.publish(res)
                self.get_logger().info(f'{task_id} -> {winner} (slot {i+1}/{N}, offset {ox:.0f},{oy:.0f})')
            return

        if result.assigned_to:
            self.auction_results[task_id] = result  # store for idempotent re-ack

        self.publisher_.publish(result)
        if result.assigned_to:
            self.get_logger().info(
                f"{task_id} -> {result.assigned_to} (path: {' -> '.join(result.path)})"
            )
        else:
            self.get_logger().info(f'{task_id} -> UNASSIGNED')

    # ------------------------------------------------------------------
    # mission-state aggregation (leader only) -> single event per task
    # ------------------------------------------------------------------
    def on_status(self, m):
        self.station[(m.task_id, m.label)] = (m.phase, time.time())
        winners = self.winners.get(m.task_id)
        if not winners or not getattr(self, 'is_leader', True):
            return  # only the elected leader aggregates mission state
        now = time.time()

        def st(w):
            return self.station.get((m.task_id, w), ('', 0))

        on = all(st(w)[0] == 'ON_STATION' and now - st(w)[1] < STATUS_FRESH_SEC for w in winners)
        released = any(st(w)[0] == 'RELEASED' for w in winners)
        cur = self.formed_state.get(m.task_id, False)
        if released and cur:
            self.formed_state[m.task_id] = False
            self._emit(m.task_id, 'RELEASED', 'swarm released - RTB')
        elif on and not cur:
            self.formed_state[m.task_id] = True
            self._emit(m.task_id, 'PERIMETER_FORMED',
                       f'{len(winners)}/{len(winners)} on station - awaiting next action')
        elif not on and cur and not released:
            self.formed_state[m.task_id] = False
            k = sum(1 for w in winners if st(w)[0] == 'ON_STATION')
            self._emit(m.task_id, 'PERIMETER_DEGRADED', f'{k}/{len(winners)} on station')

    def _emit(self, task_id, event, detail):
        e = MissionEvent()
        e.header.stamp = self.get_clock().now().to_msg()
        e.task_id = task_id
        e.event = event
        e.detail = detail
        self.event_pub.publish(e)
        self.get_logger().warn(f'{task_id}: {event} ({detail})')


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
