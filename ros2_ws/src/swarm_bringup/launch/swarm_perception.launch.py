"""Perception add-on. perception_node runs inside the vision venv so
ultralytics stays confined; image_replay + task_generator use system ROS."""
import os
from launch import LaunchDescription
from launch_ros.actions import Node

MODEL = os.path.expanduser('~/swarm-projectII/swarm-project/vision/yolov8n.pt')
if not os.path.exists(MODEL):
    MODEL = 'yolov8n.pt'

_VENV_CANDIDATES = [
    os.path.expanduser('~/swarm_venv/bin/python'),
    os.path.expanduser('~/swarm-projectII/swarm-project/venv/bin/python'),
    os.path.expanduser('~/swarm-project/venv/bin/python'),
]
VENV_PY = next((p for p in _VENV_CANDIDATES if os.path.exists(p)), None)

PERCEPTION_PARAMS = [{'model_path': MODEL, 'min_confidence': 0.5, 'classes': ['person']}]


def generate_launch_description():
    if VENV_PY:
        perception = Node(
            executable=VENV_PY,
            arguments=['-m', 'swarm_perception.perception_node'],
            name='perception_node',
            parameters=PERCEPTION_PARAMS,
        )
    else:
        perception = Node(
            package='swarm_perception', executable='perception_node',
            name='perception_node', parameters=PERCEPTION_PARAMS,
        )

    return LaunchDescription([
        perception,
        Node(package='swarm_perception', executable='image_replay',
             name='image_replay',
             parameters=[{'drone_label': 'D5', 'period_s': 4.0}]),
        Node(package='swarm_perception', executable='task_generator',
             name='task_generator',
             parameters=[{'cooldown_s': 60.0}]),
    ])
