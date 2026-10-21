"""End-to-end swarm behaviour in the ROS-free simulator (real brain + FSM)."""
import pytest

from swarm_common.sim import scenarios


@pytest.mark.parametrize("name", list(scenarios.ALL))
def test_scenario(name):
    r = scenarios.ALL[name]()
    assert r.passed, r.summary()


@pytest.mark.parametrize("name", ["single_dispatch", "perimeter", "drone_loss"])
def test_scenarios_survive_heavy_packet_loss(name):
    r = scenarios.ALL[name](seed=31, loss=0.3)
    assert r.passed, r.summary()
