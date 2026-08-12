#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__DroneTelemetry() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__DroneTelemetry__init(msg: *mut DroneTelemetry) -> bool;
    fn swarm_interfaces__msg__DroneTelemetry__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DroneTelemetry>, size: usize) -> bool;
    fn swarm_interfaces__msg__DroneTelemetry__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DroneTelemetry>);
    fn swarm_interfaces__msg__DroneTelemetry__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DroneTelemetry>, out_seq: *mut rosidl_runtime_rs::Sequence<DroneTelemetry>) -> bool;
}

// Corresponds to swarm_interfaces__msg__DroneTelemetry
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DroneTelemetry {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub label: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lat: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lon: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub alt: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub battery_pct: f64,

}



impl Default for DroneTelemetry {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__DroneTelemetry__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__DroneTelemetry__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DroneTelemetry {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DroneTelemetry__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DroneTelemetry__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DroneTelemetry__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DroneTelemetry {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DroneTelemetry where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/DroneTelemetry";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__DroneTelemetry() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__MeshEdge() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__MeshEdge__init(msg: *mut MeshEdge) -> bool;
    fn swarm_interfaces__msg__MeshEdge__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MeshEdge>, size: usize) -> bool;
    fn swarm_interfaces__msg__MeshEdge__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MeshEdge>);
    fn swarm_interfaces__msg__MeshEdge__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MeshEdge>, out_seq: *mut rosidl_runtime_rs::Sequence<MeshEdge>) -> bool;
}

// Corresponds to swarm_interfaces__msg__MeshEdge
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MeshEdge {

    // This member is not documented.
    #[allow(missing_docs)]
    pub a: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub b: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distance_km: f64,

}



impl Default for MeshEdge {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__MeshEdge__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__MeshEdge__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MeshEdge {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__MeshEdge__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__MeshEdge__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__MeshEdge__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MeshEdge {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MeshEdge where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/MeshEdge";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__MeshEdge() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__MeshTopology() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__MeshTopology__init(msg: *mut MeshTopology) -> bool;
    fn swarm_interfaces__msg__MeshTopology__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MeshTopology>, size: usize) -> bool;
    fn swarm_interfaces__msg__MeshTopology__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MeshTopology>);
    fn swarm_interfaces__msg__MeshTopology__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MeshTopology>, out_seq: *mut rosidl_runtime_rs::Sequence<MeshTopology>) -> bool;
}

// Corresponds to swarm_interfaces__msg__MeshTopology
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MeshTopology {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub active_drones: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub edges: rosidl_runtime_rs::Sequence<super::super::msg::rmw::MeshEdge>,

}



impl Default for MeshTopology {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__MeshTopology__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__MeshTopology__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MeshTopology {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__MeshTopology__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__MeshTopology__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__MeshTopology__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MeshTopology {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MeshTopology where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/MeshTopology";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__MeshTopology() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskRequest() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__TaskRequest__init(msg: *mut TaskRequest) -> bool;
    fn swarm_interfaces__msg__TaskRequest__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TaskRequest>, size: usize) -> bool;
    fn swarm_interfaces__msg__TaskRequest__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TaskRequest>);
    fn swarm_interfaces__msg__TaskRequest__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TaskRequest>, out_seq: *mut rosidl_runtime_rs::Sequence<TaskRequest>) -> bool;
}

// Corresponds to swarm_interfaces__msg__TaskRequest
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskRequest {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lat: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lon: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub description: rosidl_runtime_rs::String,

}



impl Default for TaskRequest {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__TaskRequest__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__TaskRequest__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TaskRequest {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskRequest__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskRequest__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskRequest__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TaskRequest {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TaskRequest where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/TaskRequest";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskRequest() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskAssignment() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__TaskAssignment__init(msg: *mut TaskAssignment) -> bool;
    fn swarm_interfaces__msg__TaskAssignment__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TaskAssignment>, size: usize) -> bool;
    fn swarm_interfaces__msg__TaskAssignment__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TaskAssignment>);
    fn swarm_interfaces__msg__TaskAssignment__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TaskAssignment>, out_seq: *mut rosidl_runtime_rs::Sequence<TaskAssignment>) -> bool;
}

// Corresponds to swarm_interfaces__msg__TaskAssignment
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskAssignment {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub assigned_to: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub path: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,

}



impl Default for TaskAssignment {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__TaskAssignment__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__TaskAssignment__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TaskAssignment {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskAssignment__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskAssignment__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskAssignment__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TaskAssignment {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TaskAssignment where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/TaskAssignment";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskAssignment() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskComplete() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__TaskComplete__init(msg: *mut TaskComplete) -> bool;
    fn swarm_interfaces__msg__TaskComplete__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TaskComplete>, size: usize) -> bool;
    fn swarm_interfaces__msg__TaskComplete__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TaskComplete>);
    fn swarm_interfaces__msg__TaskComplete__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TaskComplete>, out_seq: *mut rosidl_runtime_rs::Sequence<TaskComplete>) -> bool;
}

// Corresponds to swarm_interfaces__msg__TaskComplete
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskComplete {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub drone_label: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: rosidl_runtime_rs::String,

}



impl Default for TaskComplete {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__TaskComplete__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__TaskComplete__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TaskComplete {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskComplete__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskComplete__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskComplete__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TaskComplete {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TaskComplete where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/TaskComplete";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskComplete() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__Detection() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__Detection__init(msg: *mut Detection) -> bool;
    fn swarm_interfaces__msg__Detection__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Detection>, size: usize) -> bool;
    fn swarm_interfaces__msg__Detection__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Detection>);
    fn swarm_interfaces__msg__Detection__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Detection>, out_seq: *mut rosidl_runtime_rs::Sequence<Detection>) -> bool;
}

// Corresponds to swarm_interfaces__msg__Detection
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub class_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_w: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_h: f64,

}



impl Default for Detection {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__Detection__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__Detection__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Detection {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__Detection__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__Detection__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__Detection__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Detection {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Detection where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/Detection";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__Detection() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__DetectionArray() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__DetectionArray__init(msg: *mut DetectionArray) -> bool;
    fn swarm_interfaces__msg__DetectionArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>, size: usize) -> bool;
    fn swarm_interfaces__msg__DetectionArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>);
    fn swarm_interfaces__msg__DetectionArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DetectionArray>, out_seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>) -> bool;
}

// Corresponds to swarm_interfaces__msg__DetectionArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectionArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detections: rosidl_runtime_rs::Sequence<super::super::msg::rmw::Detection>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub count: u32,

}



impl Default for DetectionArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__DetectionArray__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__DetectionArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DetectionArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DetectionArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DetectionArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DetectionArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DetectionArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DetectionArray where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/DetectionArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__DetectionArray() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__DroneCommand() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__DroneCommand__init(msg: *mut DroneCommand) -> bool;
    fn swarm_interfaces__msg__DroneCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DroneCommand>, size: usize) -> bool;
    fn swarm_interfaces__msg__DroneCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DroneCommand>);
    fn swarm_interfaces__msg__DroneCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DroneCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<DroneCommand>) -> bool;
}

// Corresponds to swarm_interfaces__msg__DroneCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DroneCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub label: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub command: rosidl_runtime_rs::String,

}



impl Default for DroneCommand {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__DroneCommand__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__DroneCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DroneCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DroneCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DroneCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__DroneCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DroneCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DroneCommand where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/DroneCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__DroneCommand() }
  }
}


#[link(name = "swarm_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskRelinquish() -> *const std::ffi::c_void;
}

#[link(name = "swarm_interfaces__rosidl_generator_c")]
extern "C" {
    fn swarm_interfaces__msg__TaskRelinquish__init(msg: *mut TaskRelinquish) -> bool;
    fn swarm_interfaces__msg__TaskRelinquish__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TaskRelinquish>, size: usize) -> bool;
    fn swarm_interfaces__msg__TaskRelinquish__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TaskRelinquish>);
    fn swarm_interfaces__msg__TaskRelinquish__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TaskRelinquish>, out_seq: *mut rosidl_runtime_rs::Sequence<TaskRelinquish>) -> bool;
}

// Corresponds to swarm_interfaces__msg__TaskRelinquish
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskRelinquish {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub label: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub reason: rosidl_runtime_rs::String,

}



impl Default for TaskRelinquish {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !swarm_interfaces__msg__TaskRelinquish__init(&mut msg as *mut _) {
        panic!("Call to swarm_interfaces__msg__TaskRelinquish__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TaskRelinquish {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskRelinquish__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskRelinquish__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { swarm_interfaces__msg__TaskRelinquish__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TaskRelinquish {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TaskRelinquish where Self: Sized {
  const TYPE_NAME: &'static str = "swarm_interfaces/msg/TaskRelinquish";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__swarm_interfaces__msg__TaskRelinquish() }
  }
}


