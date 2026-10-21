"""Geodesy helpers. All swarm logic runs in a local ENU frame (metres).

Lat/lon is converted only at the system edges (MAVLink, GCS). An
equirectangular projection around a shared origin is accurate to well
under 1 m over the ~10 km operating areas this project targets.
"""
import math
from dataclasses import dataclass

EARTH_R = 6371000.0
M_PER_DEG_LAT = 111320.0


@dataclass(frozen=True)
class Origin:
    lat: float
    lon: float

    def to_enu(self, lat: float, lon: float):
        """lat/lon (deg) -> (east, north) metres relative to this origin."""
        x = (lon - self.lon) * M_PER_DEG_LAT * math.cos(math.radians(self.lat))
        y = (lat - self.lat) * M_PER_DEG_LAT
        return x, y

    def to_latlon(self, x: float, y: float):
        """(east, north) metres -> lat/lon (deg)."""
        lat = self.lat + y / M_PER_DEG_LAT
        lon = self.lon + x / (M_PER_DEG_LAT * math.cos(math.radians(self.lat)))
        return lat, lon


def haversine_m(lat1, lon1, lat2, lon2):
    for name, val, lo, hi in (("lat1", lat1, -90, 90), ("lat2", lat2, -90, 90),
                              ("lon1", lon1, -180, 180), ("lon2", lon2, -180, 180)):
        if not (lo <= val <= hi):
            raise ValueError(f"haversine_m: {name}={val} out of range [{lo}, {hi}]")
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return EARTH_R * 2 * math.asin(math.sqrt(a))


def dist2(a, b):
    """Planar distance between two (x, y[, ...]) points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def wrap_pi(a):
    return (a + math.pi) % (2 * math.pi) - math.pi
