"""Perception geometry and the shared world model.

* project_bbox: bounding-box centre in the image -> point on the ground,
  using the camera model, gimbal, vehicle attitude and altitude. Replaces
  the old "task = wherever the spotting drone happens to be".
* WorldModel: observations from every drone (relayed by gossip) are fused
  locally. Every drone runs the same deterministic fusion on the same
  observation set, so they agree on which survivors exist and where.
* Target tracks: a constant-velocity least-squares fit over recent
  observations from any number of drones, used to steer intercept rings.
"""
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

from .config import PerceptionCfg


def footprint_radius(alt_agl: float, cfg: PerceptionCfg) -> float:
    """Radius of a circle approximating a nadir camera's ground footprint."""
    half = math.radians(cfg.hfov_deg + cfg.vfov_deg) / 4.0
    return max(0.0, alt_agl) * math.tan(half)


def _rot_zyx(roll, pitch, yaw):
    """Body->world (ENU) rotation matrix for yaw (CCW from east), pitch, roll."""
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]


def _mv(m, v):
    return [sum(m[r][c] * v[c] for c in range(3)) for r in range(3)]


def project_bbox(u: float, v: float, x: float, y: float, alt_agl: float,
                 roll: float, pitch: float, yaw_enu: float, cfg: PerceptionCfg
                 ) -> Optional[Tuple[float, float]]:
    """Ground point (ENU) seen at normalised image coords (u, v) in [0, 1].

    Camera convention: optical axis = body +x when gimbal pitch is 0, image
    right = body -y, image down = body -z. The gimbal pitches the camera
    down by -gimbal_pitch_deg (-90 = nadir). yaw_enu is CCW from east.
    Returns None if the ray never hits the ground (points at the sky).
    """
    if alt_agl <= 0.5:
        return None
    ax = math.tan(math.radians(cfg.hfov_deg) / 2) * (2 * u - 1)    # right
    ay = math.tan(math.radians(cfg.vfov_deg) / 2) * (2 * v - 1)    # down
    ray_cam = [1.0, -ax, -ay]                                      # in body axes, gimbal level
    gp = math.radians(-cfg.gimbal_pitch_deg)                        # positive = look down
    cg, sg = math.cos(gp), math.sin(gp)
    # pitch the camera down about body y (nose-down rotation)
    rb = [cg * ray_cam[0] + sg * ray_cam[2], ray_cam[1], -sg * ray_cam[0] + cg * ray_cam[2]]
    rw = _mv(_rot_zyx(roll, pitch, yaw_enu), rb)
    if rw[2] >= -1e-6:
        return None
    t = alt_agl / -rw[2]
    return x + rw[0] * t, y + rw[1] * t


@dataclass
class Observation:
    oid: str            # "<observer>-<seq>", globally unique
    cls: str
    x: float
    y: float
    conf: float
    t: float
    observer: int
    vx: float = 0.0     # optional velocity estimate (moving targets)
    vy: float = 0.0

    def to_wire(self):
        return asdict(self)


@dataclass
class Track:
    tid: str            # oid of the oldest observation in the cluster (deterministic)
    cls: str
    x: float
    y: float
    vx: float
    vy: float
    t: float
    n: int


class WorldModel:
    def __init__(self, cfg: PerceptionCfg, keep_s: float = 600.0):
        self.cfg = cfg
        self.keep_s = keep_s
        self.obs: Dict[str, Observation] = {}
        self.version = 0
        self._static_cache: Dict[str, Tuple[int, List["Track"]]] = {}

    def add(self, o: Observation) -> bool:
        if o.oid in self.obs:
            return False
        self.obs[o.oid] = o
        self.version += 1
        return True

    def merge(self, wire: List[dict]) -> bool:
        changed = False
        for d in wire:
            try:
                changed |= self.add(Observation(**d))
            except TypeError:
                continue
        return changed

    def _keep_for(self, o: Observation) -> float:
        # moving targets only matter inside the tracking window; static objects persist
        return 2 * self.cfg.target_track_window_s if o.cls == "target" else self.keep_s

    def prune(self, now: float):
        stale = [k for k, o in self.obs.items() if now - o.t > self._keep_for(o)]
        for k in stale:
            del self.obs[k]
        if stale:
            self.version += 1

    def recent_wire(self, now: float, window_s: float) -> List[dict]:
        out = []
        for o in self.obs.values():
            w = min(window_s, self.cfg.target_track_window_s) if o.cls == "target" else window_s
            if now - o.t <= w:
                out.append(o.to_wire())
        return out

    def static_tracks(self, cls: str) -> List[Track]:
        """Greedy deterministic clustering of static objects (e.g. people).

        Observations are processed oldest-first and joined to the nearest
        cluster centroid within fuse_radius_m. Result is cached until the
        observation set changes.
        """
        hit = self._static_cache.get(cls)
        if hit is not None and hit[0] == self.version:
            return hit[1]
        pts = sorted((o for o in self.obs.values() if o.cls == cls), key=lambda o: (o.t, o.oid))
        # cluster: [first_oid, sum_x, sum_y, n, sum_wx, sum_wy, sum_w, t_last]
        clusters: List[list] = []
        for o in pts:
            best, bd = None, self.cfg.fuse_radius_m
            for c in clusters:
                d = math.hypot(o.x - c[1] / c[3], o.y - c[2] / c[3])
                if d <= bd:
                    best, bd = c, d
            if best is None:
                clusters.append([o.oid, o.x, o.y, 1, o.x * o.conf, o.y * o.conf, o.conf, o.t])
            else:
                best[1] += o.x
                best[2] += o.y
                best[3] += 1
                best[4] += o.x * o.conf
                best[5] += o.y * o.conf
                best[6] += o.conf
                best[7] = max(best[7], o.t)
        out = [Track(c[0], cls, c[4] / (c[6] or 1.0), c[5] / (c[6] or 1.0), 0.0, 0.0, c[7], c[3])
               for c in clusters]
        self._static_cache[cls] = (self.version, out)
        return out

    def moving_track(self, cls: str, now: float) -> Optional[Track]:
        """Constant-velocity least-squares fit over the recent window."""
        win = [o for o in self.obs.values()
               if o.cls == cls and now - o.t <= self.cfg.target_track_window_s]
        if not win:
            return None
        win.sort(key=lambda o: (o.t, o.oid))
        if len(win) == 1:
            o = win[0]
            return Track(o.oid, cls, o.x + o.vx * (now - o.t), o.y + o.vy * (now - o.t),
                         o.vx, o.vy, o.t, 1)
        t0 = win[0].t
        ts = [o.t - t0 for o in win]
        tm = sum(ts) / len(ts)
        var = sum((t - tm) ** 2 for t in ts)
        xm = sum(o.x for o in win) / len(win)
        ym = sum(o.y for o in win) / len(win)
        if var < 1e-6:
            vx = sum(o.vx for o in win) / len(win)
            vy = sum(o.vy for o in win) / len(win)
        else:
            vx = sum((t - tm) * (o.x - xm) for t, o in zip(ts, win)) / var
            vy = sum((t - tm) * (o.y - ym) for t, o in zip(ts, win)) / var
        dt = (now - t0) - tm
        return Track(win[0].oid, cls, xm + vx * dt, ym + vy * dt, vx, vy, win[-1].t, len(win))
