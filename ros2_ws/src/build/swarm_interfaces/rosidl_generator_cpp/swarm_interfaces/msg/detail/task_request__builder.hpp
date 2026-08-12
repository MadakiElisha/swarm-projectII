// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/TaskRequest.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_request.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/task_request__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_TaskRequest_description
{
public:
  explicit Init_TaskRequest_description(::swarm_interfaces::msg::TaskRequest & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::TaskRequest description(::swarm_interfaces::msg::TaskRequest::_description_type arg)
  {
    msg_.description = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRequest msg_;
};

class Init_TaskRequest_lon
{
public:
  explicit Init_TaskRequest_lon(::swarm_interfaces::msg::TaskRequest & msg)
  : msg_(msg)
  {}
  Init_TaskRequest_description lon(::swarm_interfaces::msg::TaskRequest::_lon_type arg)
  {
    msg_.lon = std::move(arg);
    return Init_TaskRequest_description(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRequest msg_;
};

class Init_TaskRequest_lat
{
public:
  explicit Init_TaskRequest_lat(::swarm_interfaces::msg::TaskRequest & msg)
  : msg_(msg)
  {}
  Init_TaskRequest_lon lat(::swarm_interfaces::msg::TaskRequest::_lat_type arg)
  {
    msg_.lat = std::move(arg);
    return Init_TaskRequest_lon(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRequest msg_;
};

class Init_TaskRequest_task_id
{
public:
  explicit Init_TaskRequest_task_id(::swarm_interfaces::msg::TaskRequest & msg)
  : msg_(msg)
  {}
  Init_TaskRequest_lat task_id(::swarm_interfaces::msg::TaskRequest::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_TaskRequest_lat(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRequest msg_;
};

class Init_TaskRequest_header
{
public:
  Init_TaskRequest_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskRequest_task_id header(::swarm_interfaces::msg::TaskRequest::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_TaskRequest_task_id(msg_);
  }

private:
  ::swarm_interfaces::msg::TaskRequest msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::TaskRequest>()
{
  return swarm_interfaces::msg::builder::Init_TaskRequest_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__BUILDER_HPP_
