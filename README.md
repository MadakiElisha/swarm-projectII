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
* **Building-aware flight** over real cities: OpenStreetMap buildings → A* routes around
  anything taller than the drone's layer, re-verified every tick, plus a look-ahead brake
* **Shared world model**: detections projected to the ground, fused and
  de-duplicated across drones; a multi-candidate tracker that locks on to the vehicle that
  actually moves (parked cars can't pull an intercept away)
* **Missions**: search & rescue, perimeter, pursue target, **perimeter patrol with
  automatic intruder intercept**, **flood recon with a shared flood map**
* **One self-calibrating energy model** for bidding and battery self-checks (no
  assign-then-relinquish thrash)
* Real ArduPilot over MAVLink (ACK-checked, mode-by-name) in **Gazebo Harmonic worlds
  generated from OSM** (any city; Lagos presets), cameras → **VisDrone-trained YOLO11**,
  ROS 2 Jazzy, and a CesiumJS 3D web GCS

How it works and what each mechanism guarantees: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** ·
fresh machine to swarm flying over Lagos: **[docs/SETUP_UBUNTU_24.04.md](docs/SETUP_UBUNTU_24.04.md)** ·
drones, radios, launch sites: **[docs/HARDWARE.md](docs/HARDWARE.md)**.

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
| `swarm_perception` | camera → JPEG (`camera_compressor`) → YOLO11 (VisDrone, optional SAHI slicing) → `/swarm/<label>/detections` |
| `swarm_mesh` | `mesh_observer`: GCS-side visualisation of measured links (display only) |
| `swarm_tasks` | `target_mover` / `gz_quarry`: the moving target for intercept demos (sim prop) |
| `swarm_bringup` | launch files + **`config/fleet.yaml`, the single source of truth for the fleet** |

To add a drone, add one line to `fleet.yaml`. Launch files, SITL scripts,
the GCS and the tests all read it.

## 3. Quick start

### a) No ROS at all: the simulator (seconds)

```bash
pip install pyyaml pytest
cd ros2_ws/src/swarm_common
python3 -m swarm_common.sim                    # 14 scenarios, PASS/FAIL report
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

### d) Gazebo city + ArduPilot + cameras (the full thing)

```bash
python3 scripts/make_area.py eko --drones 5                          # OSM buildings for Lagos Island
python3 scripts/gz/make_world.py --fleet areas/eko/fleet.yaml        # Gazebo world, drones with cameras
source sim/gz/eko/env.sh && scripts/gz/run_swarm.sh                  # Gazebo + one ArduCopter SITL each
SWARM_FLEET=areas/eko/fleet.yaml ros2 launch swarm_bringup swarm_gazebo.launch.py
```

Step-by-step for a fresh Ubuntu 24.04 + NVIDIA machine, detector training and
troubleshooting: [docs/SETUP_UBUNTU_24.04.md](docs/SETUP_UBUNTU_24.04.md).

### e) One container per drone, over a real virtual network

```bash
docker compose -f deploy/docker/docker-compose.yml up --build
deploy/docker/netem.sh loss drone3 30%
deploy/docker/netem.sh split "drone1 drone2" "drone3 drone4 drone5"
deploy/docker/netem.sh heal
```

## 4. Missions

| mission | operator does | the swarm does (no leader) |
|---|---|---|
| Search & rescue `SEARCH-n` | marks an area | splits it, re-covers gaps of lost drones; fused "person" sightings → RESCUE suggestion → operator confirms → one drone goes |
| Perimeter `SWARM-n` | clicks a point | ring slots by consensus; holds, refills a lost drone's slot, releases |
| Pursue target `INTERCEPT-n` | clicks the vehicle | locks on to the one that moves away from the click; ring follows the fused track, cutters lead it |
| Perimeter patrol `PATROL-n` | clicks a centre + radius | standing patrol ring with a reserve; anything moving inside → `INTRUDER` → automatic intercept by the nearest patrollers; batteries hand over shifts |
| Flood recon `FLOOD-n` | marks a district | survey + flood map (cells seen under water, merged by gossip), stranded people flagged, `FLOOD_MAP` report |

## 5. The web GCS

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
| Coverage | the searched-cells G-Set filling in; flood map in blue |
| Buildings | the area's OSM buildings coloured by height (or white), Cesium OSM Buildings / Google Photorealistic 3D Tiles with a token |
| Sensors | camera footprints, the selected drone's frustum, every drone's sightings |
| Target | fused constant-velocity track with uncertainty and a 30 s prediction (plus sim ground truth) |
| Fleet panel | phase, task, battery with a "needed to get home" marker, learned drain ×, links, FSM locks |
| Swarm mind | tasks with per-slot consensus state and an event feed (claims, handovers, losses, perimeter events) |

Drones bank and pitch from their real acceleration, props spin with throttle, a lost drone falls.
Timeline scrubbing replays any moment. Click a drone to select it and double-click to ride along.
Live mode adds operator tools (Dispatch, Perimeter, Intercept, Search, Patrol, Flood recon, RTL/LAND/RESUME/E-STOP, ALL).

* `?replay=demos/x.json` · `?live=ws://host:9090` · `?lite=1` (phones/weak GPUs) · `?t=500` (start time)
* Settings ⚙: paste a free [Cesium ion](https://ion.cesium.com) token for world terrain, 3D buildings and
  photorealistic tiles; choose the building style; open the other mission recordings.
* Recordings: `demos/showcase.json`, `demos/patrol.json`, `demos/flood.json`. Record your own:
  `python3 scripts/record_demo.py --mission patrol --fleet areas/eko/fleet.yaml` (flies among real buildings).
* Publish the replay at a public link: enable GitHub Pages (Source: GitHub Actions), then run the
  **Publish GCS demo** workflow.
* The previous 2D/three.js page is kept as `gcs/legacy.html`.

## 6. Testing

| what | where | CI |
|---|---|---|
| 85 core tests: CBBA convergence (lossy multi-hop, bundles, ties, dead agents), CRDT merge laws, FSM priorities (incl. slow pre-arm / slow climb), ORCA, projection, fusion, coverage, target tracker vs parked cars | `swarm_common/tests` | ✅ |
| 14 swarm scenarios with the real brain + FSM: miscalibrated batteries, dispatch, perimeter, intercept, intercept among 8 parked look-alikes, search & rescue, flood recon, patrol + intruder, city ops among 110 m towers (0 building strikes), battery handover, drone loss + refill, partition + heal, dense crossing, RTL sticks; plus heavy-loss variants | `swarm_common/sim/scenarios.py` | ✅ |
| MAVLink backend against a fake ArduCopter over real MAVLink/UDP: ACKs, retries, mode-by-name, pre-arm failures, no re-arm in flight, params | `swarm_backends/tests` | ✅ |
| colcon build + live ROS acceptance (A1–A6) with the sim backend | `scripts/ros_acceptance.py` | ✅ |
| live acceptance against ArduPilot SITL | `scripts/regression.sh` | manual |
| live acceptance against ArduPilot SITL **in Gazebo physics** (OSM city world): 6/6 | `scripts/gz/run_swarm.sh` + `ros_acceptance.py` | manual |

## 7. Known limitations (honest)

* The fast simulator's vehicles are point masses and its radio is a disc model with
  random loss. Gazebo + SITL gives real physics; the container/netem harness a real network.
* Gossip sends full state, which is fine to about 20 drones. Larger fleets need delta sync.
* Swarm packets are **not authenticated** yet. Add signing before any real
  deployment (see ARCHITECTURE §10).
* PX4 support in `MavlinkBackend` is written but untested; ArduPilot is the
  tested path.
* Buildings come from OSM: a building with a missing/low height tag is a real risk.
  No terrain or manned-aircraft avoidance yet.
* YOLO detections are projected with a flat-ground assumption.
* Flood mapping runs camera → water cells → shared map, but the only water
  detector so far is a colour baseline for Gazebo; real floodwater needs a
  segmentation model (FloodNet) passed as `water_model`.
* Clocks must be synchronised (GPS time + chrony) on real drones.

## 8. Roadmap

**Done:** leaderless CBBA allocation · CRDT gossip · vehicle authority FSM ·
ORCA + altitude layers · OSM building-aware routing · fused perception + HITL ·
target tracker · search, perimeter, intercept, patrol + auto-intercept, flood recon ·
Gazebo Harmonic + ArduPilot worlds from OSM · VisDrone training pipeline ·
CesiumJS 3D GCS · simulator + CI · container/netem harness.

**Next:** FloodNet water segmentation on the camera path · packet authentication ·
delta gossip for large fleets · terrain-aware projection · PX4 SITL validation ·
hardware P0–P4.

## 9. Hardware deployment

Per drone: Pixhawk (ArduCopter 4.6), Jetson Orin Nano or RPi 5 + Hailo-8L,
camera, mesh radio, a separate C2 failsafe link, GPS-synced clock. Co-located
launch (one site, pads 15 m apart, take off together) and distributed launch
(drones staged at different sites across a region, joined by relays or a
backhaul) are both supported; parameters, wiring, phasing P0–P4 and the
trade-offs: **[docs/HARDWARE.md](docs/HARDWARE.md)**.

**Bandwidth rule:** observations cross the mesh; video never goes on the
swarm bus (pull it selectively over RTSP/WebRTC).

## 10. Safety

The vehicle FSM enforces E-stop, critical-battery RTL, geofence RTL, a brain
watchdog (hold, then RTL), and latched operator overrides. RTL altitudes are
staggered per drone. ArduPilot's own failsafes remain active underneath.
Fly VLOS first; BVLOS only under waiver.

## 11. License

MIT. Built on ArduPilot, ROS 2, Gazebo, CesiumJS, OpenStreetMap data (ODbL),
the VisDrone dataset and Ultralytics YOLO, with gratitude to those communities.
