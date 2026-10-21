#!/usr/bin/env bash
# Stop the swarm. Matches exact process names (never the calling shell).
for name in vehicle_manager drone_brain mesh_observer target_mover gz_quarry camera_compressor perception_node parameter_bridge arducopter zenohd; do
    pkill -x "$name" 2>/dev/null
done
# launch processes and the GCS web server, excluding this script and its parent
for pat in "ros2 launch swarm_bringup" "rosbridge_websocket" "http.server 8080" "worlds/swarm.sdf"; do
    for pid in $(pgrep -f "$pat"); do
        [ "$pid" != "$$" ] && [ "$pid" != "$PPID" ] && kill "$pid" 2>/dev/null
    done
done
echo "swarm down"
