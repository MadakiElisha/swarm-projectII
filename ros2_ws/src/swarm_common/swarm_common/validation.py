"""Boundary validation for external (untrusted) data, e.g. MAVLink/SITL.

Internal ROS messages are already type-safe; this exists only for the
points where raw external values enter the system, preserving the
'fail loudly, never publish garbage' intent from the hardening pass.
"""


class ValidationError(ValueError):
    """Distinct type so callers can catch boundary failures specifically."""


def validate_lat(lat: float) -> float:
    if not (-90 <= lat <= 90):
        raise ValidationError(f"lat out of range: {lat}")
    return lat


def validate_lon(lon: float) -> float:
    if not (-180 <= lon <= 180):
        raise ValidationError(f"lon out of range: {lon}")
    return lon


def validate_battery(pct: float) -> float:
    if not (0 <= pct <= 100):
        raise ValidationError(f"battery_pct out of range: {pct}")
    return pct


def validate_label(label: str) -> str:
    if not label:
        raise ValidationError("label cannot be empty")
    return label
