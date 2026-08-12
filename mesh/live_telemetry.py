"""
Phase 3.5 - Live telemetry collector.

Connects to ALL drones in the fleet simultaneously (real MAVLink
connections, one per port) and keeps an up-to-date snapshot of each
drone's actual live position and battery, as reported by that drone
itself in real time.

This replaces Phase 3's hardcoded Drone() objects with real,
live-updating state.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymavlink import mavutil
from dataclasses import dataclass
from sim.launch_fleet import FLEET


@dataclass
class LiveDroneState:
    label: str
    system_id: int
    lat: float = None
    lon: float = None
    battery_pct: float = None
    got_heartbeat: bool = False


def collect_live_snapshot(timeout_per_drone=3):
    """Connect to every drone's live MAVLink stream and read its
    current state. Returns a dict of label -> LiveDroneState."""
    states = {}

    for d in FLEET:
        state = LiveDroneState(label=d["label"], system_id=d["id"])
        conn = mavutil.mavlink_connection(f'udpin:127.0.0.1:{d["port"]}')

        import time
        deadline = time.time() + timeout_per_drone
        while time.time() < deadline:
            msg = conn.recv_match(blocking=True, timeout=1)
            if msg is None:
                continue
            mtype = msg.get_type()
            if mtype == "HEARTBEAT":
                state.got_heartbeat = True
            elif mtype == "GLOBAL_POSITION_INT":
                state.lat = msg.lat / 1e7
                state.lon = msg.lon / 1e7
            elif mtype == "SYS_STATUS":
                state.battery_pct = msg.battery_remaining

            # stop early once we have everything we need for this drone
            if state.got_heartbeat and state.lat is not None and state.battery_pct is not None:
                break

        states[d["label"]] = state
        status = "OK" if state.lat is not None else "NO DATA"
        print(f"[Telemetry] {d['label']}: lat={state.lat}, lon={state.lon}, "
              f"battery={state.battery_pct}%  [{status}]")

    return states


if __name__ == "__main__":
    print("[Telemetry] Collecting live snapshot from all drones "
          "(make sure launch_fleet.py is already running)...\n")
    snapshot = collect_live_snapshot()
    print(f"\n[Telemetry] Snapshot complete: {len(snapshot)} drones checked.")
