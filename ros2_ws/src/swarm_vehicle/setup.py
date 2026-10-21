from setuptools import find_packages, setup

package_name = 'swarm_vehicle'

setup(
    name=package_name,
    version='0.2.0',
    packages=find_packages(exclude=['test', 'tests']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='stefannelisha@gmail.com',
    description='Per-drone vehicle authority: safety FSM between the brain and the flight controller',
    license='MIT',
    entry_points={
        'console_scripts': [
            'vehicle_manager = swarm_vehicle.vehicle_manager:main',
        ],
    },
)
