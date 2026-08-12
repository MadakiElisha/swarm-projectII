"""
Phase 3.5 - Multi-drone launcher.

Spawns several fake_drone.py processes at once, each simulating a
DIFFERENT drone at a different starting GPS position, each
broadcasting its own real MAVLink stream on its own UDP port.

This replaces the "one drone at a time" setup from Phase 1 with an
actual live multi-drone scenario - the same 5-drone flood layout
used in Phase 2's mesh demo and Phase 3's auction demo, but now each
drone is a REAL, independently running, live MAVLink source instead
of hardcoded numbers.
"""
import subprocess
import sys
import os
import time

# Same 5-drone layout used in Phase 2 and Phase 3, so results are comparable
FLEET = [
    {"id": 1, "port": 14551, "lat": 6.5244, "lon": 3.3792, "label": "D1"},
    {"id": 2, "port": 14552, "lat": 6.5300, "lon": 3.3850, "label": "D2"},
    {"id": 3, "port": 14553, "lat": 6.5360, "lon": 3.3910, "label": "D3"},
    {"id": 4, "port": 14554, "lat": 6.5420, "lon": 3.3970, "label": "D4"},
    {"id": 5, "port": 14555, "lat": 6.5480, "lon": 3.4030, "label": "D5"},
]


def launch_fleet():
    here = os.path.dirname(os.path.abspath(__file__))
    fake_drone_path = os.path.join(here, "fake_drone.py")
    processes = []

    for d in FLEET:
        cmd = [
            sys.executable, fake_drone_path,
            "--id", str(d["id"]),
            "--port", str(d["port"]),
            "--lat", str(d["lat"]),
            "--lon", str(d["lon"]),
        ]
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(p)
        print(f"[Launcher] Started {d['label']} (system id {d['id']}) "
              f"on port {d['port']}, PID {p.pid}")

    return processes


if __name__ == "__main__":
    procs = launch_fleet()
    print(f"\n[Launcher] {len(procs)} live drones running. Press Ctrl+C to stop all.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Launcher] Stopping all drones...")
        for p in procs:
            p.terminate()
