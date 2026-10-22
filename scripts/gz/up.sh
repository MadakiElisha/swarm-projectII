#!/usr/bin/env bash
# Start a whole swarm session, each part in its own terminal tab.
#
#   scripts/gz/up.sh [area]              real ArduPilot (SITL) + simulated cameras, no Gazebo  (light, default)
#   scripts/gz/up.sh [area] --gazebo    + Gazebo physics/rendering, YOLO on 2 rendered cameras (heavy)
#   scripts/gz/up.sh [area] --gazebo --gui   ... with the Gazebo window
#
#   tab "autopilots"  one ArduCopter per drone (+ Gazebo in --gazebo mode)
#   tab "swarm"       the drones' software (vehicle managers, brains, cameras)
#   tab "status"      live board: link / FSM / altitude / battery / task / detections
#   tab "gcs"         rosbridge + web GCS on http://localhost:8080 (opens the browser)
#   tab "operator"    a shell ready for scripts/mission.py and the acceptance test
#
# Stop everything: scripts/swarm_down.sh
# Uses gnome-terminal tabs; falls back to a tmux session "swarm" (tmux attach -t swarm).
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AREA="eko"; MODE=sitl; GUI=0
for a in "$@"; do
  case "$a" in --gazebo) MODE=gazebo;; --gui) GUI=1;; -*) echo "unknown option $a"; exit 1;; *) AREA="$a";; esac
done
VENV="${SWARM_VENV:-$HOME/swarm_venv}"
GZ_ENV="$ROOT/sim/gz/$AREA/env.sh"
[ -f "$ROOT/areas/$AREA/fleet.yaml" ] || { echo "no area '$AREA': python3 scripts/make_area.py $AREA --drones 5"; exit 1; }
if [ "$MODE" = gazebo ] && [ ! -f "$GZ_ENV" ]; then
  echo "no Gazebo world for '$AREA': python3 scripts/gz/make_world.py --fleet areas/$AREA/fleet.yaml"; exit 1
fi

mkdir -p "$ROOT/logs/gz"
SESSION_ENV="$ROOT/logs/gz/session_env.sh"
cat > "$SESSION_ENV" <<EOF
[ -f ~/.bashrc ] && source ~/.bashrc
source "${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
[ -f "$VENV/bin/activate" ] && source "$VENV/bin/activate"
source "$ROOT/ros2_ws/install/setup.bash"
[ -f "$GZ_ENV" ] && source "$GZ_ENV"
export SWARM_FLEET="$ROOT/areas/$AREA/fleet.yaml"
# the standard ROS 2 middleware, whatever ~/.bashrc says (rmw_zenoh needs a router), on our own channel
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=\${SWARM_DOMAIN:-7}
export ARDUPILOT_HOME="\${ARDUPILOT_HOME:-\$HOME/ardupilot}" ARDUPILOT_GAZEBO="\${ARDUPILOT_GAZEBO:-\$HOME/ardupilot_gazebo}"
cd "$ROOT"
EOF

# preflight (stop on hard failures)
( source "$SESSION_ENV" >/dev/null 2>&1; python3 scripts/check.py "$AREA" $([ "$MODE" = gazebo ] && echo --gazebo) ) || {
  echo; if [ -n "${SWARM_YES:-}" ]; then a=y; else read -r -p "preflight found problems - start anyway? [y/N] " a; fi
  [ "$a" = y ] || exit 1; }

"$ROOT/scripts/swarm_down.sh" >/dev/null 2>&1 || true
( source "$SESSION_ENV" >/dev/null 2>&1; ros2 daemon stop >/dev/null 2>&1 ) || true
sleep 2

if [ "$MODE" = gazebo ]; then
  HL=$([ "$GUI" = 1 ] && echo 0 || echo 1)
  T1="HEADLESS=$HL scripts/gz/run_swarm.sh && echo && echo 'Leave this tab open. Autopilot logs: logs/gz/D*.log'"
  T2="echo 'waiting 25 s for the autopilots...'; sleep 25; ros2 launch swarm_bringup swarm_gazebo.launch.py"
else
  T1="scripts/start_sitl_fleet.sh \"\$SWARM_FLEET\" && echo && echo 'Leave this tab open. Autopilot logs: logs/sitl/D*.log'"
  T2="echo 'waiting 15 s for the autopilots...'; sleep 15; ros2 launch swarm_bringup swarm_sitl.launch.py flood:=$([ -n "${SWARM_FLOOD:-}" ] && echo true || echo false)"
fi
T3="sleep 30; python3 scripts/swarm_status.py"
T4="(ros2 launch rosbridge_server rosbridge_websocket_launch.xml > logs/gz/rosbridge.log 2>&1 &); python3 scripts/fleet_info.py --json > gcs/fleet.local.json; (sleep 4; xdg-open http://localhost:8080 >/dev/null 2>&1 &); cd gcs && python3 -m http.server 8080"
T5="cat docs/RUNBOOK.md | sed -n '/## 4/,/## 5/p' | head -60"

# one small script per tab (no quoting gymnastics)
names=(autopilots swarm status gcs operator)
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
  tmux new-session -d -s swarm -n autopilots "bash $ROOT/logs/gz/tab_autopilots.sh"
  for n in swarm status gcs operator; do
    tmux new-window -t swarm: -n "$n" "bash $ROOT/logs/gz/tab_$n.sh"
  done
  echo "tmux session 'swarm': tmux attach -t swarm   (Ctrl-b n / p = next / previous tab)"
fi
