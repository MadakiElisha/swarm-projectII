// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/MeshTopology.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_topology.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/mesh_topology__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_MeshTopology_edges
{
public:
  explicit Init_MeshTopology_edges(::swarm_interfaces::msg::MeshTopology & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::MeshTopology edges(::swarm_interfaces::msg::MeshTopology::_edges_type arg)
  {
    msg_.edges = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::MeshTopology msg_;
};

class Init_MeshTopology_active_drones
{
public:
  explicit Init_MeshTopology_active_drones(::swarm_interfaces::msg::MeshTopology & msg)
  : msg_(msg)
  {}
  Init_MeshTopology_edges active_drones(::swarm_interfaces::msg::MeshTopology::_active_drones_type arg)
  {
    msg_.active_drones = std::move(arg);
    return Init_MeshTopology_edges(msg_);
  }

private:
  ::swarm_interfaces::msg::MeshTopology msg_;
};

class Init_MeshTopology_header
{
public:
  Init_MeshTopology_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MeshTopology_active_drones header(::swarm_interfaces::msg::MeshTopology::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_MeshTopology_active_drones(msg_);
  }

private:
  ::swarm_interfaces::msg::MeshTopology msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::MeshTopology>()
{
  return swarm_interfaces::msg::builder::Init_MeshTopology_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__BUILDER_HPP_
