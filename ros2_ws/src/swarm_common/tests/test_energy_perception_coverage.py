import math

from swarm_common.config import EnergyCfg, PerceptionCfg
from swarm_common.coverage import CoverageGrid, partition
from swarm_common.energy import DrainCalibrator, EnergyModel
from swarm_common.perception import Observation, WorldModel, project_bbox


def test_energy_one_model_for_bid_and_relinquish():
    e = EnergyModel(EnergyCfg())
    cost = e.plan_pct((0, 0), [((1000, 0), 60.0)], (0, 0))
    assert abs(cost - (2000 * 0.005 + 60 * 0.025)) < 1e-9
    # a drone that may bid on a plan is, at that moment, not forced to give it up
    batt = e.cfg.reserve_pct + cost + 0.1
    assert e.feasible(batt, cost) and not e.must_go_home(batt, (0, 0), (0, 0))


def test_nadir_centre_projects_straight_down():
    cfg = PerceptionCfg()
    gx, gy = project_bbox(0.5, 0.5, 100, 200, 50.0, 0.0, 0.0, 0.3, cfg)
    assert abs(gx - 100) < 1e-6 and abs(gy - 200) < 1e-6


def test_image_right_edge_is_right_of_heading():
    cfg = PerceptionCfg()
    gx, gy = project_bbox(1.0, 0.5, 0, 0, 50.0, 0.0, 0.0, 0.0, cfg)   # facing east
    assert gy < -30 and abs(gx) < 1e-6                                  # right of east = south
    expect = 50.0 * math.tan(math.radians(cfg.hfov_deg / 2))
    assert abs(-gy - expect) < 1e-6


def test_forward_tilted_camera_and_sky_rays():
    cfg = PerceptionCfg(gimbal_pitch_deg=-30.0)
    gx, gy = project_bbox(0.5, 0.5, 0, 0, 30.0, 0, 0, math.pi / 2, cfg)  # facing north
    assert gy > 0 and abs(gy - 30.0 / math.tan(math.radians(30))) < 1e-6
    assert project_bbox(0.5, 0.0, 0, 0, 30.0, 0, 0, 0,
                        PerceptionCfg(gimbal_pitch_deg=0.0)) is None


def test_fusion_dedups_across_observers():
    w = WorldModel(PerceptionCfg())
    for k, (obs, dx) in enumerate([(1, 0), (2, 3), (3, -4), (1, 2)]):
        w.add(Observation(f"{obs}-{k}", "person", 500 + dx, 500 - dx, 0.8, float(k), obs))
    w.add(Observation("4-9", "person", 900, 900, 0.8, 1.0, 4))
    tracks = w.static_tracks("person")
    assert len(tracks) == 2 and tracks[0].tid == "1-0"


def test_moving_track_fit():
    w = WorldModel(PerceptionCfg())
    for k in range(6):
        w.add(Observation(f"{k % 3}-{k}", "target", 3.0 * k, 1.0 * k, 0.9, float(k), k % 3))
    tr = w.moving_track("target", 6.0)
    assert abs(tr.vx - 3.0) < 1e-6 and abs(tr.vy - 1.0) < 1e-6 and abs(tr.x - 18.0) < 1e-6


def test_coverage_gset_merge_and_partition():
    a = CoverageGrid(0, 0, 400, 400, 40)
    b = CoverageGrid(0, 0, 400, 400, 40)
    a.mark_footprint(100, 100, 50)
    b.mark_footprint(300, 300, 50)
    a.merge(b.to_wire())
    b.merge(a.to_wire())
    assert a.covered == b.covered and a.to_wire() == b.to_wire()
    p1 = partition(a, [3, 1, 2])
    p2 = partition(b, [2, 3, 1])
    assert p1 == p2
    cells = [c for share in p1.values() for c in share]
    assert len(cells) == len(set(cells)) == len(a.remaining())


def test_drain_calibration_learns_real_consumption():
    e = EnergyModel(EnergyCfg())
    c = DrainCalibrator(e)
    t = 0.0
    true_rate = 4.0 * e.raw_rate_pct_s(10.0)          # battery is 4x worse than modelled
    exact = 90.0
    for _ in range(3000):
        t += 0.1
        exact -= true_rate * 0.1
        c.update(t, float(int(exact)), 10.0, True)    # autopilots report whole percent
    assert 3.5 <= e.scale <= 4.5
    before = e.scale
    c.update(t + 1, 95.0, 10.0, True)                # battery swap: no bogus sample
    assert e.scale == before


def test_calibration_tightens_feasibility():
    e = EnergyModel(EnergyCfg())
    cost_before = e.plan_pct((0, 0), [((2000, 0), 120.0)], (0, 0))
    e.scale = 4.0
    assert abs(e.plan_pct((0, 0), [((2000, 0), 120.0)], (0, 0)) - 4 * cost_before) < 1e-9
