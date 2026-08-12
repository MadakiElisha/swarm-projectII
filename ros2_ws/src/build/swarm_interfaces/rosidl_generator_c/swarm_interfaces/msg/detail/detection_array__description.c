// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from swarm_interfaces:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#include "swarm_interfaces/msg/detail/detection_array__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_swarm_interfaces
const rosidl_type_hash_t *
swarm_interfaces__msg__DetectionArray__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x37, 0x68, 0xc3, 0xbb, 0xa8, 0xd2, 0x3f, 0xd4,
      0x52, 0x2b, 0x58, 0xd0, 0xac, 0xb9, 0xf8, 0xf9,
      0x03, 0x98, 0xd1, 0x27, 0xbe, 0x6a, 0x61, 0x7b,
      0xa9, 0xf8, 0x39, 0x6f, 0x02, 0xea, 0xdb, 0x03,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "std_msgs/msg/detail/header__functions.h"
#include "swarm_interfaces/msg/detail/detection__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t std_msgs__msg__Header__EXPECTED_HASH = {1, {
    0xf4, 0x9f, 0xb3, 0xae, 0x2c, 0xf0, 0x70, 0xf7,
    0x93, 0x64, 0x5f, 0xf7, 0x49, 0x68, 0x3a, 0xc6,
    0xb0, 0x62, 0x03, 0xe4, 0x1c, 0x89, 0x1e, 0x17,
    0x70, 0x1b, 0x1c, 0xb5, 0x97, 0xce, 0x6a, 0x01,
  }};
static const rosidl_type_hash_t swarm_interfaces__msg__Detection__EXPECTED_HASH = {1, {
    0x0c, 0xae, 0xaa, 0x4a, 0x30, 0x2e, 0x06, 0xf6,
    0xf2, 0x93, 0x2f, 0xff, 0xa2, 0xfa, 0xde, 0x5e,
    0x2a, 0x98, 0xb9, 0xca, 0x87, 0xbb, 0x24, 0x8d,
    0x77, 0xc5, 0x77, 0x94, 0xd9, 0xd3, 0x97, 0x37,
  }};
#endif

static char swarm_interfaces__msg__DetectionArray__TYPE_NAME[] = "swarm_interfaces/msg/DetectionArray";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char std_msgs__msg__Header__TYPE_NAME[] = "std_msgs/msg/Header";
static char swarm_interfaces__msg__Detection__TYPE_NAME[] = "swarm_interfaces/msg/Detection";

// Define type names, field names, and default values
static char swarm_interfaces__msg__DetectionArray__FIELD_NAME__header[] = "header";
static char swarm_interfaces__msg__DetectionArray__FIELD_NAME__detections[] = "detections";
static char swarm_interfaces__msg__DetectionArray__FIELD_NAME__count[] = "count";

static rosidl_runtime_c__type_description__Field swarm_interfaces__msg__DetectionArray__FIELDS[] = {
  {
    {swarm_interfaces__msg__DetectionArray__FIELD_NAME__header, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    },
    {NULL, 0, 0},
  },
  {
    {swarm_interfaces__msg__DetectionArray__FIELD_NAME__detections, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE,
      0,
      0,
      {swarm_interfaces__msg__Detection__TYPE_NAME, 30, 30},
    },
    {NULL, 0, 0},
  },
  {
    {swarm_interfaces__msg__DetectionArray__FIELD_NAME__count, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription swarm_interfaces__msg__DetectionArray__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    {NULL, 0, 0},
  },
  {
    {swarm_interfaces__msg__Detection__TYPE_NAME, 30, 30},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
swarm_interfaces__msg__DetectionArray__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {swarm_interfaces__msg__DetectionArray__TYPE_NAME, 35, 35},
      {swarm_interfaces__msg__DetectionArray__FIELDS, 3, 3},
    },
    {swarm_interfaces__msg__DetectionArray__REFERENCED_TYPE_DESCRIPTIONS, 3, 3},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&std_msgs__msg__Header__EXPECTED_HASH, std_msgs__msg__Header__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = std_msgs__msg__Header__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&swarm_interfaces__msg__Detection__EXPECTED_HASH, swarm_interfaces__msg__Detection__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[2].fields = swarm_interfaces__msg__Detection__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "std_msgs/Header header\n"
  "Detection[] detections\n"
  "uint32 count";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
swarm_interfaces__msg__DetectionArray__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {swarm_interfaces__msg__DetectionArray__TYPE_NAME, 35, 35},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 59, 59},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
swarm_interfaces__msg__DetectionArray__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[4];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 4, 4};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *swarm_interfaces__msg__DetectionArray__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *std_msgs__msg__Header__get_individual_type_description_source(NULL);
    sources[3] = *swarm_interfaces__msg__Detection__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
