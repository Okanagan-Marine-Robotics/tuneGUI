from setuptools import setup
from glob import glob
import os

package_name = 'tune_gui'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='OKMR Team',
    maintainer_email='okmr@ubco.ca',
    description='PyQt5-based GUI for tuning ROS2 node parameters and params.yaml files',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tune_gui = tune_gui.main_window:main',
        ],
    },
)