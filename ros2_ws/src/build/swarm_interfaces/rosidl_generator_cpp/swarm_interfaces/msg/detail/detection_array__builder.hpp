// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from swarm_interfaces:msg/DetectionArray.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/detection_array.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "swarm_interfaces/msg/detail/detection_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace swarm_interfaces
{

namespace msg
{

namespace builder
{

class Init_DetectionArray_count
{
public:
  explicit Init_DetectionArray_count(::swarm_interfaces::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  ::swarm_interfaces::msg::DetectionArray count(::swarm_interfaces::msg::DetectionArray::_count_type arg)
  {
    msg_.count = std::move(arg);
    return std::move(msg_);
  }

private:
  ::swarm_interfaces::msg::DetectionArray msg_;
};

class Init_DetectionArray_detections
{
public:
  explicit Init_DetectionArray_detections(::swarm_interfaces::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  Init_DetectionArray_count detections(::swarm_interfaces::msg::DetectionArray::_detections_type arg)
  {
    msg_.detections = std::move(arg);
    return Init_DetectionArray_count(msg_);
  }

private:
  ::swarm_interfaces::msg::DetectionArray msg_;
};

class Init_DetectionArray_header
{
public:
  Init_DetectionArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DetectionArray_detections header(::swarm_interfaces::msg::DetectionArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DetectionArray_detections(msg_);
  }

private:
  ::swarm_interfaces::msg::DetectionArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::swarm_interfaces::msg::DetectionArray>()
{
  return swarm_interfaces::msg::builder::Init_DetectionArray_header();
}

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
