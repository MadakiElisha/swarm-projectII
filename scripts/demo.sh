#!/usr/bin/env bash
# Exhibition: start the swarm and the demo director in one go.
#
#   scripts/demo.sh [area]              light mode (real ArduPilot, simulated cameras) + GCS show mode
#   scripts/demo.sh [area] --gazebo --gui   the same in Gazebo (heavy; the Gazebo camera follows the action)
#
# The "operator" tab runs scripts/demo.py: press Enter there to start each round
# (r + Enter = reset now, q + Enter = quit). Stop everything: scripts/swarm_down.sh
exec "$(dirname "$0")/gz/up.sh" "${1:-eko}" --demo "${@:2}"
