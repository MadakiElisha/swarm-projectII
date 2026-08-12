// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from swarm_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/detection.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DETECTION__TRAITS_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DETECTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "swarm_interfaces/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace swarm_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const Detection & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: class_name
  {
    out << "class_name: ";
    rosidl_generator_traits::value_to_yaml(msg.class_name, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: bbox_x
  {
    out << "bbox_x: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x, out);
    out << ", ";
  }

  // member: bbox_y
  {
    out << "bbox_y: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y, out);
    out << ", ";
  }

  // member: bbox_w
  {
    out << "bbox_w: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_w, out);
    out << ", ";
  }

  // member: bbox_h
  {
    out << "bbox_h: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_h, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Detection & msg,
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

  // member: class_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "class_name: ";
    rosidl_generator_traits::value_to_yaml(msg.class_name, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }

  // member: bbox_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_x: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x, out);
    out << "\n";
  }

  // member: bbox_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_y: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y, out);
    out << "\n";
  }

  // member: bbox_w
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_w: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_w, out);
    out << "\n";
  }

  // member: bbox_h
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_h: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_h, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Detection & msg, bool use_flow_style = false)
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
  const swarm_interfaces::msg::Detection & msg,
  std::ostream & out, size_t indentation = 0)
{
  swarm_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use swarm_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const swarm_interfaces::msg::Detection & msg)
{
  return swarm_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<swarm_interfaces::msg::Detection>()
{
  return "swarm_interfaces::msg::Detection";
}

template<>
inline const char * name<swarm_interfaces::msg::Detection>()
{
  return "swarm_interfaces/msg/Detection";
}

template<>
struct has_fixed_size<swarm_interfaces::msg::Detection>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<swarm_interfaces::msg::Detection>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<swarm_interfaces::msg::Detection>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SWARM_INTERFACES__MSG__DETAIL__DETECTION__TRAITS_HPP_
