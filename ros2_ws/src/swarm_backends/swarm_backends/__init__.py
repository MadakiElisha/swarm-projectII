from .adapter import (Capabilities, CommandRequest, CommandStatus, TelemetryFrame,
                      VehicleAdapter, VehicleSnapshot, VehicleType)

__all__ = ["Capabilities", "CommandRequest", "CommandStatus", "TelemetryFrame",
           "VehicleAdapter", "VehicleSnapshot", "VehicleType", "MavlinkBackend", "SimBackend"]


def __getattr__(name):
    # lazy imports: SimBackend needs swarm_common, MavlinkBackend needs pymavlink
    if name == "MavlinkBackend":
        from .mavlink_backend import MavlinkBackend
        return MavlinkBackend
    if name == "SimBackend":
        from .sim_backend import SimBackend
        return SimBackend
    raise AttributeError(name)
