"""
Hardening pass - centralized configuration.

Every phase so far had constants (radio range, ground station label,
ports) duplicated across multiple files. This module is the single
source of truth - change a value here, and everything that imports
it stays in sync, instead of hunting through 6 files.
"""

# --- Mesh / radio ---
RADIO_RANGE_KM = 2.0
STALE_TELEMETRY_AFTER_SEC = 5.0  # ignore a drone's data if not heard from recently

# --- Swarm roles ---
GROUND_STATION_LABEL = "D1"  # the drone treated as the exit point to the outside world

# --- Task auction ---
BATTERY_SAFETY_MARGIN_PCT = 15  # minimum battery reserve required beyond estimated need
BATTERY_PCT_PER_KM = 4.0        # rough estimate: % battery consumed per km traveled

# --- MAVLink / networking ---
DEFAULT_MAVLINK_PORT = 14550
FLEET_LAYOUT = [
    # Same 5-drone flood-zone layout used consistently since Phase 2
    {"id": 1, "port": 14551, "lat": 6.5244, "lon": 3.3792, "label": "D1"},
    {"id": 2, "port": 14552, "lat": 6.5300, "lon": 3.3850, "label": "D2"},
    {"id": 3, "port": 14553, "lat": 6.5360, "lon": 3.3910, "label": "D3"},
    {"id": 4, "port": 14554, "lat": 6.5420, "lon": 3.3970, "label": "D4"},
    {"id": 5, "port": 14555, "lat": 6.5480, "lon": 3.4030, "label": "D5"},
]
