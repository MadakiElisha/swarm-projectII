// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from swarm_interfaces:msg/MeshEdge.idl
// generated code does not contain a copyright notice
#include "swarm_interfaces/msg/detail/mesh_edge__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "swarm_interfaces/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "swarm_interfaces/msg/detail/mesh_edge__struct.h"
#include "swarm_interfaces/msg/detail/mesh_edge__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif

#include "rosidl_runtime_c/string.h"  // a, b
#include "rosidl_runtime_c/string_functions.h"  // a, b

// forward declare type support functions


using _MeshEdge__ros_msg_type = swarm_interfaces__msg__MeshEdge;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_serialize_swarm_interfaces__msg__MeshEdge(
  const swarm_interfaces__msg__MeshEdge * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: a
  {
    const rosidl_runtime_c__String * str = &ros_message->a;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: b
  {
    const rosidl_runtime_c__String * str = &ros_message->b;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: distance_km
  {
    cdr << ros_message->distance_km;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_deserialize_swarm_interfaces__msg__MeshEdge(
  eprosima::fastcdr::Cdr & cdr,
  swarm_interfaces__msg__MeshEdge * ros_message)
{
  // Field name: a
  {
    std::string tmp;
    cdr >> tmp;
    if (!ros_message->a.data) {
      rosidl_runtime_c__String__init(&ros_message->a);
    }
    bool succeeded = rosidl_runtime_c__String__assign(
      &ros_message->a,
      tmp.c_str());
    if (!succeeded) {
      fprintf(stderr, "failed to assign string into field 'a'\n");
      return false;
    }
  }

  // Field name: b
  {
    std::string tmp;
    cdr >> tmp;
    if (!ros_message->b.data) {
      rosidl_runtime_c__String__init(&ros_message->b);
    }
    bool succeeded = rosidl_runtime_c__String__assign(
      &ros_message->b,
      tmp.c_str());
    if (!succeeded) {
      fprintf(stderr, "failed to assign string into field 'b'\n");
      return false;
    }
  }

  // Field name: distance_km
  {
    cdr >> ros_message->distance_km;
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t get_serialized_size_swarm_interfaces__msg__MeshEdge(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _MeshEdge__ros_msg_type * ros_message = static_cast<const _MeshEdge__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: a
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->a.size + 1);

  // Field name: b
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->b.size + 1);

  // Field name: distance_km
  {
    size_t item_size = sizeof(ros_message->distance_km);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t max_serialized_size_swarm_interfaces__msg__MeshEdge(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Field name: a
  {
    size_t array_size = 1;
    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Field name: b
  {
    size_t array_size = 1;
    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Field name: distance_km
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = swarm_interfaces__msg__MeshEdge;
    is_plain =
      (
      offsetof(DataType, distance_km) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
bool cdr_serialize_key_swarm_interfaces__msg__MeshEdge(
  const swarm_interfaces__msg__MeshEdge * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: a
  {
    const rosidl_runtime_c__String * str = &ros_message->a;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: b
  {
    const rosidl_runtime_c__String * str = &ros_message->b;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: distance_km
  {
    cdr << ros_message->distance_km;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t get_serialized_size_key_swarm_interfaces__msg__MeshEdge(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _MeshEdge__ros_msg_type * ros_message = static_cast<const _MeshEdge__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: a
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->a.size + 1);

  // Field name: b
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->b.size + 1);

  // Field name: distance_km
  {
    size_t item_size = sizeof(ros_message->distance_km);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_swarm_interfaces
size_t max_serialized_size_key_swarm_interfaces__msg__MeshEdge(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;
  // Field name: a
  {
    size_t array_size = 1;
    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Field name: b
  {
    size_t array_size = 1;
    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Field name: distance_km
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = swarm_interfaces__msg__MeshEdge;
    is_plain =
      (
      offsetof(DataType, distance_km) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _MeshEdge__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const swarm_interfaces__msg__MeshEdge * ros_message = static_cast<const swarm_interfaces__msg__MeshEdge *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_swarm_interfaces__msg__MeshEdge(ros_message, cdr);
}

static bool _MeshEdge__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  swarm_interfaces__msg__MeshEdge * ros_message = static_cast<swarm_interfaces__msg__MeshEdge *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_swarm_interfaces__msg__MeshEdge(cdr, ros_message);
}

static uint32_t _MeshEdge__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_swarm_interfaces__msg__MeshEdge(
      untyped_ros_message, 0));
}

static size_t _MeshEdge__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_swarm_interfaces__msg__MeshEdge(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_MeshEdge = {
  "swarm_interfaces::msg",
  "MeshEdge",
  _MeshEdge__cdr_serialize,
  _MeshEdge__cdr_deserialize,
  _MeshEdge__get_serialized_size,
  _MeshEdge__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _MeshEdge__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_MeshEdge,
  get_message_typesupport_handle_function,
  &swarm_interfaces__msg__MeshEdge__get_type_hash,
  &swarm_interfaces__msg__MeshEdge__get_type_description,
  &swarm_interfaces__msg__MeshEdge__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, swarm_interfaces, msg, MeshEdge)() {
  return &_MeshEdge__type_support;
}

#if defined(__cplusplus)
}
#endif
