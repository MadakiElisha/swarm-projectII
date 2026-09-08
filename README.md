# 🛰️ SWARM-PROJECT II

### A Decentralized, Vendor-Agnostic Cognitive Drone Swarm

Real ArduPilot flight physics (SITL), a typed ROS 2 pub/sub architecture over
Zenoh, a Contract-Net task auction with replicated self-healing coordination,
per-drone energy cognition, YOLOv8 sightings with human-in-the-loop dispatch,
synchronized perimeter maneuvers, moving-target pursuit, mission-state
feedback, and a live 2D/3D web GCS — gated by an automated regression suite.

Demos: [main_swarm.mp4](main_swarm.mp4) ·
[Screen.Recording.2026-09-03.124931.mp4](Screen.Recording.2026-09-03.124931.mp4) ·
one-pager: [docs/swarm_one_pager.pdf](docs/swarm_one_pager.pdf)

<img width="1917" height="1078" alt="Screenshot 2026-09-04 121209" src="https://github.com/user-attachments/assets/3564bdb8-5c8a-48a5-a3fa-0b09c24b9b98" />

<img width="1917" height="1020" alt="Screenshot 2026-09-04 164611" src="https://github.com/user-attachments/assets/2dfbb28c-012f-443b-b303-8abb7d6dc475" />


---

## 1. What This Is

Disaster response (floods, earthquakes, wildfires, maritime SAR) needs drones
that coordinate without relying on a single fragile link back to a human
operator. This project is a working prototype of that: drones publish
telemetry, build a live mesh of who-can-reach-whom, bid on tasks based on
distance/battery/wind, veto unsafe work, relinquish and hand off tasks when depleted, form
perimeters, pursue moving targets, and *declare their own mission state*
(FORMED / DEGRADED / RELEASED) — all validated against real ArduPilot flight
physics in SITL, and shaped for real hardware.

## 2. Architecture

    Cloud dashboard/GCS
            ↑
    Mesh radio network (802.11s/batman-adv or Mesh Rider)
            ↑
    Companion computer (Jetson Orin Nano/RPI 5 + Halio8L — perception, agent, bridge)
            ↑
    MAVLink (shared language) ←→ proprietary adapter possible (e.g DJI SDK)
            ↑
    Flight controller (ArduPilot/PX4)

| Layer | Role | Implementation |
| --- | --- | --- |
| Flight controller | Keeps the airframe stable | ArduPilot (SITL) |
| MAVLink | Shared telemetry/command protocol | `pymavlink` via `MavlinkBackend` |
| Companion | Runs cognition + perception | Jetson Orin Nano/RPI 5 + Halio8L |
| Mesh routing | Who-can-reach-whom | `networkx` topology in `swarm_mesh` |
| Transport | Pub/sub, mesh-friendly | ROS 2 Jazzy over **Zenoh** (peer mode) |
| Ground control | Human oversight | Custom Leaflet + three.js GCS (`gcs/`) |
| Task coordination | Who does what | Contract-Net auction, replicated + elected leader |
| Sensors | What drones perceive | GPS + camera (YOLOv8, namespaced per drone) |
| Backend | Vendor-agnostic control | `VehicleAdapter` (`MavlinkBackend`, `SimBackend`) |

**Vendor-agnosticism:** the swarm brain (mesh, auction, agents, GCS) never
talks to a flight controller directly. Everything goes through the small
`VehicleAdapter` interface; a proprietary adapter implements the same
interface and the coordination stack above it never changes.

**Live data flow:**

    cameras Dx -> perception Dx -> /swarm/detections -> task_generator -> /swarm/task_requests
    /swarm/telemetry -> mesh_builder -> /swarm/mesh_topology -+
    /swarm/task_requests -> auction replicas (elected leader) -> /swarm/task_assignments
    /swarm/task_assignments -> mavlink_bridge Dx -> ArduPilot (SITL or real FC)
    bridges -> /swarm/mission_status -> leader aggregation -> /swarm/mission_event -> GCS banner

**Key topics:** `/swarm/telemetry` · `/swarm/mesh_topology` ·
`/swarm/task_requests` · `/swarm/task_assignments` · `/swarm/mission_status` ·
`/swarm/mission_event` · `/swarm/target_track` · `/swarm/detections` ·
`/swarm/Dx/camera/compressed` · `/swarm/auction_alive`

**Decentralization audit:** execution, cognition (battery vetoes, relinquish,
climb-to-heal) and pursuit are per-drone; the auction leader is *elected,
replicated, kill-tolerant* (kill it: a standby promotes in ~3 s); rosbridge/GCS
are operator-side only, never autonomy dependencies.

## 3. Use Cases

Verified end-to-end in SITL:

| Mission | Trigger | Verified swarm behavior |
| --- | --- | --- |
| Flood / disaster SAR | YOLO person sighting → amber suggestion → human confirm | nearest *eligible* drone dispatched (mesh + battery aware); wind-budgeted; low-battery relinquish + handover |
| Perimeter / static intercept | `SWARM converge` → one click | simultaneous lift, rotating 300 m ring, staggered alts, GO/NO-GO preflight, `PERIMETER FORMED` banner, auto-release RTL |
| Moving-target pursuit | `INTERCEPT` → one click (mover auto-starts) | ring chases live `TargetTrack`; lead-pursuit cutters; stale-track orbit hold; human release |

Extensible by construction — tasks are `label + point + priority`; swap
detector classes and prefixes and the coordination stack runs unchanged:

| Scenario | Detector classes | Task type |
| --- | --- | --- |
| Flood response (demo) | person, bus, boat | RESCUE |
| Earthquake / collapse SAR | person, rubble | RESCUE |
| Wildfire | fire, smoke | FIRE-PERIMETER |
| Maritime distress | person-in-water, boat | MARITIME |
| Post-disaster recon | (waypoint survey) | RECON |
| Medical resupply | survivor clusters | DELIVER |
| Infrastructure inspection | fault markers | INSPECT |
| Perimeter security | intrusion classes | VANTAGE |

## 4. Behavior Pipeline

    detect -> auction -> converge -> declare -> pursue -> release

1. **Detect** — per-drone YOLO publishes typed `DetectionArray`; person
   sightings become `RESCUE-` requests held as amber suggestions until a
   human confirms (HITL).
2. **Auction** — contract-net bids scored by distance + wind-aware battery
   belief; reachability over the mesh graph; unsafe bids vetoed locally.
3. **Converge** — winners lift simultaneously into rotating ring slots with
   staggered altitudes; GO/NO-GO preflight gates every takeoff.
4. **Declare** — bridges self-report `ENROUTE / ON_STATION / RELEASED`
   (radial band test); the leader emits exactly one `PERIMETER_FORMED`
   (or `DEGRADED` / `RELEASED`) event → GCS banner + logs.
5. **Pursue** — `INTERCEPT-` tasks re-center the ring on the live
   `TargetTrack`; two cutters hold lead-pursuit slots; stale track degrades
   to orbiting the last fix.
6. **Release** — human command, battery relinquish, or hold expiry → RTL.

## 5. GCS & Visualization

- **2D:** Leaflet satellite map, roster with live battery bars, mission
  history, dispatch popups, HITL suggestion stars, perimeter rings, red
  quarry marker + dashed chase trail.
- **3D:** three.js ops panel — X500-style airframes (carbon X-arms, motor
  bells, spinning props, skids, gimbal), 5 Hz attitude-first rendering with
  correct YXZ aircraft order, velocity arrows, comet streaks, altitude/speed
  chips, battery halos + ground beams, explanatory legend, mission banner,
  live 3D quarry + moving intercept ring, follow-cam on double-click,
  logarithmic depth buffer for km-scale stability.
- Note: This was built used the ArduPilot *Gazebo plugin* path was attempted and kept crashing. Abandoned for now, will try again later. Gazebo remains an optional B-roll experiment.

## 6. Repository Structure

    swarm-project/
    ├── ros2_ws/src/
    │   ├── swarm_interfaces/   # typed msgs (telemetry, mesh, tasks, status, events, tracks, detections)
    │   ├── swarm_common/       # config, validation, vision core, pure math + pytest tests
    │   ├── swarm_backends/     # VehicleAdapter ABC + MavlinkBackend + SimBackend
    │   ├── swarm_mavlink/      # per-drone bridge: telemetry, commands, preflight, mission execution
    │   ├── swarm_mesh/         # mesh_builder
    │   ├── swarm_tasks/        # auctioneer core + resident fleeing-target mover
    │   ├── swarm_agents/       # cognitive agents + replicated auctioneers (elected leader)
    │   ├── swarm_perception/   # namespaced per-drone YOLO + task_generator
    │   └── swarm_bringup/      # launch files + fleet.yaml
    ├── gcs/                    # web GCS (2D Leaflet + 3D three.js, no build step)
    ├── scripts/                # fleet start, regression gate + graphs, swarm_up/down
    ├── docs/                   # one-pager (HTML + PDF)
    ├── reports/                # regression acceptance graphs + history
    └── README.md

## 7. Quick Start

| Requirement | Notes |
| --- | --- |
| Ubuntu 24.04 / WSL2 | tested on WSL2 |
| ROS 2 Jazzy | desktop install |
| ArduPilot SITL | 5 daemons via `scripts/start_sitl_fleet.sh` |
| `ros-jazzy-rosbridge-suite`, `ros-jazzy-rmw-zenoh-cpp` | GCS + Zenoh transport |
| Python | vision venv (`ultralytics`, `opencv-python`), `python3-matplotlib` |

    T1  scripts/start_sitl_fleet.sh              # wait HEALTHY + 45 s
    T2  ros2 run rmw_zenoh_cpp rmw_zenohd
    T3  ros2 launch swarm_bringup swarm_real.launch.py
    T4  ros2 launch swarm_bringup swarm_agents.launch.py
    T5  ros2 launch swarm_bringup swarm_perception.launch.py
    T6  ros2 launch rosbridge_server rosbridge_websocket_launch.xml
    T7  cd gcs && python3 -m http.server 8080    # open http://localhost:8080

One-command alternative: `scripts/swarm_up.sh` / `scripts/swarm_down.sh`.

Operate:

| Action | Result |
| --- | --- |
| Click map → Dispatch | auction → winner flies the wind-budgeted leg |
| (autonomous) | YOLO sightings spawn amber RESCUE suggestions (HITL confirm) |
| (autonomous) | low battery → relinquish → re-auction → handover → home |
| `SWARM converge` → click | five lift as one, rotating perimeter, FORMED banner, auto-RTL |
| `INTERCEPT` → click | mover auto-starts; ring chases the red quarry with cutters |
| Select drone → ARM/TAKEOFF/RTL/LAND | real MAVLink control, live ACKs |
| 3D panel ⤢ full / double-click | fullscreen tactical view / follow-cam |

## 8. Testing & Reliability Posture

- `scripts/regression.sh` — self-flying acceptance gate on a fresh fleet:
  C1 telemetry×5 · C2 mesh links · C3 five auction replicas · C4 five
  assignments · C5 PERIMETER_FORMED (<240 s, 120 m radial band) · C6 mover
  auto-start. Emits `reports/run_*.png` acceptance graphs + `history.csv`.
- `python3 -m pytest ros2_ws/src/swarm_common/tests -q` — fast core tests.
- Boundary validation on every inbound field; crash-proof handlers (a
  malformed message can never kill a node); abort channel (RTL cancels
  in-flight gotos); two-layer watchdogs (fleet heartbeat + auction
  dead-member coverage); idempotent auctions (safe retries over lossy links).

## 9. Known Limitations (honest)

- Gazebo visual physics attempted, currently not working; SITL internal physics is used
  (real dynamics, not rendered). Does not affect logic.
- Single-machine sim: the mesh is distance-derived; real radio loss/latency
  not yet exercised (radio-realism milestone queued).
- Five YOLO instances share one laptop CPU in sim (~0.4 Hz aggregate); on
  hardware each drone runs its own Jetson and this disappears.
- 3D ground is flat satellite tiles (no building geometry); photoreal
  (CesiumJS) queued.
- Batteries drain ~1 %/4 s under load in SITL — demos and the regression
  gate need fresh fleets.

## 10. Roadmap

**Done:** M1 fleet+telemetry · M2 mesh+auction · M3 perception/HITL, wind
budgets, self-healing replicated auctioneers, synchronized perimeter,
mission-state feedback · M3.7 pursuit · M4.1 namespaced perception · viz arc ·
Phase H hardening (gate, graphs, tests, one-command bring-up).

**Next:** consolidation pass + deterministic mission-math tests · safety pack
(geofence, RTL-on-link-loss, E-stop) · radio realism (loss/latency injection,
NS-3) · **hardware P1–P4** · CesiumJS/Gazebo B-roll · advisory NNs · VisDrone
evaluation.

## 11. Hardware Deployment (plan)

Per drone: Pixhawk (ArduPilot 4.6+), Jetson Orin Nano, CSI cam, mesh radio,
915 MHz C2 failsafe. **Bandwidth rule:** detections cross the mesh; video is
pulled selectively (RTSP/WebRTC), never on the ROS bus. Phasing: P1 bench
(1 real FC + 4 SITL, one launch file, two worlds) → P2 1-real+4-SITL flight →
P3 3 real → P4 5-real field mesh test.

## 12. Safety

Sim enforces GO/NO-GO preflight, battery vetoes, relinquish. Hardware adds
geofence, RTL-on-link-loss, RC override, VLOS-first operations (BVLOS under
waiver).

## 13. License & Contact

MIT · see package manifests · Built on ArduPilot, ROS 2, Zenoh, Leaflet, three.js, Ultralytics YOLOv8 —
with gratitude to those communities.
