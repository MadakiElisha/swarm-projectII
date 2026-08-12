"""
Phase 1 - Minimal ground control station.

Connects to the fake_drone.py MAVLink stream and DECODES real
MAVLink messages, exactly as QGroundControl or Mission Planner would
under the hood. This proves we can read genuine drone telemetry
programmatically - the foundation everything else builds on.
"""
import argparse
import time
from pymavlink import mavutil


def run_ground_station(udp_port: int, duration_sec: int):
    conn = mavutil.mavlink_connection(f'udpin:127.0.0.1:{udp_port}')
    print(f"[GCS] Listening on UDP port {udp_port} for {duration_sec}s...\n")

    start = time.time()
    seen_heartbeat = False
    msg_count = 0

    while time.time() - start < duration_sec:
        msg = conn.recv_match(blocking=True, timeout=2)
        if msg is None:
            continue

        msg_count += 1
        msg_type = msg.get_type()

        if msg_type == "HEARTBEAT" and not seen_heartbeat:
            seen_heartbeat = True
            print(f"[GCS] Heartbeat received from system {msg.get_srcSystem()} "
                  f"- autopilot type {msg.autopilot}, mode flags {msg.base_mode}")

        elif msg_type == "GLOBAL_POSITION_INT":
            lat = msg.lat / 1e7
            lon = msg.lon / 1e7
            alt_m = msg.alt / 1000
            print(f"[GCS] Position update: lat={lat:.6f}, lon={lon:.6f}, alt={alt_m:.1f}m")

        elif msg_type == "SYS_STATUS":
            print(f"[GCS] Battery: {msg.battery_remaining}%")

    print(f"\n[GCS] Done. Received {msg_count} total MAVLink messages in {duration_sec}s.")
    if msg_count > 0:
        print("[GCS] SUCCESS: real MAVLink telemetry pipeline confirmed working.")
    else:
        print("[GCS] FAILURE: no messages received - check that fake_drone.py is running.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14550)
    parser.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()
    run_ground_station(args.port, args.duration)
