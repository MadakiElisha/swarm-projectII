import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'swarm_bringup'

setup(
    name=package_name,
    version='0.2.0',
    packages=find_packages(exclude=['test', 'tests']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='stefannelisha@gmail.com',
    description='Launch files and the single fleet.yaml',
    license='MIT',
    entry_points={
        'console_scripts': [
        ],
    },
)
