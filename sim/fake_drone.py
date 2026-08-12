"""
Phase 1 - Simulated single drone emitting real MAVLink telemetry.

This is not a toy format - it uses pymavlink to construct actual
MAVLink v2 HEARTBEAT and GLOBAL_POSITION_INT messages, the same
messages a real ArduPilot/PX4 flight controller sends.

Run this, then run ground_station.py in another terminal (or process)
to see it receive and decode real telemetry.
"""
import time
import math
import argparse
from pymavlink import mavutil


def run_fake_drone(system_id: int, udp_port: int, start_lat: float, start_lon: float):
    # Create a MAVLink connection that BROADCASTS as a drone would
    conn = mavutil.mavlink_connection(
        f'udpout:127.0.0.1:{udp_port}',
        source_system=system_id,
        source_component=1,
    )

    print(f"[Drone {system_id}] Starting, broadcasting on UDP port {udp_port}")

    battery_pct = 100
    t = 0
    while True:
        # HEARTBEAT: every real drone sends this ~1Hz to say "I'm alive, here's my mode"
        conn.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_QUADROTOR,
            mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
            mavutil.mavlink.MAV_MODE_GUIDED_ARMED,
            0,
            mavutil.mavlink.MAV_STATE_ACTIVE,
        )

        # Simulate slow circular movement so lat/lon actually changes over time
        lat = start_lat + 0.0005 * math.sin(t / 10)
        lon = start_lon + 0.0005 * math.cos(t / 10)
        alt_mm = 50000  # 50m altitude, in millimeters (MAVLink uses mm)

        # GLOBAL_POSITION_INT: real position telemetry message
        conn.mav.global_position_int_send(
            int(time.time() * 1000) & 0xFFFFFFFF,  # time_boot_ms
            int(lat * 1e7),   # MAVLink encodes lat/lon as int, degrees * 1e7
            int(lon * 1e7),
            alt_mm,
            alt_mm,
            0, 0, 0,          # velocity x,y,z
            0,                # heading
        )

        # SYS_STATUS: includes battery percentage
        battery_pct = max(0, battery_pct - 0.05)  # slow drain for demo
        conn.mav.sys_status_send(
            0, 0, 0, 0, 12000, 0, int(battery_pct),
            0, 0, 0, 0, 0, 0,
        )

        t += 1
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=int, default=1, help="MAVLink system ID for this drone")
    parser.add_argument("--port", type=int, default=14550, help="UDP port to broadcast on")
    parser.add_argument("--lat", type=float, default=6.5244, help="Starting latitude (default: Lagos)")
    parser.add_argument("--lon", type=float, default=3.3792, help="Starting longitude (default: Lagos)")
    args = parser.parse_args()
    run_fake_drone(args.id, args.port, args.lat, args.lon)
