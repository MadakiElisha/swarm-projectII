"""
Hardening pass - automated tests for mesh_core.py

Run with: pytest tests/test_mesh.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from mesh.mesh_core import haversine_km, build_mesh_graph, relay_path


def test_haversine_same_point_is_zero():
    assert haversine_km(6.5244, 3.3792, 6.5244, 3.3792) == pytest.approx(0.0, abs=1e-6)


def test_haversine_known_distance():
    # Lagos to Abuja, roughly 500-530km depending on exact coordinates used -
    # sanity check against a known real-world value
    dist = haversine_km(6.5244, 3.3792, 9.0765, 7.3986)
    assert 480 < dist < 560  # generous bounds, just proving it's in the right ballpark


def test_haversine_rejects_invalid_latitude():
    with pytest.raises(ValueError):
        haversine_km(999, 3.3792, 6.5244, 3.3792)


def test_haversine_rejects_invalid_longitude():
    with pytest.raises(ValueError):
        haversine_km(6.5244, 3.3792, 6.5244, 999)


def test_build_mesh_graph_empty_input():
    G = build_mesh_graph({})
    assert G.number_of_nodes() == 0


def test_build_mesh_graph_single_drone_no_edges():
    G = build_mesh_graph({"D1": (6.5244, 3.3792)})
    assert G.number_of_nodes() == 1
    assert G.number_of_edges() == 0


def test_build_mesh_graph_close_drones_connect():
    positions = {
        "D1": (6.5244, 3.3792),
        "D2": (6.5250, 3.3800),  # very close, should be in range
    }
    G = build_mesh_graph(positions, radio_range_km=2.0)
    assert G.has_edge("D1", "D2")


def test_build_mesh_graph_far_drones_dont_connect():
    positions = {
        "D1": (6.5244, 3.3792),
        "D2": (9.0765, 7.3986),  # Abuja - hundreds of km away
    }
    G = build_mesh_graph(positions, radio_range_km=2.0)
    assert not G.has_edge("D1", "D2")


def test_relay_path_multihop_success():
    # Reproduces the exact Phase 2 scenario: D5 and D1 not in direct
    # range, but reachable via D3
    positions = {
        "D1": (6.5244, 3.3792),
        "D2": (6.5300, 3.3850),
        "D3": (6.5360, 3.3910),
        "D4": (6.5420, 3.3970),
        "D5": (6.5480, 3.4030),
    }
    G = build_mesh_graph(positions, radio_range_km=2.0)
    assert not G.has_edge("D1", "D5")  # confirm the premise: not directly connected

    path = relay_path(G, "D5", "D1")
    assert path is not None
    assert path[0] == "D5"
    assert path[-1] == "D1"
    assert len(path) >= 2  # at least one hop


def test_relay_path_unreachable_returns_none():
    positions = {
        "D1": (6.5244, 3.3792),
        "D2": (9.0765, 7.3986),  # isolated, hundreds of km away
    }
    G = build_mesh_graph(positions, radio_range_km=2.0)
    path = relay_path(G, "D1", "D2")
    assert path is None


def test_relay_path_missing_node_returns_none_not_crash():
    positions = {"D1": (6.5244, 3.3792)}
    G = build_mesh_graph(positions)
    assert relay_path(G, "D1", "D99") is None
    assert relay_path(G, "D99", "D1") is None
