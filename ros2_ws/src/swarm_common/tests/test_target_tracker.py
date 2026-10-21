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
    tk, _ = _feed(quarry_v=(0.0, 0.0), t_end=100)
    assert tk.locked is not None
    assert math.hypot(tk.locked.x - 1000, tk.locked.y - 900) < 20


def test_same_observations_same_answer_on_every_drone():
    a, ea = _feed(seed=3)
    b, eb = _feed(seed=3)
    assert ea == eb
