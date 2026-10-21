#!/usr/bin/env python3
"""Probe a SITL MAVLink stream: verify position + battery fields arrive."""
import sys
from pymavlink import mavutil

port = int(sys.argv[1]) if len(sys.argv) > 1 else 14551
conn = mavutil.mavlink_connection(f'udpin:127.0.0.1:{port}')
print(f'[probe] waiting for heartbeat on udpin:{port} ...')
conn.wait_heartbeat(timeout=30)
print(f'[probe] heartbeat OK (sysid={conn.target_system})')

seen_gps = seen_batt = False
while not (seen_gps and seen_batt):
    m = conn.recv_match(type=['GLOBAL_POSITION_INT', 'SYS_STATUS'],
                        blocking=True, timeout=30)
    if m is None:
        print('[probe] TIMEOUT waiting for telemetry')
        break
    if m.get_type() == 'GLOBAL_POSITION_INT':
        print(f'[probe] GPS: lat={m.lat/1e7:.6f} lon={m.lon/1e7:.6f}')
        seen_gps = True
    else:
        print(f'[probe] BATTERY: remaining={m.battery_remaining}%')
        seen_batt = True
print('[probe] done')
