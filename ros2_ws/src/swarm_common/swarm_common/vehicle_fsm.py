"""Vehicle authority: the ONLY thing allowed to command the flight controller.

Pure state machine (no ROS, no MAVLink): the vehicle_manager node feeds it
observations and executes the actions it returns. Priorities, highest first:

  1. E-STOP (operator)                         -> LAND now, latched
  2. hard failsafes: critical battery, geofence -> RTL, latched
  3. operator RTL / LAND                        -> latched until RESUME
  4. brain watchdog: setpoints stale -> HOLD; dead -> RTL (latched)
  5. brain setpoints (mission)                  -> only when nothing above applies

"Latched" means mission setpoints are ignored until an operator RESUME (or
TAKEOFF) and the cause has cleared. This is what makes RTL actually stick:
the mission layer physically cannot override it.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# states
GROUND, TAKEOFF, GUIDED, HOLD, RTL, LAND, ESTOP = (
    "GROUND", "TAKEOFF", "GUIDED", "HOLD", "RTL", "LAND", "ESTOP")

# setpoint kinds coming from the brain
SP_IDLE, SP_VEL, SP_POS, SP_HOLD, SP_RTB, SP_LAND = "IDLE", "VEL", "POS", "HOLD", "RTB", "LAND"
FLY_KINDS = {SP_VEL, SP_POS, SP_HOLD}


@dataclass
class VehicleObs:
    """What the vehicle currently reports (from the adapter)."""
    t: float
    x: float
    y: float
    alt: float
    battery: float
    armed: bool
    mode: str                 # normalised: GUIDED / RTL / LAND / LOITER / STABILIZE / ...
    connected: bool = True


@dataclass
class Setpoint:
    t: float
    kind: str = SP_IDLE
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    x: float = 0.0
    y: float = 0.0
    alt: float = 30.0
    yaw: Optional[float] = None


@dataclass
class Action:
    kind: str                 # arm / takeoff / velocity / position / hold / rtl / land
    params: dict = field(default_factory=dict)


@dataclass
class FsmCfg:
    critical_pct: float = 12.0
    fence_radius_m: float = 8000.0
    fence_max_alt_m: float = 120.0
    fence_center: Tuple[float, float] = (0.0, 0.0)
    brain_stale_s: float = 1.5
    brain_dead_s: float = 10.0
    takeoff_timeout_s: float = 45.0
    resend_s: float = 3.0
    airborne_alt_m: float = 1.0


class VehicleFSM:
    def __init__(self, cfg: FsmCfg):
        self.cfg = cfg
        self.state = GROUND
        self.latch: Optional[str] = None       # reason mission control is locked out
        self.since = 0.0
        self._last_send = -1e9
        self._takeoff_alt = 30.0
        self._sp: Optional[Setpoint] = None
        self._sp_rx = -1e9
        self.events: List[str] = []

    # ---------------------------------------------------------------- inputs
    def on_setpoint(self, sp: Setpoint, now: float):
        self._sp, self._sp_rx = sp, now

    def on_operator(self, cmd: str, now: float, obs: Optional[VehicleObs] = None) -> List[Action]:
        cmd = cmd.upper()
        if cmd in ("ESTOP", "E-STOP", "KILL"):
            return self._enter(ESTOP, now, latch="operator E-STOP", act=Action("land"))
        if cmd == "RTL":
            return self._enter(RTL, now, latch="operator RTL", act=Action("rtl"))
        if cmd == "LAND":
            return self._enter(LAND, now, latch="operator LAND", act=Action("land"))
        if cmd in ("RESUME", "TAKEOFF", "ARM"):
            if obs is not None and obs.battery < self.cfg.critical_pct:
                self.events.append("RESUME refused: battery critical")
                return []
            if obs is not None and self._fence_breach(obs):
                self.events.append("RESUME refused: outside geofence")
                return []
            self.latch = None
            self.events.append(f"operator {cmd}: mission control re-enabled")
            if cmd in ("TAKEOFF", "ARM") and self.state == GROUND:
                return self._enter(TAKEOFF, now, act=None)
            if self.state in (RTL, LAND, ESTOP) and obs is not None and obs.alt > self.cfg.airborne_alt_m:
                return self._enter(HOLD, now, act=Action("hold"))
            return []
        self.events.append(f"unknown operator command {cmd}")
        return []

    # ------------------------------------------------------------------ tick
    def tick(self, obs: VehicleObs, now: float) -> List[Action]:
        c = self.cfg
        airborne = obs.alt > c.airborne_alt_m
        # ---- hard failsafes (always evaluated, highest priority after ESTOP)
        if self.state != ESTOP and airborne:
            if obs.battery < c.critical_pct and self.latch != "critical battery":
                return self._enter(RTL, now, latch="critical battery", act=Action("rtl"))
            if self._fence_breach(obs) and self.latch != "geofence":
                return self._enter(RTL, now, latch="geofence", act=Action("rtl"))

        sp = self._sp
        sp_age = now - self._sp_rx
        fresh = sp is not None and sp_age <= c.brain_stale_s

        if self.state == GROUND:
            if not self.latch and fresh and sp.kind in FLY_KINDS:
                self._takeoff_alt = max(5.0, sp.alt)
                return self._enter(TAKEOFF, now, act=None)
            return []

        if self.state == TAKEOFF:
            if airborne and obs.alt >= 0.85 * self._takeoff_alt:
                return self._enter(GUIDED, now, act=None)
            if now - self.since > c.takeoff_timeout_s:
                self.events.append("takeoff timed out")
                return self._enter(LAND if airborne else GROUND, now,
                                   act=Action("land") if airborne else None)
            if now - self._last_send >= c.resend_s * 2:
                self._last_send = now
                return [Action("takeoff", {"alt": self._takeoff_alt})]
            return []

        if self.state in (RTL, LAND, ESTOP):
            if not airborne and not obs.armed:
                st = self.state
                self.state, self.since = GROUND, now
                self.events.append(f"{st} complete: on ground")
                if self.latch and self.latch.startswith("brain"):
                    self.latch = None
                return []
            want = "RTL" if self.state == RTL else "LAND"
            if obs.mode != want and now - self._last_send >= c.resend_s:
                self._last_send = now
                return [Action("rtl" if self.state == RTL else "land")]
            return []

        # airborne, mission-controllable states: GUIDED / HOLD
        if not airborne and self.state == GUIDED and now - self.since > 5.0:
            return self._enter(GROUND, now, act=None)
        if not fresh:
            if sp is not None and sp_age > c.brain_dead_s:
                return self._enter(RTL, now, latch="brain dead", act=Action("rtl"))
            if self.state != HOLD:
                return self._enter(HOLD, now, act=Action("hold"))
            return []
        if sp.kind == SP_RTB:
            return self._enter(RTL, now, latch="brain RTB", act=Action("rtl"))
        if sp.kind == SP_LAND:
            return self._enter(LAND, now, latch="brain LAND", act=Action("land"))
        if self.state == HOLD:
            self.state, self.since = GUIDED, now
        if sp.kind == SP_VEL:
            return [Action("velocity", {"vx": sp.vx, "vy": sp.vy, "vz": sp.vz,
                                        "alt": sp.alt, "yaw": sp.yaw})]
        if sp.kind == SP_POS:
            return [Action("position", {"x": sp.x, "y": sp.y, "alt": sp.alt})]
        if sp.kind in (SP_HOLD, SP_IDLE):
            return [Action("hold")] if now - self._last_send >= c.resend_s else []
        return []

    # --------------------------------------------------------------- helpers
    @property
    def mission_enabled(self) -> bool:
        return self.latch is None and self.state in (GROUND, TAKEOFF, GUIDED, HOLD)

    def _fence_breach(self, obs: VehicleObs) -> bool:
        dx, dy = obs.x - self.cfg.fence_center[0], obs.y - self.cfg.fence_center[1]
        return (dx * dx + dy * dy) ** 0.5 > self.cfg.fence_radius_m or obs.alt > self.cfg.fence_max_alt_m

    def _enter(self, state: str, now: float, latch: Optional[str] = None,
               act: Optional[Action] = None) -> List[Action]:
        if state != self.state:
            self.events.append(f"{self.state} -> {state}" + (f" ({latch})" if latch else ""))
        self.state, self.since = state, now
        if latch:
            self.latch = latch
        self._last_send = now if act else -1e9
        return [act] if act else []
