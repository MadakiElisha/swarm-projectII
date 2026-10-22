#!/usr/bin/env bash
# Start EVERYTHING for a Gazebo swarm session, each part in its own terminal tab:
#
#   scripts/gz/up.sh [area]          (default area: eko)
#
#   tab 1 "gazebo"   Gazebo (GUI) + one ArduCopter SITL per drone
#   tab 2 "swarm"    the drones' software (vehicle managers, brains, cameras, YOLO)
#   tab 3 "status"   live board: link / FSM / altitude / battery / task / detections
#   tab 4 "gcs"      rosbridge + web GCS on http://localhost:8080 (opens the browser)
#   tab 5 "operator" a shell ready for scripts/mission.py and the acceptance test
#
# Stop everything: scripts/swarm_down.sh
# Uses gnome-terminal tabs; falls back to a tmux session "swarm" (tmux attach -t swarm).
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AREA="${1:-eko}"
VENV="${SWARM_VENV:-$HOME/swarm_venv}"
GZ_ENV="$ROOT/sim/gz/$AREA/env.sh"
[ -f "$GZ_ENV" ] || { echo "no Gazebo world for '$AREA': python3 scripts/gz/make_world.py --fleet areas/$AREA/fleet.yaml"; exit 1; }

mkdir -p "$ROOT/logs/gz"
SESSION_ENV="$ROOT/logs/gz/session_env.sh"
cat > "$SESSION_ENV" <<EOF
[ -f ~/.bashrc ] && source ~/.bashrc
source "${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
[ -f "$VENV/bin/activate" ] && source "$VENV/bin/activate"
source "$ROOT/ros2_ws/install/setup.bash"
source "$GZ_ENV"
export SWARM_FLEET="$ROOT/areas/$AREA/fleet.yaml"
export ARDUPILOT_HOME="\${ARDUPILOT_HOME:-\$HOME/ardupilot}" ARDUPILOT_GAZEBO="\${ARDUPILOT_GAZEBO:-\$HOME/ardupilot_gazebo}"
cd "$ROOT"
EOF

# preflight (stop on hard failures)
( source "$SESSION_ENV" >/dev/null 2>&1; python3 scripts/check.py "$AREA" ) || {
  echo; if [ -n "${SWARM_YES:-}" ]; then a=y; else read -r -p "preflight found problems - start anyway? [y/N] " a; fi
  [ "$a" = y ] || exit 1; }

"$ROOT/scripts/swarm_down.sh" >/dev/null 2>&1 || true
sleep 2

T1="scripts/gz/run_swarm.sh && echo && echo 'Gazebo + autopilots up. SITL logs: logs/gz/D*.log' && sleep 3 && tail -n 3 -F logs/gz/D1.log"
T2="echo 'waiting 25 s for the autopilots...'; sleep 25; ros2 launch swarm_bringup swarm_gazebo.launch.py"
T3="sleep 30; python3 scripts/swarm_status.py"
T4="(ros2 launch rosbridge_server rosbridge_websocket_launch.xml > logs/gz/rosbridge.log 2>&1 &); python3 scripts/fleet_info.py --json > gcs/fleet.local.json; (sleep 4; xdg-open http://localhost:8080 >/dev/null 2>&1 &); cd gcs && python3 -m http.server 8080"
T5="cat docs/RUNBOOK.md | sed -n '/## 4/,/## 5/p' | head -60"

# one small script per tab (no quoting gymnastics)
names=(gazebo swarm status gcs operator)
cmds=("$T1" "$T2" "$T3" "$T4" "$T5")
for i in "${!names[@]}"; do
  f="$ROOT/logs/gz/tab_${names[$i]}.sh"
  printf 'source %q\n%s\nexec bash --rcfile %q\n' "$SESSION_ENV" "${cmds[$i]}" "$SESSION_ENV" > "$f"
done

if command -v gnome-terminal >/dev/null && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && [ -z "${SWARM_TMUX:-}" ]; then
  # run from inside a GNOME Terminal, --tab opens tabs in this window
  for n in "${names[@]}"; do
    gnome-terminal --tab --title="$n" -- bash "$ROOT/logs/gz/tab_$n.sh"
    sleep 0.3
  done
  echo "opened tabs: ${names[*]}   (stop everything: scripts/swarm_down.sh)"
else
  command -v tmux >/dev/null || { echo "need gnome-terminal or tmux (sudo apt install tmux)"; exit 1; }
  tmux kill-session -t swarm 2>/dev/null || true
  tmux new-session -d -s swarm -n gazebo "bash $ROOT/logs/gz/tab_gazebo.sh"
  for n in swarm status gcs operator; do
    tmux new-window -t swarm: -n "$n" "bash $ROOT/logs/gz/tab_$n.sh"
  done
  echo "tmux session 'swarm': tmux attach -t swarm   (Ctrl-b n / p = next / previous tab)"
fi
