# Hardware deployment

The software that flies is the software you ran in Gazebo: `drone.launch.py`
on each companion computer runs `vehicle_manager` (safety FSM → the flight
controller over MAVLink) and `drone_brain` (gossip, CBBA, planning,
perception fusion). There is no server. The only per-drone difference is
one line in `fleet.yaml`.

## 1. One drone

| part | suggestion | why |
|---|---|---|
| frame | 450–650 mm quad, 20–30 min endurance with camera | what the energy model and 30–60 m altitude layers assume |
| flight controller | Pixhawk 6C / Cube Orange, **ArduCopter 4.6.x** (tested: Copter-4.6.3) | same firmware as SITL |
| companion | Jetson Orin Nano 8 GB (TensorRT), or Raspberry Pi 5 + Hailo-8L | YOLO11s at 5–15 fps on 1024 px |
| camera | global-shutter or good rolling-shutter, nadir or 2-axis gimbal (record the pitch in `perception:`) | projection uses camera pitch + vehicle attitude |
| swarm radio | 802.11s / batman-adv mesh: Doodle Labs Mesh Rider, Silvus, or Wi-Fi HaLow for cheap trials | the gossip bus, multi-hop |
| C2 failsafe | separate 868/915 MHz telemetry or RC link to each FC | operator RTL/E-STOP even if the mesh dies |
| time | GPS time into the companion via `gpsd` + `chrony` | brains compare timestamps (task age, ring rotation clock): keep clocks within ~100 ms |

Wiring: FC TELEM2 ↔ companion UART (`SERIAL2_PROTOCOL 2`, `SERIAL2_BAUD 921`),
then `mavlink_url: serial:///dev/ttyTHS1:921600` (Jetson) or `/dev/ttyAMA0` (Pi).

ArduPilot parameters to set per drone (beyond a normal tune):

| param | value |
|---|---|
| `SYSID_THISMAV` | the drone's `id` in fleet.yaml |
| `RTL_ALT` | staggered like the brain's altitude layers: 3000 + 600·((id−1) mod 5) cm; with more than 5 drones raise `motion.layers` so no two share an RTL height |
| `FENCE_ENABLE`, `FENCE_RADIUS`, `FENCE_ALT_MAX` | slightly *outside* the swarm geofence (FC is the backstop) |
| `BATT_*`, `BATT_FS_LOW_ACT=2` (RTL), `BATT_FS_CRT_ACT=1` (LAND) | ArduPilot's own failsafes stay on underneath the swarm FSM |
| `FS_GCS_ENABLE` | 0 for the MAVLink link to the companion (the swarm FSM owns that watchdog); keep RC/C2 failsafe on |
| `GUID_OPTIONS` | 0 (default) |

On the companion:

```bash
ros2 launch swarm_bringup drone.launch.py drone_id:=3 backend:=mavlink \
     mavlink_url:=serial:///dev/ttyTHS1:921600 link_emulation:=false
# camera driver -> /swarm/D3/camera/image (e.g. v4l2_camera / gscam), then:
ros2 run swarm_perception camera_compressor --ros-args -p drone_label:=D3 -p max_hz:=5.0
ros2 run swarm_perception perception_node --ros-args -p drone_label:=D3 \
     -p model_path:=$HOME/swarm_models/visdrone_yolo11s.engine -p min_confidence:=0.35
```

Set `ROS_DOMAIN_ID` the same on every drone and the GCS; use a DDS/Zenoh config
that only uses the mesh interface. Video never goes on the swarm bus (pull it
on demand over RTSP/WebRTC).

## 2. Where the drones take off

### a) Co-located: one launch site, take off together

This is what `scripts/make_area.py` produces and what Gazebo runs.

* Pads ≥ 15 m apart (more than twice the 6 m safety radius), one `home_lat/home_lon`
  per drone in fleet.yaml. Each drone returns to **its own** pad.
* All drones can take off at once: each climbs to its own altitude layer (30, 36, 42 … m)
  before turning, so climb-outs never cross at the same height.
* Landing is precise over the pad (the brain centres within 2.5 m before LAND).
* Radio is trivial at launch; the mesh stretches as they spread. Keep the
  furthest task within multi-hop range (a ring of 5 at 300 m radius is fine on
  any mesh radio).

### b) Distributed: drones staged at different sites across a region

Nothing in the software assumes one site:

* Give each drone the coordinates of **its own site** as its home. The swarm
  origin is just the map frame (put it at the region's centre) and the geofence
  radius must cover the whole region.
* CBBA bids include the distance from where each drone *is*, and the energy
  model checks "task + return to **my** home": the drone staged nearest a task
  wins it, and nobody accepts a task it can't fly home from.
* Drones only cooperate with drones they can hear. Sites beyond radio range form
  **separate partitions**; each works on the tasks it knows and they reconcile
  when they meet (the `partition_heal` scenario). For one coherent swarm across a
  region you need either:
  * a **relay**: a drone (or a mast/aerostat) parked between sites as a mesh hop, or
  * a **backhaul**: an LTE/Starlink bridge at each site carrying `/swarm/radio`
    between site meshes (the brains don't care how packets travel; latency
    under ~1 s is fine).
* The operator's tasks travel by gossip, so the GCS must reach at least one drone
  in each partition (or go through the backhaul).
* Battery: a distributed launch shortens the average leg to a task, which is the
  point; the per-drone energy check keeps the far ones from over-committing.

Rule of thumb: co-located for SAR / perimeter around one incident; distributed
for standing patrol of a long perimeter, a coastline, or a city-wide flood
survey, where each site covers its neighbourhood and drones migrate to where
the work is.

## 3. Phased bring-up

| phase | setup | pass criteria |
|---|---|---|
| **P0 bench** | 1 real FC (props off) + 4 SITL on a laptop, mesh radios on the bench | `ros_acceptance.py` 6/6; RTL / E-STOP from GCS and from the C2 radio |
| **P1 tethered hover** | 1 drone, real companion + camera | takeoff/hold/land by the FSM; detections at 30 m match the ground truth markers within 5 m |
| **P2 one real + 4 virtual** | 1 drone flying, 4 SITL on the GCS laptop gossiping over the same mesh | the real drone takes its CBBA share of a search; ring slot hand-over to/from SITL drones |
| **P3 three real** | co-located launch | perimeter forms/holds/releases; one drone RTL'd mid-ring → spare refills; kill the GCS → mission continues |
| **P4 five real, field mesh** | co-located then two sites 1–2 km apart with a relay | search + rescue confirmation; patrol with an intruder vehicle; partition → heal |

Fly VLOS with a safety pilot per drone (RC override) until P4 is boring.

## 4. Regulatory (Nigeria and elsewhere)

Multi-drone, BVLOS and night operations need explicit approval. In Nigeria that
means NCAA RPAS authorisation and the security clearance that goes with it; check
the current NCAA requirements before any flight outside a closed test range.
Everywhere: remote ID where required, insurance, and a written emergency
procedure (lost link, flyaway, manned aircraft).

## 5. Known gaps before real deployment

* **Packet authentication**: gossip is not signed yet. Add per-drone keys
  (Ed25519 over the packet) before flying near anyone who might inject packets.
* **Flood segmentation on the camera path**: the flood map is wired end to end in the
  brain and GCS but the camera side needs a water-segmentation model (train on FloodNet).
* **Terrain**: projection assumes flat ground at the origin's elevation; fine for Lagos,
  not for hills.
* **PX4**: the MAVLink backend speaks PX4 but only ArduPilot is tested.
