// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from swarm_interfaces:msg/TaskAssignment.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_assignment.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_ASSIGNMENT__TRAITS_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_ASSIGNMENT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "swarm_interfaces/msg/detail/task_assignment__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace swarm_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const TaskAssignment & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: task_id
  {
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << ", ";
  }

  // member: assigned_to
  {
    out << "assigned_to: ";
    rosidl_generator_traits::value_to_yaml(msg.assigned_to, out);
    out << ", ";
  }

  // member: path
  {
    if (msg.path.size() == 0) {
      out << "path: []";
    } else {
      out << "path: [";
      size_t pending_items = msg.path.size();
      for (auto item : msg.path) {
        rosidl_generator_traits::value_to_yaml(item, out);
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
  const TaskAssignment & msg,
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

  // member: task_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << "\n";
  }

  // member: assigned_to
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "assigned_to: ";
    rosidl_generator_traits::value_to_yaml(msg.assigned_to, out);
    out << "\n";
  }

  // member: path
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.path.size() == 0) {
      out << "path: []\n";
    } else {
      out << "path:\n";
      for (auto item : msg.path) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const TaskAssignment & msg, bool use_flow_style = false)
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
  const swarm_interfaces::msg::TaskAssignment & msg,
  std::ostream & out, size_t indentation = 0)
{
  swarm_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use swarm_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const swarm_interfaces::msg::TaskAssignment & msg)
{
  return swarm_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<swarm_interfaces::msg::TaskAssignment>()
{
  return "swarm_interfaces::msg::TaskAssignment";
}

template<>
inline const char * name<swarm_interfaces::msg::TaskAssignment>()
{
  return "swarm_interfaces/msg/TaskAssignment";
}

template<>
struct has_fixed_size<swarm_interfaces::msg::TaskAssignment>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<swarm_interfaces::msg::TaskAssignment>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<swarm_interfaces::msg::TaskAssignment>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_ASSIGNMENT__TRAITS_HPP_
