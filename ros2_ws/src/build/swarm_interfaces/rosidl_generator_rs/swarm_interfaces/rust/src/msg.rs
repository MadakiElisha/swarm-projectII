#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to swarm_interfaces__msg__DroneTelemetry

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DroneTelemetry {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub label: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DroneTelemetry::default())
  }
}

impl rosidl_runtime_rs::Message for DroneTelemetry {
  type RmwMsg = super::msg::rmw::DroneTelemetry;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        label: msg.label.as_str().into(),
        lat: msg.lat,
        lon: msg.lon,
        alt: msg.alt,
        battery_pct: msg.battery_pct,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        label: msg.label.as_str().into(),
      lat: msg.lat,
      lon: msg.lon,
      alt: msg.alt,
      battery_pct: msg.battery_pct,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      label: msg.label.to_string(),
      lat: msg.lat,
      lon: msg.lon,
      alt: msg.alt,
      battery_pct: msg.battery_pct,
    }
  }
}


// Corresponds to swarm_interfaces__msg__MeshEdge

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MeshEdge {

    // This member is not documented.
    #[allow(missing_docs)]
    pub a: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub b: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distance_km: f64,

}



impl Default for MeshEdge {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MeshEdge::default())
  }
}

impl rosidl_runtime_rs::Message for MeshEdge {
  type RmwMsg = super::msg::rmw::MeshEdge;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        a: msg.a.as_str().into(),
        b: msg.b.as_str().into(),
        distance_km: msg.distance_km,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        a: msg.a.as_str().into(),
        b: msg.b.as_str().into(),
      distance_km: msg.distance_km,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      a: msg.a.to_string(),
      b: msg.b.to_string(),
      distance_km: msg.distance_km,
    }
  }
}


// Corresponds to swarm_interfaces__msg__MeshTopology

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MeshTopology {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub active_drones: Vec<std::string::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub edges: Vec<super::msg::MeshEdge>,

}



impl Default for MeshTopology {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MeshTopology::default())
  }
}

impl rosidl_runtime_rs::Message for MeshTopology {
  type RmwMsg = super::msg::rmw::MeshTopology;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        active_drones: msg.active_drones
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        edges: msg.edges
          .into_iter()
          .map(|elem| super::msg::MeshEdge::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        active_drones: msg.active_drones
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        edges: msg.edges
          .iter()
          .map(|elem| super::msg::MeshEdge::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      active_drones: msg.active_drones
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      edges: msg.edges
          .into_iter()
          .map(super::msg::MeshEdge::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to swarm_interfaces__msg__TaskRequest

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskRequest {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lat: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub lon: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub description: std::string::String,

}



impl Default for TaskRequest {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::TaskRequest::default())
  }
}

impl rosidl_runtime_rs::Message for TaskRequest {
  type RmwMsg = super::msg::rmw::TaskRequest;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        task_id: msg.task_id.as_str().into(),
        lat: msg.lat,
        lon: msg.lon,
        description: msg.description.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        task_id: msg.task_id.as_str().into(),
      lat: msg.lat,
      lon: msg.lon,
        description: msg.description.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      task_id: msg.task_id.to_string(),
      lat: msg.lat,
      lon: msg.lon,
      description: msg.description.to_string(),
    }
  }
}


// Corresponds to swarm_interfaces__msg__TaskAssignment

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskAssignment {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub assigned_to: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub path: Vec<std::string::String>,

}



impl Default for TaskAssignment {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::TaskAssignment::default())
  }
}

impl rosidl_runtime_rs::Message for TaskAssignment {
  type RmwMsg = super::msg::rmw::TaskAssignment;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        task_id: msg.task_id.as_str().into(),
        assigned_to: msg.assigned_to.as_str().into(),
        path: msg.path
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        task_id: msg.task_id.as_str().into(),
        assigned_to: msg.assigned_to.as_str().into(),
        path: msg.path
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      task_id: msg.task_id.to_string(),
      assigned_to: msg.assigned_to.to_string(),
      path: msg.path
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
    }
  }
}


// Corresponds to swarm_interfaces__msg__TaskComplete

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskComplete {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub drone_label: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: std::string::String,

}



impl Default for TaskComplete {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::TaskComplete::default())
  }
}

impl rosidl_runtime_rs::Message for TaskComplete {
  type RmwMsg = super::msg::rmw::TaskComplete;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        drone_label: msg.drone_label.as_str().into(),
        task_id: msg.task_id.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        drone_label: msg.drone_label.as_str().into(),
        task_id: msg.task_id.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      drone_label: msg.drone_label.to_string(),
      task_id: msg.task_id.to_string(),
    }
  }
}


// Corresponds to swarm_interfaces__msg__Detection

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub class_name: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Detection::default())
  }
}

impl rosidl_runtime_rs::Message for Detection {
  type RmwMsg = super::msg::rmw::Detection;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        class_name: msg.class_name.as_str().into(),
        confidence: msg.confidence,
        bbox_x: msg.bbox_x,
        bbox_y: msg.bbox_y,
        bbox_w: msg.bbox_w,
        bbox_h: msg.bbox_h,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        class_name: msg.class_name.as_str().into(),
      confidence: msg.confidence,
      bbox_x: msg.bbox_x,
      bbox_y: msg.bbox_y,
      bbox_w: msg.bbox_w,
      bbox_h: msg.bbox_h,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      class_name: msg.class_name.to_string(),
      confidence: msg.confidence,
      bbox_x: msg.bbox_x,
      bbox_y: msg.bbox_y,
      bbox_w: msg.bbox_w,
      bbox_h: msg.bbox_h,
    }
  }
}


// Corresponds to swarm_interfaces__msg__DetectionArray

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectionArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detections: Vec<super::msg::Detection>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub count: u32,

}



impl Default for DetectionArray {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DetectionArray::default())
  }
}

impl rosidl_runtime_rs::Message for DetectionArray {
  type RmwMsg = super::msg::rmw::DetectionArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        detections: msg.detections
          .into_iter()
          .map(|elem| super::msg::Detection::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
        count: msg.count,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        detections: msg.detections
          .iter()
          .map(|elem| super::msg::Detection::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      count: msg.count,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      detections: msg.detections
          .into_iter()
          .map(super::msg::Detection::from_rmw_message)
          .collect(),
      count: msg.count,
    }
  }
}


// Corresponds to swarm_interfaces__msg__DroneCommand

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DroneCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub label: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub command: std::string::String,

}



impl Default for DroneCommand {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DroneCommand::default())
  }
}

impl rosidl_runtime_rs::Message for DroneCommand {
  type RmwMsg = super::msg::rmw::DroneCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        label: msg.label.as_str().into(),
        command: msg.command.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        label: msg.label.as_str().into(),
        command: msg.command.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      label: msg.label.to_string(),
      command: msg.command.to_string(),
    }
  }
}


// Corresponds to swarm_interfaces__msg__TaskRelinquish

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TaskRelinquish {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub task_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub label: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub reason: std::string::String,

}



impl Default for TaskRelinquish {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::TaskRelinquish::default())
  }
}

impl rosidl_runtime_rs::Message for TaskRelinquish {
  type RmwMsg = super::msg::rmw::TaskRelinquish;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        task_id: msg.task_id.as_str().into(),
        label: msg.label.as_str().into(),
        reason: msg.reason.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        task_id: msg.task_id.as_str().into(),
        label: msg.label.as_str().into(),
        reason: msg.reason.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      task_id: msg.task_id.to_string(),
      label: msg.label.to_string(),
      reason: msg.reason.to_string(),
    }
  }
}


