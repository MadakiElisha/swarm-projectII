from setuptools import find_packages, setup

package_name = 'swarm_tasks'

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
    description='Task auctioneer node',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'task_auctioneer = swarm_tasks.task_auctioneer:main',
        ],
    },
)
