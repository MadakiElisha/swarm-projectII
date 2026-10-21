"""Property tests: CBBA must converge to a conflict-free allocation that every
agent agrees on, over lossy multi-hop networks, with no leader."""
import math
import random

import pytest

from swarm_common.cbba import CBBA, NONE


def _world(seed, n_agents, n_tasks):
    rnd = random.Random(seed)
    pos = {i: (rnd.uniform(0, 2000), rnd.uniform(0, 2000)) for i in range(1, n_agents + 1)}
    items = {f"T{j:02d}": (rnd.uniform(0, 2000), rnd.uniform(0, 2000)) for j in range(n_tasks)}
    return rnd, pos, items


def _score(pos, items, i):
    def f(path):
        t, cur, s = 0.0, pos[i], 0.0
        for j in path:
            t += math.dist(cur, items[j]) / 10.0
            s += 100 * 0.995 ** t
            cur = items[j]
        return s
    return f


def _run(seed, n_agents=8, n_tasks=6, L=1, loss=0.3, topology="line", rounds=300, dead=()):
    rnd, pos, items = _world(seed, n_agents, n_tasks)
    agents = {i: CBBA(i, L) for i in pos}
    ids = sorted(pos)
    if topology == "line":
        nbr = {i: [k for k in ids if abs(k - i) == 1] for i in ids}
    else:
        nbr = {i: [k for k in ids if k != i] for i in ids}
    for r in range(rounds):
        for i, a in agents.items():
            if i not in dead:
                a.build_bundle(items, _score(pos, items, i), now=r)
        msgs = {i: a.message() for i, a in agents.items()}
        for i, a in agents.items():
            for k in nbr[i]:
                if k not in dead and i not in dead and rnd.random() >= loss:
                    a.receive(k, msgs[k], r)
    return agents, items


def _check(agents, items, dead=()):
    live = {i: a for i, a in agents.items() if i not in dead}
    views = [a.assignments() for a in live.values()]
    assert all(v == views[0] for v in views), "agents disagree on the allocation"
    owners = {}
    for i, a in live.items():
        for j in a.bundle:
            owners.setdefault(j, []).append(i)
    assert all(len(o) == 1 for o in owners.values()), f"conflict: {owners}"
    return owners


@pytest.mark.parametrize("seed", range(10))
def test_converges_on_lossy_multihop_line(seed):
    agents, items = _run(seed)
    owners = _check(agents, items)
    assert len(owners) == len(items)       # 8 agents, 6 tasks: everything assigned


@pytest.mark.parametrize("seed", range(5))
def test_bundles_of_three(seed):
    agents, items = _run(seed, n_agents=6, n_tasks=15, L=3, loss=0.2, rounds=500)
    owners = _check(agents, items)
    assert len(owners) == 15


def test_more_tasks_than_capacity_assigns_capacity():
    agents, items = _run(1, n_agents=3, n_tasks=7, L=1, loss=0.0, topology="full")
    assert len(_check(agents, items)) == 3


def test_release_hands_task_to_next_best():
    agents, items = _run(2, n_agents=4, n_tasks=1, L=1, loss=0.0, topology="full", rounds=50)
    owner = _check(agents, items)["T00"][0]
    agents[owner].release("T00")
    rnd, pos, items = _world(2, 4, 1)
    for r in range(50, 100):
        for i, a in agents.items():
            if i != owner:     # the tired drone stops bidding
                a.build_bundle(items, _score(pos, items, i), now=r)
        msgs = {i: a.message() for i, a in agents.items()}
        for i, a in agents.items():
            for k in agents:
                if k != i:
                    a.receive(k, msgs[k], r)
    new = _check(agents, items)["T00"][0]
    assert new != owner


def test_dead_agents_claims_are_dropped():
    a = CBBA(1)
    a.z["T1"], a.y["T1"] = 7, 50.0
    a.sync_items(["T1"], alive={1, 2})
    assert a.winner("T1") == NONE


def test_tie_breaks_to_lower_id():
    a, b = CBBA(1), CBBA(2)
    f = lambda path: 10.0 * len(path)
    a.build_bundle(["T"], f)
    b.build_bundle(["T"], f)
    a.receive(2, b.message(), 1)
    b.receive(1, a.message(), 1)
    assert a.winner("T") == b.winner("T") == 1


def test_malformed_message_is_ignored():
    a = CBBA(1)
    assert a.receive(2, {"y": {"T": "x"}, "z": None}, 0) is False
