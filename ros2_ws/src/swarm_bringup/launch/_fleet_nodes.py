"""Shared helper for launch files: per-drone nodes generated from fleet.yaml."""
from launch_ros.actions import Node

from swarm_common.config import load_fleet


def drone_nodes(drone_id, backend, fleet_file='', mavlink_url='', link_emulation=False,
                loss=0.0, sim_target=False, seed=0):
    """vehicle_manager + drone_brain for ONE drone (what runs on its companion computer)."""
    label = f'D{drone_id}'
    common = {'drone_id': int(drone_id), 'fleet_file': fleet_file}
    return [
        Node(package='swarm_vehicle', executable='vehicle_manager',
             name=f'vehicle_{label.lower()}', output='screen',
             parameters=[dict(common, backend=backend, mavlink_url=mavlink_url)]),
        Node(package='swarm_agents', executable='drone_brain',
             name=f'brain_{label.lower()}', output='screen',
             parameters=[dict(common, link_emulation=bool(link_emulation), emu_loss=float(loss),
                              simulate_target_sensor=bool(sim_target), seed=int(seed))]),
    ]


def fleet_nodes(backend, fleet_file='', link_emulation=True, loss=0.0, sim_target=True, seed=0):
    fleet = load_fleet(fleet_file or None)
    nodes = []
    for d in fleet.drones:
        nodes += drone_nodes(d.id, backend, fleet_file, '', link_emulation, loss, sim_target, seed)
    return nodes
