#!/usr/bin/env bash
# Stop the swarm: the drones' software, autopilots, Gazebo, rosbridge and the GCS web server.
# Never matches the calling shell (exact names / installed-executable paths only).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
me=$$; parent=$PPID
killp() {   # kill every process whose full command line matches the extended regex $1
    for pid in $(pgrep -f -- "$1"); do
        [ "$pid" != "$me" ] && [ "$pid" != "$parent" ] && kill "$pid" 2>/dev/null
    done
}
# our ROS nodes run as "python3 .../install/<pkg>/lib/<pkg>/<node>" (comm is python3, so match the path)
for node in vehicle_manager drone_brain mesh_observer target_mover gz_quarry sim_world \
            camera_compressor perception_node image_replay; do
    killp "/lib/swarm_[a-z]+/${node}( |$)"
done
for name in parameter_bridge arducopter zenohd; do
    pkill -x "$name" 2>/dev/null
done
for pat in "ros2 launch swarm_bringup" "rosbridge_websocket" "rosapi_node" "http.server 8080" "worlds/swarm.sdf"; do
    killp "$pat"
done
sleep 2
# anything that ignored SIGTERM (some ROS nodes, rosbridge): force
for pat in "/lib/swarm_[a-z]+/[a-z_]+( |$)" "rosbridge_websocket" "rosapi_node" "worlds/swarm.sdf"; do
    for pid in $(pgrep -f -- "$pat"); do
        [ "$pid" != "$me" ] && [ "$pid" != "$parent" ] && kill -9 "$pid" 2>/dev/null
    done
done
pkill -9 -x arducopter 2>/dev/null
mkdir -p "$ROOT/logs/gz" && echo "$(date '+%F %T') swarm_down.sh run from $(tty 2>/dev/null)" >> "$ROOT/logs/gz/down.log"
echo "swarm down (Gazebo, autopilots and all swarm nodes stopped)"
