"""ONE drone: what runs on each drone's companion computer (or one container).

    ros2 launch swarm_bringup drone.launch.py drone_id:=3 backend:=mavlink \
        mavlink_url:=serial:///dev/ttyTHS1:921600

On real hardware keep link_emulation:=false - the mesh radio decides who
hears whom.
"""
import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration

sys.path.insert(0, os.path.dirname(__file__))
from _fleet_nodes import drone_nodes  # noqa: E402


def _setup(context):
    lc = lambda k: LaunchConfiguration(k).perform(context)  # noqa: E731
    return drone_nodes(int(lc('drone_id')), lc('backend'), lc('fleet_file'), lc('mavlink_url'),
                       lc('link_emulation').lower() == 'true', float(lc('loss')),
                       lc('simulate_target_sensor').lower() == 'true')


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('drone_id', default_value='1'),
        DeclareLaunchArgument('backend', default_value='mavlink'),
        DeclareLaunchArgument('mavlink_url', default_value=''),
        DeclareLaunchArgument('fleet_file', default_value=''),
        DeclareLaunchArgument('link_emulation', default_value='false'),
        DeclareLaunchArgument('loss', default_value='0.0'),
        DeclareLaunchArgument('simulate_target_sensor', default_value='false'),
        OpaqueFunction(function=_setup),
    ])
