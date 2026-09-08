"""Pure auction logic. No ROS dependencies - fully unit-testable."""
from .config import BATTERY_SAFETY_MARGIN_PCT, BATTERY_PCT_PER_KM
from .mesh_core import haversine_km


def calculate_bid(drone_lat, drone_lon, drone_battery_pct, task_lat, task_lon, is_busy=False):
    if is_busy:
        return None
    if not (0 <= drone_battery_pct <= 100):
        raise ValueError(f"calculate_bid: battery_pct out of range: {drone_battery_pct}")
    dist = haversine_km(drone_lat, drone_lon, task_lat, task_lon)
    estimated_battery_needed = dist * BATTERY_PCT_PER_KM
    if drone_battery_pct < estimated_battery_needed + BATTERY_SAFETY_MARGIN_PCT:
        return None
    return (dist * 1.0) + ((100 - drone_battery_pct) * 0.05)


def run_auction(candidates: dict, task_lat: float, task_lon: float, busy_labels: set = None):
    busy_labels = busy_labels or set()
    if not candidates:
        return None, None
    bids = {}
    for label, (lat, lon, batt) in candidates.items():
        try:
            bid = calculate_bid(lat, lon, batt, task_lat, task_lon, is_busy=(label in busy_labels))
        except ValueError:
            continue
        if bid is not None:
            bids[label] = bid
    if not bids:
        return None, None
    winner = min(bids, key=bids.get)
    return winner, bids[winner]
