// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/TaskRelinquish.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_relinquish.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_RELINQUISH__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_RELINQUISH__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/task_relinquish__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_TaskRelinquish_reason
{
public:
  explicit Init_TaskRelinquish_reason(::swarm_interfaces::msg::TaskRelinquish & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::TaskRelinquish reason(::swarm_interfaces::msg::TaskRelinquish::_reason_type arg)
  {
    msg_.reason = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRelinquish msg_;
};

class Init_TaskRelinquish_label
{
public:
  explicit Init_TaskRelinquish_label(::swarm_interfaces::msg::TaskRelinquish & msg)
  : msg_(msg)
  {}
  Init_TaskRelinquish_reason label(::swarm_interfaces::msg::TaskRelinquish::_label_type arg)
  {
    msg_.label = std::move(arg);
    return Init_TaskRelinquish_reason(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRelinquish msg_;
};

class Init_TaskRelinquish_task_id
{
public:
  explicit Init_TaskRelinquish_task_id(::swarm_interfaces::msg::TaskRelinquish & msg)
  : msg_(msg)
  {}
  Init_TaskRelinquish_label task_id(::swarm_interfaces::msg::TaskRelinquish::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_TaskRelinquish_label(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRelinquish msg_;
};

class Init_TaskRelinquish_header
{
public:
  Init_TaskRelinquish_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskRelinquish_task_id header(::swarm_interfaces::msg::TaskRelinquish::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_TaskRelinquish_task_id(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRelinquish msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::TaskRelinquish>()
{
  return swarm_interfaces::msg::builder::Init_TaskRelinquish_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_RELINQUISH__BUILDER_HPP_
