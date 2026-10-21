"""A tiny fake ArduCopter speaking real MAVLink over UDP, for backend tests.

It answers COMMAND_LONG with COMMAND_ACK, honours mode changes, arming and
takeoff, and streams HEARTBEAT / GLOBAL_POSITION_INT / SYS_STATUS. It can
be told to refuse arming (pre-arm failure) or to drop ACKs.
"""
import threading
import time

from pymavlink import mavutil

M = mavutil.mavlink
MODES = {"STABILIZE": 0, "GUIDED": 4, "LOITER": 5, "RTL": 6, "LAND": 9, "BRAKE": 17}


class FakeArduCopter:
    def __init__(self, port: int):
        self.c = mavutil.mavlink_connection(f"udpout:127.0.0.1:{port}", source_system=1,
                                            source_component=1)
        self.mode = MODES["STABILIZE"]
        self.armed = False
        self.alt = 0.0
        self.refuse_arm = False
        self.drop_acks = 0
        self.commands = []
        self.velocity_msgs = 0
        self.params = {}
        self._stop = threading.Event()
        threading.Thread(target=self._tx, daemon=True).start()
        threading.Thread(target=self._rx, daemon=True).start()

    def _tx(self):
        while not self._stop.is_set():
            if self._stop.wait(0.0):
                return
            base = M.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED | (M.MAV_MODE_FLAG_SAFETY_ARMED if self.armed else 0)
            self.c.mav.heartbeat_send(M.MAV_TYPE_QUADROTOR, M.MAV_AUTOPILOT_ARDUPILOTMEGA,
                                      base, self.mode, M.MAV_STATE_ACTIVE)
            self.c.mav.global_position_int_send(0, int(6.5244e7), int(3.3792e7), 0,
                                                int(self.alt * 1000), 0, 0, 0, 0)
            try:
                self.c.mav.sys_status_send(0, 0, 0, 0, 12000, 0, 87, 0, 0, 0, 0, 0, 0)
            except OSError:
                return
            time.sleep(0.1)

    def _ack(self, cmd, result):
        if self.drop_acks > 0:
            self.drop_acks -= 1
            return
        self.c.mav.command_ack_send(cmd, result)

    def _rx(self):
        while not self._stop.is_set():
            try:
                m = self.c.recv_match(blocking=True, timeout=0.2)
            except OSError:
                return
            if m is None:
                continue
            t = m.get_type()
            if t == "COMMAND_LONG":
                self.commands.append(m.command)
                if m.command == M.MAV_CMD_DO_SET_MODE:
                    self.mode = int(m.param2)
                    self._ack(m.command, M.MAV_RESULT_ACCEPTED)
                elif m.command == M.MAV_CMD_COMPONENT_ARM_DISARM:
                    if self.refuse_arm and m.param1 == 1:
                        self.c.mav.statustext_send(M.MAV_SEVERITY_CRITICAL, b"PreArm: GPS bad")
                        self._ack(m.command, M.MAV_RESULT_FAILED)
                    else:
                        self.armed = m.param1 == 1
                        self._ack(m.command, M.MAV_RESULT_ACCEPTED)
                elif m.command == M.MAV_CMD_NAV_TAKEOFF:
                    ok = self.armed and self.mode == MODES["GUIDED"]
                    if ok:
                        self.alt = m.param7
                    self._ack(m.command, M.MAV_RESULT_ACCEPTED if ok else M.MAV_RESULT_DENIED)
                else:
                    self._ack(m.command, M.MAV_RESULT_ACCEPTED)
            elif t == "SET_MODE":
                self.mode = m.custom_mode
            elif t == "SET_POSITION_TARGET_LOCAL_NED":
                self.velocity_msgs += 1
            elif t == "PARAM_SET":
                name = m.param_id if isinstance(m.param_id, str) else m.param_id.decode()
                self.params[name] = m.param_value
                self.c.mav.param_value_send(m.param_id.encode() if isinstance(m.param_id, str)
                                            else m.param_id, m.param_value,
                                            M.MAV_PARAM_TYPE_REAL32, 1, 0)

    def close(self):
        self._stop.set()
        time.sleep(0.3)
        self.c.close()
