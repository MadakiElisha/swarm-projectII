#!/usr/bin/env bash
# Live regression gate + acceptance graphs.
# RUN ON A FRESH IDLE FLEET (restart T1, HEALTHY+45s, no prior clicks, charged batteries).
# Acceptance criteria (what we test against):
#   C1 telemetry from 5 drones within 8 s
#   C2 mesh topology with >=4 links
#   C3 5 auction replicas heartbeating
#   C4 SWARM request -> 5 assignments within 30 s
#   C5 PERIMETER_FORMED within 240 s with all |dist-R| < 120 m
#   C6 INTERCEPT request -> mover auto-starts within 10 s
set +u
source ~/swarm-projectII/swarm-project/ros2_ws/install/setup.bash
cd "$(dirname "$0")/.." || exit 1
mkdir -p reports
TS=$(date +%Y%m%d-%H%M%S)
CSV=reports/run_$TS.csv; PNG=reports/run_$TS.png

python3 scripts/regression_logger.py "$CSV" & LOGPID=$!
sleep 2
PASS=0; FAIL=0
ok(){ echo "PASS: $1"; PASS=$((PASS+1)); }
bad(){ echo "FAIL: $1"; FAIL=$((FAIL+1)); }
RTS=$(date +%s)

n=$(timeout 8 ros2 topic echo /swarm/telemetry --field label 2>/dev/null | sort -u | wc -l)
[ "$n" -ge 5 ] && ok "C1 telemetry x5" || bad "C1 telemetry labels=$n"
n=$(timeout 10 ros2 topic echo /swarm/mesh_topology --once 2>/dev/null | grep -cE "^[[:space:]]*-[[:space:]]")
[ "$n" -ge 4 ] && ok "C2 mesh links" || bad "C2 mesh topology"
n=$(timeout 4 ros2 topic echo /swarm/auction_alive --field data 2>/dev/null | sort -u | wc -l)
[ "$n" -ge 5 ] && ok "C3 5 replicas alive" || bad "C3 replicas=$n"

ros2 topic pub --once /swarm/task_requests swarm_interfaces/msg/TaskRequest \
  "{task_id: 'SWARM-REG-$RTS', lat: 6.537, lon: 3.388, description: 'regression'}" >/dev/null
n=$(timeout 30 ros2 topic echo /swarm/task_assignments --field assigned_to 2>/dev/null | sort -u | grep -c "D")
[ "$n" -ge 5 ] && ok "C4 SWARM 5 assignments" || bad "C4 assignments=$n"
ev=$(timeout 240 ros2 topic echo /swarm/mission_event --field event 2>/dev/null | grep -m1 PERIMETER_FORMED)
[ -n "$ev" ] && ok "C5 PERIMETER_FORMED" || bad "C5 no PERIMETER_FORMED"

ros2 topic pub --once /swarm/task_requests swarm_interfaces/msg/TaskRequest \
  "{task_id: 'INTERCEPT-REG-$RTS', lat: 6.535, lon: 3.392, description: 'regression'}" >/dev/null
n=$(timeout 10 ros2 topic echo /swarm/target_track --once 2>/dev/null | grep -c "lat")
[ "$n" -ge 1 ] && ok "C6 mover auto-start" || bad "C6 no target_track"

kill -TERM $LOGPID 2>/dev/null; wait $LOGPID 2>/dev/null
echo "$TS,$PASS,$FAIL" >> reports/history.csv
python3 scripts/regression_plot.py "$CSV" "$PNG" 2>&1
echo "=== REGRESSION: $PASS passed, $FAIL failed ==="
echo "graphs: $PNG   history: reports/history.csv"
[ "$FAIL" -eq 0 ]
