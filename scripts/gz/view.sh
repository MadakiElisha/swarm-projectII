#!/usr/bin/env bash
# Point the Gazebo window's camera (needs the GUI: scripts/gz/up.sh <area> --gazebo --gui).
#
#   scripts/gz/view.sh site            # look at the launch site and the drones on their pads
#   scripts/gz/view.sh follow D2       # chase camera behind drone D2 (it keeps following)
#   scripts/gz/view.sh follow quarry   # follow the target car
#   scripts/gz/view.sh free            # stop following
#
# Uses the Gazebo GUI's camera services (/gui/move_to/pose, /gui/follow, /gui/follow/offset).
set -u
: "${SWARM_GZ_INFO:?source sim/gz/<area>/env.sh first}"
cmd="${1:-site}"
call() { gz service -s "$1" --reqtype "$2" --reptype gz.msgs.Boolean --timeout 3000 --req "$3" > /dev/null; }

case "$cmd" in
  site)
    req=$(python3 - "$SWARM_GZ_INFO" <<'EOF'
import json, math, sys
d = json.load(open(sys.argv[1]))["drones"]
cx = sum(p["x"] for p in d) / len(d)
cy = sum(p["y"] for p in d) / len(d)
yaw, pitch, dist, h = math.radians(35), math.radians(32), 38.0, 24.0     # from the south-west, looking down
x, y = cx - dist * math.cos(yaw), cy - dist * math.sin(yaw)
cr, sr = 1.0, 0.0
cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
cy_, sy_ = math.cos(yaw / 2), math.sin(yaw / 2)
qw, qx = cp * cy_, -sp * sy_
qy, qz = sp * cy_, cp * sy_
print(f"pose: {{position: {{x: {x:.1f}, y: {y:.1f}, z: {h:.1f}}}, "
      f"orientation: {{x: {qx:.4f}, y: {qy:.4f}, z: {qz:.4f}, w: {qw:.4f}}}}}")
EOF
)
    call /gui/move_to/pose gz.msgs.GUICamera "$req" && echo "view: launch site" ;;
  follow)
    target="${2:-D1}"
    call /gui/follow gz.msgs.StringMsg "data: \"$target\"" &&
    call /gui/follow/offset gz.msgs.Vector3d "x: -12, y: -6, z: 7" && echo "view: following $target" ;;
  free)
    call /gui/follow gz.msgs.StringMsg 'data: ""' && echo "view: free camera" ;;
  *) echo "usage: $0 site | follow <D1|quarry> | free"; exit 1 ;;
esac
