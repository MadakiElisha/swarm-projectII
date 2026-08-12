"""
Hardening pass - automated tests for auction_core.py

Run with: pytest tests/test_auction.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from mesh.auction_core import calculate_bid, run_auction


def test_calculate_bid_busy_drone_returns_none():
    bid = calculate_bid(6.5244, 3.3792, 95, 6.5300, 3.3850, is_busy=True)
    assert bid is None


def test_calculate_bid_low_battery_returns_none():
    # Task is far away, battery is low - should be rejected on safety margin
    bid = calculate_bid(6.5244, 3.3792, 10, 9.0765, 7.3986, is_busy=False)
    assert bid is None


def test_calculate_bid_healthy_drone_returns_number():
    bid = calculate_bid(6.5244, 3.3792, 95, 6.5250, 3.3800, is_busy=False)
    assert bid is not None
    assert bid > 0


def test_calculate_bid_closer_drone_bids_lower():
    close_bid = calculate_bid(6.5244, 3.3792, 90, 6.5250, 3.3800, is_busy=False)
    far_bid = calculate_bid(6.5244, 3.3792, 90, 6.5480, 3.4030, is_busy=False)
    assert close_bid < far_bid


def test_calculate_bid_rejects_invalid_battery():
    with pytest.raises(ValueError):
        calculate_bid(6.5244, 3.3792, 150, 6.5250, 3.3800, is_busy=False)


def test_run_auction_picks_lowest_bid():
    # Reproduces the exact Phase 3 scenario
    candidates = {
        "D1": (6.5244, 3.3792, 95),
        "D2": (6.5300, 3.3850, 40),
        "D4": (6.5420, 3.3970, 70),
        "D5": (6.5480, 3.4030, 25),
    }
    winner, bid = run_auction(candidates, 6.5430, 3.3980)
    assert winner == "D4"  # D4 is genuinely closest with good battery


def test_run_auction_respects_busy_set():
    candidates = {
        "D1": (6.5244, 3.3792, 95),
        "D4": (6.5420, 3.3970, 70),
    }
    winner, bid = run_auction(candidates, 6.5430, 3.3980, busy_labels={"D4"})
    assert winner == "D1"  # D4 would win otherwise, but it's busy


def test_run_auction_no_candidates_returns_none():
    winner, bid = run_auction({}, 6.5430, 3.3980)
    assert winner is None
    assert bid is None


def test_run_auction_all_busy_returns_none():
    candidates = {"D1": (6.5244, 3.3792, 95)}
    winner, bid = run_auction(candidates, 6.5430, 3.3980, busy_labels={"D1"})
    assert winner is None
