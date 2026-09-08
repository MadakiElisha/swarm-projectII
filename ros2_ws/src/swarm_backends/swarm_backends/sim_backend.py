"""SimBackend: kinematic simulator for testing without real drones."""
import math
import time
import threading
from typing import Iterator

from .adapter import (
    VehicleAdapter, TelemetryFrame, CommandRequest, CommandStatus,
    Capabilities, VehicleType
)


class SimBackend(VehicleAdapter):
    def __init__(self, lat: float, lon: float, wind_speed: float = 0.0):
        self.lat = lat
        self.lon = lon
        self.alt = 0.0
        self.battery_pct = 100.0
        self.yaw = 0.0
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = 0.0
        self.wind_speed = wind_speed  # m/s
        self.wind_dir = 0.0  # radians
        self._stop = False
        self._lock = threading.Lock()
        threading.Thread(target=self._physics_loop, daemon=True).start()
    
    def _physics_loop(self):
        while not self._stop:
            with self._lock:
                if self.target_alt > 0:
                    # climb/descent
                    dz = self.target_alt - self.alt
                    self.alt += 0.5 * math.copysign(min(abs(dz), 5), dz)
                
                if self.target_lat != self.lat or self.target_lon != self.lon:
                    # move toward target
                    dlat = self.target_lat - self.lat
                    dlon = self.target_lon - self.lon
                    dist = math.sqrt(dlat**2 + dlon**2)
                    if dist > 1e-6:
                        speed = 5.0 / 111000  # 5 m/s in degrees
                        self.lat += speed * dlat / dist
                        self.lon += speed * dlon / dist
                        self.yaw = math.atan2(dlon, dlat)
                    
                    # wind drift
                    if self.wind_speed > 0:
                        drift = self.wind_speed * 0.1 / 111000
                        self.lat += drift * math.cos(self.wind_dir)
                        self.lon += drift * math.sin(self.wind_dir)
                
                # battery drain when moving
                if self.alt > 0 or self.target_lat != self.lat:
                    self.battery_pct = max(0, self.battery_pct - 0.05)
            time.sleep(0.1)
    
    def capabilities(self) -> Capabilities:
        return Capabilities(
            vehicle_type=VehicleType.MULTICOPTER,
            can_goto=True, can_rtl=True, can_land=True
        )
    
    def telemetry(self) -> Iterator[TelemetryFrame]:
        while not self._stop:
            with self._lock:
                frame = TelemetryFrame(
                    lat=self.lat, lon=self.lon, alt=self.alt,
                    battery_pct=self.battery_pct,
                    roll=0.0, pitch=0.0, yaw=self.yaw,
                    timestamp=time.time())
            yield frame          # OUTSIDE the lock - never yield while holding it
            time.sleep(0.1)
    
    def execute(self, cmd: CommandRequest) -> CommandStatus:
        cmd_str = cmd.command.lower()
        with self._lock:
            if cmd_str == 'arm':
                pass
            elif cmd_str == 'takeoff':
                self.target_alt = cmd.params.get('alt', 30)
            elif cmd_str == 'goto':
                self.target_lat = cmd.params['lat']
                self.target_lon = cmd.params['lon']
                self.target_alt = cmd.params.get('alt', 30)
            elif cmd_str == 'rtl':
                self.target_lat = self.lat  # stay put for now
                self.target_alt = 0.0
            elif cmd_str == 'land':
                self.target_alt = 0.0
            else:
                return CommandStatus.denied(f"unknown command {cmd.command}")
        return CommandStatus.ok()
    
    def close(self):
        self._stop = True
