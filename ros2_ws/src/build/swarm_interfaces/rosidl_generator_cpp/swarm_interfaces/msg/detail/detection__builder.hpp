// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/detection.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DETECTION__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_Detection_bbox_h
{
public:
  explicit Init_Detection_bbox_h(::swarm_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::Detection bbox_h(::swarm_interfaces::msg::Detection::_bbox_h_type arg)
  {
    msg_.bbox_h = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

class Init_Detection_bbox_w
{
public:
  explicit Init_Detection_bbox_w(::swarm_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_bbox_h bbox_w(::swarm_interfaces::msg::Detection::_bbox_w_type arg)
  {
    msg_.bbox_w = std::move(arg);
    return Init_Detection_bbox_h(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

class Init_Detection_bbox_y
{
public:
  explicit Init_Detection_bbox_y(::swarm_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_bbox_w bbox_y(::swarm_interfaces::msg::Detection::_bbox_y_type arg)
  {
    msg_.bbox_y = std::move(arg);
    return Init_Detection_bbox_w(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

class Init_Detection_bbox_x
{
public:
  explicit Init_Detection_bbox_x(::swarm_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_bbox_y bbox_x(::swarm_interfaces::msg::Detection::_bbox_x_type arg)
  {
    msg_.bbox_x = std::move(arg);
    return Init_Detection_bbox_y(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

class Init_Detection_confidence
{
public:
  explicit Init_Detection_confidence(::swarm_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_bbox_x confidence(::swarm_interfaces::msg::Detection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_Detection_bbox_x(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

class Init_Detection_class_name
{
public:
  explicit Init_Detection_class_name(::swarm_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_confidence class_name(::swarm_interfaces::msg::Detection::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return Init_Detection_confidence(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

class Init_Detection_header
{
public:
  Init_Detection_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection_class_name header(::swarm_interfaces::msg::Detection::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Detection_class_name(msg_);
  }

private:
  ::swarm_interfaces::msg::Detection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::Detection>()
{
  return swarm_interfaces::msg::builder::Init_Detection_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__DETECTION__BUILDER_HPP_
