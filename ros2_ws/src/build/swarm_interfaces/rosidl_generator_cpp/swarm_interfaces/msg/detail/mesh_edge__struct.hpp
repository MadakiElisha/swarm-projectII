// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from swarm_interfaces:msg/MeshEdge.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_edge.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__STRUCT_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__swarm_interfaces__msg__MeshEdge __attribute__((deprecated))
#else
# define DEPRECATED__swarm_interfaces__msg__MeshEdge __declspec(deprecated)
#endif

namespace swarm_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct MeshEdge_
{
  using Type = MeshEdge_<ContainerAllocator>;

  explicit MeshEdge_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->a = "";
      this->b = "";
      this->distance_km = 0.0;
    }
  }

  explicit MeshEdge_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : a(_alloc),
    b(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->a = "";
      this->b = "";
      this->distance_km = 0.0;
    }
  }

  // field types and members
  using _a_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _a_type a;
  using _b_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _b_type b;
  using _distance_km_type =
    double;
  _distance_km_type distance_km;

  // setters for named parameter idiom
  Type & set__a(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->a = _arg;
    return *this;
  }
  Type & set__b(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->b = _arg;
    return *this;
  }
  Type & set__distance_km(
    const double & _arg)
  {
    this->distance_km = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    swarm_interfaces::msg::MeshEdge_<ContainerAllocator> *;
  using ConstRawPtr =
    const swarm_interfaces::msg::MeshEdge_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__swarm_interfaces__msg__MeshEdge
    std::shared_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__swarm_interfaces__msg__MeshEdge
    std::shared_ptr<swarm_interfaces::msg::MeshEdge_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const MeshEdge_ & other) const
  {
    if (this->a != other.a) {
      return false;
    }
    if (this->b != other.b) {
      return false;
    }
    if (this->distance_km != other.distance_km) {
      return false;
    }
    return true;
  }
  bool operator!=(const MeshEdge_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct MeshEdge_

// alias to use template instance with default allocator
using MeshEdge =
  swarm_interfaces::msg::MeshEdge_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_EDGE__STRUCT_HPP_
