import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'swarm_perception'

setup(
    name=package_name,
    version='0.2.0',
    packages=find_packages(exclude=['test', 'tests']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'assets'), glob('assets/*.jpg') + glob('assets/*.png')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='stefannelisha@gmail.com',
    description='Per-drone camera + YOLOv8 detections',
    license='MIT',
    entry_points={
        'console_scripts': [
            'camera_compressor = swarm_perception.camera_compressor:main',
            'perception_node = swarm_perception.perception_node:main',
            'image_replay = swarm_perception.image_replay:main',
        ],
    },
)
