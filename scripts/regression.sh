#!/usr/bin/env bash
# Regression gate. Two layers:
#   1. ROS-free scenarios (fast, deterministic, also run in CI)
#   2. acceptance test against a RUNNING ROS swarm (sim or SITL), with graphs
# Usage: scripts/regression.sh            (layer 1 + layer 2 if a swarm is up)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
mkdir -p reports
TS=$(date +%Y%m%d-%H%M%S)
FAIL=0

echo "=== layer 1: simulator scenarios ==="
( cd ros2_ws/src/swarm_common && python3 -m swarm_common.sim ) || FAIL=1

if timeout 5 ros2 topic list 2>/dev/null | grep -q /swarm/telemetry; then
    echo "=== layer 2: live ROS swarm acceptance ==="
    python3 scripts/ros_acceptance.py --csv "reports/run_$TS.csv" || FAIL=1
    python3 scripts/regression_plot.py "reports/run_$TS.csv" "reports/run_$TS.png" || true
else
    echo "(no running swarm: skipping layer 2 - start one with scripts/swarm_up.sh)"
fi
echo "$TS,$FAIL" >> reports/history.csv
[ "$FAIL" -eq 0 ] && echo "=== REGRESSION PASSED ===" || echo "=== REGRESSION FAILED ==="
exit "$FAIL"
