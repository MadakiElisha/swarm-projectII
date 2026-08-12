"""Single source of truth for swarm-wide constants."""

# --- Mesh / radio ---
RADIO_RANGE_KM = 3.5
STALE_TELEMETRY_AFTER_SEC = 5.0

# --- Swarm roles ---
GROUND_STATION_LABEL = "D1"

# --- Task auction ---
BATTERY_SAFETY_MARGIN_PCT = 15
BATTERY_PCT_PER_KM = 4.0

# --- MAVLink / networking ---
DEFAULT_MAVLINK_PORT = 14550

# Cleaned: removed trailing spaces in keys from the original config.py
FLEET_LAYOUT = [
    {"id": 1, "port": 14551, "lat": 6.5244, "lon": 3.3792, "label": "D1"},
    {"id": 2, "port": 14552, "lat": 6.5300, "lon": 3.3850, "label": "D2"},
    {"id": 3, "port": 14553, "lat": 6.5360, "lon": 3.3910, "label": "D3"},
    {"id": 4, "port": 14554, "lat": 6.5420, "lon": 3.3970, "label": "D4"},
    {"id": 5, "port": 14555, "lat": 6.5480, "lon": 3.4030, "label": "D5"},
]
