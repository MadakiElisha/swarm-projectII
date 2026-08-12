from setuptools import setup, find_packages
setup(
    name='swarm_agents', version='0.1.0', packages=find_packages(),
    entry_points={'console_scripts': ['agent_node = swarm_agents.agent_node:main']},
)
