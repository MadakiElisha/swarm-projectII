// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from swarm_interfaces:msg/MeshEdge.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_edge.h"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__STRUCT_H_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'a'
// Member 'b'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/MeshEdge in the package swarm_interfaces.
typedef struct swarm_interfaces__msg__MeshEdge
{
  rosidl_runtime_c__String a;
  rosidl_runtime_c__String b;
  double distance_km;
} swarm_interfaces__msg__MeshEdge;

// Struct for a sequence of swarm_interfaces__msg__MeshEdge.
typedef struct swarm_interfaces__msg__MeshEdge__Sequence
{
  swarm_interfaces__msg__MeshEdge * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} swarm_interfaces__msg__MeshEdge__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__STRUCT_H_
