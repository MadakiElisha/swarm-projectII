#!/usr/bin/env bash
# One-command bring-up of the full sim stack. Logs: ~/.swarm_logs/
set +u
ROOT=~/swarm-projectII/swarm-project
WS=$ROOT/ros2_ws
LOG=$HOME/.swarm_logs
mkdir -p "$LOG"
source /opt/ros/jazzy/setup.bash
source $WS/install/setup.bash

pgrep -x zenohd >/dev/null || { nohup ros2 run rmw_zenoh_cpp rmw_zenohd >"$LOG/zenohd.log" 2>&1 & echo "zenohd: started"; }

if ! pgrep -f arducopter >/dev/null; then
  nohup "$ROOT/scripts/start_sitl_fleet.sh" >"$LOG/fleet.log" 2>&1 &
  echo -n "fleet: waiting HEALTHY "
  c=0
  for i in $(seq 1 90); do c=$(grep -c HEALTHY "$LOG/fleet.log" 2>/dev/null); [ "$c" -ge 5 ] && break; sleep 1; done
  echo "($c/5) + 45s settle"; sleep 45
else echo "fleet: already up"; fi

nohup ros2 launch swarm_bringup swarm_real.launch.py      >"$LOG/real.log" 2>&1 &
nohup ros2 launch swarm_bringup swarm_agents.launch.py    >"$LOG/agents.log" 2>&1 &
nohup ros2 launch swarm_bringup swarm_perception.launch.py>"$LOG/perception.log" 2>&1 &
nohup ros2 launch rosbridge_server rosbridge_websocket_launch.xml >"$LOG/rosbridge.log" 2>&1 &
( cd "$ROOT/gcs" && nohup python3 -m http.server 8080 >"$LOG/gcs.log" 2>&1 & )
sleep 8
echo "--- health ---"
n=$(timeout 8 ros2 topic echo /swarm/telemetry --field label 2>/dev/null | sort -u | wc -l); echo "telemetry drones: $n/5"
n=$(timeout 4 ros2 topic echo /swarm/auction_alive --field data 2>/dev/null | sort -u | wc -l); echo "auction replicas: $n/5"
echo "GCS: http://localhost:8080   logs: $LOG"
