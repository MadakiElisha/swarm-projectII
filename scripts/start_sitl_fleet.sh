#!/usr/bin/env bash
# Start one ArduCopter SITL per drone in fleet.yaml (no MAVProxy needed).
#   ARDUPILOT_HOME=~/ardupilot scripts/start_sitl_fleet.sh [fleet.yaml]
# SITL instance i listens on tcp 5760+10*i, so fleet.yaml's
# tcp:127.0.0.1:5770 -> instance 1, 5780 -> instance 2, ...
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AP="${ARDUPILOT_HOME:-$HOME/ardupilot}"
BIN="${SITL_BIN:-$AP/build/sitl/bin/arducopter}"
DEFAULTS="${SITL_DEFAULTS:-$AP/Tools/autotest/default_params/copter.parm}"
LOGDIR="$ROOT/logs/sitl"
mkdir -p "$LOGDIR"
[ -x "$BIN" ] || { echo "arducopter SITL binary not found at $BIN (set ARDUPILOT_HOME or SITL_BIN)"; exit 1; }

pkill -f "$BIN" 2>/dev/null; sleep 1
n=0
while read -r id label lat lon url; do
    port="${url##*:}"
    case "$url" in tcp:127.0.0.1:*|tcp:localhost:*) ;; *) echo "skip $label: $url is not a local SITL url"; continue;; esac
    inst=$(( (port - 5760) / 10 ))
    echo "[fleet] $label: SITL instance $inst sysid $id tcp:$port home $lat,$lon"
    ( cd "$LOGDIR" && setsid nohup "$BIN" -I"$inst" --sysid "$id" --model + --speedup 1 \
        --defaults "$DEFAULTS" --home "$lat,$lon,20,0" > "$LOGDIR/$label.log" 2>&1 < /dev/null & ) \
        > /dev/null 2>&1    # never inherit the caller's stdout (keeps pipes like | tee from hanging)
    n=$((n + 1))
    sleep 0.5
done < <(python3 "$ROOT/scripts/fleet_info.py" "${1:-}")

for attempt in 1 2 3 4 5 6; do
    sleep 3
    alive=$(pgrep -fc "$BIN" || true)
    echo "[fleet] check $attempt: $alive/$n SITL processes"
    [ "$alive" -ge "$n" ] && { echo "[fleet] HEALTHY ($n drones). EKF needs ~30 s before arming."; exit 0; }
done
echo "[fleet] not all SITL instances are running; see $LOGDIR"; exit 1
