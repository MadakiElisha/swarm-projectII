// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from swarm_interfaces:msg/TaskComplete.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "swarm_interfaces/msg/detail/task_complete__functions.h"
#include "swarm_interfaces/msg/detail/task_complete__struct.hpp"
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

void TaskComplete_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) swarm_interfaces::msg::TaskComplete(_init);
}

void TaskComplete_fini_function(void * message_memory)
{
  auto typed_message = static_cast<swarm_interfaces::msg::TaskComplete *>(message_memory);
  typed_message->~TaskComplete();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember TaskComplete_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::TaskComplete, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "drone_label",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::TaskComplete, drone_label),  // bytes offset in struct
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
    offsetof(swarm_interfaces::msg::TaskComplete, task_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers TaskComplete_message_members = {
  "swarm_interfaces::msg",  // message namespace
  "TaskComplete",  // message name
  3,  // number of fields
  sizeof(swarm_interfaces::msg::TaskComplete),
  false,  // has_any_key_member_
  TaskComplete_message_member_array,  // message members
  TaskComplete_init_function,  // function to initialize message memory (memory has to be allocated)
  TaskComplete_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t TaskComplete_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &TaskComplete_message_members,
  get_message_typesupport_handle_function,
  &swarm_interfaces__msg__TaskComplete__get_type_hash,
  &swarm_interfaces__msg__TaskComplete__get_type_description,
  &swarm_interfaces__msg__TaskComplete__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace swarm_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<swarm_interfaces::msg::TaskComplete>()
{
  return &::swarm_interfaces::msg::rosidl_typesupport_introspection_cpp::TaskComplete_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, swarm_interfaces, msg, TaskComplete)() {
  return &::swarm_interfaces::msg::rosidl_typesupport_introspection_cpp::TaskComplete_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
