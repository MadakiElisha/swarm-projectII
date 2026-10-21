"""Local motion: go-to-target + reciprocal collision avoidance + altitude layers.

Produces a velocity setpoint at ~10 Hz. Collision avoidance uses ONLY the
positions/velocities neighbours broadcast in their beacons.
"""
import math
from typing import Iterable, Optional, Tuple

from .config import MotionCfg
from .orca import Neighbor, orca_velocity

Vec = Tuple[float, float]
KEEP_RIGHT_RAD = math.radians(10.0)   # rule of the road: breaks symmetric deadlocks


def altitude_layer(drone_id: int, cfg: MotionCfg) -> float:
    return cfg.base_alt_m + cfg.layer_spacing_m * ((drone_id - 1) % max(1, cfg.layers))


def _rot(v: Vec, a: float) -> Vec:
    c, s = math.cos(a), math.sin(a)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])


def preferred_velocity(pos: Vec, target: Vec, cfg: MotionCfg, target_vel: Vec = (0.0, 0.0),
                       slow_radius_m: float = 40.0) -> Vec:
    """Head for target at cruise speed, slowing inside slow_radius, plus feed-forward."""
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return target_vel
    speed = cfg.cruise_speed_mps * min(1.0, d / slow_radius_m)
    vx, vy = dx / d * speed + target_vel[0], dy / d * speed + target_vel[1]
    # never exceed what the airframe can do
    vmax = cfg.cruise_speed_mps * 1.5
    n = math.hypot(vx, vy)
    if n > vmax:
        vx, vy = vx / n * vmax, vy / n * vmax
    return vx, vy


def avoid(pos: Vec, vel: Vec, pref: Vec, my_alt: float,
          neighbors: Iterable[Tuple[Vec, Vec, float]], cfg: MotionCfg, dt: float) -> Vec:
    """ORCA over neighbours that share (roughly) my altitude band.

    neighbors: iterable of ((x, y), (vx, vy), alt)
    """
    near = []
    for npos, nvel, nalt in neighbors:
        if abs(nalt - my_alt) >= cfg.layer_spacing_m * 0.9 and my_alt > 5 and nalt > 5:
            continue                       # different altitude layer: no conflict
        if math.hypot(npos[0] - pos[0], npos[1] - pos[1]) > 15 * cfg.cruise_speed_mps:
            continue
        near.append(Neighbor(npos, nvel, cfg.safety_radius_m))
    if not near:
        return pref
    biased = _rot(pref, -KEEP_RIGHT_RAD)
    return orca_velocity(pos, vel, cfg.safety_radius_m, biased, cfg.cruise_speed_mps * 1.5,
                         near, cfg.orca_horizon_s, dt)


def limit_accel(prev: Vec, new: Vec, max_accel: float, dt: float) -> Vec:
    dvx, dvy = new[0] - prev[0], new[1] - prev[1]
    dv = math.hypot(dvx, dvy)
    lim = max_accel * dt
    if dv <= lim or dv < 1e-9:
        return new
    return prev[0] + dvx / dv * lim, prev[1] + dvy / dv * lim


def arrived(pos: Vec, target: Optional[Vec], radius: float) -> bool:
    return target is not None and math.hypot(target[0] - pos[0], target[1] - pos[1]) <= radius
