"""
Phase 3/Hardening - Task auction core logic, hardened.

Same bidding algorithm as the original task_auction.py, but with
input validation, centralized config, and proper logging.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import BATTERY_SAFETY_MARGIN_PCT, BATTERY_PCT_PER_KM
from common.logging_setup import get_logger
from mesh.mesh_core import haversine_km

log = get_logger("auction")


def calculate_bid(drone_lat, drone_lon, drone_battery_pct, task_lat, task_lon, is_busy=False):
    """
    Returns a bid (lower = better) or None if the drone can't/shouldn't bid.
    Raises ValueError on invalid inputs rather than producing a bad bid silently.
    """
    if is_busy:
        return None

    if not (0 <= drone_battery_pct <= 100):
        raise ValueError(f"calculate_bid: battery_pct out of range: {drone_battery_pct}")

    dist = haversine_km(drone_lat, drone_lon, task_lat, task_lon)
    estimated_battery_needed = dist * BATTERY_PCT_PER_KM

    if drone_battery_pct < estimated_battery_needed + BATTERY_SAFETY_MARGIN_PCT:
        log.info(f"Bid rejected: battery {drone_battery_pct}% insufficient "
                 f"for {dist:.2f}km trip (needs ~{estimated_battery_needed + BATTERY_SAFETY_MARGIN_PCT:.1f}%)")
        return None

    bid = (dist * 1.0) + ((100 - drone_battery_pct) * 0.05)
    return bid


def run_auction(candidates: dict, task_lat: float, task_lon: float, busy_labels: set = None):
    """
    candidates: dict of label -> (lat, lon, battery_pct)
    Returns (winner_label, bid_value) or (None, None) if no eligible bidder.
    """
    busy_labels = busy_labels or set()

    if not candidates:
        log.warning("run_auction called with no candidates")
        return None, None

    bids = {}
    for label, (lat, lon, batt) in candidates.items():
        try:
            bid = calculate_bid(lat, lon, batt, task_lat, task_lon, is_busy=(label in busy_labels))
        except ValueError as e:
            log.error(f"Skipping bid for {label}: {e}")
            continue
        if bid is not None:
            bids[label] = bid

    if not bids:
        log.info("No eligible bidders for this task")
        return None, None

    winner = min(bids, key=bids.get)
    log.info(f"Auction result: {winner} wins with bid {bids[winner]:.2f}")
    return winner, bids[winner]
