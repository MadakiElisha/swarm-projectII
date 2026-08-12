from setuptools import find_packages
from setuptools import setup

setup(
    name='swarm_interfaces',
    version='0.1.0',
    packages=find_packages(
        include=('swarm_interfaces', 'swarm_interfaces.*')),
)
