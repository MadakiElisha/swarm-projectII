"""Perception add-on, namespaced per drone.

perception_node runs inside the vision venv so ultralytics stays confined;
image_replay + task_generator use system ROS. On hardware, image_replay is
replaced by real per-drone camera drivers publishing the same topics.
"""
import os
from launch import LaunchDescription
from launch_ros.actions import Node

LABELS = ['D1', 'D2', 'D3', 'D4', 'D5']

MODEL = 'yolov8n.pt'  # resolved/downloaded by ultralytics; no weights in repo

_VENV_CANDIDATES = [
    os.path.expanduser('~/swarm_venv/bin/python'),
    os.path.expanduser('~/swarm-projectII/swarm-project/venv/bin/python'),
    os.path.expanduser('~/swarm-project/venv/bin/python'),
]
VENV_PY = next((p for p in _VENV_CANDIDATES if os.path.exists(p)), None)

PERCEPTION_PARAM = {'model_path': MODEL, 'min_confidence': 0.5, 'classes': ['person']}


def generate_launch_description():
    nodes = [
        Node(package='swarm_perception', executable='task_generator',
             name='task_generator', parameters=[{'cooldown_s': 60.0}]),
    ]
    for i, lab in enumerate(LABELS):
        nodes.append(Node(
            package='swarm_perception', executable='image_replay',
            name=f'image_replay_{lab.lower()}',
            parameters=[{'drone_label': lab, 'frame_offset': i * 3, 'rate_hz': 0.5}]))
        param = dict(PERCEPTION_PARAM, drone_label=lab)
        if VENV_PY:
            nodes.append(Node(
                executable=VENV_PY,
                arguments=['-m', 'swarm_perception.perception_node'],
                name=f'perception_{lab.lower()}', parameters=[param]))
        else:
            nodes.append(Node(
                package='swarm_perception', executable='perception_node',
                name=f'perception_{lab.lower()}', parameters=[param]))
    return LaunchDescription(nodes)
