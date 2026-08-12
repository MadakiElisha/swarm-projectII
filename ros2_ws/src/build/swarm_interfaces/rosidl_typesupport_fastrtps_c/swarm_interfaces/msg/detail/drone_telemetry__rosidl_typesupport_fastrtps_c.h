// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from swarm_interfaces:msg/DroneTelemetry.idl
// generated code does not contain a copyright notice
#ifndef SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "swarm_interfaces/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "swarm_interfaces/msg/detail/drone_telemetry__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_serialize_swarm_interfaces__msg__DroneTelemetry(
  const swarm_interfaces__msg__DroneTelemetry * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_deserialize_swarm_interfaces__msg__DroneTelemetry(
  eprosima::fastcdr::Cdr &,
  swarm_interfaces__msg__DroneTelemetry * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t get_serialized_size_swarm_interfaces__msg__DroneTelemetry(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t max_serialized_size_swarm_interfaces__msg__DroneTelemetry(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_serialize_key_swarm_interfaces__msg__DroneTelemetry(
  const swarm_interfaces__msg__DroneTelemetry * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t get_serialized_size_key_swarm_interfaces__msg__DroneTelemetry(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t max_serialized_size_key_swarm_interfaces__msg__DroneTelemetry(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, swarm_interfaces, msg, DroneTelemetry)();

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
