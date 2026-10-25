#!/usr/bin/env bash
# Exhibition: start the swarm and the demo director in one go.
#
#   scripts/demo.sh [area]                      patrol story: launch -> intrusion -> track -> home
#   scripts/demo.sh [area] --inspect            structure-inspection story: precision approach + standoff
#   scripts/demo.sh [area] --gazebo --gui       the same in Gazebo (heavy; the Gazebo camera follows)
#   scripts/demo.sh [area] --inspect --gazebo --gui
#
# Any other flags (e.g. --radius, --structure, --inspect-hold) are passed to scripts/demo.py.
# The "operator" tab runs the director: press Enter there to start each round
# (r + Enter = reset now, q + Enter = quit). Stop everything: scripts/swarm_down.sh
set -euo pipefail
AREA="eko"; UP_ARGS=(); DEMO_ARGS=()
first=1
for a in "$@"; do
  case "$a" in
    --gazebo|--gui) UP_ARGS+=("$a") ;;
    --inspect)      DEMO_ARGS+=(--mission inspect) ;;
    -*)             DEMO_ARGS+=("$a") ;;
    *)              if [ "$first" = 1 ]; then AREA="$a"; else DEMO_ARGS+=("$a"); fi ;;
  esac
  first=0
done
export SWARM_DEMO_ARGS="${DEMO_ARGS[*]}"
exec "$(dirname "$0")/gz/up.sh" "$AREA" --demo "${UP_ARGS[@]}"
