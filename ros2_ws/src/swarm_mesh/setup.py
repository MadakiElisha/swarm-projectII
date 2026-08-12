from setuptools import find_packages, setup

package_name = 'swarm_mesh'

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
    description='Mesh builder node',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mesh_builder = swarm_mesh.mesh_builder:main',
        ],
    },
)
