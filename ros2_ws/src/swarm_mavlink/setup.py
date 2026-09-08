from setuptools import find_packages, setup

package_name = 'swarm_mavlink'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pymavlink'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='stefannelisha@gmail.com',
    description='Telemetry sources: simulated publisher + real MAVLink bridge',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'telemetry_publisher = swarm_mavlink.telemetry_publisher:main',
            'mavlink_bridge = swarm_mavlink.mavlink_bridge:main',
            'command_bridge = swarm_mavlink.command_bridge:main',
        ],
    },
)
