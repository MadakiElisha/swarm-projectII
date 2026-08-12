#!/bin/bash
# Phase 7B - Launch N real ArduPilot SITL instances from one terminal.
#
# This does NOT change the architecture - each instance is still a
# fully separate, independent OS process (same as running each in
# its own terminal manually). This script just automates the
# launching; it doesn't centralize anything about how they behave.
#
# Output for each drone goes to its own log file (logs/droneN.log)
# instead of an interactive console, since we're not manually typing
# arm/takeoff commands into most of them during normal mesh testing.
# If you need the interactive console for a specific drone (e.g. to
# manually arm/takeoff it), launch that one separately with
# --console in its own terminal instead, alongside this script.
#
# Usage: ./launch_fleet.sh <num_drones>
# Example: ./launch_fleet.sh 6

set -e

NUM_DRONES=${1:-2}
ARDUPILOT_DIR=~/ardupilot
LOG_DIR=~/swarm-project/logs
BASE_MAVLINK_PORT=14551

mkdir -p "$LOG_DIR"

echo "Launching $NUM_DRONES real ArduPilot SITL instances (Gazebo must already be running)..."

for ((i=0; i<NUM_DRONES; i++)); do
    SYSID=$((i + 1))
    PORT=$((BASE_MAVLINK_PORT + i))
    LOGFILE="$LOG_DIR/drone${SYSID}.log"

    echo "  Drone $SYSID: instance -I$i, sysid $SYSID, MAVLink out port $PORT, log: $LOGFILE"

    (cd "$ARDUPILOT_DIR" && \
        ./Tools/autotest/sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON \
        -I"$i" --sysid "$SYSID" --out=127.0.0.1:"$PORT" --no-rebuild \
        < /dev/null > "$LOGFILE" 2>&1 --daemon &)

    sleep 10  # sim_vehicle.py runs its own "kill existing tasks" cleanup on
              # startup, which isn't cleanly scoped to just its own instance -
              # launching too close together causes each new instance to kill
              # the ones just started before it. Give each one time to fully
              # come up first.
done

echo ""
echo "All $NUM_DRONES instances launching in the background."
echo "Check progress with: tail -f $LOG_DIR/drone1.log  (or drone2.log, etc.)"
echo "Check all are still running with: ps aux | grep arducopter"
echo "Stop everything with: pkill -f sim_vehicle.py; pkill -f arducopter; pkill -f mavproxy"
