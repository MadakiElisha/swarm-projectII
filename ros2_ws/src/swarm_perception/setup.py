from setuptools import find_packages, setup

package_name = 'swarm_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='stefannelisha@gmail.com',
    description='Edge vision: YOLOv8 detections as typed ROS messages',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'perception_node = swarm_perception.perception_node:main',
            'image_replay = swarm_perception.image_replay:main',
            'task_generator = swarm_perception.task_generator:main',
        ],
    },
)
