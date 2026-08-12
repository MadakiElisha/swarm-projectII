"""
Phase 3.5 - Full live pipeline: Telemetry -> Mesh -> Auction.

This is the integration step. It:
  1. Reads LIVE telemetry from all 5 running drones (real MAVLink,
     via live_telemetry.py) instead of hardcoded numbers.
  2. Builds a REAL mesh graph from their live positions (reusing
     Phase 2's radio-range logic).
  3. Runs the Phase 3 auction using that live data.
  4. NEW: checks that the winning drone's bid can actually be
     RELAYED back to the ground station (D1) through the mesh -
     if the winner is out of relay range entirely, the task is
     correctly rejected, even if that drone had the best bid.

Run order required:
  Terminal 1: python3 sim/launch_fleet.py       (leave running)
  Terminal 2: python3 mesh/live_pipeline.py     (this script)
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
from mesh.live_telemetry import collect_live_snapshot
from sim.launch_fleet import FLEET

GROUND_STATION_LABEL = "D1"  # D1 is the drone at the edge with outside signal
RADIO_RANGE_KM = 2.0


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def build_live_mesh_graph(snapshot):
    """Same logic as Phase 2's mesh_sim.py, but fed with LIVE
    telemetry instead of hardcoded DroneNode objects."""
    G = nx.Graph()
    labels = list(snapshot.keys())
    for label in labels:
        G.add_node(label)

    for i, a_label in enumerate(labels):
        a = snapshot[a_label]
        for b_label in labels[i + 1:]:
            b = snapshot[b_label]
            if a.lat is None or b.lat is None:
                continue
            dist = haversine_km(a.lat, a.lon, b.lat, b.lon)
            if dist <= RADIO_RANGE_KM:
                G.add_edge(a_label, b_label, weight=dist)
    return G


def bid_for_task(drone_state, task_lat, task_lon, busy_labels):
    """Same bidding logic as Phase 3, now using LIVE battery/position."""
    if drone_state.label in busy_labels:
        return None
    if drone_state.lat is None or drone_state.battery_pct is None:
        return None  # no live data available - can't safely bid

    dist = haversine_km(drone_state.lat, drone_state.lon, task_lat, task_lon)
    estimated_battery_needed = dist * 4
    if drone_state.battery_pct < estimated_battery_needed + 15:
        return None

    return (dist * 1.0) + ((100 - drone_state.battery_pct) * 0.05)


def run_live_pipeline():
    print("=== STEP 1: Collecting LIVE telemetry from all drones ===")
    snapshot = collect_live_snapshot(timeout_per_drone=3)

    print("\n=== STEP 2: Building REAL mesh graph from live positions ===")
    G = build_live_mesh_graph(snapshot)
    for edge in G.edges(data=True):
        print(f"  {edge[0]} <-> {edge[1]}  (distance: {edge[2]['weight']:.2f} km)")

    task_lat, task_lon = 6.5430, 3.3980
    print(f"\n=== STEP 3: Running auction for task at ({task_lat}, {task_lon}) ===")

    bids = {}
    for label, state in snapshot.items():
        bid = bid_for_task(state, task_lat, task_lon, busy_labels=set())
        if bid is not None:
            bids[label] = bid
            print(f"  {label}: bid = {bid:.2f}")
        else:
            print(f"  {label}: NO BID")

    if not bids:
        print("  No eligible bidders. Task unassigned.")
        return

    # Sort candidates best-to-worst, then check REACHABILITY for each
    # in order - this is the new, real check Phase 3 didn't have.
    ranked = sorted(bids, key=bids.get)

    print(f"\n=== STEP 4: Checking mesh reachability to ground station ({GROUND_STATION_LABEL}) ===")
    for candidate in ranked:
        if candidate == GROUND_STATION_LABEL:
            reachable = True
            path = [candidate]
        elif candidate in G and GROUND_STATION_LABEL in G and nx.has_path(G, candidate, GROUND_STATION_LABEL):
            reachable = True
            path = nx.shortest_path(G, candidate, GROUND_STATION_LABEL, weight="weight")
        else:
            reachable = False
            path = None

        if reachable:
            print(f"  {candidate}: REACHABLE via {' -> '.join(path)} "
                  f"({len(path)-1} hop(s))")
            print(f"\nFINAL RESULT: {candidate} wins task AND can report back "
                  f"to ground station. Task confirmed assigned.")
            return
        else:
            print(f"  {candidate}: bid was good but UNREACHABLE from ground station "
                  f"- rejecting, trying next best bid")

    print("\nFINAL RESULT: No bidder both won AND was reachable. Task unassigned.")


if __name__ == "__main__":
    run_live_pipeline()
