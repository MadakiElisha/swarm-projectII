"""MavlinkBackend: ArduPilot (tested in SITL) and PX4 (best effort) over MAVLink.

Fixes over the previous version:
  * every command waits for COMMAND_ACK (with retries) instead of assuming success;
  * flight modes are set BY NAME via the autopilot's own mode map, then
    confirmed from the heartbeat, so it is not hard-wired to ArduCopter's
    mode number 4;
  * takeoff does not re-arm an airborne vehicle;
  * velocity/goto are non-blocking sends (vehicle_manager streams them at 10 Hz);
  * RTL is a mode change the swarm layer can no longer override (the FSM
    latches it), and RTL altitude can be staggered per drone via set_param.
"""
import math
import threading
import time
from collections import deque
from typing import Dict, List, Tuple

from pymavlink import mavutil

from .adapter import (Capabilities, CommandStatus, VehicleAdapter, VehicleSnapshot,
                      VehicleType)

M = mavutil.mavlink

# normalised mode -> candidate autopilot mode names (ArduPilot first, then PX4)
MODE_CANDIDATES = {
    "GUIDED": ("GUIDED", "OFFBOARD"),
    "RTL": ("RTL", "AUTO_RTL"),
    "LAND": ("LAND", "AUTO_LAND"),
    "HOLD": ("BRAKE", "LOITER", "AUTO_LOITER", "HOLD"),
}
# autopilot mode name -> normalised
MODE_NORMALISE = {
    "GUIDED": "GUIDED", "GUIDED_NOGPS": "GUIDED", "OFFBOARD": "GUIDED",
    "RTL": "RTL", "SMART_RTL": "RTL", "AUTO_RTL": "RTL",
    "LAND": "LAND", "AUTO_LAND": "LAND",
    "BRAKE": "HOLD", "LOITER": "HOLD", "POSHOLD": "HOLD", "AUTO_LOITER": "HOLD", "HOLD": "HOLD",
    "TAKEOFF": "TAKEOFF", "AUTO_TAKEOFF": "TAKEOFF",
    "STABILIZE": "STABILIZE", "STABILIZED": "STABILIZE", "ALT_HOLD": "STABILIZE",
    "MANUAL": "STABILIZE", "ALTCTL": "STABILIZE", "POSCTL": "STABILIZE",
    "AUTO": "AUTO", "MISSION": "AUTO", "AUTO_MISSION": "AUTO",
}

VEL_MASK = 0b0000_1101_1100_0111            # use vx, vy, vz only
VEL_YAW_MASK = 0b0000_1001_1100_0111        # vx, vy, vz + yaw
POS_MASK = 0b0000_1101_1111_1000            # use lat, lon, alt only


class MavlinkBackend(VehicleAdapter):
    def __init__(self, url: str, source_system: int = 255, ack_timeout_s: float = 1.5,
                 retries: int = 3, connect_timeout_s: float = 15.0):
        self.url = url
        self.source_system = source_system
        self.ack_timeout_s = ack_timeout_s
        self.retries = retries
        self.connect_timeout_s = connect_timeout_s
        self.conn = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._snap = VehicleSnapshot()
        self._acks: Dict[int, Tuple[int, float]] = {}
        self._params: Dict[str, Tuple[float, float]] = {}
        self._texts: deque = deque(maxlen=50)
        self._last_hb = 0.0
        self._boot = time.time()
        self.autopilot = "unknown"
        threading.Thread(target=self._recv_loop, name="mav-recv", daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, name="mav-hb", daemon=True).start()

    # ---------------------------------------------------------------- links
    def _connect(self):
        nc = mavutil.mavlink_connection(self.url, source_system=self.source_system,
                                        source_component=M.MAV_COMP_ID_MISSIONPLANNER,
                                        autoreconnect=True)
        hb = nc.wait_heartbeat(timeout=self.connect_timeout_s)
        if hb is None:
            nc.close()
            raise TimeoutError("no heartbeat")
        self.autopilot = "px4" if hb.autopilot == M.MAV_AUTOPILOT_PX4 else "ardupilot"
        nc.target_system = hb.get_srcSystem()
        nc.target_component = hb.get_srcComponent() or M.MAV_COMP_ID_AUTOPILOT1
        with self._lock:
            self.conn = nc
        self._request_streams(nc)

    def _request_streams(self, c):
        rates_hz = {M.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: 10, M.MAVLINK_MSG_ID_ATTITUDE: 10,
                    M.MAVLINK_MSG_ID_SYS_STATUS: 2, M.MAVLINK_MSG_ID_BATTERY_STATUS: 1,
                    M.MAVLINK_MSG_ID_HOME_POSITION: 0.2}
        for mid, hz in rates_hz.items():
            c.mav.command_long_send(c.target_system, c.target_component,
                                    M.MAV_CMD_SET_MESSAGE_INTERVAL, 0, mid, 1e6 / hz,
                                    0, 0, 0, 0, 0)
        # legacy fallback for older firmwares
        c.mav.request_data_stream_send(c.target_system, c.target_component,
                                       M.MAV_DATA_STREAM_ALL, 10, 1)
        c.mav.command_long_send(c.target_system, c.target_component,
                                M.MAV_CMD_REQUEST_MESSAGE, 0, M.MAVLINK_MSG_ID_HOME_POSITION,
                                0, 0, 0, 0, 0, 0)

    def _heartbeat_loop(self):
        while not self._stop.is_set():
            c = self.conn
            if c is not None:
                try:
                    c.mav.heartbeat_send(M.MAV_TYPE_GCS, M.MAV_AUTOPILOT_INVALID, 0, 0, 0)
                except Exception:
                    pass
            self._stop.wait(1.0)

    def _recv_loop(self):
        while not self._stop.is_set():
            c = self.conn
            if c is None:
                try:
                    self._connect()
                except Exception:
                    self._stop.wait(2.0)
                continue
            try:
                msg = c.recv_match(blocking=True, timeout=0.5)
            except Exception:
                with self._lock:
                    self.conn = None
                self._snap.connected = False
                continue
            now = time.time()
            if now - self._last_hb > 5.0:
                self._snap.connected = False
            if msg is None:
                continue
            if msg.get_srcSystem() != c.target_system:
                continue
            try:
                self._handle(c, msg, now)
            except Exception:       # a malformed message must never kill the receive thread
                continue

    def _handle(self, c, msg, now):
        t = msg.get_type()
        s = self._snap
        if t == "HEARTBEAT":
            if msg.type == M.MAV_TYPE_GCS or msg.get_srcComponent() != c.target_component:
                return
            self._last_hb = now
            s.connected = True
            s.armed = bool(msg.base_mode & M.MAV_MODE_FLAG_SAFETY_ARMED)
            s.mode = MODE_NORMALISE.get(str(c.flightmode).upper(), "OTHER")
        elif t == "GLOBAL_POSITION_INT":
            s.lat, s.lon = msg.lat / 1e7, msg.lon / 1e7
            s.alt = msg.relative_alt / 1000.0
            s.vn, s.ve, s.vd = msg.vx / 100.0, msg.vy / 100.0, msg.vz / 100.0
            s.t = now
        elif t == "SYS_STATUS" and msg.battery_remaining >= 0:
            s.battery_pct = float(msg.battery_remaining)
        elif t == "BATTERY_STATUS" and msg.battery_remaining >= 0:
            s.battery_pct = float(msg.battery_remaining)
        elif t == "ATTITUDE":
            s.roll, s.pitch, s.yaw = msg.roll, msg.pitch, msg.yaw
        elif t == "WIND":
            s.wind_speed, s.wind_dir = float(msg.speed), math.radians(float(msg.direction))
        elif t == "HOME_POSITION":
            s.home_lat, s.home_lon = msg.latitude / 1e7, msg.longitude / 1e7
        elif t == "COMMAND_ACK":
            self._acks[msg.command] = (msg.result, now)
        elif t == "PARAM_VALUE":
            self._params[str(msg.param_id).strip("\x00")] = (float(msg.param_value), now)
        elif t == "STATUSTEXT":
            self._texts.append(str(msg.text))

    # -------------------------------------------------------------- helpers
    def _command(self, cmd: int, *params: float) -> CommandStatus:
        c = self.conn
        if c is None:
            return CommandStatus.denied("no connection")
        p = list(params) + [0.0] * (7 - len(params))
        for attempt in range(self.retries):
            sent = time.time()
            c.mav.command_long_send(c.target_system, c.target_component, cmd, attempt, *p)
            while time.time() - sent < self.ack_timeout_s:
                ack = self._acks.get(cmd)
                if ack and ack[1] >= sent:
                    if ack[0] == M.MAV_RESULT_ACCEPTED:
                        return CommandStatus.ok()
                    if ack[0] == M.MAV_RESULT_IN_PROGRESS:
                        sent = time.time()      # keep waiting for the final ACK
                        continue
                    texts = "; ".join(list(self._texts)[-3:])
                    return CommandStatus.denied(f"cmd {cmd} result {ack[0]} {texts}".strip())
                time.sleep(0.02)
        return CommandStatus.denied(f"cmd {cmd}: no ACK after {self.retries} tries")

    def _set_mode(self, normalised: str, timeout_s: float = 3.0) -> CommandStatus:
        c = self.conn
        if c is None:
            return CommandStatus.denied("no connection")
        if self._snap.mode == normalised:
            return CommandStatus.ok()
        mapping = c.mode_mapping() or {}
        name = next((n for n in MODE_CANDIDATES[normalised] if n in mapping), None)
        if name is None:
            return CommandStatus.denied(f"autopilot has no mode for {normalised}")
        for _ in range(self.retries):
            c.set_mode(name)
            t0 = time.time()
            while time.time() - t0 < timeout_s / self.retries:
                if self._snap.mode == normalised:
                    return CommandStatus.ok()
                time.sleep(0.05)
        return CommandStatus.denied(f"mode {name} not confirmed by heartbeat")

    def _ms(self) -> int:
        return int((time.time() - self._boot) * 1000) & 0xFFFFFFFF

    # ----------------------------------------------------------- interface
    def capabilities(self) -> Capabilities:
        return Capabilities(VehicleType.MULTICOPTER)

    def snapshot(self) -> VehicleSnapshot:
        s = self._snap
        return VehicleSnapshot(**{k: getattr(s, k) for k in s.__dataclass_fields__})

    def takeoff(self, alt_m: float) -> CommandStatus:
        s = self._snap
        if s.armed and s.alt > 1.0:
            return self._set_mode("GUIDED")      # already flying: just take control
        st = self._set_mode("GUIDED") if self.autopilot != "px4" else CommandStatus.ok()
        if not st.accepted:
            return st
        if not s.armed:
            st = self._command(M.MAV_CMD_COMPONENT_ARM_DISARM, 1)
            if not st.accepted:
                return CommandStatus.denied(f"arm refused: {st.reason}")
        return self._command(M.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, float("nan"), float("nan"),
                             float("nan"), float(alt_m))

    def velocity(self, vn, ve, vd, yaw=None) -> CommandStatus:
        c = self.conn
        if c is None:
            return CommandStatus.denied("no connection")
        mask = VEL_MASK if yaw is None else VEL_YAW_MASK
        c.mav.set_position_target_local_ned_send(
            self._ms(), c.target_system, c.target_component, M.MAV_FRAME_LOCAL_NED, mask,
            0, 0, 0, float(vn), float(ve), float(vd), 0, 0, 0, float(yaw or 0.0), 0)
        if self.autopilot == "px4" and self._snap.mode != "GUIDED":
            threading.Thread(target=self._set_mode, args=("GUIDED",), daemon=True).start()
        return CommandStatus.ok()

    def goto(self, lat, lon, alt_m) -> CommandStatus:
        c = self.conn
        if c is None:
            return CommandStatus.denied("no connection")
        c.mav.set_position_target_global_int_send(
            self._ms(), c.target_system, c.target_component,
            M.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT, POS_MASK,
            int(lat * 1e7), int(lon * 1e7), float(alt_m), 0, 0, 0, 0, 0, 0, 0, 0)
        return CommandStatus.ok()

    def hold(self) -> CommandStatus:
        if self.autopilot == "px4":
            return self._set_mode("HOLD")
        return self.velocity(0.0, 0.0, 0.0)      # ArduCopter GUIDED: stop and hold

    def rtl(self) -> CommandStatus:
        return self._set_mode("RTL")

    def land(self) -> CommandStatus:
        return self._set_mode("LAND")

    def set_param(self, name: str, value: float) -> CommandStatus:
        c = self.conn
        if c is None:
            return CommandStatus.denied("no connection")
        for _ in range(self.retries):
            sent = time.time()
            c.mav.param_set_send(c.target_system, c.target_component, name.encode(),
                                 float(value), M.MAV_PARAM_TYPE_REAL32)
            while time.time() - sent < self.ack_timeout_s:
                got = self._params.get(name)
                if got and got[1] >= sent and abs(got[0] - value) < 1e-3:
                    return CommandStatus.ok()
                time.sleep(0.02)
        return CommandStatus.denied(f"param {name} not confirmed")

    def status_texts(self) -> List[str]:
        out = list(self._texts)
        self._texts.clear()
        return out

    def close(self):
        self._stop.set()
        c = self.conn
        if c is not None:
            try:
                c.close()
            except Exception:
                pass
