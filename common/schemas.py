"""
Hardening pass - typed message schemas.

Previously, every message (telemetry, task requests, task
assignments) was a raw dict thrown into json.dumps/json.loads with
no validation. A typo in a field name, or a missing value, would
fail silently or crash somewhere far from the actual mistake.

These dataclasses validate on construction AND on parsing, so bad
data is caught immediately, with a clear error, at the point it
enters the system - not three function calls later.
"""
from dataclasses import dataclass, asdict
import json


class SchemaValidationError(ValueError):
    """Raised when a message fails validation - deliberately a
    distinct exception type so callers can catch this specifically,
    rather than swallowing unrelated ValueErrors."""
    pass


@dataclass
class DroneTelemetry:
    label: str
    lat: float
    lon: float
    battery_pct: float

    def __post_init__(self):
        if not self.label:
            raise SchemaValidationError("DroneTelemetry.label cannot be empty")
        if not (-90 <= self.lat <= 90):
            raise SchemaValidationError(f"DroneTelemetry.lat out of range: {self.lat}")
        if not (-180 <= self.lon <= 180):
            raise SchemaValidationError(f"DroneTelemetry.lon out of range: {self.lon}")
        if not (0 <= self.battery_pct <= 100):
            raise SchemaValidationError(f"DroneTelemetry.battery_pct out of range: {self.battery_pct}")

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "DroneTelemetry":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"DroneTelemetry: invalid JSON: {e}")
        try:
            return DroneTelemetry(**data)
        except TypeError as e:
            raise SchemaValidationError(f"DroneTelemetry: missing/extra field(s): {e}")


@dataclass
class TaskRequest:
    task_id: str
    lat: float
    lon: float
    description: str = ""

    def __post_init__(self):
        if not self.task_id:
            raise SchemaValidationError("TaskRequest.task_id cannot be empty")
        if not (-90 <= self.lat <= 90):
            raise SchemaValidationError(f"TaskRequest.lat out of range: {self.lat}")
        if not (-180 <= self.lon <= 180):
            raise SchemaValidationError(f"TaskRequest.lon out of range: {self.lon}")

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "TaskRequest":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"TaskRequest: invalid JSON: {e}")
        try:
            return TaskRequest(**data)
        except TypeError as e:
            raise SchemaValidationError(f"TaskRequest: missing/extra field(s): {e}")


@dataclass
class TaskAssignment:
    task_id: str
    assigned_to: str = None
    path: list = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "TaskAssignment":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"TaskAssignment: invalid JSON: {e}")
        try:
            return TaskAssignment(**data)
        except TypeError as e:
            raise SchemaValidationError(f"TaskAssignment: missing/extra field(s): {e}")
