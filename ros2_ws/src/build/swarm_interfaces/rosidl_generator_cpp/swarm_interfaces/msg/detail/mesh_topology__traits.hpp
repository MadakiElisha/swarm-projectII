// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from swarm_interfaces:msg/MeshTopology.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_topology.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__TRAITS_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "swarm_interfaces/msg/detail/mesh_topology__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'edges'
#include "swarm_interfaces/msg/detail/mesh_edge__traits.hpp"

namespace swarm_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const MeshTopology & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: active_drones
  {
    if (msg.active_drones.size() == 0) {
      out << "active_drones: []";
    } else {
      out << "active_drones: [";
      size_t pending_items = msg.active_drones.size();
      for (auto item : msg.active_drones) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: edges
  {
    if (msg.edges.size() == 0) {
      out << "edges: []";
    } else {
      out << "edges: [";
      size_t pending_items = msg.edges.size();
      for (auto item : msg.edges) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MeshTopology & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: active_drones
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.active_drones.size() == 0) {
      out << "active_drones: []\n";
    } else {
      out << "active_drones:\n";
      for (auto item : msg.active_drones) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: edges
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.edges.size() == 0) {
      out << "edges: []\n";
    } else {
      out << "edges:\n";
      for (auto item : msg.edges) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MeshTopology & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace swarm_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use swarm_interfaces::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const swarm_interfaces::msg::MeshTopology & msg,
  std::ostream & out, size_t indentation = 0)
{
  swarm_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use swarm_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const swarm_interfaces::msg::MeshTopology & msg)
{
  return swarm_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<swarm_interfaces::msg::MeshTopology>()
{
  return "swarm_interfaces::msg::MeshTopology";
}

template<>
inline const char * name<swarm_interfaces::msg::MeshTopology>()
{
  return "swarm_interfaces/msg/MeshTopology";
}

template<>
struct has_fixed_size<swarm_interfaces::msg::MeshTopology>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<swarm_interfaces::msg::MeshTopology>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<swarm_interfaces::msg::MeshTopology>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__TRAITS_HPP_
