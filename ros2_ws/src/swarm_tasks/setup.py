from setuptools import find_packages, setup

package_name = 'swarm_tasks'

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
    description='Simulation props (scripted moving target)',
    license='MIT',
    entry_points={
        'console_scripts': [
            'gz_quarry = swarm_tasks.gz_quarry:main',
            'target_mover = swarm_tasks.target_mover:main',
        ],
    },
)
