// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from swarm_interfaces:msg/TaskComplete.idl
// generated code does not contain a copyright notice
#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_COMPLETE__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_COMPLETE__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "swarm_interfaces/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "swarm_interfaces/msg/detail/task_complete__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_serialize_swarm_interfaces__msg__TaskComplete(
  const swarm_interfaces__msg__TaskComplete * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_deserialize_swarm_interfaces__msg__TaskComplete(
  eprosima::fastcdr::Cdr &,
  swarm_interfaces__msg__TaskComplete * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t get_serialized_size_swarm_interfaces__msg__TaskComplete(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t max_serialized_size_swarm_interfaces__msg__TaskComplete(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_serialize_key_swarm_interfaces__msg__TaskComplete(
  const swarm_interfaces__msg__TaskComplete * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t get_serialized_size_key_swarm_interfaces__msg__TaskComplete(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t max_serialized_size_key_swarm_interfaces__msg__TaskComplete(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, swarm_interfaces, msg, TaskComplete)();

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_COMPLETE__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
