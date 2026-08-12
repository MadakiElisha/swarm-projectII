// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from swarm_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/detection.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__swarm_interfaces__msg__Detection __attribute__((deprecated))
#else
# define DEPRECATED__swarm_interfaces__msg__Detection __declspec(deprecated)
#endif

namespace swarm_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Detection_
{
  using Type = Detection_<ContainerAllocator>;

  explicit Detection_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->class_name = "";
      this->confidence = 0.0;
      this->bbox_x = 0.0;
      this->bbox_y = 0.0;
      this->bbox_w = 0.0;
      this->bbox_h = 0.0;
    }
  }

  explicit Detection_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    class_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->class_name = "";
      this->confidence = 0.0;
      this->bbox_x = 0.0;
      this->bbox_y = 0.0;
      this->bbox_w = 0.0;
      this->bbox_h = 0.0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _class_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _class_name_type class_name;
  using _confidence_type =
    double;
  _confidence_type confidence;
  using _bbox_x_type =
    double;
  _bbox_x_type bbox_x;
  using _bbox_y_type =
    double;
  _bbox_y_type bbox_y;
  using _bbox_w_type =
    double;
  _bbox_w_type bbox_w;
  using _bbox_h_type =
    double;
  _bbox_h_type bbox_h;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__class_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->class_name = _arg;
    return *this;
  }
  Type & set__confidence(
    const double & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__bbox_x(
    const double & _arg)
  {
    this->bbox_x = _arg;
    return *this;
  }
  Type & set__bbox_y(
    const double & _arg)
  {
    this->bbox_y = _arg;
    return *this;
  }
  Type & set__bbox_w(
    const double & _arg)
  {
    this->bbox_w = _arg;
    return *this;
  }
  Type & set__bbox_h(
    const double & _arg)
  {
    this->bbox_h = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    swarm_interfaces::msg::Detection_<ContainerAllocator> *;
  using ConstRawPtr =
    const swarm_interfaces::msg::Detection_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::Detection_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::Detection_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__swarm_interfaces__msg__Detection
    std::shared_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__swarm_interfaces__msg__Detection
    std::shared_ptr<swarm_interfaces::msg::Detection_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Detection_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->class_name != other.class_name) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->bbox_x != other.bbox_x) {
      return false;
    }
    if (this->bbox_y != other.bbox_y) {
      return false;
    }
    if (this->bbox_w != other.bbox_w) {
      return false;
    }
    if (this->bbox_h != other.bbox_h) {
      return false;
    }
    return true;
  }
  bool operator!=(const Detection_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Detection_

// alias to use template instance with default allocator
using Detection =
  swarm_interfaces::msg::Detection_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_HPP_
