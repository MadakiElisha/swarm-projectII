"""Real-physics swarm: one mavlink_bridge per SITL daemon (TCP endpoints),
plus mesh_builder and task_auctioneer. The swarm brain is unchanged."""
from launch import LaunchDescription
from launch_ros.actions import Node

# SITL instance i exposes MAVLink on tcp 5760+10*i
FLEET = [
    ("D1", "tcp:127.0.0.1:5770"),
    ("D2", "tcp:127.0.0.1:5780"),
    ("D3", "tcp:127.0.0.1:5790"),
    ("D4", "tcp:127.0.0.1:5800"),
    ("D5", "tcp:127.0.0.1:5810"),
]


def generate_launch_description():
    nodes = []
    for label, url in FLEET:
        nodes.append(Node(
            package='swarm_mavlink',
            executable='mavlink_bridge',
            name=f'bridge_{label.lower()}',
            parameters=[{'drone_label': label, 'mavlink_url': url}],
        ))

    nodes.append(Node(package='swarm_mesh', executable='mesh_builder', name='mesh_builder'))
    nodes.append(Node(package='swarm_tasks', executable='task_auctioneer', name='task_auctioneer'))

    return LaunchDescription(nodes)
