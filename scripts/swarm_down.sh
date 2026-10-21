#!/usr/bin/env bash
pkill -f "swarm_bringup" ; pkill -f "vehicle_manager|drone_brain|mesh_observer|target_mover"
pkill -f rosbridge_websocket; pkill -f "http.server 8080"; pkill -f "arducopter" ; pkill -x zenohd
echo "swarm down"
