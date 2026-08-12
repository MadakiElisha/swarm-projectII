import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/madakie/swarm-projectII/swarm-project/ros2_ws/src/swarm_mavlink/install/swarm_mavlink'
