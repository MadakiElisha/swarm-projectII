"""Per-drone camera replay + YOLOv8, one pair per fleet.yaml drone.

perception_node runs inside the vision venv (ultralytics) when one exists;
on hardware image_replay is replaced by the real camera driver publishing
/swarm/<label>/camera/compressed.
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from swarm_common.config import load_fleet

MODEL = 'yolov8n.pt'      # resolved/downloaded by ultralytics; no weights in the repo


def _venv_python():
    env = os.environ.get('SWARM_VISION_PY')
    cands = [env] if env else []
    cands += [os.path.expanduser('~/swarm_venv/bin/python'),
              os.path.join(os.getcwd(), 'venv', 'bin', 'python')]
    return next((p for p in cands if p and os.path.exists(p)), None)


def _setup(context):
    fleet = load_fleet(LaunchConfiguration('fleet_file').perform(context) or None)
    py = _venv_python()
    nodes = []
    for i, d in enumerate(fleet.drones):
        lab = d.label
        nodes.append(Node(package='swarm_perception', executable='image_replay',
                          name=f'image_replay_{lab.lower()}',
                          parameters=[{'drone_label': lab, 'frame_offset': i * 3, 'rate_hz': 0.5}]))
        param = {'model_path': MODEL, 'min_confidence': 0.5, 'classes': ['person'],
                 'drone_label': lab}
        if py:
            nodes.append(Node(executable=py, arguments=['-m', 'swarm_perception.perception_node'],
                              name=f'perception_{lab.lower()}', parameters=[param]))
        else:
            nodes.append(Node(package='swarm_perception', executable='perception_node',
                              name=f'perception_{lab.lower()}', parameters=[param]))
    return nodes


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument('fleet_file', default_value=''),
                              OpaqueFunction(function=_setup)])
