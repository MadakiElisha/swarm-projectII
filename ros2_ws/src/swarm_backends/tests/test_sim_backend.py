import time

from swarm_backends.sim_backend import SimBackend
from swarm_common.geo import Origin


def test_sim_backend_flies_and_returns():
    o = Origin(6.5244, 3.3792)
    b = SimBackend(6.5244, 3.3792, o, rate_hz=200)
    try:
        assert b.takeoff(10.0).accepted
        t0 = time.time()
        while b.snapshot().alt < 9.0 and time.time() - t0 < 8:
            time.sleep(0.05)
        assert b.snapshot().alt >= 9.0 and b.snapshot().armed
        for _ in range(20):
            b.velocity(5.0, 0.0, 0.0)
            time.sleep(0.05)
        assert b.snapshot().lat > 6.5244
        b.rtl()
        assert b.snapshot().mode == "RTL"
    finally:
        b.close()
