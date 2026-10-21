"""ORCA - Optimal Reciprocal Collision Avoidance (2D, agent-agent).

Port of the agent part of RVO2 (van den Berg, Guy, Snape, Lin, Manocha,
"Reciprocal n-body Collision Avoidance", ISRR 2011). Each drone runs this
locally on its own preferred velocity using only neighbours' broadcast
positions/velocities; because every drone takes half the responsibility,
the swarm avoids collisions with no coordinator.
"""
import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

Vec = Tuple[float, float]
EPS = 1e-9


def _det(a: Vec, b: Vec) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1])


def _mul(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k)


def _norm(a: Vec) -> Vec:
    n = math.hypot(a[0], a[1])
    return (a[0] / n, a[1] / n) if n > EPS else (0.0, 0.0)


@dataclass
class Line:
    point: Vec
    direction: Vec


@dataclass
class Neighbor:
    pos: Vec
    vel: Vec
    radius: float
    cooperative: bool = True    # False -> we take full responsibility


def _lp1(lines: List[Line], no: int, radius: float, opt: Vec, dir_opt: bool):
    ln = lines[no]
    dot = _dot(ln.point, ln.direction)
    disc = dot * dot + radius * radius - _dot(ln.point, ln.point)
    if disc < 0.0:
        return None
    sq = math.sqrt(disc)
    t_left, t_right = -dot - sq, -dot + sq
    for i in range(no):
        den = _det(ln.direction, lines[i].direction)
        num = _det(lines[i].direction, _sub(ln.point, lines[i].point))
        if abs(den) <= EPS:
            if num < 0.0:
                return None
            continue
        t = num / den
        if den >= 0.0:
            t_right = min(t_right, t)
        else:
            t_left = max(t_left, t)
        if t_left > t_right:
            return None
    if dir_opt:
        t = t_right if _dot(opt, ln.direction) > 0.0 else t_left
    else:
        t = _dot(ln.direction, _sub(opt, ln.point))
        t = min(max(t, t_left), t_right)
    return _add(ln.point, _mul(ln.direction, t))


def _lp2(lines: List[Line], radius: float, opt: Vec, dir_opt: bool):
    if dir_opt:
        result = _mul(opt, radius)
    elif _dot(opt, opt) > radius * radius:
        result = _mul(_norm(opt), radius)
    else:
        result = opt
    for i, ln in enumerate(lines):
        if _det(ln.direction, _sub(ln.point, result)) > 0.0:
            r = _lp1(lines, i, radius, opt, dir_opt)
            if r is None:
                return i, result
            result = r
    return len(lines), result


def _lp3(lines: List[Line], begin: int, radius: float, result: Vec) -> Vec:
    distance = 0.0
    for i in range(begin, len(lines)):
        li = lines[i]
        if _det(li.direction, _sub(li.point, result)) > distance:
            proj: List[Line] = []
            for j in range(i):
                lj = lines[j]
                d = _det(li.direction, lj.direction)
                if abs(d) <= EPS:
                    if _dot(li.direction, lj.direction) > 0.0:
                        continue
                    point = _mul(_add(li.point, lj.point), 0.5)
                else:
                    point = _add(li.point, _mul(li.direction,
                                                _det(lj.direction, _sub(li.point, lj.point)) / d))
                proj.append(Line(point, _norm(_sub(lj.direction, li.direction))))
            n, r = _lp2(proj, radius, (-li.direction[1], li.direction[0]), True)
            if n >= len(proj):
                result = r
            distance = _det(li.direction, _sub(li.point, result))
    return result


def orca_velocity(pos: Vec, vel: Vec, radius: float, pref_vel: Vec, max_speed: float,
                  neighbors: Sequence[Neighbor], time_horizon: float, dt: float) -> Vec:
    """Collision-free velocity closest to pref_vel."""
    inv_th = 1.0 / time_horizon
    lines: List[Line] = []
    for nb in neighbors:
        rel_pos = _sub(nb.pos, pos)
        rel_vel = _sub(vel, nb.vel)
        dist_sq = _dot(rel_pos, rel_pos)
        r = radius + nb.radius
        r_sq = r * r
        if dist_sq > r_sq:
            w = _sub(rel_vel, _mul(rel_pos, inv_th))
            w_len_sq = _dot(w, w)
            dot1 = _dot(w, rel_pos)
            if dot1 < 0.0 and dot1 * dot1 > r_sq * w_len_sq:
                w_len = math.sqrt(w_len_sq)
                unit_w = _mul(w, 1.0 / w_len) if w_len > EPS else (1.0, 0.0)
                direction = (unit_w[1], -unit_w[0])
                u = _mul(unit_w, r * inv_th - w_len)
            else:
                leg = math.sqrt(dist_sq - r_sq)
                if _det(rel_pos, w) > 0.0:
                    direction = ((rel_pos[0] * leg - rel_pos[1] * r) / dist_sq,
                                 (rel_pos[0] * r + rel_pos[1] * leg) / dist_sq)
                else:
                    direction = (-(rel_pos[0] * leg + rel_pos[1] * r) / dist_sq,
                                 -(-rel_pos[0] * r + rel_pos[1] * leg) / dist_sq)
                dot2 = _dot(rel_vel, direction)
                u = _sub(_mul(direction, dot2), rel_vel)
        else:   # already overlapping: get out within one step
            inv_dt = 1.0 / dt
            w = _sub(rel_vel, _mul(rel_pos, inv_dt))
            w_len = math.hypot(*w)
            unit_w = _mul(w, 1.0 / w_len) if w_len > EPS else (1.0, 0.0)
            direction = (unit_w[1], -unit_w[0])
            u = _mul(unit_w, r * inv_dt - w_len)
        share = 0.5 if nb.cooperative else 1.0
        lines.append(Line(_add(vel, _mul(u, share)), direction))
    n, result = _lp2(lines, max_speed, pref_vel, False)
    if n < len(lines):
        result = _lp3(lines, n, max_speed, result)
    return result
