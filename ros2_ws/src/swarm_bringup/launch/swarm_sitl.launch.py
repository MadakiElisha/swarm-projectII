"""The whole swarm on real ArduPilot flight code (SITL, ArduPilot's own physics), no Gazebo.

    scripts/start_sitl_fleet.sh areas/eko/fleet.yaml      # one ArduCopter per drone, on its own pad
    SWARM_FLEET=areas/eko/fleet.yaml ros2 launch swarm_bringup swarm_sitl.launch.py

Per drone: vehicle_manager (safety FSM -> MAVLink -> its autopilot) + drone_brain,
exactly what runs on a drone's companion computer. sim_world plays the cameras:
it turns each drone's real pose into the detections its YOLO would report
(people / vehicles / flood water) on /swarm/<D>/detections. Light enough for a
laptop; watch it in the web GCS.

Arguments: sim_camera:=true  flood:=false  loss:=0.05  link_emulation:=true
"""
import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(__file__))
from _fleet_nodes import fleet_nodes  # noqa: E402


def _setup(context):
    lc = lambda k: LaunchConfiguration(k).perform(context)  # noqa: E731
    cam = lc('sim_camera').lower() == 'true'
    # with simulated cameras the brains must DETECT the target like a real drone would;
    # without them they are handed its position (simulate_target_sensor)
    nodes = fleet_nodes('mavlink', lc('fleet_file'),
                        link_emulation=lc('link_emulation').lower() == 'true',
                        loss=float(lc('loss')), sim_target=not cam, seed=int(lc('seed')))
    nodes.append(Node(package='swarm_mesh', executable='mesh_observer', name='mesh_observer'))
    nodes.append(Node(package='swarm_tasks', executable='target_mover', name='target_mover'))
    if cam:
        nodes.append(Node(package='swarm_tasks', executable='sim_world', name='sim_world', output='screen',
                          parameters=[{'fleet_file': lc('fleet_file'), 'flood': lc('flood').lower() == 'true'}]))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('fleet_file', default_value=''),
        DeclareLaunchArgument('link_emulation', default_value='true'),
        DeclareLaunchArgument('loss', default_value='0.05'),
        DeclareLaunchArgument('seed', default_value='0'),
        DeclareLaunchArgument('sim_camera', default_value='true'),
        DeclareLaunchArgument('flood', default_value='false'),
        OpaqueFunction(function=_setup),
    ])
