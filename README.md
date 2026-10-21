# 🛰️ SWARM-PROJECT II

### A leaderless, vendor-agnostic drone swarm for disaster response

Every drone runs the same software and decides for itself; drones agree with
each other over a lossy multi-hop radio. Nothing in the system is a single
point of failure: no auctioneer, no leader, no mesh server, no task
generator. The ground station is an optional observer and operator uplink.

* **Leaderless task allocation**: CBBA consensus auction (Choi, Brunet & How 2009)
* **Replicated state by gossip**: CRDT task registry, roster, coverage and
  observations that converge despite loss, duplication and partitions
* **Vehicle authority FSM**: E-stop > failsafes > operator RTL/LAND >
  brain watchdog > mission, so an RTL can no longer be overridden by the mission loop
* **ORCA collision avoidance** plus per-drone altitude layers, with 10 Hz velocity control
* **Shared world model**: detections projected to the ground, fused and
  de-duplicated across drones, with moving-target tracking for intercepts
* **Decentralized search**: drones split an area and re-cover gaps when a drone is lost
* **One energy model** for both bidding and battery self-checks (no
  assign-then-relinquish thrash)
* Real ArduPilot over MAVLink (ACK-checked, mode-by-name), a sim backend,
  ROS 2 Jazzy, and a Leaflet + three.js web GCS

How it works and what each mechanism guarantees: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

Demos of the previous (centralized-auction) version: [main_swarm.mp4](main_swarm.mp4) ·
[Screen.Recording.2026-09-03.124931.mp4](Screen.Recording.2026-09-03.124931.mp4)

---

## 1. Why decentralized

Floods, earthquakes, wildfires and maritime SAR need drones that keep
working when links drop, when the operator is out of range, and when drones
are lost. In this system:

| if… | then… |
|---|---|
| the GCS disconnects | drones finish their tasks, re-allocate among themselves, and return home |
| a drone dies mid-mission | its claims expire from everyone's roster, a spare drone takes its slot, and the ring reports DEGRADED then FORMED |
| the network splits | each side keeps working independently; on heal, CBBA reconciles to one executor per task |
| a battery drains faster than expected | the drone relinquishes and flies home, and another drone takes the task |
| an operator presses RTL | the vehicle FSM latches it; the mission layer cannot cancel it |

## 2. Architecture

Each drone runs two processes on its companion computer:

```
 camera ─► perception ─► drone_brain ──setpoint──► vehicle_manager ─► ArduPilot / PX4
                          ▲      │   ◄─vehicle_state──  (safety FSM)      (or SimBackend)
                 /swarm/radio    │
          (broadcast, lossy) ◄───┘──► assignments / events / suggestions ─► GCS (optional)
```

| package | role |
|---|---|
| `swarm_common` | **pure-Python core**: `brain.py` (DroneBrain), `cbba.py`, `tasks.py` (CRDT registry), `gossip.py`, `vehicle_fsm.py`, `orca.py`, `motion.py`, `energy.py`, `perception.py`, `coverage.py`, `config.py`, plus the `sim/` simulator |
| `swarm_agents` | `drone_brain` node: a thin ROS shell around DroneBrain |
| `swarm_vehicle` | `vehicle_manager` node: the only thing that commands the flight controller |
| `swarm_backends` | `VehicleAdapter` + `MavlinkBackend` (ArduPilot; PX4 best effort) + `SimBackend` |
| `swarm_interfaces` | messages: `SwarmPacket`, `VehicleState`, `Setpoint`, `NeighborReport`, … |
| `swarm_perception` | per-drone camera replay + YOLOv8 → `/swarm/<label>/detections` |
| `swarm_mesh` | `mesh_observer`: GCS-side visualisation of measured links (display only) |
| `swarm_tasks` | `target_mover`: scripted moving quarry for intercept demos (sim prop) |
| `swarm_bringup` | launch files + **`config/fleet.yaml`, the single source of truth for the fleet** |

To add a drone, add one line to `fleet.yaml`. Launch files, SITL scripts,
the GCS and the tests all read it.

## 3. Quick start

### a) No ROS at all: the simulator (seconds)

```bash
pip install pyyaml pytest
cd ros2_ws/src/swarm_common
python3 -m swarm_common.sim                    # 9 scenarios, PASS/FAIL report
python3 -m swarm_common.sim perimeter --loss 0.3 --plot /tmp/perimeter.png
python3 -m pytest -q tests                     # full core test suite
```

### b) Full ROS 2 stack with simulated vehicles (no ArduPilot)

| requirement | notes |
|---|---|
| Ubuntu 24.04 / WSL2 + ROS 2 Jazzy | `ros-jazzy-ros-base` |
| `pip install pymavlink pyyaml` | |
| `ros-jazzy-rosbridge-suite` | only for the web GCS |

```bash
cd ros2_ws && colcon build && source install/setup.bash && cd ..
ros2 launch swarm_bringup swarm_sim.launch.py loss:=0.1      # 5 drones, 10% emulated loss
python3 scripts/ros_acceptance.py                            # drive it like an operator: 6 checks
```

or `scripts/swarm_up.sh sim` (adds rosbridge + the GCS at http://localhost:8080).

### c) ArduPilot SITL

```bash
ARDUPILOT_HOME=~/ardupilot scripts/start_sitl_fleet.sh      # one SITL per fleet.yaml drone
ros2 launch swarm_bringup swarm_sitl.launch.py
python3 scripts/ros_acceptance.py
```

or `scripts/swarm_up.sh sitl`. Then `scripts/regression.sh` runs simulator
scenarios plus live acceptance and writes graphs to `reports/`.

### d) One container per drone, over a real virtual network

```bash
docker compose -f deploy/docker/docker-compose.yml up --build
deploy/docker/netem.sh loss drone3 30%
deploy/docker/netem.sh split "drone1 drone2" "drone3 drone4 drone5"
deploy/docker/netem.sh heal
```

## 4. Operating it (web GCS)

| action | what happens |
|---|---|
| click map → Dispatch | GOTO task; the nearest drone that can afford it wins by consensus, flies, holds, completes |
| `SWARM converge` → click | ring of up to 5 slots, allocated by CBBA, rotating; `PERIMETER_FORMED` banner; auto-release after the hold |
| `INTERCEPT` → click | ring centred on the fused track of the moving quarry; two cutters lead-pursue |
| `SEARCH area` → two clicks | idle drones split the rectangle, sweep it at search altitude, and raise survivor suggestions |
| pulsing amber marker | perception suggestion; **Confirm** turns it into a RESCUE task (human-in-the-loop) |
| RTL / LAND / E-STOP / RESUME | operator overrides via the vehicle FSM (latched until RESUME); `ALL` targets every drone |

Mesh lines show **measured** link quality (packet-receipt ratio): blue > 80%, amber > 50%, red below.

## 5. Testing

| what | where | CI |
|---|---|---|
| 69 core tests: CBBA convergence (lossy multi-hop, bundles, ties, dead agents), CRDT merge laws, FSM priorities, ORCA, projection, fusion, coverage | `swarm_common/tests` | ✅ |
| 9 swarm scenarios with the real brain + FSM: dispatch, perimeter, intercept, search & rescue, battery handover, drone loss + refill, partition + heal, dense crossing (10 drones, one layer), RTL sticks; plus heavy-loss variants | `swarm_common/sim/scenarios.py` | ✅ |
| MAVLink backend against a fake ArduCopter over real MAVLink/UDP: ACKs, retries, mode-by-name, pre-arm failures, no re-arm in flight, params | `swarm_backends/tests` | ✅ |
| colcon build + live ROS acceptance (A1–A6) with the sim backend | `scripts/ros_acceptance.py` | ✅ |
| live acceptance against ArduPilot SITL | `scripts/regression.sh` | manual |

## 6. Known limitations (honest)

* Simulator vehicles are point masses and its radio is a disc model with
  random loss. Use SITL plus the container/netem harness for higher fidelity.
* Gossip sends full state, which is fine to about 20 drones. Larger fleets need delta sync.
* Swarm packets are **not authenticated** yet. Add signing before any real
  deployment (see ARCHITECTURE §10).
* PX4 support in `MavlinkBackend` is written but untested; ArduPilot is the
  tested path.
* Collision avoidance is drone-to-drone only: no terrain, buildings or manned aircraft.
* Perception in sim replays still images; YOLO detections are projected with
  a flat-ground assumption (terrain data in `terrain/` is not yet used).
* Gazebo visual physics is still not working; SITL's internal physics is used.

## 7. Roadmap

**Done:** fleet + telemetry · leaderless CBBA allocation · CRDT gossip ·
vehicle authority FSM · ORCA + altitude layers · fused perception + HITL ·
decentralized search · perimeter and intercept rings · simulator + CI ·
container/netem harness.

**Next:** packet authentication · delta gossip for large fleets · terrain-aware
projection and avoidance · PX4 SITL validation · hardware P1–P4 (below) ·
CesiumJS 3D · VisDrone evaluation.

## 8. Hardware deployment (plan)

Per drone: Pixhawk (ArduPilot 4.6+), Jetson Orin Nano or RPi 5 + Hailo-8L,
CSI camera, mesh radio (802.11s/batman-adv or Mesh Rider), and a 915 MHz C2
failsafe. Run `drone.launch.py drone_id:=N backend:=mavlink
mavlink_url:=serial:///dev/ttyTHS1:921600` on each companion computer, with
link emulation off.

**Bandwidth rule:** observations cross the mesh; video never goes on the
swarm bus (pull it selectively over RTSP/WebRTC).

Phasing: P1 bench (1 real FC + 4 SITL) → P2 one real drone flying with 4 SITL
→ P3 three real → P4 five-drone field mesh test.

## 9. Safety

The vehicle FSM enforces E-stop, critical-battery RTL, geofence RTL, a brain
watchdog (hold, then RTL), and latched operator overrides. RTL altitudes are
staggered per drone. ArduPilot's own failsafes remain active underneath.
Fly VLOS first; BVLOS only under waiver.

## 10. License

MIT. Built on ArduPilot, ROS 2, Leaflet, three.js and Ultralytics YOLOv8,
with gratitude to those communities.
