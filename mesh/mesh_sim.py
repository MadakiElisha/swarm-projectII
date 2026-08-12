"""
Phase 2 - Mesh network simulation.

Simulates N drones as nodes with GPS positions. Two drones can only
talk directly if they're within radio range (like real LoRa/WiFi
radios). We then run a shortest-path relay (the same core idea as
batman-adv / AODV) so a message can hop through intermediate drones
to reach a destination that's out of direct range.

This is a real, runnable proof of the mesh-relay concept - the same
one you'd later replace with real LoRa/Meshtastic hardware.
"""
import math
import networkx as nx


class DroneNode:
    def __init__(self, node_id, lat, lon, radio_range_km=2.0):
        self.node_id = node_id
        self.lat = lat
        self.lon = lon
        self.radio_range_km = radio_range_km

    def distance_km(self, other):
        # Haversine formula - real distance between two GPS points
        R = 6371.0
        dlat = math.radians(other.lat - self.lat)
        dlon = math.radians(other.lon - self.lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(self.lat)) * math.cos(math.radians(other.lat)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def in_range_of(self, other):
        return self.distance_km(other) <= self.radio_range_km


def build_mesh_graph(nodes):
    """Build a graph where an edge exists only if two drones are
    within each other's radio range - this is the real-world
    constraint that makes mesh routing necessary."""
    G = nx.Graph()
    for n in nodes:
        G.add_node(n.node_id, obj=n)

    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if a.in_range_of(b):
                dist = a.distance_km(b)
                G.add_edge(a.node_id, b.node_id, weight=dist)
    return G


def relay_message(G, source_id, dest_id):
    """Find the multi-hop relay path a message would take, the same
    problem batman-adv/AODV solve on real hardware."""
    if not nx.has_path(G, source_id, dest_id):
        return None
    path = nx.shortest_path(G, source_id, dest_id, weight="weight")
    return path


def demo():
    # 5 drones spread across a simulated flood zone in Lagos.
    # Deliberately spaced so NOT all of them are in direct range of each other.
    nodes = [
        DroneNode("D1", 6.5244, 3.3792, radio_range_km=2.0),  # edge of zone (has outside link)
        DroneNode("D2", 6.5300, 3.3850, radio_range_km=2.0),
        DroneNode("D3", 6.5360, 3.3910, radio_range_km=2.0),
        DroneNode("D4", 6.5420, 3.3970, radio_range_km=2.0),
        DroneNode("D5", 6.5480, 3.4030, radio_range_km=2.0),  # deep in flood zone, stranded person here
    ]

    G = build_mesh_graph(nodes)

    print("=== Mesh topology (who can directly talk to who) ===")
    for edge in G.edges(data=True):
        print(f"  {edge[0]} <-> {edge[1]}  (distance: {edge[2]['weight']:.2f} km)")

    print(f"\nTotal direct links: {G.number_of_edges()} out of "
          f"{len(nodes) * (len(nodes) - 1) // 2} possible pairs")

    print("\n=== Testing message relay: D5 (stranded person) -> D1 (edge, has signal) ===")
    path = relay_message(G, "D5", "D1")
    if path:
        print(f"SUCCESS: message relayed via path: {' -> '.join(path)}")
        print(f"That's {len(path) - 1} hop(s) - D5 and D1 are NOT in direct range, "
              f"but the mesh got the message through anyway.")
    else:
        print("FAILURE: no path exists - network is partitioned.")

    return G


if __name__ == "__main__":
    demo()
