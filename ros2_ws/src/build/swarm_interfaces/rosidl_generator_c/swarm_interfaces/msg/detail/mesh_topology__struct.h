// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from swarm_interfaces:msg/MeshTopology.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_topology.h"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__STRUCT_H_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__STRUCT_H_

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
// Member 'active_drones'
#include "rosidl_runtime_c/string.h"
// Member 'edges'
#include "swarm_interfaces/msg/detail/mesh_edge__struct.h"

/// Struct defined in msg/MeshTopology in the package swarm_interfaces.
typedef struct swarm_interfaces__msg__MeshTopology
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String__Sequence active_drones;
  swarm_interfaces__msg__MeshEdge__Sequence edges;
} swarm_interfaces__msg__MeshTopology;

// Struct for a sequence of swarm_interfaces__msg__MeshTopology.
typedef struct swarm_interfaces__msg__MeshTopology__Sequence
{
  swarm_interfaces__msg__MeshTopology * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} swarm_interfaces__msg__MeshTopology__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__STRUCT_H_
