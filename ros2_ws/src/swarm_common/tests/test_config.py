from swarm_common.config import (BATTERY_PCT_PER_KM, BATTERY_SAFETY_MARGIN_PCT,
                                 RADIO_RANGE_KM, STALE_TELEMETRY_AFTER_SEC)


def test_sanity():
    assert BATTERY_PCT_PER_KM > 0
    assert BATTERY_SAFETY_MARGIN_PCT > 0
    assert RADIO_RANGE_KM > 0
    assert STALE_TELEMETRY_AFTER_SEC > 0
