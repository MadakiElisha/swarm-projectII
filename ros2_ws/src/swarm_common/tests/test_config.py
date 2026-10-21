import pytest

from swarm_common.config import fleet_from_dict, label_to_id, load_fleet, synthetic_fleet


def test_repo_fleet_loads_and_is_consistent():
    f = load_fleet()
    assert [d.id for d in f.drones] == sorted(d.id for d in f.drones)
    assert f.swarm.energy.critical_pct < f.swarm.energy.reserve_pct
    for d in f.drones:
        x, y = f.home_enu(d.id)
        assert abs(x) < f.swarm.geofence.radius_m and abs(y) < f.swarm.geofence.radius_m


def test_unknown_keys_fail_loudly():
    with pytest.raises(ValueError):
        fleet_from_dict({"swarm": {"radio_rnage_m": 1}, "drones": []})


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):
        fleet_from_dict({"drones": [{"id": 1, "home_lat": 0, "home_lon": 0},
                                    {"id": 1, "home_lat": 0, "home_lon": 0}]})


def test_label_parsing_is_numeric_not_lexical():
    assert label_to_id("D10") == 10 and label_to_id("D2") == 2
    with pytest.raises(ValueError):
        label_to_id("X3")


def test_synthetic_fleet():
    f = synthetic_fleet(12)
    assert len(f.drones) == 12 and f.drones[-1].label == "D12"
