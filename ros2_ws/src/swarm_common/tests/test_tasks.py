import itertools
import random

from swarm_common.config import FormationCfg
from swarm_common.tasks import (DONE, FORMATION, GOTO, MERGED, OPEN, RESCUE, SUGGESTED, Task,
                                TaskRegistry, derive_work_items, merge_task)


def _t(tid="T1", status=OPEN, st=0.0, created=1.0, creator=1, kind=GOTO, x=0.0):
    return Task(tid, kind, x, 0.0, created, creator, status, st, {})


def test_merge_is_commutative_associative_idempotent():
    vs = [_t(status=OPEN, st=1), _t(status=DONE, st=5, creator=2, created=0.5),
          _t(status=SUGGESTED, st=0, creator=3)]
    for a, b in itertools.permutations(vs, 2):
        assert merge_task(a, b) == merge_task(b, a)
        assert merge_task(a, a) == a
    for a, b, c in itertools.permutations(vs, 3):
        assert merge_task(merge_task(a, b), c) == merge_task(a, merge_task(b, c))


def test_status_is_monotone():
    r = TaskRegistry()
    r.upsert(_t(status=DONE, st=5))
    r.upsert(_t(status=OPEN, st=9))
    assert r.get("T1").status == DONE
    assert not r.set_status("T1", OPEN, 10)


def test_registries_converge_under_random_gossip_order():
    rnd = random.Random(0)
    updates = [_t(f"T{rnd.randint(0, 4)}", rnd.choice([SUGGESTED, OPEN, DONE]), rnd.random(),
                  rnd.choice([1.0, 2.0]), rnd.randint(1, 3)).to_wire() for _ in range(60)]
    regs = []
    for _ in range(5):
        r = TaskRegistry()
        u = updates[:]
        rnd.shuffle(u)
        for chunk in range(0, len(u), 7):
            r.merge(u[chunk:chunk + 7] + u[:3])     # with duplicates
        regs.append({k: v for k, v in r.tasks.items()})
    assert all(r == regs[0] for r in regs)


def test_duplicate_rescues_fold_deterministically():
    a, b = TaskRegistry(), TaskRegistry()
    t1 = Task("RESCUE-1-1", RESCUE, 100, 100, 10.0, 1, SUGGESTED, 10, {})
    t2 = Task("RESCUE-2-7", RESCUE, 110, 95, 11.0, 2, OPEN, 12, {})     # same person, confirmed
    for r, order in ((a, (t1, t2)), (b, (t2, t1))):
        for t in order:
            r.upsert(t)
        r.resolve_duplicates(RESCUE, 50.0, now=20)
    for r in (a, b):
        assert r.get("RESCUE-1-1").status == OPEN       # survivor inherits confirmation
        assert r.get("RESCUE-2-7").status == MERGED
    assert a.tasks == b.tasks


def test_malformed_wire_entries_are_skipped():
    r = TaskRegistry()
    assert not r.merge([{"id": "x"}, {"bogus": 1}, None.__class__ and {}])


def test_formation_slots_are_derived_identically():
    cfg = FormationCfg()
    regs = []
    for _ in range(2):
        r = TaskRegistry()
        r.upsert(Task("SWARM-1", FORMATION, 0, 0, 5.0, 1, OPEN, 5, {"n_slots": 4, "expires_at": 900}))
        regs.append(derive_work_items(r, 100.0, cfg))
    assert regs[0] == regs[1] and sorted(regs[0]) == [f"SWARM-1/s{i}" for i in range(4)]
    assert len({it.group for it in regs[0].values()}) == 1


def test_suggested_tasks_are_not_allocatable():
    r = TaskRegistry()
    r.upsert(Task("RESCUE-9", RESCUE, 0, 0, 1, 1, SUGGESTED, 1, {}))
    assert derive_work_items(r, 2.0, FormationCfg()) == {}
