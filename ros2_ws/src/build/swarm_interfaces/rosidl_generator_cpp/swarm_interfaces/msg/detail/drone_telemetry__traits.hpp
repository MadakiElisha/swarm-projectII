// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from swarm_interfaces:msg/DroneTelemetry.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/drone_telemetry.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__TRAITS_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "swarm_interfaces/msg/detail/drone_telemetry__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace swarm_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const DroneTelemetry & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: label
  {
    out << "label: ";
    rosidl_generator_traits::value_to_yaml(msg.label, out);
    out << ", ";
  }

  // member: lat
  {
    out << "lat: ";
    rosidl_generator_traits::value_to_yaml(msg.lat, out);
    out << ", ";
  }

  // member: lon
  {
    out << "lon: ";
    rosidl_generator_traits::value_to_yaml(msg.lon, out);
    out << ", ";
  }

  // member: alt
  {
    out << "alt: ";
    rosidl_generator_traits::value_to_yaml(msg.alt, out);
    out << ", ";
  }

  // member: battery_pct
  {
    out << "battery_pct: ";
    rosidl_generator_traits::value_to_yaml(msg.battery_pct, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DroneTelemetry & msg,
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

  // member: label
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "label: ";
    rosidl_generator_traits::value_to_yaml(msg.label, out);
    out << "\n";
  }

  // member: lat
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lat: ";
    rosidl_generator_traits::value_to_yaml(msg.lat, out);
    out << "\n";
  }

  // member: lon
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lon: ";
    rosidl_generator_traits::value_to_yaml(msg.lon, out);
    out << "\n";
  }

  // member: alt
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "alt: ";
    rosidl_generator_traits::value_to_yaml(msg.alt, out);
    out << "\n";
  }

  // member: battery_pct
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "battery_pct: ";
    rosidl_generator_traits::value_to_yaml(msg.battery_pct, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DroneTelemetry & msg, bool use_flow_style = false)
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
  const swarm_interfaces::msg::DroneTelemetry & msg,
  std::ostream & out, size_t indentation = 0)
{
  swarm_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use swarm_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const swarm_interfaces::msg::DroneTelemetry & msg)
{
  return swarm_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<swarm_interfaces::msg::DroneTelemetry>()
{
  return "swarm_interfaces::msg::DroneTelemetry";
}

template<>
inline const char * name<swarm_interfaces::msg::DroneTelemetry>()
{
  return "swarm_interfaces/msg/DroneTelemetry";
}

template<>
struct has_fixed_size<swarm_interfaces::msg::DroneTelemetry>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<swarm_interfaces::msg::DroneTelemetry>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<swarm_interfaces::msg::DroneTelemetry>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__TRAITS_HPP_
