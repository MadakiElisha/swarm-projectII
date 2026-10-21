import os
import sys

# make `swarm_common` importable without a ROS install
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
