"""VehicleAdapter: the vendor-agnostic contract between the swarm and an airframe.

Only vehicle_manager talks to an adapter. A DJI/Skydio/Parrot SDK backend
implements this same interface and nothing above it changes.

Conventions: lat/lon degrees, altitude metres above home, velocities NED
(north/east/down) m/s, attitude radians in the autopilot's own (NED/FRD)
convention. vehicle_manager converts to the swarm's ENU frame.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class VehicleType(Enum):
    MULTICOPTER = "multicopter"
    FIXED_WING = "fixed_wing"
    VTOL = "vtol"
    ROVER = "rover"


@dataclass
class Capabilities:
    vehicle_type: VehicleType = VehicleType.MULTICOPTER
    can_velocity: bool = True
    can_goto: bool = True
    can_rtl: bool = True
    can_land: bool = True
    max_altitude_m: float = 120.0


@dataclass
class VehicleSnapshot:
    t: float = 0.0
    connected: bool = False
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0              # relative to home
    vn: float = 0.0
    ve: float = 0.0
    vd: float = 0.0
    battery_pct: float = -1.0     # -1 = unknown
    armed: bool = False
    mode: str = "UNKNOWN"         # normalised, see NORMALISED_MODES
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0              # NED heading, radians clockwise from north
    wind_speed: float = 0.0
    wind_dir: float = 0.0
    home_lat: Optional[float] = None
    home_lon: Optional[float] = None


NORMALISED_MODES = ("GUIDED", "RTL", "LAND", "HOLD", "TAKEOFF", "STABILIZE", "AUTO", "OTHER")


@dataclass
class CommandStatus:
    accepted: bool
    reason: str = ""

    @staticmethod
    def ok() -> "CommandStatus":
        return CommandStatus(True)

    @staticmethod
    def denied(reason: str) -> "CommandStatus":
        return CommandStatus(False, reason)


# Kept for backwards compatibility with code that built generic requests.
@dataclass
class CommandRequest:
    command: str
    params: dict = None

    def __post_init__(self):
        self.params = self.params or {}


# Kept for backwards compatibility (old name for a telemetry sample).
TelemetryFrame = VehicleSnapshot


class VehicleAdapter(ABC):
    """Everything vehicle_manager needs. Methods must not block for long
    (except takeoff, which vehicle_manager runs on a worker thread)."""

    @abstractmethod
    def capabilities(self) -> Capabilities: ...

    @abstractmethod
    def snapshot(self) -> VehicleSnapshot:
        """Latest known state (never blocks)."""

    @abstractmethod
    def takeoff(self, alt_m: float) -> CommandStatus:
        """Switch to guided, arm, climb to alt_m. May block a few seconds."""

    @abstractmethod
    def velocity(self, vn: float, ve: float, vd: float, yaw: Optional[float] = None) -> CommandStatus:
        """Stream a velocity setpoint (call at >= 2 Hz)."""

    @abstractmethod
    def goto(self, lat: float, lon: float, alt_m: float) -> CommandStatus: ...

    @abstractmethod
    def hold(self) -> CommandStatus: ...

    @abstractmethod
    def rtl(self) -> CommandStatus: ...

    @abstractmethod
    def land(self) -> CommandStatus: ...

    def set_param(self, name: str, value: float) -> CommandStatus:
        return CommandStatus.denied("not supported")

    def status_texts(self) -> List[str]:
        """Drain autopilot status messages (e.g. pre-arm failures)."""
        return []

    @abstractmethod
    def close(self): ...
