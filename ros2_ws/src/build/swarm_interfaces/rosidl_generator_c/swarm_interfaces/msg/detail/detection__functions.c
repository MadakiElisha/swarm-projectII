// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from swarm_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice
#include "swarm_interfaces/msg/detail/detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

bool
swarm_interfaces__msg__Detection__init(swarm_interfaces__msg__Detection * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    swarm_interfaces__msg__Detection__fini(msg);
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__init(&msg->class_name)) {
    swarm_interfaces__msg__Detection__fini(msg);
    return false;
  }
  // confidence
  // bbox_x
  // bbox_y
  // bbox_w
  // bbox_h
  return true;
}

void
swarm_interfaces__msg__Detection__fini(swarm_interfaces__msg__Detection * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // class_name
  rosidl_runtime_c__String__fini(&msg->class_name);
  // confidence
  // bbox_x
  // bbox_y
  // bbox_w
  // bbox_h
}

bool
swarm_interfaces__msg__Detection__are_equal(const swarm_interfaces__msg__Detection * lhs, const swarm_interfaces__msg__Detection * rhs)
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
  // class_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->class_name), &(rhs->class_name)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // bbox_x
  if (lhs->bbox_x != rhs->bbox_x) {
    return false;
  }
  // bbox_y
  if (lhs->bbox_y != rhs->bbox_y) {
    return false;
  }
  // bbox_w
  if (lhs->bbox_w != rhs->bbox_w) {
    return false;
  }
  // bbox_h
  if (lhs->bbox_h != rhs->bbox_h) {
    return false;
  }
  return true;
}

bool
swarm_interfaces__msg__Detection__copy(
  const swarm_interfaces__msg__Detection * input,
  swarm_interfaces__msg__Detection * output)
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
  // class_name
  if (!rosidl_runtime_c__String__copy(
      &(input->class_name), &(output->class_name)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  // bbox_x
  output->bbox_x = input->bbox_x;
  // bbox_y
  output->bbox_y = input->bbox_y;
  // bbox_w
  output->bbox_w = input->bbox_w;
  // bbox_h
  output->bbox_h = input->bbox_h;
  return true;
}

swarm_interfaces__msg__Detection *
swarm_interfaces__msg__Detection__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  swarm_interfaces__msg__Detection * msg = (swarm_interfaces__msg__Detection *)allocator.allocate(sizeof(swarm_interfaces__msg__Detection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(swarm_interfaces__msg__Detection));
  bool success = swarm_interfaces__msg__Detection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
swarm_interfaces__msg__Detection__destroy(swarm_interfaces__msg__Detection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    swarm_interfaces__msg__Detection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
swarm_interfaces__msg__Detection__Sequence__init(swarm_interfaces__msg__Detection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  swarm_interfaces__msg__Detection * data = NULL;

  if (size) {
    data = (swarm_interfaces__msg__Detection *)allocator.zero_allocate(size, sizeof(swarm_interfaces__msg__Detection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = swarm_interfaces__msg__Detection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        swarm_interfaces__msg__Detection__fini(&data[i - 1]);
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
swarm_interfaces__msg__Detection__Sequence__fini(swarm_interfaces__msg__Detection__Sequence * array)
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
      swarm_interfaces__msg__Detection__fini(&array->data[i]);
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

swarm_interfaces__msg__Detection__Sequence *
swarm_interfaces__msg__Detection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  swarm_interfaces__msg__Detection__Sequence * array = (swarm_interfaces__msg__Detection__Sequence *)allocator.allocate(sizeof(swarm_interfaces__msg__Detection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = swarm_interfaces__msg__Detection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
swarm_interfaces__msg__Detection__Sequence__destroy(swarm_interfaces__msg__Detection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    swarm_interfaces__msg__Detection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
swarm_interfaces__msg__Detection__Sequence__are_equal(const swarm_interfaces__msg__Detection__Sequence * lhs, const swarm_interfaces__msg__Detection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!swarm_interfaces__msg__Detection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
swarm_interfaces__msg__Detection__Sequence__copy(
  const swarm_interfaces__msg__Detection__Sequence * input,
  swarm_interfaces__msg__Detection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(swarm_interfaces__msg__Detection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    swarm_interfaces__msg__Detection * data =
      (swarm_interfaces__msg__Detection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!swarm_interfaces__msg__Detection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          swarm_interfaces__msg__Detection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!swarm_interfaces__msg__Detection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
