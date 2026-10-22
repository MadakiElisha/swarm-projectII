import json
import math
import os

from swarm_common.config import PerceptionCfg
from swarm_common.perception import project_bbox
from swarm_common.simcam import SimCamera, make_scene

AREA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "areas", "test-city",
                                   "area.json")))


def test_scene_points_are_on_open_ground():
    sc = make_scene(AREA, seed=3, people=8, cars=8, flood=True, radius=400)
    assert len(sc["people"]) == 8 and len(sc["cars"]) == 8 and len(sc["flood"]) == 2
    from swarm_common.area import point_in_poly
    for x, y in sc["people"] + sc["cars"]:
        assert not any(point_in_poly(x, y, b["poly"]) for b in AREA["buildings"])


def test_detections_project_back_onto_the_object():
    cfg = PerceptionCfg()
    sc = {"people": [], "cars": [(20.0, 10.0)], "flood": []}
    cam = SimCamera(cfg, sc, seed=1, false_pos_rate=0.0)
    hits = []
    for _ in range(50):
        for d in cam.detect(0.0, 0.0, 40.0, 0.02, -0.03, 1.0):
            g = project_bbox(d["u0"] + d["w"] / 2, d["v0"] + d["h"] / 2, 0.0, 0.0, 40.0, 0.02, -0.03, 1.0, cfg)
            hits.append(math.hypot(g[0] - 20, g[1] - 10))
    assert len(hits) > 35 and max(hits) < 3.0


def test_small_people_from_high_up_are_often_missed():
    cfg = PerceptionCfg()
    sc = {"people": [(0.0, 0.0)], "cars": [], "flood": []}
    low = SimCamera(cfg, sc, seed=2, false_pos_rate=0.0)
    high = SimCamera(cfg, sc, seed=2, false_pos_rate=0.0)
    n_low = sum(len(low.detect(1, 1, 30, 0, 0, 0)) for _ in range(200))
    n_high = sum(len(high.detect(1, 1, 110, 0, 0, 0)) for _ in range(200))
    assert n_low > 120 and n_high < n_low / 2


def test_water_cells_reported_over_flood():
    cfg = PerceptionCfg()
    sc = {"people": [], "cars": [], "flood": [[[-500, -500], [500, -500], [500, 500], [-500, 500]]]}
    d = SimCamera(cfg, sc, seed=0, false_pos_rate=0.0).detect(0, 0, 50, 0, 0, 0)
    assert sum(1 for x in d if x["class"] == "water") == 40
