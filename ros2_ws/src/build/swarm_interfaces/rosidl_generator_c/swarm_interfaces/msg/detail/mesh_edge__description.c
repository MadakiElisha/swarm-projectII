// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from swarm_interfaces:msg/MeshEdge.idl
// generated code does not contain a copyright notice

#include "swarm_interfaces/msg/detail/mesh_edge__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_swarm_interfaces
const rosidl_type_hash_t *
swarm_interfaces__msg__MeshEdge__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xa3, 0xcf, 0x04, 0x54, 0xf7, 0x71, 0x8f, 0xf1,
      0x6d, 0x43, 0x1f, 0x54, 0xd7, 0xfd, 0x4a, 0x4c,
      0x8c, 0x87, 0xb4, 0x30, 0xa7, 0x43, 0xfa, 0x09,
      0x7f, 0x99, 0x3e, 0xff, 0xa8, 0xb5, 0x3a, 0xf1,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char swarm_interfaces__msg__MeshEdge__TYPE_NAME[] = "swarm_interfaces/msg/MeshEdge";

// Define type names, field names, and default values
static char swarm_interfaces__msg__MeshEdge__FIELD_NAME__a[] = "a";
static char swarm_interfaces__msg__MeshEdge__FIELD_NAME__b[] = "b";
static char swarm_interfaces__msg__MeshEdge__FIELD_NAME__distance_km[] = "distance_km";

static rosidl_runtime_c__type_description__Field swarm_interfaces__msg__MeshEdge__FIELDS[] = {
  {
    {swarm_interfaces__msg__MeshEdge__FIELD_NAME__a, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {swarm_interfaces__msg__MeshEdge__FIELD_NAME__b, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {swarm_interfaces__msg__MeshEdge__FIELD_NAME__distance_km, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
swarm_interfaces__msg__MeshEdge__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {swarm_interfaces__msg__MeshEdge__TYPE_NAME, 29, 29},
      {swarm_interfaces__msg__MeshEdge__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "string a\n"
  "string b\n"
  "float64 distance_km";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
swarm_interfaces__msg__MeshEdge__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {swarm_interfaces__msg__MeshEdge__TYPE_NAME, 29, 29},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 38, 38},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
swarm_interfaces__msg__MeshEdge__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *swarm_interfaces__msg__MeshEdge__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
