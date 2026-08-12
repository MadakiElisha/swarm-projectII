# 🛰️ SWARM-PROJECT II

### A Decentralized, Vendor-Agnostic Drone Swarm for Disaster Response

Real ArduPilot flight physics (SITL), a typed ROS 2 pub/sub architecture, a Contract-Net-style task auction, YOLOv8-based autonomous sighting → task generation, and a live 2D/3D web ground control station.

---

## 1. What This Is
Disaster response (floods, earthquakes, wildfires, maritime SAR) needs drones that can coordinate without relying on a single fragile link back to a human operator. This project is a working prototype of that: drones publish telemetry, build a live mesh of who-can-reach-whom, bid on tasks based on distance/battery, and hand off work automatically when a drone needs to return home.

## 2. Architecture

| Layer | Role | Implementation |
| --- | --- | --- |
| Flight controller | Keeps the airframe stable | ArduPilot (SITL now, Pixhawk later) |
| MAVLink | Shared telemetry/command protocol | `pymavlink` |
| Companion computer | Runs coordination logic | RPi 4/5-class (target); dev machine today |
| Mesh radio | Physical inter-drone link | Wi-Fi/LoRa (planned) |
| Mesh routing | Who-can-reach-whom | `networkx` topology in `swarm_mesh` |
| Ground control | Human oversight | Custom Leaflet + three.js GCS |
| Task coordination | Who does what | Contract-Net auction in `swarm_tasks` |
| Sensors | What drones perceive | GPS + camera (YOLOv8) |
| Backend | Vendor-agnostic drone control | `VehicleAdapter` ABC |

**Vendor-agnosticism:** The swarm brain never talks to a flight controller directly. Everything goes through a small `VehicleAdapter` interface. A proprietary adapter (e.g. DJI Mobile SDK) would implement the same interface — the coordination stack above it never changes.

## 3. Use Cases Beyond Flooding
Tasks are `label + point + priority`; swap detector classes and task prefixes and the coordination stack runs unchanged:

* Flood response (person, bus, boat -> RESCUE)
* Earthquake / collapse SAR (person, rubble -> RESCUE)
* Wildfire (fire, smoke -> FIRE-PERIMETER)
* Maritime distress (person-in-water, boat -> MARITIME)
* Infrastructure inspection (fault markers -> INSPECT)

## 4. Repository Structure
See codebase structure under `ros2_ws/src/`.

## 5. Quick Start
See codebase for launch files and prerequisites.

## 6. Testing & Reliability
* Pure cores covered by pytest.
* Crash-proof handlers: a malformed message can never kill a node.
* Idempotent task auctions: duplicate requests re-publish the stored result.

## 7. Roadmap
* **M3.5:** Wind-aware agents, per-drone auctioneer, HITL confirmation.
* **M5:** NS-3 radio fidelity, hardware cabling.

## 8. License
MIT.
