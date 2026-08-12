"""VehicleAdapter: the drone-agnostic contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional
from enum import Enum


class VehicleType(Enum):
    MULTICOPTER = "multicopter"
    FIXED_WING = "fixed_wing"
    ROVER = "rover"
    VTOL = "vtol"


@dataclass
class Capabilities:
    """What this vehicle can do."""
    vehicle_type: VehicleType
    can_goto: bool = True
    can_rtl: bool = True
    can_land: bool = True
    max_altitude_m: float = 120.0
    

@dataclass
class TelemetryFrame:
    """One telemetry sample from the vehicle."""
    lat: float
    lon: float
    alt: float  # relative to home, meters
    battery_pct: float
    roll: float = 0.0  # radians
    pitch: float = 0.0
    yaw: float = 0.0
    timestamp: float = 0.0


@dataclass
class CommandRequest:
    """A command to execute."""
    command: str  # 'arm', 'takeoff', 'rtl', 'land', 'goto'
    params: dict = None
    
    def __post_init__(self):
        self.params = self.params or {}
        
        
@dataclass
class CommandStatus:
    """Result of a command."""
    accepted: bool
    reason: str = ""
    
    @staticmethod
    def ok():
        return CommandStatus(accepted=True)
    
    @staticmethod
    def denied(reason: str):
        return CommandStatus(accepted=False, reason=reason)
        
        
class VehicleAdapter(ABC):
    """The contract every drone must satisfy."""
    
    @abstractmethod
    def capabilities(self) -> Capabilities:
        """What can this vehicle do?"""
        pass
    
    @abstractmethod
    def telemetry(self) -> Iterator[TelemetryFrame]:
        """Stream telemetry frames forever."""
        pass
    
    @abstractmethod
    def execute(self, cmd: CommandRequest) -> CommandStatus:
        """Execute a command. Return accepted/denied + reason."""
        pass
    
    @abstractmethod
    def close(self):
        """Clean up resources."""
        pass
