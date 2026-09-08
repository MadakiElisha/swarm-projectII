from setuptools import setup, find_packages

setup(
    name='swarm_backends',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['pymavlink'],
    zip_safe=True,
)
