# One image, one container PER DRONE: each container has its own ROS 2
# participant, so the swarm communicates over a real (virtual) network that
# you can degrade with tc/netem and partition with iptables.
FROM ros:jazzy-ros-base
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip python3-yaml iproute2 iptables iputils-ping \
    && pip3 install --break-system-packages pymavlink \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /swarm
COPY ros2_ws/src ros2_ws/src
RUN . /opt/ros/jazzy/setup.sh && cd ros2_ws && colcon build
COPY deploy/docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
