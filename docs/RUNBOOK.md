# Runbook: run the swarm and test every mission

All commands run from `~/swarm-projectII`.

## What runs where

| part | what it is | real or simulated |
|---|---|---|
| **autopilots** | one ArduCopter per drone (the Pixhawk firmware) | **real** flight controller + ArduPilot's flight physics |
| **swarm** | per drone: safety controller (talks MAVLink to its autopilot) + brain | **real** – the exact code a drone runs |
| **cameras** | what each drone's camera + YOLO would report (people, vehicles, water) | simulated from each drone's real position and attitude |
| **GCS** | the web ground station: Lagos in 3D, launch site with pads, drones, tasks | – |

Two modes:

* **Light (default)**: everything above, no Gazebo. Smooth on a laptop. Use it for all mission testing.
* **Gazebo** (`--gazebo`): adds Gazebo's physics and rendered cameras with the real YOLO on 2 drones.
  Heavy; only to check the detector on rendered images.

## 0. After every `git pull` (one terminal)

```bash
cd ~/swarm-projectII && git pull
source /opt/ros/jazzy/setup.bash && source ~/swarm_venv/bin/activate
(cd ros2_ws && python3 -m colcon build) && source ros2_ws/install/setup.bash
python3 scripts/check.py eko
```

Go on when it says **READY** (a `!` line is a warning, not a stop).

## 1. Start (one command)

```bash
scripts/gz/up.sh eko
```

Five tabs open:

| tab | you should see |
|---|---|
| **autopilots** | `[fleet] HEALTHY (5 drones)` – leave it open |
| **swarm** | scrolling logs; after ~1 min `[D1 FC] EKF3 IMU0 is using GPS` for each drone |
| **status** | the live board (below) |
| **gcs** | the browser opens http://localhost:8080 showing **LIVE** |
| **operator** | a prompt – you type the commands below here |

**Ready when the status board shows, for all 5 drones:** `link ok` · `FSM GROUND` · `batt% 100` · `hears 4`.
Give GPS a minute after that.

In the GCS you see the **launch site**: a concrete apron with one marked helipad per drone
(D1…D5), the drones sitting on them, and the people and cars in the area.

## 2. Tests, in order (operator tab)

Watch the **status** tab and the **GCS** while each one runs.

**Test 1 – acceptance (≈10 min)**
```bash
python3 scripts/ros_acceptance.py --formation-timeout 600
```
✅ ends with `ACCEPTANCE: 6/6 passed`. In the GCS the drones lift off their pads, one flies to a
point, then a ring forms, one drone is sent home and lands on its pad, the others report the loss.
Afterwards: `python3 scripts/mission.py resume ALL`

**Test 2 – search & rescue**
```bash
python3 scripts/mission.py search --at 0,0 --size 700x500
```
✅ phase `SEARCH`; GCS: the area fills in (coverage); `seen` shows `person:` / `vehicle:`;
`RESCUE-…` **suggested** tasks appear (one per person found). Confirm one:
```bash
python3 scripts/mission.py confirm RESCUE-3-1      # use an id from the status board / GCS
```
✅ one drone flies to that person and holds over them.

**Test 3 – perimeter**
```bash
python3 scripts/mission.py perimeter --at 100,50 --radius 120
```
✅ event `PERIMETER_FORMED`; try `python3 scripts/mission.py rtl D3` → `PERIMETER_DEGRADED`, a free
drone takes the slot → `FORMED` again.

**Test 4 – pursue a moving car**
```bash
python3 scripts/mission.py intercept --at 200,0
```
✅ a yellow car drives along the streets in the GCS; drones detect it as `vehicle`, ring it and follow it.

**Test 5 – perimeter surveillance**
```bash
python3 scripts/mission.py patrol --at 0,0 --radius 200
# after PERIMETER_FORMED on PATROL-…:
python3 scripts/mission.py intruder --at 450,0 --to 0,0
```
✅ `INTRUDER` event, a new `INTERCEPT-…` forms around the car; the reserve drone keeps the patrol going.

**Test 6 – flood recon** (needs a flooded scene: restart with flood on)
```bash
scripts/swarm_down.sh
SWARM_FLOOD=1 scripts/gz/up.sh eko
python3 scripts/mission.py flood --at 0,0 --size 700x500
```
✅ blue flood cells fill in, people in the water become RESCUE suggestions, `FLOOD_MAP` at the end.

Between tests: `python3 scripts/mission.py rtl ALL` (they fly home and land on their pads), then
`python3 scripts/mission.py resume ALL`.

## 3. The GCS

* **Left – fleet:** each drone: phase, task, battery (the tick = battery needed to get home).
  Click = select, double-click = chase camera behind it.
* **Right – swarm mind:** every task, who holds each slot (green = all drones agree), event feed.
* **Bottom – layers:** Links, Packets (radio), Consensus, Avoidance, Coverage, Sensors (camera
  footprints), Trails, Target, World (people, cars, water).
* **Bottom – tools:** click a tool, then the map (Search / Flood: two corners). RTL / LAND /
  RESUME / E-STOP act on the selected drone, or all if none is selected.
* **⚙ Settings:** buildings *Photorealistic* (default with a Cesium token: Google 3D tiles of the
  real city), *OSM by height*, *white*, *off*; drone size (1 = true size); other recordings.

## 4. Stop

```bash
scripts/swarm_down.sh
```
Only when you are done – it stops everything.

## 5. Gazebo mode (optional, heavy)

```bash
python3 scripts/gz/make_world.py --fleet areas/eko/fleet.yaml --victims 8 --cars 12   # once
scripts/gz/up.sh eko --gazebo          # add --gui for the Gazebo window
```
Same tabs, same tests. Gazebo does the physics; D1 and D2 have rendered cameras with the real
VisDrone YOLO (one shared process); the others use simulated cameras. If the PC struggles:
fewer drones, or `--camera-drones 1` when building the world.

## 6. If something looks wrong

| you see | do |
|---|---|
| status board: `none` for every drone | the swarm tab isn't running, or the tabs aren't on the same ROS setup – restart with `up.sh` |
| `link DOWN` | that autopilot stopped: autopilots tab / `logs/sitl/D<n>.log` |
| FSM stuck in `TAKEOFF`, `Arm: ...` messages in the swarm tab | autopilot warming up (GPS/EKF); it retries for 3 min |
| `lock: geofence` / `critical battery` | the safety controller sent it home; `resume D<n>` once the cause is gone |
| `hears 0` | that drone's brain isn't running (swarm tab errors) |
| GCS `OFFLINE` | rosbridge not running (gcs tab) |
| GCS buildings missing | ⚙ Settings → Buildings; with a token wait a few seconds for the 3D tiles |

Quick logic check without any of this (seconds): `cd ros2_ws/src/swarm_common && python3 -m swarm_common.sim`
