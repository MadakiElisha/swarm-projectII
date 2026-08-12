// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from swarm_interfaces:msg/DetectionArray.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/detection_array.h"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
#define SWARM_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_

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
// Member 'detections'
#include "swarm_interfaces/msg/detail/detection__struct.h"

/// Struct defined in msg/DetectionArray in the package swarm_interfaces.
typedef struct swarm_interfaces__msg__DetectionArray
{
  std_msgs__msg__Header header;
  swarm_interfaces__msg__Detection__Sequence detections;
  uint32_t count;
} swarm_interfaces__msg__DetectionArray;

// Struct for a sequence of swarm_interfaces__msg__DetectionArray.
typedef struct swarm_interfaces__msg__DetectionArray__Sequence
{
  swarm_interfaces__msg__DetectionArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} swarm_interfaces__msg__DetectionArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
