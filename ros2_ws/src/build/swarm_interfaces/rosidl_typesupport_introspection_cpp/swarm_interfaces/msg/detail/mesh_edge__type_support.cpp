// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from swarm_interfaces:msg/MeshEdge.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "swarm_interfaces/msg/detail/mesh_edge__functions.h"
#include "swarm_interfaces/msg/detail/mesh_edge__struct.hpp"
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

void MeshEdge_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) swarm_interfaces::msg::MeshEdge(_init);
}

void MeshEdge_fini_function(void * message_memory)
{
  auto typed_message = static_cast<swarm_interfaces::msg::MeshEdge *>(message_memory);
  typed_message->~MeshEdge();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember MeshEdge_message_member_array[3] = {
  {
    "a",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::MeshEdge, a),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "b",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::MeshEdge, b),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "distance_km",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(swarm_interfaces::msg::MeshEdge, distance_km),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers MeshEdge_message_members = {
  "swarm_interfaces::msg",  // message namespace
  "MeshEdge",  // message name
  3,  // number of fields
  sizeof(swarm_interfaces::msg::MeshEdge),
  false,  // has_any_key_member_
  MeshEdge_message_member_array,  // message members
  MeshEdge_init_function,  // function to initialize message memory (memory has to be allocated)
  MeshEdge_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t MeshEdge_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &MeshEdge_message_members,
  get_message_typesupport_handle_function,
  &swarm_interfaces__msg__MeshEdge__get_type_hash,
  &swarm_interfaces__msg__MeshEdge__get_type_description,
  &swarm_interfaces__msg__MeshEdge__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace swarm_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<swarm_interfaces::msg::MeshEdge>()
{
  return &::swarm_interfaces::msg::rosidl_typesupport_introspection_cpp::MeshEdge_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, swarm_interfaces, msg, MeshEdge)() {
  return &::swarm_interfaces::msg::rosidl_typesupport_introspection_cpp::MeshEdge_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
