from swarm_common.vehicle_fsm import (ESTOP, GROUND, GUIDED, HOLD, RTL, TAKEOFF, FsmCfg,
                                      SP_RTB, SP_VEL, Setpoint, VehicleFSM, VehicleObs)


def _obs(t, alt=30.0, batt=80.0, mode="GUIDED", armed=True, x=0.0, y=0.0):
    return VehicleObs(t, x, y, alt, batt, armed, mode)


def _airborne_guided():
    f = VehicleFSM(FsmCfg())
    f.on_setpoint(Setpoint(0.0, SP_VEL, 1, 0, alt=30), 0.0)
    f.tick(_obs(0.0, alt=0, armed=False, mode="STABILIZE"), 0.0)
    assert f.state == TAKEOFF
    acts = f.tick(_obs(0.1, alt=0, armed=False, mode="STABILIZE"), 0.1)
    assert [a.kind for a in acts] == ["takeoff"]
    f.on_setpoint(Setpoint(10.0, SP_VEL, 1, 0, alt=30), 10.0)
    f.tick(_obs(10.0, alt=29.0), 10.0)
    assert f.state == GUIDED
    return f


def test_takeoff_then_forward_setpoints():
    f = _airborne_guided()
    f.on_setpoint(Setpoint(11.0, SP_VEL, 2, 3, alt=30), 11.0)
    acts = f.tick(_obs(11.0), 11.0)
    assert acts[0].kind == "velocity" and acts[0].params["vx"] == 2


def test_operator_rtl_sticks_against_mission_setpoints():
    f = _airborne_guided()
    acts = f.on_operator("RTL", 12.0)
    assert acts[0].kind == "rtl" and f.state == RTL
    for k in range(50):                       # the brain keeps asking to fly
        t = 12.1 + k * 0.1
        f.on_setpoint(Setpoint(t, SP_VEL, 5, 5, alt=30), t)
        acts = f.tick(_obs(t, mode="RTL"), t)
        assert all(a.kind != "velocity" for a in acts)
    assert f.state == RTL and f.latch == "operator RTL"


def test_rtl_is_resent_if_mode_did_not_change():
    f = _airborne_guided()
    f.on_operator("RTL", 12.0)
    acts = f.tick(_obs(16.0, mode="GUIDED"), 16.0)
    assert [a.kind for a in acts] == ["rtl"]


def test_critical_battery_latches_rtl():
    f = _airborne_guided()
    f.on_setpoint(Setpoint(11.0, SP_VEL, 1, 0), 11.0)
    acts = f.tick(_obs(11.0, batt=5.0), 11.0)
    assert acts[0].kind == "rtl" and f.latch == "critical battery"
    assert f.on_operator("RESUME", 12.0, _obs(12.0, batt=5.0)) == []
    assert f.latch == "critical battery"


def test_geofence_breach_latches_rtl():
    f = _airborne_guided()
    f.on_setpoint(Setpoint(11.0, SP_VEL, 1, 0), 11.0)
    f.tick(_obs(11.0, x=9000.0), 11.0)
    assert f.state == RTL and f.latch == "geofence"


def test_brain_watchdog_hold_then_rtl():
    f = _airborne_guided()
    acts = f.tick(_obs(12.0), 12.0)            # last setpoint at t=10 -> stale
    assert f.state == HOLD and acts[0].kind == "hold"
    f.tick(_obs(25.0), 25.0)                   # > brain_dead_s
    assert f.state == RTL and f.latch == "brain dead"


def test_estop_lands_and_needs_resume():
    f = _airborne_guided()
    acts = f.on_operator("ESTOP", 12.0)
    assert f.state == ESTOP and acts[0].kind == "land"
    f.tick(_obs(30.0, alt=0.0, armed=False, mode="LAND"), 30.0)
    assert f.state == GROUND and f.latch == "operator E-STOP"
    f.on_setpoint(Setpoint(31.0, SP_VEL, 1, 0), 31.0)
    f.tick(_obs(31.0, alt=0.0, armed=False, mode="STABILIZE"), 31.0)
    assert f.state == GROUND                    # no takeoff while latched
    f.on_operator("RESUME", 32.0, _obs(32.0, alt=0.0, armed=False))
    f.on_setpoint(Setpoint(32.0, SP_VEL, 1, 0), 32.0)
    f.tick(_obs(32.0, alt=0.0, armed=False, mode="STABILIZE"), 32.0)
    assert f.state == TAKEOFF


def test_brain_rtb_latch_clears_on_landing():
    f = _airborne_guided()
    f.on_setpoint(Setpoint(11.0, SP_RTB), 11.0)
    f.tick(_obs(11.0), 11.0)
    assert f.state == RTL and f.latch == "brain RTB"
    f.tick(_obs(60.0, alt=0.0, armed=False, mode="RTL"), 60.0)
    assert f.state == GROUND and f.latch is None
