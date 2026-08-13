

https://github.com/user-attachments/assets/fb174598-473b-4603-9ef0-38e4017aa85b



# 🛰️ SWARM-PROJECT II

### A Decentralized, Vendor-Agnostic Drone Swarm

Real ArduPilot flight physics (SITL), a typed ROS 2 pub/sub architecture,
a Contract-Net-style task auction, YOLOv8-based autonomous sighting → task
generation, and a live 2D/3D web ground control station — built from pure
`pymavlink` telemetry scripts up to a coordinated 5-drone fleet. Can be scaled.

---

## 1. What This Is

Disaster response (floods, earthquakes, wildfires, maritime SAR) needs
drones that can coordinate without relying on a single fragile link back
to a human operator. This project is a working prototype of that: drones
publish telemetry, build a live mesh of who-can-reach-whom, bid on tasks
based on distance/battery, and hand off work automatically when a drone
needs to return home — all validated against real ArduPilot flight physics
in SITL.

## 2. Architecture

    Cloud dashboard
            ↑
    Mesh radio network (LoRa/Meshtastic relay chain)
            ↑
    Companion computer (RPi/Jetson — task logic, mesh software, ROS 2)
            ↑
    MAVLink (shared language) ←→ DJI translator (proprietary)
            ↑
    Flight controller (PX4/ArduPilot)

| Layer | Role | Implementation |
| --- | --- | --- |
| Flight controller | Keeps the airframe stable | ArduPilot (SITL now, Hardware later) |
| MAVLink | Shared telemetry/command protocol | `pymavlink` |
| Companion computer | Runs coordination logic | RPi 5 + Halio-8L, Jetson Orin Nano |
| Mesh radio | Physical inter-drone link | Wi-Fi/LoRa |
| Mesh routing | Who-can-reach-whom | `networkx`-based topology in `swarm_mesh` |
| Ground control | Human oversight | Custom Leaflet + three.js GCS (`gcs/index.html`) |
| Task coordination | Who does what | Contract-Net-style auction in `swarm_tasks` |
| Sensors | What drones perceive | GPS + camera (YOLOv8) |
| Backend | Vendor-agnostic drone control | `VehicleAdapter` (`MavlinkBackend`, `SimBackend`) |

**Vendor-agnosticism:** The swarm brain (mesh, auction, agents, GCS) never
talks to a flight controller directly. Everything goes through a small
`VehicleAdapter` interface. `MavlinkBackend` implements it for ArduPilot/PX4;
`SimBackend` implements it as a kinematic simulator for chaos testing. A
proprietary adapter (e.g. DJI Mobile/Cloud SDK) would implement the same
interface — the coordination stack above it never changes.

## 3. Use Cases Beyond Flooding

Tasks are `label + point + priority`; swap detector classes and task
prefixes and the coordination stack runs unchanged:

| Scenario | Detector classes | Task type |
| --- | --- | --- |
| Flood response (demo) | person, bus, boat | RESCUE |
| Earthquake / collapse SAR | person, rubble | RESCUE |
| Wildfire | fire, smoke | FIRE-PERIMETER |
| Maritime distress | person-in-water, boat | MARITIME |
| Post-disaster recon | (waypoint survey) | RECON |
| Medical resupply | survivor clusters | DELIVER |
| Infrastructure inspection | fault markers | INSPECT |
| Traffic incident | car, truck | INCIDENT |
| Perimeter security | intrusion classes | VANTAGE |

## 4. Repository Structure

    swarm-project/
    ├── ros2_ws/src/
    │   ├── swarm_interfaces/   # typed msgs (telemetry, mesh, tasks, relinquish…)
    │   ├── swarm_common/       # pure, tested cores: mesh/auction/vision/validation
    │   ├── swarm_backends/     # VehicleAdapter ABC + MavlinkBackend + SimBackend
    │   ├── swarm_mavlink/      # mavlink_bridge + command_bridge nodes
    │   ├── swarm_mesh/         # mesh_builder
    │   ├── swarm_tasks/        # task_auctioneer (+ watchdog, re-auction, idempotency)
    │   ├── swarm_agents/       # agent_core (pure) + agent_node
    │   ├── swarm_perception/   # image_replay, perception_node, task_generator
    │   └── swarm_bringup/      # launch files
    ├── scripts/                # fleet launcher, watchdog, task injector
    ├── gcs/index.html          # 2D + 3D ground control station (no build step)
    ├── tests/                  # pytest for pure cores
    └── README.md

## 5. Quick Start

Prerequisites:

| Requirement | Notes |
| --- | --- |
| Ubuntu 24.04 / WSL2 | tested on WSL2 |
| ROS 2 Jazzy | desktop install |
| ArduPilot SITL | built at `~/ardupilot` |
| `ros-jazzy-rosbridge-suite`, `ros-jazzy-rmw-zenoh-cpp` | GCS + Zenoh transport |
| Python | `pymavlink`, `ultralytics`, `opencv-python` |

Build & run (one terminal each):

    cd ros2_ws && source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install && source install/setup.bash
    scripts/start_sitl_fleet.sh                          # T1 — 5x ArduPilot SITL
    ros2 run rmw_zenoh_cpp rmw_zenohd                    # T2 — Zenoh router
    ros2 launch swarm_bringup swarm_real.launch.py       # T3 — mesh + bridges
    ros2 launch swarm_bringup swarm_agents.launch.py     # T4 — agents
    ros2 launch swarm_bringup swarm_perception.launch.py # T5 — YOLOv8 perception
    ros2 launch rosbridge_server rosbridge_websocket_launch.xml  # T6 — GCS bridge
    cd gcs && python3 -m http.server 8080                # T7 → localhost:8080

Operate:

| Action | Result |
| --- | --- |
| Click map → ★ Dispatch | auction → winner flies to the star |
| (autonomous) | YOLO sightings spawn RESCUE stars and launch drones |
| (autonomous) | low battery → relinquish → re-auction → handover → home |
| Select drone → TAKEOFF/RTL/LAND | real MAVLink control, live ACKs |
| 3D panel ⤢ full | fullscreen tactical view (orbit/pan/follow) |

## 6. Testing & Reliability Posture

- Pure cores (mesh, auction, vision, validation) covered by pytest.
- Boundary validation on every inbound field (lat/lon/battery/label).
- Crash-proof handlers: a malformed message can never kill a node.
- One persistent reading MAVLink link per drone (SITL-safe by design).
- Abort channel: RTL cancels in-flight gotos.
- Watchdogs at two layers: fleet heartbeat (revive) and auction dead-member
  coverage — a drone can't rely solely on self-reporting its own death.
- Idempotent task auctions: duplicate requests re-publish the stored result
  instead of re-auctioning, so retries over a lossy link are safe.

## 7. Known Limitation — Gazebo Visual Physics

3D physics visualization via Gazebo + the ArduPilot Gazebo plugin was
attempted and is not currently working; the swarm runs on ArduPilot
SITL's internal physics model instead (still real flight dynamics, just
not rendered). This does not affect flight logic, mesh, auction, or
perception — only the 3D rendered view.

## 8. Roadmap

- **M3.5** — environmental agents: wind-aware budgets (`WIND_EST`),
  climb-to-heal links; per-drone auctioneer + kill/partition proofs
  (true decentralization of task coordination); Human-in-the-Loop (HITL)
  "Autonomy-to-Suggest" confirmation for YOLO tasks.
- **M5** — NS-3 radio fidelity; mesh-as-communication-constraint relay;
  advisory NNs on auction logs; hardware cabling; CesiumJS/Gazebo photoreal.

## 9. License

MIT — see package manifests. Built on ArduPilot, ROS 2, Zenoh, Leaflet,
three.js, and Ultralytics YOLOv8; with gratitude to those communities.
