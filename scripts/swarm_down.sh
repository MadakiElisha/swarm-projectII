#!/usr/bin/env bash
pkill -f "swarm_real.launch"; pkill -f "swarm_agents.launch"; pkill -f "swarm_perception.launch"
pkill -f rosbridge_websocket; pkill -f "http.server 8080"; pkill -f arducopter; pkill -x zenohd
echo "swarm down"
