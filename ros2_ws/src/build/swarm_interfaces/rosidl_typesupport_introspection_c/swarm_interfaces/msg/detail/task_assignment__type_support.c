// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from swarm_interfaces:msg/TaskAssignment.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "swarm_interfaces/msg/detail/task_assignment__rosidl_typesupport_introspection_c.h"
#include "swarm_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "swarm_interfaces/msg/detail/task_assignment__functions.h"
#include "swarm_interfaces/msg/detail/task_assignment__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `task_id`
// Member `assigned_to`
// Member `path`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  swarm_interfaces__msg__TaskAssignment__init(message_memory);
}

void swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_fini_function(void * message_memory)
{
  swarm_interfaces__msg__TaskAssignment__fini(message_memory);
}

size_t swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__size_function__TaskAssignment__path(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__get_const_function__TaskAssignment__path(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__get_function__TaskAssignment__path(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__fetch_function__TaskAssignment__path(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__get_const_function__TaskAssignment__path(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__assign_function__TaskAssignment__path(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__get_function__TaskAssignment__path(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__resize_function__TaskAssignment__path(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_member_array[4] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces__msg__TaskAssignment, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "task_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces__msg__TaskAssignment, task_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "assigned_to",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces__msg__TaskAssignment, assigned_to),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "path",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces__msg__TaskAssignment, path),  // bytes offset in struct
    NULL,  // default value
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__size_function__TaskAssignment__path,  // size() function pointer
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__get_const_function__TaskAssignment__path,  // get_const(index) function pointer
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__get_function__TaskAssignment__path,  // get(index) function pointer
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__fetch_function__TaskAssignment__path,  // fetch(index, &value) function pointer
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__assign_function__TaskAssignment__path,  // assign(index, value) function pointer
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__resize_function__TaskAssignment__path  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_members = {
  "swarm_interfaces__msg",  // message namespace
  "TaskAssignment",  // message name
  4,  // number of fields
  sizeof(swarm_interfaces__msg__TaskAssignment),
  false,  // has_any_key_member_
  swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_member_array,  // message members
  swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_init_function,  // function to initialize message memory (memory has to be allocated)
  swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_type_support_handle = {
  0,
  &swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_members,
  get_message_typesupport_handle_function,
  &swarm_interfaces__msg__TaskAssignment__get_type_hash,
  &swarm_interfaces__msg__TaskAssignment__get_type_description,
  &swarm_interfaces__msg__TaskAssignment__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_swarm_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, swarm_interfaces, msg, TaskAssignment)() {
  swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_type_support_handle.typesupport_identifier) {
    swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &swarm_interfaces__msg__TaskAssignment__rosidl_typesupport_introspection_c__TaskAssignment_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
