// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from swarm_interfaces:msg/TaskRequest.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/task_request.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__STRUCT_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__STRUCT_HPP_

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
# define DEPRECATED__swarm_interfaces__msg__TaskRequest __attribute__((deprecated))
#else
# define DEPRECATED__swarm_interfaces__msg__TaskRequest __declspec(deprecated)
#endif

namespace swarm_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct TaskRequest_
{
  using Type = TaskRequest_<ContainerAllocator>;

  explicit TaskRequest_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
      this->lat = 0.0;
      this->lon = 0.0;
      this->description = "";
    }
  }

  explicit TaskRequest_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    task_id(_alloc),
    description(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
      this->lat = 0.0;
      this->lon = 0.0;
      this->description = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _task_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_id_type task_id;
  using _lat_type =
    double;
  _lat_type lat;
  using _lon_type =
    double;
  _lon_type lon;
  using _description_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _description_type description;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__task_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_id = _arg;
    return *this;
  }
  Type & set__lat(
    const double & _arg)
  {
    this->lat = _arg;
    return *this;
  }
  Type & set__lon(
    const double & _arg)
  {
    this->lon = _arg;
    return *this;
  }
  Type & set__description(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->description = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    swarm_interfaces::msg::TaskRequest_<ContainerAllocator> *;
  using ConstRawPtr =
    const swarm_interfaces::msg::TaskRequest_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::TaskRequest_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::TaskRequest_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__swarm_interfaces__msg__TaskRequest
    std::shared_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__swarm_interfaces__msg__TaskRequest
    std::shared_ptr<swarm_interfaces::msg::TaskRequest_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TaskRequest_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->task_id != other.task_id) {
      return false;
    }
    if (this->lat != other.lat) {
      return false;
    }
    if (this->lon != other.lon) {
      return false;
    }
    if (this->description != other.description) {
      return false;
    }
    return true;
  }
  bool operator!=(const TaskRequest_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TaskRequest_

// alias to use template instance with default allocator
using TaskRequest =
  swarm_interfaces::msg::TaskRequest_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__TASK_REQUEST__STRUCT_HPP_
