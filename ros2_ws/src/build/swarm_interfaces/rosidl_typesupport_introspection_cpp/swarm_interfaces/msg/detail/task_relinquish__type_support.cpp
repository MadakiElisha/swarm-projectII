// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from swarm_interfaces:msg/TaskRelinquish.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "swarm_interfaces/msg/detail/task_relinquish__functions.h"
#include "swarm_interfaces/msg/detail/task_relinquish__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace swarm_interfaces
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void TaskRelinquish_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) swarm_interfaces::msg::TaskRelinquish(_init);
}

void TaskRelinquish_fini_function(void * message_memory)
{
  auto typed_message = static_cast<swarm_interfaces::msg::TaskRelinquish *>(message_memory);
  typed_message->~TaskRelinquish();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember TaskRelinquish_message_member_array[4] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::TaskRelinquish, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "task_id",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::TaskRelinquish, task_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "label",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::TaskRelinquish, label),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "reason",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::TaskRelinquish, reason),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers TaskRelinquish_message_members = {
  "swarm_interfaces::msg",  // message namespace
  "TaskRelinquish",  // message name
  4,  // number of fields
  sizeof(swarm_interfaces::msg::TaskRelinquish),
  false,  // has_any_key_member_
  TaskRelinquish_message_member_array,  // message members
  TaskRelinquish_init_function,  // function to initialize message memory (memory has to be allocated)
  TaskRelinquish_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t TaskRelinquish_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &TaskRelinquish_message_members,
  get_message_typesupport_handle_function,
  &swarm_interfaces__msg__TaskRelinquish__get_type_hash,
  &swarm_interfaces__msg__TaskRelinquish__get_type_description,
  &swarm_interfaces__msg__TaskRelinquish__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace swarm_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<swarm_interfaces::msg::TaskRelinquish>()
{
  return &::swarm_interfaces::msg::rosidl_typesupport_introspection_cpp::TaskRelinquish_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, swarm_interfaces, msg, TaskRelinquish)() {
  return &::swarm_interfaces::msg::rosidl_typesupport_introspection_cpp::TaskRelinquish_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
