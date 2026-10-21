"""Operator side: rosbridge for the web GCS + mesh visualisation. Optional.

The swarm runs without any of this; it only lets a human watch and task it.
Serve the page with:  cd gcs && python3 -m http.server 8080
"""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(AnyLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('rosbridge_server'), 'launch', 'rosbridge_websocket_launch.xml']))),
        Node(package='swarm_mesh', executable='mesh_observer', name='mesh_observer_gcs'),
    ])
