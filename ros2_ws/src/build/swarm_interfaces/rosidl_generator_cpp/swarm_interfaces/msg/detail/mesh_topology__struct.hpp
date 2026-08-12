// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from swarm_interfaces:msg/MeshTopology.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "swarm_interfaces/msg/mesh_topology.hpp"


#ifndef SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__STRUCT_HPP_
#define SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__STRUCT_HPP_

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
// Member 'edges'
#include "swarm_interfaces/msg/detail/mesh_edge__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__swarm_interfaces__msg__MeshTopology __attribute__((deprecated))
#else
# define DEPRECATED__swarm_interfaces__msg__MeshTopology __declspec(deprecated)
#endif

namespace swarm_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct MeshTopology_
{
  using Type = MeshTopology_<ContainerAllocator>;

  explicit MeshTopology_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit MeshTopology_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _active_drones_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _active_drones_type active_drones;
  using _edges_type =
    std::vector<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>>;
  _edges_type edges;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__active_drones(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->active_drones = _arg;
    return *this;
  }
  Type & set__edges(
    const std::vector<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<swarm_interfaces::msg::MeshEdge_<ContainerAllocator>>> & _arg)
  {
    this->edges = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    swarm_interfaces::msg::MeshTopology_<ContainerAllocator> *;
  using ConstRawPtr =
    const swarm_interfaces::msg::MeshTopology_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::MeshTopology_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      swarm_interfaces::msg::MeshTopology_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__swarm_interfaces__msg__MeshTopology
    std::shared_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__swarm_interfaces__msg__MeshTopology
    std::shared_ptr<swarm_interfaces::msg::MeshTopology_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const MeshTopology_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->active_drones != other.active_drones) {
      return false;
    }
    if (this->edges != other.edges) {
      return false;
    }
    return true;
  }
  bool operator!=(const MeshTopology_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct MeshTopology_

// alias to use template instance with default allocator
using MeshTopology =
  swarm_interfaces::msg::MeshTopology_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace swarm_interfaces

#endif  // SWARM_INTERFACES__MSG__DETAIL__MESH_TOPOLOGY__STRUCT_HPP_
