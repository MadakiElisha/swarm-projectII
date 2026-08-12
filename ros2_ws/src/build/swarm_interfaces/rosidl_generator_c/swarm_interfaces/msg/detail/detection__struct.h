// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from swarm_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/detection.h"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_H_
#define SWARM_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_H_

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
// Member 'class_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Detection in the package swarm_interfaces.
typedef struct swarm_interfaces__msg__Detection
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String class_name;
  double confidence;
  double bbox_x;
  double bbox_y;
  double bbox_w;
  double bbox_h;
} swarm_interfaces__msg__Detection;

// Struct for a sequence of swarm_interfaces__msg__Detection.
typedef struct swarm_interfaces__msg__Detection__Sequence
{
  swarm_interfaces__msg__Detection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} swarm_interfaces__msg__Detection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_H_
