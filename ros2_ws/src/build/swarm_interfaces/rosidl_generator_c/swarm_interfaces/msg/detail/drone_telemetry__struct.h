// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from swarm_interfaces:msg/DroneTelemetry.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/drone_telemetry.h"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__STRUCT_H_
#define SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__STRUCT_H_

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
// Member 'label'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/DroneTelemetry in the package swarm_interfaces.
typedef struct swarm_interfaces__msg__DroneTelemetry
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String label;
  double lat;
  double lon;
  double alt;
  double battery_pct;
} swarm_interfaces__msg__DroneTelemetry;

// Struct for a sequence of swarm_interfaces__msg__DroneTelemetry.
typedef struct swarm_interfaces__msg__DroneTelemetry__Sequence
{
  swarm_interfaces__msg__DroneTelemetry * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} swarm_interfaces__msg__DroneTelemetry__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__STRUCT_H_
