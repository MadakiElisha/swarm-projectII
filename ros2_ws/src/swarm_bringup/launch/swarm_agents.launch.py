from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

FLEET = {
    'D1': (6.5244, 3.3792), 'D2': (6.5299, 3.3850), 'D3': (6.5360, 3.3910),
    'D4': (6.5420, 3.3970), 'D5': (6.5480, 3.4030),
}

def generate_launch_description():
    reserve = LaunchConfiguration('reserve_pct')
    nodes = [
        Node(package='swarm_agents', executable='agent_node', name=f'agent_{d}',
             parameters=[{'drone_label': d, 'reserve_pct': reserve,
                          'home_lat': lat, 'home_lon': lon}])
        for d, (lat, lon) in FLEET.items()
    ]
    return LaunchDescription([DeclareLaunchArgument('reserve_pct', default_value='30.0')] + nodes)
