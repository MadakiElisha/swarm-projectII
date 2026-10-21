import math

from swarm_common.config import MotionCfg
from swarm_common.motion import altitude_layer, avoid, limit_accel, preferred_velocity
from swarm_common.orca import Neighbor, orca_velocity


def test_raw_orca_keeps_separation_head_on():
    p = [(-100.0, 0.0), (100.0, 0.0)]
    v = [(0.0, 0.0), (0.0, 0.0)]
    dmin = 1e9
    for _ in range(300):
        nv = [orca_velocity(p[i], v[i], 5.0, (8.0 if i == 0 else -8.0, 0.0), 10.0,
                            [Neighbor(p[1 - i], v[1 - i], 5.0)], 5.0, 0.1) for i in range(2)]
        v = nv
        p = [(p[i][0] + v[i][0] * 0.1, p[i][1] + v[i][1] * 0.1) for i in range(2)]
        dmin = min(dmin, math.dist(p[0], p[1]))
    assert dmin >= 9.9      # (a perfectly symmetric pair may stall: see keep-right test)


def test_head_on_pair_passes_with_keep_right():
    cfg = MotionCfg(layers=1, cruise_speed_mps=8.0, safety_radius_m=5.0)
    p = [(-100.0, 0.0), (100.0, 0.0)]
    v = [(0.0, 0.0), (0.0, 0.0)]
    goals = [(100.0, 0.0), (-100.0, 0.0)]
    dmin = 1e9
    for _ in range(600):
        nv = []
        for i in range(2):
            pref = preferred_velocity(p[i], goals[i], cfg)
            nv.append(avoid(p[i], v[i], pref, 30.0, [(p[1 - i], v[1 - i], 30.0)], cfg, 0.1))
        v = nv
        p = [(p[i][0] + v[i][0] * 0.1, p[i][1] + v[i][1] * 0.1) for i in range(2)]
        dmin = min(dmin, math.dist(p[0], p[1]))
    assert dmin >= 9.9
    assert math.dist(p[0], goals[0]) < 5


def test_circle_swap_twelve_agents():
    cfg = MotionCfg(layers=1, cruise_speed_mps=8.0)
    n, R = 12, 200.0
    pos = [(R * math.cos(2 * math.pi * i / n), R * math.sin(2 * math.pi * i / n)) for i in range(n)]
    goal = [(-x, -y) for x, y in pos]
    vel = [(0.0, 0.0)] * n
    dmin = 1e9
    for _ in range(1500):
        new = []
        for i in range(n):
            pref = preferred_velocity(pos[i], goal[i], cfg)
            nb = [(pos[j], vel[j], 30.0) for j in range(n) if j != i]
            new.append(avoid(pos[i], vel[i], pref, 30.0, nb, cfg, 0.1))
        vel = new
        pos = [(p[0] + v[0] * 0.1, p[1] + v[1] * 0.1) for p, v in zip(pos, vel)]
        for i in range(n):
            for j in range(i + 1, n):
                dmin = min(dmin, math.dist(pos[i], pos[j]))
    assert dmin >= 2 * cfg.safety_radius_m - 0.1
    assert max(math.dist(p, g) for p, g in zip(pos, goal)) < 5.0


def test_different_layers_do_not_interact():
    cfg = MotionCfg()
    pref = (8.0, 0.0)
    out = avoid((0, 0), (8, 0), pref, 30.0, [((10, 0), (-8, 0), 42.0)], cfg, 0.1)
    assert out == pref


def test_altitude_layers_distinct():
    cfg = MotionCfg()
    alts = {altitude_layer(i, cfg) for i in range(1, cfg.layers + 1)}
    assert len(alts) == cfg.layers


def test_accel_limit():
    v = limit_accel((0, 0), (10, 0), 3.0, 0.1)
    assert abs(v[0] - 0.3) < 1e-9
