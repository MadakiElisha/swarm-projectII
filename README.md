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
* **One self-calibrating energy model** for bidding and battery self-checks (no
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

## 4. The web GCS

A CesiumJS 3D ground station that shows **what the swarm is thinking**, not just where it is.

```bash
cd gcs && python3 -m http.server 8080        # open http://localhost:8080
```

With no swarm running, it plays the recorded showcase mission (`gcs/demos/showcase.json`). Seven drones
launch together, search a flood zone, fuse sightings and rescue, form a perimeter, lose a drone (a spare
takes its slot), then intercept a moving target. With rosbridge up it goes **live** and decodes the
drones' own gossip packets from `/swarm/radio`.

| layer | what it shows |
|---|---|
| Links · Packets | measured radio links (colour = packet-receipt ratio), beacons and gossip packets in flight |
| Consensus | every work item, the drone(s) each brain believes holds it; amber = drones still disagree, green = agreed |
| Avoidance | ORCA bubbles when drones on one altitude layer get close |
| Coverage | the searched-cells G-Set filling in |
| Sensors | camera footprints, the selected drone's frustum, every drone's sightings |
| Target | fused constant-velocity track with uncertainty and a 30 s prediction (plus sim ground truth) |
| Fleet panel | phase, task, battery with a "needed to get home" marker, learned drain ×, links, FSM locks |
| Swarm mind | tasks with per-slot consensus state and an event feed (claims, handovers, losses, perimeter events) |

Drones bank and pitch from their real acceleration, props spin with throttle, a lost drone falls.
Timeline scrubbing replays any moment. Click a drone to select it and double-click to ride along.
Live mode adds operator tools (Dispatch, Perimeter, Intercept, Search area, RTL/LAND/RESUME/E-STOP, ALL).

* `?replay=demos/x.json` · `?live=ws://host:9090` · `?lite=1` (phones/weak GPUs) · `?t=500` (start time)
* Settings ⚙: paste a free [Cesium ion](https://ion.cesium.com) token for world terrain + 3D buildings.
* Record your own mission: `python3 scripts/record_demo.py` (any simulator scenario can be recorded).
* Publish the replay at a public link: enable GitHub Pages (Source: GitHub Actions), then run the
  **Publish GCS demo** workflow.
* The previous 2D/three.js page is kept as `gcs/legacy.html`.

## 5. Testing

| what | where | CI |
|---|---|---|
| 71 core tests: CBBA convergence (lossy multi-hop, bundles, ties, dead agents), CRDT merge laws, FSM priorities, ORCA, projection, fusion, coverage | `swarm_common/tests` | ✅ |
| 10 swarm scenarios with the real brain + FSM: miscalibrated batteries (in-flight drain learning), dispatch, perimeter, intercept, search & rescue, battery handover, drone loss + refill, partition + heal, dense crossing (10 drones, one layer), RTL sticks; plus heavy-loss variants | `swarm_common/sim/scenarios.py` | ✅ |
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
