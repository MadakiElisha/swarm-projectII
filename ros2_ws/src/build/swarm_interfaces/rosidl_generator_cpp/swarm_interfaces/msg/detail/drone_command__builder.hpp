// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/DroneCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/drone_command.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DRONE_COMMAND__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DRONE_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/drone_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_DroneCommand_command
{
public:
  explicit Init_DroneCommand_command(::swarm_interfaces::msg::DroneCommand & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::DroneCommand command(::swarm_interfaces::msg::DroneCommand::_command_type arg)
  {
    msg_.command = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneCommand msg_;
};

class Init_DroneCommand_label
{
public:
  explicit Init_DroneCommand_label(::swarm_interfaces::msg::DroneCommand & msg)
  : msg_(msg)
  {}
  Init_DroneCommand_command label(::swarm_interfaces::msg::DroneCommand::_label_type arg)
  {
    msg_.label = std::move(arg);
    return Init_DroneCommand_command(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneCommand msg_;
};

class Init_DroneCommand_header
{
public:
  Init_DroneCommand_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DroneCommand_label header(::swarm_interfaces::msg::DroneCommand::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DroneCommand_label(msg_);
  }

private:
  ::swarm_interfaces::msg::DroneCommand msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::DroneCommand>()
{
  return swarm_interfaces::msg::builder::Init_DroneCommand_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__DRONE_COMMAND__BUILDER_HPP_
