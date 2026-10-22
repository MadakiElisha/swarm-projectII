"""Fleet + swarm configuration, loaded from ONE file: swarm_bringup/config/fleet.yaml.

Lookup order for the file:
  1. explicit path argument
  2. $SWARM_FLEET
  3. the installed swarm_bringup share directory (ROS)
  4. the source tree (ros2_ws/src/swarm_bringup/config/fleet.yaml)
"""
import os
from dataclasses import dataclass, field, fields, is_dataclass
from typing import List, Optional

import yaml

from .geo import Origin


@dataclass
class EnergyCfg:
    pct_per_m: float = 0.005
    pct_per_s_hover: float = 0.025
    pct_per_mps_wind_per_km: float = 0.3
    reserve_pct: float = 20.0
    critical_pct: float = 12.0


@dataclass
class CbbaCfg:
    max_bundle: int = 1
    discount_per_s: float = 0.995
    rebid_margin: float = 0.10
    hitl_required: bool = True


@dataclass
class MotionCfg:
    cruise_speed_mps: float = 10.0
    max_accel_mps2: float = 3.0
    base_alt_m: float = 30.0
    layer_spacing_m: float = 6.0
    layers: int = 5
    safety_radius_m: float = 6.0
    orca_horizon_s: float = 6.0
    arrive_radius_m: float = 15.0
    intercept_speed_mps: float = 14.0   # scramble / chase speed (autopilot WPNAV_SPEED must allow it)


@dataclass
class FormationCfg:
    max_slots: int = 5
    ring_radius_m: float = 300.0
    ring_period_s: float = 480.0
    on_station_band_m: float = 60.0
    hold_s: float = 180.0
    lead_time_s: float = 6.0
    intercept_radius_m: float = 80.0   # tight ring; slot 0 shadows the target overhead (camera on it)


@dataclass
class PerceptionCfg:
    hfov_deg: float = 78.0
    vfov_deg: float = 49.0
    gimbal_pitch_deg: float = -90.0
    fuse_radius_m: float = 25.0
    target_track_window_s: float = 8.0


@dataclass
class CoverageCfg:
    cell_m: float = 40.0
    search_alt_m: float = 70.0     # higher = wider camera footprint (layer offset added)


@dataclass
class GeofenceCfg:
    radius_m: float = 8000.0
    max_alt_m: float = 120.0


@dataclass
class SwarmCfg:
    origin: Origin = field(default_factory=lambda: Origin(6.5244, 3.3792))
    radio_range_m: float = 3500.0
    beacon_hz: float = 5.0
    state_hz: float = 1.0
    neighbor_timeout_s: float = 3.0
    isolation_rtb_s: float = 90.0
    energy: EnergyCfg = field(default_factory=EnergyCfg)
    cbba: CbbaCfg = field(default_factory=CbbaCfg)
    motion: MotionCfg = field(default_factory=MotionCfg)
    formation: FormationCfg = field(default_factory=FormationCfg)
    perception: PerceptionCfg = field(default_factory=PerceptionCfg)
    coverage: CoverageCfg = field(default_factory=CoverageCfg)
    geofence: GeofenceCfg = field(default_factory=GeofenceCfg)
    brain_stale_s: float = 1.5
    brain_dead_s: float = 10.0
    area_file: str = ""            # OSM-derived area (buildings) - enables path planning


@dataclass
class DroneSpec:
    id: int
    home_lat: float
    home_lon: float
    mavlink_url: str = ""

    @property
    def label(self) -> str:
        return f"D{self.id}"


@dataclass
class Fleet:
    swarm: SwarmCfg
    drones: List[DroneSpec]
    area: Optional[dict] = None    # loaded area (buildings/water), see swarm_common.area

    def by_id(self, drone_id: int) -> DroneSpec:
        for d in self.drones:
            if d.id == drone_id:
                return d
        raise KeyError(f"drone id {drone_id} not in fleet")

    def home_enu(self, drone_id: int):
        d = self.by_id(drone_id)
        return self.swarm.origin.to_enu(d.home_lat, d.home_lon)


def label_to_id(label: str) -> int:
    """'D7' -> 7. Raises ValueError on anything else."""
    if not label or label[0] not in "Dd" or not label[1:].isdigit():
        raise ValueError(f"bad drone label {label!r}")
    return int(label[1:])


def _fill(cls, data):
    """Recursively build a dataclass from a dict, ignoring unknown keys loudly."""
    if data is None:
        return cls()
    kwargs = {}
    known = {f.name: f for f in fields(cls)}
    for k, v in data.items():
        if k not in known:
            raise ValueError(f"unknown config key {cls.__name__}.{k}")
        sub = _SUBS.get((cls.__name__, k))
        if sub is Origin:
            kwargs[k] = Origin(**v)
        elif sub is not None and is_dataclass(sub):
            kwargs[k] = _fill(sub, v)
        else:
            kwargs[k] = v
    return cls(**kwargs)


_SUBS = {
    ("SwarmCfg", "origin"): Origin,
    ("SwarmCfg", "energy"): EnergyCfg,
    ("SwarmCfg", "cbba"): CbbaCfg,
    ("SwarmCfg", "motion"): MotionCfg,
    ("SwarmCfg", "formation"): FormationCfg,
    ("SwarmCfg", "perception"): PerceptionCfg,
    ("SwarmCfg", "coverage"): CoverageCfg,
    ("SwarmCfg", "geofence"): GeofenceCfg,
}


def find_fleet_file(path: Optional[str] = None) -> str:
    candidates = [path, os.environ.get("SWARM_FLEET")]
    try:  # installed ROS workspace
        from ament_index_python.packages import get_package_share_directory
        candidates.append(os.path.join(get_package_share_directory("swarm_bringup"),
                                       "config", "fleet.yaml"))
    except Exception:
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(here, "..", "..", "swarm_bringup", "config", "fleet.yaml"))
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    raise FileNotFoundError("fleet.yaml not found (set $SWARM_FLEET)")


def reference_fleet_file() -> str:
    """The repo's own fleet.yaml (what the simulator scenarios are written for), ignoring $SWARM_FLEET."""
    saved = os.environ.pop("SWARM_FLEET", None)
    try:
        return find_fleet_file(None)
    finally:
        if saved is not None:
            os.environ["SWARM_FLEET"] = saved


def load_fleet(path: Optional[str] = None) -> Fleet:
    fpath = find_fleet_file(path)
    with open(fpath) as f:
        raw = yaml.safe_load(f)
    fleet = fleet_from_dict(raw)
    af = fleet.swarm.area_file
    if af:
        candidates = [af, os.path.join(os.path.dirname(fpath), af),
                      os.path.join(os.path.dirname(fpath), "..", "..", "..", "..", af)]
        hit = next((c for c in candidates if os.path.isfile(c)), None)
        if hit is None:
            raise FileNotFoundError(f"area_file {af!r} not found (looked next to {fpath})")
        from .area import load_area
        fleet.area = load_area(hit)
    return fleet


def fleet_from_dict(raw: dict) -> Fleet:
    swarm = _fill(SwarmCfg, raw.get("swarm", {}))
    drones = [DroneSpec(**d) for d in raw.get("drones", [])]
    ids = [d.id for d in drones]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate drone ids in fleet: {ids}")
    if any(i <= 0 for i in ids):
        raise ValueError("drone ids must be positive integers")
    return Fleet(swarm=swarm, drones=sorted(drones, key=lambda d: d.id))


def synthetic_fleet(n: int, spacing_m: float = 150.0, swarm: Optional[SwarmCfg] = None) -> Fleet:
    """An n-drone fleet in a row along the east axis (for simulation/tests)."""
    swarm = swarm or SwarmCfg()
    drones = []
    for i in range(1, n + 1):
        lat, lon = swarm.origin.to_latlon((i - 1) * spacing_m, 0.0)
        drones.append(DroneSpec(id=i, home_lat=lat, home_lon=lon))
    return Fleet(swarm=swarm, drones=drones)
