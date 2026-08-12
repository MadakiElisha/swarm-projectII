// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from swarm_interfaces:msg/DroneTelemetry.idl
// generated code does not contain a copyright notice
#include "swarm_interfaces/msg/detail/drone_telemetry__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `label`
#include "rosidl_runtime_c/string_functions.h"

bool
swarm_interfaces__msg__DroneTelemetry__init(swarm_interfaces__msg__DroneTelemetry * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    swarm_interfaces__msg__DroneTelemetry__fini(msg);
    return false;
  }
  // label
  if (!rosidl_runtime_c__String__init(&msg->label)) {
    swarm_interfaces__msg__DroneTelemetry__fini(msg);
    return false;
  }
  // lat
  // lon
  // alt
  // battery_pct
  return true;
}

void
swarm_interfaces__msg__DroneTelemetry__fini(swarm_interfaces__msg__DroneTelemetry * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // label
  rosidl_runtime_c__String__fini(&msg->label);
  // lat
  // lon
  // alt
  // battery_pct
}

bool
swarm_interfaces__msg__DroneTelemetry__are_equal(const swarm_interfaces__msg__DroneTelemetry * lhs, const swarm_interfaces__msg__DroneTelemetry * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // label
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->label), &(rhs->label)))
  {
    return false;
  }
  // lat
  if (lhs->lat != rhs->lat) {
    return false;
  }
  // lon
  if (lhs->lon != rhs->lon) {
    return false;
  }
  // alt
  if (lhs->alt != rhs->alt) {
    return false;
  }
  // battery_pct
  if (lhs->battery_pct != rhs->battery_pct) {
    return false;
  }
  return true;
}

bool
swarm_interfaces__msg__DroneTelemetry__copy(
  const swarm_interfaces__msg__DroneTelemetry * input,
  swarm_interfaces__msg__DroneTelemetry * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // label
  if (!rosidl_runtime_c__String__copy(
      &(input->label), &(output->label)))
  {
    return false;
  }
  // lat
  output->lat = input->lat;
  // lon
  output->lon = input->lon;
  // alt
  output->alt = input->alt;
  // battery_pct
  output->battery_pct = input->battery_pct;
  return true;
}

swarm_interfaces__msg__DroneTelemetry *
swarm_interfaces__msg__DroneTelemetry__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  swarm_interfaces__msg__DroneTelemetry * msg = (swarm_interfaces__msg__DroneTelemetry *)allocator.allocate(sizeof(swarm_interfaces__msg__DroneTelemetry), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(swarm_interfaces__msg__DroneTelemetry));
  bool success = swarm_interfaces__msg__DroneTelemetry__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
swarm_interfaces__msg__DroneTelemetry__destroy(swarm_interfaces__msg__DroneTelemetry * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    swarm_interfaces__msg__DroneTelemetry__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
swarm_interfaces__msg__DroneTelemetry__Sequence__init(swarm_interfaces__msg__DroneTelemetry__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  swarm_interfaces__msg__DroneTelemetry * data = NULL;

  if (size) {
    data = (swarm_interfaces__msg__DroneTelemetry *)allocator.zero_allocate(size, sizeof(swarm_interfaces__msg__DroneTelemetry), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = swarm_interfaces__msg__DroneTelemetry__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        swarm_interfaces__msg__DroneTelemetry__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
swarm_interfaces__msg__DroneTelemetry__Sequence__fini(swarm_interfaces__msg__DroneTelemetry__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      swarm_interfaces__msg__DroneTelemetry__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

swarm_interfaces__msg__DroneTelemetry__Sequence *
swarm_interfaces__msg__DroneTelemetry__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  swarm_interfaces__msg__DroneTelemetry__Sequence * array = (swarm_interfaces__msg__DroneTelemetry__Sequence *)allocator.allocate(sizeof(swarm_interfaces__msg__DroneTelemetry__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = swarm_interfaces__msg__DroneTelemetry__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
swarm_interfaces__msg__DroneTelemetry__Sequence__destroy(swarm_interfaces__msg__DroneTelemetry__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    swarm_interfaces__msg__DroneTelemetry__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
swarm_interfaces__msg__DroneTelemetry__Sequence__are_equal(const swarm_interfaces__msg__DroneTelemetry__Sequence * lhs, const swarm_interfaces__msg__DroneTelemetry__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!swarm_interfaces__msg__DroneTelemetry__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
swarm_interfaces__msg__DroneTelemetry__Sequence__copy(
  const swarm_interfaces__msg__DroneTelemetry__Sequence * input,
  swarm_interfaces__msg__DroneTelemetry__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(swarm_interfaces__msg__DroneTelemetry);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    swarm_interfaces__msg__DroneTelemetry * data =
      (swarm_interfaces__msg__DroneTelemetry *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!swarm_interfaces__msg__DroneTelemetry__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          swarm_interfaces__msg__DroneTelemetry__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!swarm_interfaces__msg__DroneTelemetry__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
