import random

from swarm_common.brain import DroneBrain, OwnState
from swarm_common.config import load_fleet


def test_garbage_packets_never_crash_the_brain():
    b = DroneBrain(load_fleet(), 1)
    b.on_vehicle(OwnState(0.0, 0.0, 0.0, 0.0))
    rnd = random.Random(0)
    junk = [None, 1, "x", {}, {"v": 1}, {"v": 1, "src": "a", "seq": 1, "k": "S"},
            {"v": 1, "src": 2, "seq": 1, "k": "S", "d": {"tasks": [{"id": 3}], "r": [1, 2],
                                                         "cbba": {"y": 5}, "obs": "zz",
                                                         "cov": {"SEARCH-1": [[1, "b"]]}}},
            {"v": 1, "src": 2, "seq": 2, "k": "B", "d": {"x": "nan"}}]
    for k in range(200):
        p = rnd.choice(junk)
        try:
            b.on_packet(p if isinstance(p, dict) else {"v": 1, "src": 2, "seq": k, "k": "S", "d": p}, k)
        except Exception as e:   # pragma: no cover
            raise AssertionError(f"brain crashed on {p!r}: {e}")
        b.tick(float(k))


def test_operator_confirm_promotes_suggestion():
    f = load_fleet()
    b = DroneBrain(f, 1)
    b.on_vehicle(OwnState(0.0, 0.0, 0.0, 0.0))
    b.on_operator_task("SEARCH-1", 500.0, 500.0, 0.0, params={"area": [300.0, 300.0, 700.0, 700.0]})
    for k in range(3):
        b.on_detection("person", 500.0, 500.0, 0.9, float(k))
    out = b.tick(5.0)
    assert out.suggestions and out.suggestions[0].status == "SUGGESTED"
    tid = out.suggestions[0].id
    assert b.on_operator_task(tid, 500.0, 500.0, 6.0) == "confirmed"
    assert b.registry.get(tid).status == "OPEN"


def test_people_seen_outside_a_search_raise_no_suggestions():
    """Patrols and chases see people on the street: they are not casualties."""
    b = DroneBrain(load_fleet(), 1)
    b.on_vehicle(OwnState(0.0, 0.0, 0.0, 0.0))
    for k in range(5):
        b.on_detection("person", 500.0, 500.0, 0.9, float(k))
    out = b.tick(6.0)
    assert not out.suggestions
    assert not [t for t in b.registry.tasks.values() if t.kind == "RESCUE"]
    # ...and inside a search area they do
    b.on_operator_task("SEARCH-1", 500.0, 500.0, 7.0, params={"area": [300.0, 300.0, 700.0, 700.0]})
    for k in range(3):
        b.on_detection("person", 510.0, 505.0, 0.9, 8.0 + k)
    assert b.tick(12.0).suggestions
