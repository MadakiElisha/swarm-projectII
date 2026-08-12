// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/MeshEdge.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_edge.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/mesh_edge__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_MeshEdge_distance_km
{
public:
  explicit Init_MeshEdge_distance_km(::swarm_interfaces::msg::MeshEdge & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::MeshEdge distance_km(::swarm_interfaces::msg::MeshEdge::_distance_km_type arg)
  {
    msg_.distance_km = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::MeshEdge msg_;
};

class Init_MeshEdge_b
{
public:
  explicit Init_MeshEdge_b(::swarm_interfaces::msg::MeshEdge & msg)
  : msg_(msg)
  {}
  Init_MeshEdge_distance_km b(::swarm_interfaces::msg::MeshEdge::_b_type arg)
  {
    msg_.b = std::move(arg);
    return Init_MeshEdge_distance_km(msg_);
  }

private:
  ::swarm_interfaces::msg::MeshEdge msg_;
};

class Init_MeshEdge_a
{
public:
  Init_MeshEdge_a()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MeshEdge_b a(::swarm_interfaces::msg::MeshEdge::_a_type arg)
  {
    msg_.a = std::move(arg);
    return Init_MeshEdge_b(msg_);
  }

private:
  ::swarm_interfaces::msg::MeshEdge msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::MeshEdge>()
{
  return swarm_interfaces::msg::builder::Init_MeshEdge_a();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__BUILDER_HPP_
