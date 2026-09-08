#!/usr/bin/env python3
"""Records telemetry/status/events to CSV during a regression run."""
import csv, signal, sys, time
import rclpy
from rclpy.node import Node
from swarm_interfaces.msg import DroneTelemetry, MissionStatus, MissionEvent

running = True
def stop(sig, frame):
    global running; running = False

def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    out = sys.argv[1] if len(sys.argv) > 1 else 'reports/run.csv'
    rclpy.init()
    n = Node('regression_logger')
    f = open(out, 'w', newline='')
    w = csv.writer(f)
    w.writerow(['t', 'kind', 'label', 'alt', 'batt', 'phase', 'dist', 'event'])
    t0 = time.time()
    def row(*a):
        # pad to exactly 7 args so [t] + args = 8 columns (matches header)
        args = list(a) + [''] * (7 - len(a))
        w.writerow([f'{time.time() - t0:.2f}'] + args)
        f.flush()
    n.create_subscription(DroneTelemetry, '/swarm/telemetry',
        lambda m: row('telem', m.label, f'{m.alt:.1f}', f'{m.battery_pct:.0f}', '', '', ''), 10)
    n.create_subscription(MissionStatus, '/swarm/mission_status',
        lambda m: row('status', m.label, '', '', m.phase, f'{m.dist_to_slot_m:.0f}', ''), 10)
    n.create_subscription(MissionEvent, '/swarm/mission_event',
        lambda m: row('event', '', '', '', '', '', m.event), 10)
    try:
        while running and rclpy.ok():
            rclpy.spin_once(n, timeout_sec=0.5)
    except Exception:
        pass
    finally:
        f.close()
        try:
            n.destroy_node()
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()
