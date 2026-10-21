#!/usr/bin/env bash
# One-command bring-up.   scripts/swarm_up.sh [sim|sitl]     (default: sim)
#   sim : kinematic vehicles, no ArduPilot needed
#   sitl: one ArduCopter SITL per fleet.yaml drone (needs ARDUPILOT_HOME)
# Logs: logs/   GCS: http://localhost:8080
set -u
MODE="${1:-sim}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/logs"; mkdir -p "$LOG"
source "${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
source "$ROOT/ros2_ws/install/setup.bash"

if [ "$MODE" = "sitl" ]; then
    "$ROOT/scripts/start_sitl_fleet.sh" || exit 1
    echo "waiting 30 s for SITL EKF to settle"; sleep 30
    nohup ros2 launch swarm_bringup swarm_sitl.launch.py > "$LOG/swarm.log" 2>&1 &
else
    nohup ros2 launch swarm_bringup swarm_sim.launch.py > "$LOG/swarm.log" 2>&1 &
fi
if ros2 pkg prefix rosbridge_server >/dev/null 2>&1; then
    nohup ros2 launch rosbridge_server rosbridge_websocket_launch.xml > "$LOG/rosbridge.log" 2>&1 &
else
    echo "rosbridge_server not installed: GCS will not connect (apt install ros-jazzy-rosbridge-suite)"
fi
python3 "$ROOT/scripts/fleet_info.py" --json > "$ROOT/gcs/fleet.json"
( cd "$ROOT/gcs" && nohup python3 -m http.server 8080 > "$LOG/gcs.log" 2>&1 & )
sleep 10
echo "--- health ---"
n=$(timeout 8 ros2 topic echo /swarm/telemetry --field label 2>/dev/null | sort -u | wc -l)
echo "drones reporting: $n"
echo "GCS: http://localhost:8080   logs: $LOG   stop: scripts/swarm_down.sh"
