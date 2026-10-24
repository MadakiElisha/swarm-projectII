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


def world_to_image(gx: float, gy: float, x: float, y: float, alt_agl: float,
                   roll: float, pitch: float, yaw_enu: float, cfg: PerceptionCfg,
                   gz: float = 0.0) -> Optional[Tuple[float, float]]:
    """Inverse of project_bbox: where a ground point appears in the image (u, v in [0, 1]),
    or None if it is behind the camera. Used by the simulated camera."""
    rw = [gx - x, gy - y, gz - alt_agl]
    R = _rot_zyx(roll, pitch, yaw_enu)
    rb = [sum(R[r][c] * rw[r] for r in range(3)) for c in range(3)]        # R^T rw
    gp = math.radians(-cfg.gimbal_pitch_deg)
    cg, sg = math.cos(gp), math.sin(gp)
    rc = [cg * rb[0] - sg * rb[2], rb[1], sg * rb[0] + cg * rb[2]]          # undo the gimbal
    if rc[0] <= 1e-6:
        return None
    ax, ay = -rc[1] / rc[0], -rc[2] / rc[0]
    u = (ax / math.tan(math.radians(cfg.hfov_deg) / 2) + 1) / 2
    v = (ay / math.tan(math.radians(cfg.vfov_deg) / 2) + 1) / 2
    return u, v


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

    MOVING = ("target", "vehicle")
    VEHICLE_KEEP_S = 60.0          # long enough to learn which cars are parked

    def _keep_for(self, o: Observation) -> float:
        # moving things only matter for a short while; people/survivors persist
        if o.cls == "target":
            return 2 * self.cfg.target_track_window_s
        if o.cls == "vehicle":
            return self.VEHICLE_KEEP_S
        return self.keep_s

    def prune(self, now: float):
        stale = [k for k, o in self.obs.items() if now - o.t > self._keep_for(o)]
        for k in stale:
            del self.obs[k]
        if stale:
            self.version += 1

    def recent_wire(self, now: float, window_s: float) -> List[dict]:
        out = []
        for o in self.obs.values():
            w = min(window_s, self.cfg.target_track_window_s) if o.cls in self.MOVING else window_s
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

    def moving_track(self, cls, now: float, prior: Optional[Track] = None,
                     gate_m: float = 60.0) -> Optional[Track]:
        """Constant-velocity least-squares fit over the recent window.

        cls: a class name or a set of them. With a prior (the track so far) only
        sightings near where the target SHOULD be are used (gated nearest-neighbour
        association), so parked cars and other vehicles don't pull the track.
        """
        classes = {cls} if isinstance(cls, str) else set(cls)
        win = [o for o in self.obs.values()
               if o.cls in classes and now - o.t <= self.cfg.target_track_window_s]
        if prior is not None:
            gated = []
            for o in win:
                dt = o.t - prior.t
                px, py = prior.x + prior.vx * dt, prior.y + prior.vy * dt
                if prior.n:
                    g = gate_m + 2.0 * abs(dt)              # tracking: uncertainty grows with time
                else:
                    g = min(1500.0, gate_m + 25.0 * abs(dt))  # acquiring: it may have driven off
                if math.hypot(o.x - px, o.y - py) <= g:
                    gated.append(o)
            win = gated
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


# ---------------------------------------------------------------- pursuit tracker
class _AB:
    """Alpha-beta (constant velocity) filter on the ground plane."""
    __slots__ = ("x", "y", "vx", "vy", "t", "hits", "t0", "x0", "y0", "path", "hist")
    HIST_S = 15.0

    def __init__(self, o: Observation):
        self.x, self.y, self.vx, self.vy, self.t = o.x, o.y, o.vx, o.vy, o.t
        self.hits, self.t0, self.x0, self.y0 = 1, o.t, o.x, o.y
        self.path = 0.0                     # distance travelled (filtered)
        self.hist = [(o.t, o.x, o.y)]       # recent associated sightings

    def predict(self, t: float) -> Tuple[float, float]:
        dt = t - self.t
        return self.x + self.vx * dt, self.y + self.vy * dt

    def update(self, o: Observation, alpha: float, beta: float):
        dt = o.t - self.t
        px, py = self.predict(o.t)
        rx, ry = o.x - px, o.y - py
        nx, ny = px + alpha * rx, py + alpha * ry
        if dt > 1e-3:
            k = beta / max(dt, 0.5)
            self.vx += k * rx
            self.vy += k * ry
        if o.vx or o.vy:                    # detector gave a velocity: trust it partly
            self.vx = 0.5 * self.vx + 0.5 * o.vx
            self.vy = 0.5 * self.vy + 0.5 * o.vy
        self.path += math.hypot(nx - self.x, ny - self.y)
        self.x, self.y = nx, ny
        self.t = max(self.t, o.t)
        self.hits += 1
        self.hist.append((o.t, o.x, o.y))
        self.hist = [h for h in self.hist if self.t - h[0] <= self.HIST_S]
        if not (o.vx or o.vy):
            self._fit_velocity()

    def _fit_velocity(self):
        """Least-squares velocity over the recent sightings: far less noisy than beta alone."""
        h = self.hist
        if len(h) < 5:
            return
        tm = sum(a[0] for a in h) / len(h)
        var = sum((a[0] - tm) ** 2 for a in h)
        if var < 4.0:
            return
        xm = sum(a[1] for a in h) / len(h)
        ym = sum(a[2] for a in h) / len(h)
        self.vx = sum((a[0] - tm) * (a[1] - xm) for a in h) / var
        self.vy = sum((a[0] - tm) * (a[2] - ym) for a in h) / var

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def displacement(self) -> float:
        return math.hypot(self.x - self.x0, self.y - self.y0)


class TargetTracker:
    """Follows ONE moving vehicle among many look-alikes.

    A real detector only says "vehicle" - for the quarry and for every parked
    car around it. Before lock we track every vehicle we see (nearest-neighbour
    alpha-beta tracks) and lock on to the one that (a) actually moves and
    (b) started near where the operator pointed. After lock, only sightings
    inside a gate around the predicted position update it, so parked cars and
    other traffic can't pull it away. If nothing moving ever shows up, the
    stationary vehicle nearest the click is taken (the operator may have
    pointed at a parked car). Deterministic given the same observation set,
    so every drone running it on gossiped observations converges on the same
    target.
    """
    def __init__(self, x: float, y: float, t: float, classes=("target", "vehicle"),
                 gate_m: float = 25.0, alpha: float = 0.5, beta: float = 0.2,
                 acquire_speed: float = 10.0, coast_s: float = 12.0):
        self.cx, self.cy, self.ct = x, y, t
        self.hint_v = (0.0, 0.0)                 # last known velocity (after a loss): where to look
        self.coast_s = coast_s
        self.classes = set(classes)
        self.gate_m, self.alpha, self.beta = gate_m, alpha, beta
        self.acquire_speed = acquire_speed       # how far the target may have driven since the click
        self.cands: List[_AB] = []
        self.locked: Optional[_AB] = None
        self._seen: Dict[str, float] = {}

    def _gate(self, trk: _AB, t: float) -> float:
        return min(150.0, self.gate_m + 3.0 * max(0.0, t - trk.t))

    def _assoc(self, o: Observation, tracks: List[_AB]) -> Optional[_AB]:
        best, bd = None, 1e18
        for trk in tracks:
            px, py = trk.predict(o.t)
            d = math.hypot(o.x - px, o.y - py)
            if d <= self._gate(trk, o.t) and d < bd:
                best, bd = trk, d
        return best

    def _start_ok(self, trk: _AB) -> bool:
        r = 60.0 + self.acquire_speed * max(0.0, trk.t0 - self.ct)
        # project the track back to the click time: a car that drove away from
        # the click point is still "the one the operator meant"
        bx = trk.x - trk.vx * (trk.t - self.ct)
        by = trk.y - trk.vy * (trk.t - self.ct)
        return (math.hypot(trk.x0 - self.cx, trk.y0 - self.cy) <= r
                or math.hypot(bx - self.cx, by - self.cy) <= 80.0)

    def _moving(self, trk: _AB) -> bool:
        return trk.hits >= 4 and trk.t - trk.t0 >= 4.0 and trk.speed >= 1.0 and trk.displacement >= 10.0

    def _static(self, c: _AB) -> bool:
        return c.hits >= 4 and c.t - c.t0 >= 6.0 and c.displacement < 6.0

    def look_candidates(self, now: float) -> List[Tuple[float, float]]:
        """Vehicles seen recently in the area the target can have reached that are not yet
        known to be parked: worth a closer look (a drone flies over to confirm)."""
        out = []
        for c in sorted(self.cands, key=lambda c: (-c.t, c.t0)):
            if now - c.t <= 10.0 and not self._static(c) and self._start_ok(c):
                out.append(c.predict(now))
        return out

    def search_area(self, now: float) -> Tuple[float, float, float, Tuple[float, float]]:
        """(x, y, radius, hint velocity): where the target can be, while we have no lock.
        With a known heading (operator input, or the track we just lost) the area is a
        blob moving along it; without, a circle growing around the last fix."""
        dt = max(0.0, now - self.ct)
        hx, hy = self.hint_v
        if hx or hy:
            # dead-reckon along the heading for up to 90 s (it may turn, stop or hit a dead end);
            # the area keeps growing, and after 40 s the drones fan out all around it
            dh = min(dt, 90.0)
            r = 40.0 + 0.4 * math.hypot(hx, hy) * dt
            hint = self.hint_v if dt <= 40.0 else (0.0, 0.0)
            return self.cx + hx * dh, self.cy + hy * dh, min(1200.0, r), hint
        return self.cx, self.cy, min(1200.0, 40.0 + self.acquire_speed * dt * 0.8), self.hint_v

    def update(self, observations, now: float) -> Optional[Track]:
        new = [o for o in observations
               if o.cls in self.classes and o.oid not in self._seen and o.t >= self.ct - 1.0]
        new.sort(key=lambda o: (o.t, o.oid))
        for o in new:
            self._seen[o.oid] = o.t
            # global nearest neighbour: every sighting goes to the closest track, so a
            # parked car's sightings feed ITS track, not the target's, even side by side
            pool = self.cands + ([self.locked] if self.locked is not None else [])
            trk = self._assoc(o, pool)
            if trk is None:
                self.cands.append(_AB(o))
            else:
                trk.update(o, self.alpha, self.beta)
        if len(self._seen) > 5000:                       # bounded memory
            cut = now - 120.0
            self._seen = {k: t for k, t in self._seen.items() if t >= cut}
        if self.locked is None:
            self.cands = [c for c in self.cands if now - c.t <= 30.0]
            movers = [c for c in self.cands if self._moving(c) and self._start_ok(c)]
            if movers:
                self.locked = min(movers, key=lambda c: (math.hypot(c.x0 - self.cx, c.y0 - self.cy), c.t0))
            elif now - self.ct > 180.0 and not any(self._moving(c) for c in self.cands):
                still = [c for c in self.cands if c.hits >= 3
                         and math.hypot(c.x - self.cx, c.y - self.cy) <= 60.0]
                if still:
                    self.locked = min(still, key=lambda c: math.hypot(c.x - self.cx, c.y - self.cy))
            if self.locked is not None:
                self.cands = [c for c in self.cands if c is not self.locked]
        else:
            self.cands = [c for c in self.cands if now - c.t <= 30.0]
        trk = self.locked
        if trk is None or now - trk.t > self.coast_s:    # never acquired, or lost for too long
            if trk is not None:                          # lost: re-acquire around the last estimate
                self.cx, self.cy = trk.predict(now)
                self.hint_v = (trk.vx, trk.vy)
                self.ct, self.locked = now, None
                self.cands.append(trk)                   # it may well be seen again
            return None
        x, y = trk.predict(now)
        return Track("tracked", "vehicle", x, y, trk.vx, trk.vy, now, trk.hits)


GATE_MAX_M = 45.0          # MotionWatch association gate cap
UNCONFIRMED_S = 8.0        # an unconfirmed MotionWatch track dies after this long unseen
MIN_HIT_RATE = 0.3         # sightings per second: a car under a camera is seen often, false hits rarely
MIN_PROGRESS_M = 5.0       # a mover's later sightings are this far on from its earlier ones
LINE_RMS_M = 10.0          # sightings of a real mover lie on a line (constant velocity) to within this


def _straight(hist) -> bool:
    """Do these (t, x, y) sightings fit constant-velocity motion? A real car's do (to a few metres
    of detection noise); false detections strung together by the gate don't."""
    n = len(hist)
    if n < 4:
        return False
    tm = sum(h[0] for h in hist) / n
    var = sum((h[0] - tm) ** 2 for h in hist)
    if var < 1e-6:
        return False
    err = 0.0
    for k in (1, 2):
        m = sum(h[k] for h in hist) / n
        b = sum((h[0] - tm) * (h[k] - m) for h in hist) / var
        err += sum((h[k] - (m + b * (h[0] - tm))) ** 2 for h in hist)
    return math.sqrt(err / n) <= LINE_RMS_M


def _kind(cls: str) -> str:
    return "person" if cls in ("person", "pedestrian", "people") else "vehicle"


def _progress(hist) -> bool:
    """Has it actually gone somewhere? The later half of the sightings must sit clearly away
    from the earlier half. Two parked things a few metres apart, seen in turn, make a track
    that jitters back and forth (straight, even) but whose halves overlap."""
    h = sorted(hist)
    n = len(h) // 2
    if n < 2:
        return False
    a, b = h[:n], h[-n:]
    ax, ay = sum(p[1] for p in a) / n, sum(p[2] for p in a) / n
    bx, by = sum(p[1] for p in b) / n, sum(p[2] for p in b) / n
    return math.hypot(bx - ax, by - ay) >= MIN_PROGRESS_M


class MotionWatch:
    """Perimeter surveillance: which detected things are MOVING inside an area.

    Tracks every person/vehicle sighting inside the watched circle with small
    alpha-beta tracks; parked cars and standing guards stay put and are never
    reported. A track is reported once, when it is confirmed moving.
    """
    def __init__(self, cx: float, cy: float, radius_m: float, t0: float,
                 classes=("person", "vehicle", "target"), gate_m: float = 25.0):
        self.cx, self.cy, self.r, self.t0 = cx, cy, radius_m, t0
        self.classes = set(classes)
        self.gate_m = gate_m
        self.tracks: List[Tuple[str, _AB]] = []      # (first oid, track)
        self.kind: Dict[str, str] = {}                # track -> "person" / "vehicle"
        self.reported: set = set()
        self._seen: Dict[str, float] = {}

    def update(self, observations, now: float) -> List[Tuple[str, Track]]:
        new = [o for o in observations if o.cls in self.classes and o.oid not in self._seen
               and o.t >= self.t0 and math.hypot(o.x - self.cx, o.y - self.cy) <= self.r]
        new.sort(key=lambda o: (o.t, o.oid))
        for o in new:
            self._seen[o.oid] = o.t
            best, bd = None, 1e18
            grp = _kind(o.cls)
            for k, trk in self.tracks:
                if self.kind.get(k) != grp:      # a person never continues a car's track, nor vice versa
                    continue
                px, py = trk.predict(o.t)
                d = math.hypot(o.x - px, o.y - py)
                # a small gate: a wide one lets scattered false detections chain into a "mover"
                if d <= min(GATE_MAX_M, self.gate_m + 3.0 * max(0.0, o.t - trk.t)) and d < bd:
                    best, bd = trk, d
            if best is None:
                self.tracks.append((o.oid, _AB(o)))
                self.kind[o.oid] = grp
            else:
                best.update(o, 0.5, 0.2)
        if len(self._seen) > 20000:
            self._seen = {k: t for k, t in self._seen.items() if t >= now - 120.0}
        # unconfirmed tracks die quickly without sightings; reported ones linger so their
        # sightings don't start new tracks (and raise the same intruder again)
        self.tracks = [(k, trk) for k, trk in self.tracks
                       if now - trk.t <= (60.0 if k in self.reported else UNCONFIRMED_S)]
        live = {k for k, _ in self.tracks}
        self.kind = {k: g for k, g in self.kind.items() if k in live}
        out = []
        for k, trk in self.tracks:
            if k in self.reported:
                continue
            life = trk.t - trk.t0
            if trk.hits >= 6 and life >= 4.0 and trk.hits / life >= MIN_HIT_RATE \
                    and trk.speed >= 0.8 and trk.displacement >= 8.0 and _straight(trk.hist) \
                    and _progress(trk.hist):
                self.reported.add(k)
                x, y = trk.predict(now)
                out.append((k, Track(k, "intruder", x, y, trk.vx, trk.vy, now, trk.hits)))
        return out
