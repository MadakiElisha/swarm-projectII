import math
import random

from swarm_common.perception import Observation, TargetTracker


def _feed(seed=1, parked=8, quarry_v=(3.0, 1.5), t_end=120, start=(1000.0, 900.0)):
    rnd = random.Random(seed)
    obs, n = [], 0
    cars = [(1000 + 60 * k, 840 + 25 * (k % 3)) for k in range(parked)]
    tk = TargetTracker(start[0], start[1], 0.0)
    errs = []
    for t in range(1, t_end):
        qx, qy = start[0] + quarry_v[0] * t, start[1] + quarry_v[1] * t
        for drone in range(3):
            n += 1
            obs.append(Observation(f"{drone}-{n}", "vehicle", qx + rnd.gauss(0, 2), qy + rnd.gauss(0, 2), .9, t, drone))
            for (cx, cy) in cars:
                if rnd.random() < 0.7:
                    n += 1
                    obs.append(Observation(f"{drone}-{n}", "vehicle", cx + rnd.gauss(0, 2), cy + rnd.gauss(0, 2),
                                           .8, t, drone))
        tr = tk.update(obs, float(t))
        if tr is not None and t > 30:
            errs.append(math.hypot(tr.x - qx, tr.y - qy))
    return tk, errs


def test_locks_on_the_moving_car_not_the_parked_ones():
    tk, errs = _feed()
    assert tk.locked is not None and errs
    assert max(errs) < 15.0


def test_velocity_is_estimated_without_detector_velocity():
    tk, _ = _feed()
    assert abs(tk.locked.vx - 3.0) < 0.6 and abs(tk.locked.vy - 1.5) < 0.6


def test_parked_target_is_taken_when_nothing_moves():
    tk, _ = _feed(quarry_v=(0.0, 0.0), t_end=200)
    assert tk.locked is not None
    assert math.hypot(tk.locked.x - 1000, tk.locked.y - 900) < 20


def test_same_observations_same_answer_on_every_drone():
    a, ea = _feed(seed=3)
    b, eb = _feed(seed=3)
    assert ea == eb


def test_motion_watch_ignores_scattered_false_detections():
    """Random false positives all over a patrolled area must never add up to an intruder,
    while a real car driving through is still reported."""
    from swarm_common.perception import MotionWatch
    rnd = random.Random(3)
    w = MotionWatch(0.0, 0.0, 110.0, 0.0)
    obs, n = [], 0
    for k in range(600):                          # 5 drones x 2 Hz x 2 % false positives, 10 min
        t = k * 1.0
        if rnd.random() < 0.2:
            r, a = 110 * rnd.random() ** 0.5, rnd.uniform(0, 6.28)
            n += 1
            obs.append(Observation(f"fp{n}", rnd.choice(["person", "vehicle"]), r * math.cos(a), r * math.sin(a),
                                   0.6, t, 1))
        assert not w.update(obs, t), f"false intruder at t={t}"
    # a car crossing at 6 m/s, seen at 2 Hz with 2 m noise
    for k in range(40):
        t = 600.0 + 0.5 * k
        obs.append(Observation(f"car{k}", "vehicle", -100 + 3.0 * k + rnd.gauss(0, 2), 5 + rnd.gauss(0, 2),
                               0.8, t, 2))
        if w.update(obs, t):
            return
    raise AssertionError("the real car was never reported")


def test_motion_watch_two_parked_things_are_not_a_mover():
    """Seen in turn, a parked car and a person (or two parked cars) 10 m apart must not add up
    to something moving between them (live demo: a false intruder exactly like this)."""
    from swarm_common.perception import MotionWatch
    rnd = random.Random(5)
    for classes in (("person", "vehicle"), ("vehicle", "vehicle")):
        w = MotionWatch(0.0, 0.0, 110.0, 0.0)
        obs = []
        for k in range(400):
            t = 0.5 * k
            j = rnd.random() < 0.5
            x, y = (-62.0, -18.0) if j else (-66.0, -8.5)
            obs.append(Observation(f"s{k}", classes[0] if j else classes[1], x + rnd.gauss(0, 1), y + rnd.gauss(0, 1),
                                   0.7, t, 1 + k % 3))
            assert not w.update(obs, t), f"{classes}: false intruder at t={t}"
