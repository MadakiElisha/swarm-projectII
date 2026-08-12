// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/TaskAssignment.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_assignment.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_ASSIGNMENT__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_ASSIGNMENT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/task_assignment__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_TaskAssignment_path
{
public:
  explicit Init_TaskAssignment_path(::swarm_interfaces::msg::TaskAssignment & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::TaskAssignment path(::swarm_interfaces::msg::TaskAssignment::_path_type arg)
  {
    msg_.path = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskAssignment msg_;
};

class Init_TaskAssignment_assigned_to
{
public:
  explicit Init_TaskAssignment_assigned_to(::swarm_interfaces::msg::TaskAssignment & msg)
  : msg_(msg)
  {}
  Init_TaskAssignment_path assigned_to(::swarm_interfaces::msg::TaskAssignment::_assigned_to_type arg)
  {
    msg_.assigned_to = std::move(arg);
    return Init_TaskAssignment_path(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskAssignment msg_;
};

class Init_TaskAssignment_task_id
{
public:
  explicit Init_TaskAssignment_task_id(::swarm_interfaces::msg::TaskAssignment & msg)
  : msg_(msg)
  {}
  Init_TaskAssignment_assigned_to task_id(::swarm_interfaces::msg::TaskAssignment::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_TaskAssignment_assigned_to(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskAssignment msg_;
};

class Init_TaskAssignment_header
{
public:
  Init_TaskAssignment_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskAssignment_task_id header(::swarm_interfaces::msg::TaskAssignment::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_TaskAssignment_task_id(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskAssignment msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::TaskAssignment>()
{
  return swarm_interfaces::msg::builder::Init_TaskAssignment_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_ASSIGNMENT__BUILDER_HPP_
