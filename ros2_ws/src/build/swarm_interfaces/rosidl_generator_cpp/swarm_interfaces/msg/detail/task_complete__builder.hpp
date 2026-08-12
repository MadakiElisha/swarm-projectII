// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/TaskComplete.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_complete.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_COMPLETE__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_COMPLETE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/task_complete__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_TaskComplete_task_id
{
public:
  explicit Init_TaskComplete_task_id(::swarm_interfaces::msg::TaskComplete & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::TaskComplete task_id(::swarm_interfaces::msg::TaskComplete::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskComplete msg_;
};

class Init_TaskComplete_drone_label
{
public:
  explicit Init_TaskComplete_drone_label(::swarm_interfaces::msg::TaskComplete & msg)
  : msg_(msg)
  {}
  Init_TaskComplete_task_id drone_label(::swarm_interfaces::msg::TaskComplete::_drone_label_type arg)
  {
    msg_.drone_label = std::move(arg);
    return Init_TaskComplete_task_id(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskComplete msg_;
};

class Init_TaskComplete_header
{
public:
  Init_TaskComplete_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskComplete_drone_label header(::swarm_interfaces::msg::TaskComplete::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_TaskComplete_drone_label(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskComplete msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::TaskComplete>()
{
  return swarm_interfaces::msg::builder::Init_TaskComplete_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_COMPLETE__BUILDER_HPP_
