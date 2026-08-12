"""
Phase 2/Hardening - Mesh network core logic, hardened.

Same algorithm as the original mesh_sim.py, but now with:
  - input validation (bad coordinates raise a clear error, not a
    silent wrong answer)
  - centralized config instead of hardcoded constants
  - proper logging instead of print()
  - defensive handling of edge cases (empty node list, single node,
    disconnected graph)
"""
import math
import networkx as nx

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import RADIO_RANGE_KM
from common.logging_setup import get_logger

log = get_logger("mesh")


def haversine_km(lat1, lon1, lat2, lon2):
    """Real distance between two GPS points. Raises ValueError on
    invalid coordinates rather than silently producing nonsense."""
    for name, val, lo, hi in [("lat1", lat1, -90, 90), ("lat2", lat2, -90, 90),
                               ("lon1", lon1, -180, 180), ("lon2", lon2, -180, 180)]:
        if not (lo <= val <= hi):
            raise ValueError(f"haversine_km: {name}={val} out of valid range [{lo}, {hi}]")

    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def build_mesh_graph(drone_positions: dict, radio_range_km: float = RADIO_RANGE_KM) -> nx.Graph:
    """
    drone_positions: dict of label -> (lat, lon)
    Returns a graph with an edge between any two drones within
    radio_range_km of each other. Empty/single-node input returns a
    valid (if trivial) graph rather than erroring.
    """
    G = nx.Graph()

    if not drone_positions:
        log.warning("build_mesh_graph called with no drones - returning empty graph")
        return G

    for label in drone_positions:
        G.add_node(label)

    labels = list(drone_positions.keys())
    for i, a_label in enumerate(labels):
        a_lat, a_lon = drone_positions[a_label]
        for b_label in labels[i + 1:]:
            b_lat, b_lon = drone_positions[b_label]
            try:
                dist = haversine_km(a_lat, a_lon, b_lat, b_lon)
            except ValueError as e:
                log.error(f"Skipping edge {a_label}-{b_label}: {e}")
                continue
            if dist <= radio_range_km:
                G.add_edge(a_label, b_label, weight=dist)

    log.info(f"Built mesh graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def relay_path(G: nx.Graph, source: str, dest: str):
    """Returns the multi-hop path from source to dest, or None if
    unreachable. Handles missing nodes gracefully instead of raising
    a raw networkx exception."""
    if source not in G:
        log.warning(f"relay_path: source '{source}' not in graph")
        return None
    if dest not in G:
        log.warning(f"relay_path: dest '{dest}' not in graph")
        return None
    if not nx.has_path(G, source, dest):
        log.info(f"relay_path: no path exists from {source} to {dest} (network partitioned)")
        return None
    return nx.shortest_path(G, source, dest, weight="weight")
