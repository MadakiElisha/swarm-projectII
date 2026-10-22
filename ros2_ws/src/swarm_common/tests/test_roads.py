import math

from swarm_common.roads import RoadGraph, along

GRID = [{"line": [[x, -300], [x, 300]]} for x in (-300, 0, 300)] + \
       [{"line": [[-300, y], [0, y], [300, y]]} for y in (-300, 0, 300)]


def _grid():
    # vertical streets need the crossing points as vertices too (OSM ways share junction nodes)
    roads = [{"line": [[x, -300], [x, 0], [x, 300]]} for x in (-300, 0, 300)] + GRID[3:]
    return RoadGraph(roads)


def test_junctions_are_shared():
    g = _grid()
    assert len(g.nodes) == 9
    centre = g.nearest((1, 1))
    assert len(g.adj[centre]) == 4


def test_drive_stays_on_streets():
    g = _grid()
    p = g.drive((10, 10), 1500)
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]))
    assert total >= 1500
    assert all(pt in g.nodes for pt in p)


def test_shortest_and_along():
    g = _grid()
    p = g.shortest((-300, -300), (300, 300))
    assert p[0] == (-300.0, -300.0) and p[-1] == (300.0, 300.0) and len(p) == 5
    (x, y), h = along([(0, 0), (100, 0), (100, 100)], 150)
    assert (x, y) == (100, 50) and abs(h - math.pi / 2) < 1e-9
