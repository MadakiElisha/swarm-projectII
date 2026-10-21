import json

from swarm_common.config import load_fleet
from swarm_common.sim.core import SwarmSim
from swarm_common.sim.recorder import Recorder, fleet_json


def test_recording_has_everything_the_gcs_draws(tmp_path):
    sim = SwarmSim(load_fleet(), seed=1)
    rec = Recorder(sim)
    sim.at(2, lambda s: s.operator_task("SWARM-1", 1200, 1300, to={1}))
    sim.run(80)
    out = tmp_path / "rec.json"
    rec.save(str(out))
    data = json.loads(out.read_text())
    kinds = {r[1] for r in data["rows"]}
    assert {"v", "b", "T", "p", "a"} <= kinds
    assert [r[0] for r in data["rows"]] == sorted(r[0] for r in data["rows"])
    brains = [r[2] for r in data["rows"] if r[1] == "b"]
    assert any(any(k.startswith("SWARM-1/") for k in b["z"]) for b in brains)   # consensus tables
    assert data["meta"]["drones"] and data["meta"]["cfg"]["formation"]["ring_radius_m"] > 0


def test_fleet_json_matches_fleet():
    f = load_fleet()
    j = fleet_json(f)
    assert [d["id"] for d in j["drones"]] == [d.id for d in f.drones]
