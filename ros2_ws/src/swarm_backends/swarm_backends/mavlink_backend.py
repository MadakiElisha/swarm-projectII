"""MavlinkBackend: ArduPilot/PX4 over MAVLink."""
import threading
import time
from typing import Iterator
from pymavlink import mavutil

from .adapter import (
    VehicleAdapter, TelemetryFrame, CommandRequest, CommandStatus, 
    Capabilities, VehicleType
)


class MavlinkBackend(VehicleAdapter):
    def __init__(self, url: str, source_system: int = 255):
        self.url = url
        self.conn = None
        self._stop = False
        self._lock = threading.Lock()
        self.abort = threading.Event()
        self._battery = -1.0
        self._roll = self._pitch = self._yaw = 0.0
        self._telemetry_queue = []
        self._statustext_queue = []
        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
    
    def _heartbeat_loop(self):
        while not self._stop:
            with self._lock:
                c = self.conn
            if c is not None:
                try:
                    c.mav.heartbeat_send(6, 0, 0, 0, 0)
                    c.mav.request_data_stream_send(
                        c.target_system, c.target_component,
                        mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)
                except Exception:
                    pass
            time.sleep(1)

    def _recv_loop(self):
        # SINGLE owner of the connection: only this thread ever connects.
        while not self._stop:
            with self._lock:
                c = self.conn
            if c is None:
                try:
                    nc = mavutil.mavlink_connection(self.url, source_system=255)
                    nc.wait_heartbeat(timeout=15)
                    with self._lock:
                        self.conn = nc
                except Exception:
                    time.sleep(2)
                continue
            try:
                msg = c.recv_match(blocking=True, timeout=1)
            except Exception:
                with self._lock:
                    self.conn = None
                continue
            if msg is None:
                continue
            mtype = msg.get_type()
            if mtype == 'GLOBAL_POSITION_INT':
                frame = TelemetryFrame(
                    lat=msg.lat / 1e7,
                    lon=msg.lon / 1e7,
                    alt=msg.relative_alt / 1000.0,
                    battery_pct=self._battery,
                    roll=self._roll, pitch=self._pitch, yaw=self._yaw,
                    timestamp=time.time()
                )
                self._telemetry_queue.append(frame)
            elif mtype == 'SYS_STATUS' and msg.battery_remaining >= 0:
                self._battery = float(msg.battery_remaining)
            elif mtype == 'ATTITUDE':
                self._roll, self._pitch, self._yaw = msg.roll, msg.pitch, msg.yaw
            elif mtype == 'STATUSTEXT':
                self._statustext_queue.append(msg.text)
    
    def capabilities(self) -> Capabilities:
        return Capabilities(
            vehicle_type=VehicleType.MULTICOPTER,
            can_goto=True, can_rtl=True, can_land=True
        )
    
    def telemetry(self) -> Iterator[TelemetryFrame]:
        while not self._stop:
            if self._telemetry_queue:
                yield self._telemetry_queue.pop(0)
            else:
                time.sleep(0.1)
    
    def execute(self, cmd: CommandRequest) -> CommandStatus:
        with self._lock:
            c = self.conn
        if c is None:
            return CommandStatus.denied("no connection")
        
        M = mavutil.mavlink
        cmd_str = cmd.command.lower()
        
        if cmd_str == 'arm':
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
        elif cmd_str == 'disarm':
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0, 0, 0, 0, 0, 0)
        elif cmd_str == 'takeoff':
            self.abort.clear()   # a new flight cancels any prior abort
            alt = cmd.params.get('alt', 30)
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_DO_SET_MODE, 0, 1, 4, 0, 0, 0, 0, 0)
            time.sleep(1)
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
            time.sleep(2)
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, alt)
        elif cmd_str == 'goto':
            lat = cmd.params['lat']
            lon = cmd.params['lon']
            alt = cmd.params.get('alt', 30)
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_DO_SET_MODE, 0, 1, 4, 0, 0, 0, 0, 0)
            time.sleep(1)
            for _ in range(5):
                if self.abort.is_set():
                    return CommandStatus.denied('aborted')
                c.mav.set_position_target_global_int_send(
                    0, c.target_system, c.target_component,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    0b0000111111111000,
                    int(lat * 1e7), int(lon * 1e7), alt,
                    0, 0, 0, 0, 0, 0, 0, 0)
                time.sleep(1)
        elif cmd_str == 'rtl':
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_NAV_RETURN_TO_LAUNCH, 0, 0, 0, 0, 0, 0, 0, 0)
        elif cmd_str == 'land':
            c.mav.command_long_send(c.target_system, c.target_component,
                M.MAV_CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            return CommandStatus.denied(f"unknown command {cmd.command}")
        
        return CommandStatus.ok()
    
    def close(self):
        self._stop = True
