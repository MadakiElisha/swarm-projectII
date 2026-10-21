"""Whole swarm on one computer with the kinematic sim backend (no SITL needed).

    ros2 launch swarm_bringup swarm_sim.launch.py loss:=0.2

Each drone = its own vehicle_manager + drone_brain. Brains emulate radio
range/loss because on one machine every packet reaches everyone.
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
    nodes = fleet_nodes('sim', lc('fleet_file'), link_emulation=True, loss=float(lc('loss')),
                        sim_target=True, seed=int(lc('seed')))
    nodes.append(Node(package='swarm_mesh', executable='mesh_observer', name='mesh_observer'))
    nodes.append(Node(package='swarm_tasks', executable='target_mover', name='target_mover'))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('fleet_file', default_value=''),
        DeclareLaunchArgument('loss', default_value='0.1', description='emulated packet loss'),
        DeclareLaunchArgument('seed', default_value='0'),
        OpaqueFunction(function=_setup),
    ])
