"""Swarm in Gazebo: real ArduPilot SITL + Gazebo physics + Gazebo cameras.

    source sim/gz/<area>/env.sh && scripts/gz/run_swarm.sh     # Gazebo + SITL
    SWARM_FLEET=areas/<area>/fleet.yaml ros2 launch swarm_bringup swarm_gazebo.launch.py

Per drone: vehicle_manager (MAVLink to its SITL), drone_brain, and - when the
world has cameras - Gazebo image -> JPEG -> YOLO perception, i.e. the same
camera topics a real drone publishes. Brains emulate radio range/loss (one
machine); everything else is what flies on hardware.

Arguments: perception:=true|false  model:=<yolo weights>  loss:=0.1
"""
import json
import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(__file__))
from _fleet_nodes import drone_nodes  # noqa: E402

from swarm_common.config import load_fleet  # noqa: E402


def _setup(context):
    lc = lambda k: LaunchConfiguration(k).perform(context)  # noqa: E731
    fleet = load_fleet(lc('fleet_file') or None)
    info_path = os.environ.get('SWARM_GZ_INFO', '')
    info = json.load(open(info_path)) if info_path and os.path.isfile(info_path) else {}
    cams = bool(info.get('camera'))
    want_perception = lc('perception').lower() == 'true' and cams
    nodes = []
    for d in fleet.drones:
        # no camera -> let brains "see" the scripted target directly; with cameras they must detect it
        nodes += drone_nodes(d.id, 'mavlink', lc('fleet_file'), '', True, float(lc('loss')),
                             sim_target=not want_perception)
    if cams:
        topics = [f'/swarm/{d.label}/camera/image@sensor_msgs/msg/Image[gz.msgs.Image' for d in fleet.drones]
        nodes.append(Node(package='ros_gz_bridge', executable='parameter_bridge', name='gz_camera_bridge',
                          arguments=topics, output='log'))
        for d in fleet.drones:
            nodes.append(Node(package='swarm_perception', executable='camera_compressor',
                              name=f'camera_{d.label.lower()}',
                              parameters=[{'drone_label': d.label, 'max_hz': 3.0}]))
            if want_perception:
                nodes.append(Node(package='swarm_perception', executable='perception_node',
                                  name=f'perception_{d.label.lower()}',
                                  parameters=[{'drone_label': d.label, 'model_path': lc('model'),
                                               'min_confidence': 0.35,
                                               'classes': ['person', 'pedestrian', 'people', 'car', 'van',
                                                           'truck', 'bus']}]))
    nodes.append(Node(package='swarm_mesh', executable='mesh_observer', name='mesh_observer'))
    nodes.append(Node(package='swarm_tasks', executable='target_mover', name='target_mover'))
    if info.get('target'):
        nodes.append(Node(package='swarm_tasks', executable='gz_quarry', name='gz_quarry'))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('fleet_file', default_value=''),
        DeclareLaunchArgument('loss', default_value='0.05'),
        DeclareLaunchArgument('perception', default_value='true'),
        DeclareLaunchArgument('model', default_value=os.path.expanduser('~/swarm_models/visdrone_yolo11s.pt')),
        OpaqueFunction(function=_setup),
    ])
