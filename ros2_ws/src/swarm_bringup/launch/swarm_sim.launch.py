"""Launch the full simulated swarm: 5 fake drones + mesh builder + auctioneer."""
from launch import LaunchDescription
from launch_ros.actions import Node

FLEET = [
    ("D1", 6.5244, 3.3792),
    ("D2", 6.5300, 3.3850),
    ("D3", 6.5360, 3.3910),
    ("D4", 6.5420, 3.3970),
    ("D5", 6.5480, 3.4030),
]


def generate_launch_description():
    nodes = []
    for label, lat, lon in FLEET:
        nodes.append(Node(
            package='swarm_mavlink',
            executable='telemetry_publisher',
            name=f'telemetry_{label.lower()}',
            parameters=[{'drone_label': label, 'start_lat': lat, 'start_lon': lon}],
        ))

    nodes.append(Node(package='swarm_mesh', executable='mesh_builder', name='mesh_builder'))
    nodes.append(Node(package='swarm_tasks', executable='task_auctioneer', name='task_auctioneer'))

    return LaunchDescription(nodes)
