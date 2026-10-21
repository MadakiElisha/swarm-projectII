"""SimBackend: kinematic vehicle for running the full ROS stack without SITL.

Uses the same point-mass model as the ROS-free simulator, so the ROS smoke
test and the pure scenarios exercise identical vehicle behaviour.
"""
import math
import threading
import time
from typing import Optional

from swarm_common.geo import Origin
from swarm_common.sim.core import SimVehicle
from swarm_common.vehicle_fsm import Action

from .adapter import Capabilities, CommandStatus, VehicleAdapter, VehicleSnapshot


class SimBackend(VehicleAdapter):
    def __init__(self, home_lat: float, home_lon: float, origin: Origin,
                 rtl_alt_m: float = 20.0, rate_hz: float = 20.0, battery_pct: float = 100.0):
        self.origin = origin
        hx, hy = origin.to_enu(home_lat, home_lon)
        self.home = (home_lat, home_lon)
        self.v = SimVehicle(hx, hy, (hx, hy), rtl_alt=rtl_alt_m, battery=battery_pct)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._dt = 1.0 / rate_hz
        threading.Thread(target=self._loop, name="sim-physics", daemon=True).start()

    def _loop(self):
        last = time.time()
        while not self._stop.is_set():
            now = time.time()
            with self._lock:
                self.v.step(min(0.2, now - last))
            last = now
            self._stop.wait(self._dt)

    def _apply(self, kind: str, **params) -> CommandStatus:
        with self._lock:
            self.v.apply(Action(kind, params))
        return CommandStatus.ok()

    # ----------------------------------------------------------- interface
    def capabilities(self) -> Capabilities:
        return Capabilities()

    def snapshot(self) -> VehicleSnapshot:
        with self._lock:
            v = self.v
            lat, lon = self.origin.to_latlon(v.x, v.y)
            mode = {"RTL": "RTL", "LAND": "LAND", "GUIDED": "GUIDED"}.get(v.mode, "STABILIZE")
            yaw_ned = math.atan2(v.vx, v.vy) if math.hypot(v.vx, v.vy) > 0.5 else 0.0
            return VehicleSnapshot(time.time(), True, lat, lon, v.alt, v.vy, v.vx, 0.0,
                                   v.battery, v.armed, mode, 0.0, 0.0, yaw_ned,
                                   home_lat=self.home[0], home_lon=self.home[1])

    def takeoff(self, alt_m: float) -> CommandStatus:
        with self._lock:
            if self.v.battery <= 0:
                return CommandStatus.denied("battery empty")
        return self._apply("takeoff", alt=alt_m)

    def velocity(self, vn, ve, vd, yaw: Optional[float] = None) -> CommandStatus:
        with self._lock:
            alt = self.v.alt - vd * 1.0          # integrate the climb request over ~1 s
        return self._apply("velocity", vx=ve, vy=vn, alt=max(0.0, alt))

    def goto(self, lat, lon, alt_m) -> CommandStatus:
        x, y = self.origin.to_enu(lat, lon)
        return self._apply("position", x=x, y=y, alt=alt_m)

    def hold(self) -> CommandStatus:
        return self._apply("hold")

    def rtl(self) -> CommandStatus:
        return self._apply("rtl")

    def land(self) -> CommandStatus:
        return self._apply("land")

    def set_param(self, name: str, value: float) -> CommandStatus:
        if name == "RTL_ALT":
            with self._lock:
                self.v.rtl_alt = value / 100.0
            return CommandStatus.ok()
        return CommandStatus.denied("unknown param")

    def close(self):
        self._stop.set()
