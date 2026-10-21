import socket
import time

import pytest

pytest.importorskip("pymavlink")

from fake_ardupilot import FakeArduCopter, MODES  # noqa: E402
from swarm_backends.mavlink_backend import MavlinkBackend  # noqa: E402


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


@pytest.fixture
def rig():
    port = _free_port()
    be = MavlinkBackend(f"udpin:127.0.0.1:{port}", connect_timeout_s=5)
    fc = FakeArduCopter(port)
    t0 = time.time()
    while not be.snapshot().connected and time.time() - t0 < 8:
        time.sleep(0.05)
    assert be.snapshot().connected, "backend never saw a heartbeat"
    yield be, fc
    be.close()
    fc.close()


def test_snapshot_decodes_telemetry(rig):
    be, _ = rig
    time.sleep(0.3)
    s = be.snapshot()
    assert abs(s.lat - 6.5244) < 1e-6 and s.battery_pct == 87 and s.mode == "STABILIZE"


def test_takeoff_sequence_with_acks(rig):
    be, fc = rig
    st = be.takeoff(25.0)
    assert st.accepted, st.reason
    assert fc.mode == MODES["GUIDED"] and fc.armed and fc.alt == 25.0
    # already airborne: a second takeoff must NOT re-arm
    n_arm = fc.commands.count(400)
    time.sleep(0.3)
    assert be.takeoff(25.0).accepted
    assert fc.commands.count(400) == n_arm


def test_prearm_failure_is_reported_not_swallowed(rig):
    be, fc = rig
    fc.refuse_arm = True
    st = be.takeoff(25.0)
    assert not st.accepted and "arm refused" in st.reason


def test_lost_ack_is_retried(rig):
    be, fc = rig
    be.takeoff(20.0)
    fc.drop_acks = 1
    st = be._command(176, 1, 4)        # arbitrary command, first ACK dropped
    assert st.accepted


def test_rtl_and_land_confirmed_by_heartbeat(rig):
    be, fc = rig
    be.takeoff(20.0)
    assert be.rtl().accepted and fc.mode == MODES["RTL"]
    time.sleep(0.3)
    assert be.snapshot().mode == "RTL"
    assert be.land().accepted and fc.mode == MODES["LAND"]


def test_velocity_is_a_nonblocking_send(rig):
    be, fc = rig
    t0 = time.time()
    for _ in range(20):
        be.velocity(1.0, 2.0, 0.0)
    assert time.time() - t0 < 0.2
    time.sleep(0.3)
    assert fc.velocity_msgs >= 15


def test_set_param_confirmed(rig):
    be, fc = rig
    assert be.set_param("RTL_ALT", 3600.0).accepted
    assert fc.params.get("RTL_ALT") == 3600.0
