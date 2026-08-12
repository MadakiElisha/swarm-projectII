// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from swarm_interfaces:msg/DroneTelemetry.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/drone_telemetry.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__STRUCT_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__STRUCT_HPP_

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
# define DEPRECATED__swarm_interfaces__msg__DroneTelemetry __attribute__((deprecated))
#else
# define DEPRECATED__swarm_interfaces__msg__DroneTelemetry __declspec(deprecated)
#endif

namespace swarm_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DroneTelemetry_
{
  using Type = DroneTelemetry_<ContainerAllocator>;

  explicit DroneTelemetry_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->label = "";
      this->lat = 0.0;
      this->lon = 0.0;
      this->alt = 0.0;
      this->battery_pct = 0.0;
    }
  }

  explicit DroneTelemetry_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    label(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->label = "";
      this->lat = 0.0;
      this->lon = 0.0;
      this->alt = 0.0;
      this->battery_pct = 0.0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _label_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _label_type label;
  using _lat_type =
    double;
  _lat_type lat;
  using _lon_type =
    double;
  _lon_type lon;
  using _alt_type =
    double;
  _alt_type alt;
  using _battery_pct_type =
    double;
  _battery_pct_type battery_pct;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__label(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->label = _arg;
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
  Type & set__alt(
    const double & _arg)
  {
    this->alt = _arg;
    return *this;
  }
  Type & set__battery_pct(
    const double & _arg)
  {
    this->battery_pct = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator> *;
  using ConstRawPtr =
    const swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__swarm_interfaces__msg__DroneTelemetry
    std::shared_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__swarm_interfaces__msg__DroneTelemetry
    std::shared_ptr<swarm_interfaces::msg::DroneTelemetry_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DroneTelemetry_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->label != other.label) {
      return false;
    }
    if (this->lat != other.lat) {
      return false;
    }
    if (this->lon != other.lon) {
      return false;
    }
    if (this->alt != other.alt) {
      return false;
    }
    if (this->battery_pct != other.battery_pct) {
      return false;
    }
    return true;
  }
  bool operator!=(const DroneTelemetry_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DroneTelemetry_

// alias to use template instance with default allocator
using DroneTelemetry =
  swarm_interfaces::msg::DroneTelemetry_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__DRONE_TELEMETRY__STRUCT_HPP_
