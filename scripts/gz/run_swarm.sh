#!/usr/bin/env bash
# Start Gazebo + one ArduCopter SITL per drone (real ArduPilot flight code, Gazebo physics).
#
#   source sim/gz/<area>/env.sh            # written by scripts/gz/make_world.py
#   scripts/gz/run_swarm.sh                # GUI
#   HEADLESS=1 scripts/gz/run_swarm.sh     # server only (CI / no display)
#   then:  ros2 launch swarm_bringup swarm_gazebo.launch.py
#
# Needs: ARDUPILOT_HOME (default ~/ardupilot) with build/sitl/bin/arducopter.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AP="${ARDUPILOT_HOME:-$HOME/ardupilot}"
BIN="${SITL_BIN:-$AP/build/sitl/bin/arducopter}"
P="$AP/Tools/autotest/default_params"
: "${SWARM_GZ_WORLD:?source sim/gz/<area>/env.sh first}"
: "${SWARM_GZ_INFO:?source sim/gz/<area>/env.sh first}"
[ -x "$BIN" ] || { echo "SITL binary not found: $BIN (build: cd $AP && ./waf configure --board sitl && ./waf copter)"; exit 1; }
LOG="$ROOT/logs/gz"; mkdir -p "$LOG"

GZ_ARGS="-r"
[ "${HEADLESS:-0}" = "1" ] && GZ_ARGS="-s -r"
echo "[gz] starting Gazebo: $SWARM_GZ_WORLD"
( setsid nohup gz sim $GZ_ARGS -v 2 "$SWARM_GZ_WORLD" > "$LOG/gazebo.log" 2>&1 < /dev/null & ) > /dev/null 2>&1
sleep 8

ORIGIN=$(python3 -c "import json,os;o=json.load(open(os.environ['SWARM_GZ_INFO']))['origin'];print(f'{o[0]},{o[1]}')")
python3 - "$SWARM_GZ_INFO" <<'EOF' > "$LOG/drones.txt"
import json, sys
for d in json.load(open(sys.argv[1]))["drones"]:
    print(d["id"], d["label"])
EOF
while read -r id label; do
    mkdir -p "$LOG/$label"
    echo "[gz] $label: SITL instance $id, JSON fdm port $((9002 + 10 * id)), MAVLink tcp:127.0.0.1:$((5760 + 10 * id))"
    # home = WORLD ORIGIN for every drone: SITL adds Gazebo's position to it
    ( cd "$LOG/$label" && setsid nohup "$BIN" -I"$id" --model JSON --sysid "$id" --speedup 1 \
        --defaults "$P/copter.parm,$P/gazebo-iris.parm,$ROOT/scripts/sitl_swarm.parm" \
        --home "$ORIGIN,0,0" > "$LOG/$label.log" 2>&1 < /dev/null & ) > /dev/null 2>&1
done < "$LOG/drones.txt"
echo "[gz] up. GPS lock takes ~30-60 s. Logs: $LOG"
echo "[gz] next: ros2 launch swarm_bringup swarm_gazebo.launch.py"
