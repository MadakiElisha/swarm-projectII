// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/DroneTelemetry.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/drone_telemetry.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/drone_telemetry__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_DroneTelemetry_battery_pct
{
public:
  explicit Init_DroneTelemetry_battery_pct(::swarm_interfaces::msg::DroneTelemetry & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::DroneTelemetry battery_pct(::swarm_interfaces::msg::DroneTelemetry::_battery_pct_type arg)
  {
    msg_.battery_pct = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneTelemetry msg_;
};

class Init_DroneTelemetry_alt
{
public:
  explicit Init_DroneTelemetry_alt(::swarm_interfaces::msg::DroneTelemetry & msg)
  : msg_(msg)
  {}
  Init_DroneTelemetry_battery_pct alt(::swarm_interfaces::msg::DroneTelemetry::_alt_type arg)
  {
    msg_.alt = std::move(arg);
    return Init_DroneTelemetry_battery_pct(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneTelemetry msg_;
};

class Init_DroneTelemetry_lon
{
public:
  explicit Init_DroneTelemetry_lon(::swarm_interfaces::msg::DroneTelemetry & msg)
  : msg_(msg)
  {}
  Init_DroneTelemetry_alt lon(::swarm_interfaces::msg::DroneTelemetry::_lon_type arg)
  {
    msg_.lon = std::move(arg);
    return Init_DroneTelemetry_alt(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneTelemetry msg_;
};

class Init_DroneTelemetry_lat
{
public:
  explicit Init_DroneTelemetry_lat(::swarm_interfaces::msg::DroneTelemetry & msg)
  : msg_(msg)
  {}
  Init_DroneTelemetry_lon lat(::swarm_interfaces::msg::DroneTelemetry::_lat_type arg)
  {
    msg_.lat = std::move(arg);
    return Init_DroneTelemetry_lon(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneTelemetry msg_;
};

class Init_DroneTelemetry_label
{
public:
  explicit Init_DroneTelemetry_label(::swarm_interfaces::msg::DroneTelemetry & msg)
  : msg_(msg)
  {}
  Init_DroneTelemetry_lat label(::swarm_interfaces::msg::DroneTelemetry::_label_type arg)
  {
    msg_.label = std::move(arg);
    return Init_DroneTelemetry_lat(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneTelemetry msg_;
};

class Init_DroneTelemetry_header
{
public:
  Init_DroneTelemetry_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DroneTelemetry_label header(::swarm_interfaces::msg::DroneTelemetry::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DroneTelemetry_label(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneTelemetry msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::DroneTelemetry>()
{
  return swarm_interfaces::msg::builder::Init_DroneTelemetry_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__BUILDER_HPP_
