// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from swarm_interfaces:msg/TaskRequest.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_request.h"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__STRUCT_H_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'task_id'
// Member 'description'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/TaskRequest in the package swarm_interfaces.
typedef struct swarm_interfaces__msg__TaskRequest
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String task_id;
  double lat;
  double lon;
  rosidl_runtime_c__String description;
} swarm_interfaces__msg__TaskRequest;

// Struct for a sequence of swarm_interfaces__msg__TaskRequest.
typedef struct swarm_interfaces__msg__TaskRequest__Sequence
{
  swarm_interfaces__msg__TaskRequest * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} swarm_interfaces__msg__TaskRequest__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__STRUCT_H_
