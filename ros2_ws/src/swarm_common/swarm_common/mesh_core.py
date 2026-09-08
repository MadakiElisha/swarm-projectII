"""Pure mesh logic. No ROS dependencies - fully unit-testable."""
import math
import networkx as nx

from .config import RADIO_RANGE_KM


def haversine_km(lat1, lon1, lat2, lon2):
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
    G = nx.Graph()
    if not drone_positions:
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
            except ValueError:
                continue
            if dist <= radio_range_km:
                G.add_edge(a_label, b_label, weight=dist)
    return G


def relay_path(G: nx.Graph, source: str, dest: str):
    if source not in G or dest not in G:
        return None
    if not nx.has_path(G, source, dest):
        return None
    return nx.shortest_path(G, source, dest, weight="weight")
