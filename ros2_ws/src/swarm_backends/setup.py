from setuptools import find_packages, setup

package_name = 'swarm_backends'

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
    description='Vendor-agnostic vehicle adapters (MAVLink, sim)',
    license='MIT',
    entry_points={
        'console_scripts': [
        ],
    },
)
