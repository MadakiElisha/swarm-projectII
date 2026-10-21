#!/usr/bin/env bash
set -e
source /opt/ros/jazzy/setup.bash
source /swarm/ros2_ws/install/setup.bash
case "${ROLE:-drone}" in
  drone)
    # real network between containers -> no link emulation
    exec ros2 launch swarm_bringup drone.launch.py drone_id:="${DRONE_ID:?}" \
         backend:="${BACKEND:-sim}" mavlink_url:="${MAVLINK_URL:-}" \
         simulate_target_sensor:=true ;;
  gcs)
    exec bash -c "ros2 run swarm_mesh mesh_observer & ros2 run swarm_tasks target_mover & wait" ;;
  *) exec "$@" ;;
esac
