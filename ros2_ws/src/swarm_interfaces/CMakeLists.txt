cmake_minimum_required(VERSION 3.8)
project(swarm_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DroneTelemetry.msg"
  "msg/MeshEdge.msg"
  "msg/MeshTopology.msg"
  "msg/TaskRequest.msg"
  "msg/TaskAssignment.msg"
  "msg/TaskComplete.msg"
  "msg/Detection.msg"
  "msg/DetectionArray.msg"
  "msg/DroneCommand.msg"
  "msg/TaskRelinquish.msg"
  DEPENDENCIES std_msgs
)

ament_package()
