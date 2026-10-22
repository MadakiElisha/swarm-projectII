# Runbook: start the swarm in Gazebo and test every mission

Everything below assumes the one-time setup in
[SETUP_UBUNTU_24.04.md](SETUP_UBUNTU_24.04.md) is done. Commands run from
`~/swarm-projectII`.

## 0. Prepare (after every `git pull`)

One terminal:

```bash
cd ~/swarm-projectII && git pull
source /opt/ros/jazzy/setup.bash && source ~/swarm_venv/bin/activate
pip install -c scripts/venv-constraints.txt -r scripts/gz/requirements.txt pymavlink pyyaml
(cd ros2_ws && python3 -m colcon build) && source ros2_ws/install/setup.bash
python3 scripts/gz/make_world.py --fleet areas/eko/fleet.yaml --victims 8 --cars 12   # rebuild the world
echo "window.SW_ION_TOKEN = '<your Cesium token>';" > gcs/config.local.js             # once
python3 scripts/check.py eko
```

`check.py` prints ✓ / ! / ✗ for every piece with the fix next to each ✗. Go on when it says **READY**
(a `!` for the VisDrone model is fine until step 1 is done).

## 1. Train the aerial detector (first time only, ~1–1.5 h)

Gazebo must be **closed** (it needs the GPU memory).

```bash
python3 perception/visdrone.py check          # GPU ✓, ultralytics ✓
python3 perception/visdrone.py train --quick  # downloads VisDrone (~2.3 GB), trains, installs the model
python3 perception/visdrone.py demo           # annotated aerial photos -> runs/visdrone/demo/
```

Look at the images in `runs/visdrone/demo/`: people and vehicles boxed from the
air. Training prints mAP50 at the end; for the quick model expect roughly
0.3–0.4 on VisDrone (people from 30–60 m are tiny; the full `train` does better).
The model is installed to `~/swarm_models/visdrone_yolo11s.pt` and used automatically.
Until then the drones use the stock COCO `yolo11n` and see far less.

## 2. Start a session: one command

```bash
scripts/gz/up.sh eko
```

It runs the preflight, stops anything left over, and opens five tabs:

| tab | what runs | what you should see |
|---|---|---|
| **gazebo** | Gazebo GUI + 5 ArduCopter autopilots | Gazebo window with Lagos Island (buildings coloured by height), 5 drones on the pad; the tab tails `D1.log` |
| **swarm** | per drone: vehicle_manager, drone_brain, camera → JPEG → YOLO | starts after 25 s; `[D1 FC] ...` autopilot messages, then `EKF3 IMU0 is using GPS` (30–90 s) |
| **status** | `scripts/swarm_status.py` | the live board (below) |
| **gcs** | rosbridge + web GCS | browser opens http://localhost:8080 showing **LIVE** |
| **operator** | a ready shell | where you type the mission commands below |

Stop everything: `scripts/swarm_down.sh`. Without a desktop (SSH) it uses tmux:
`tmux attach -t swarm`, `Ctrl-b n` for the next tab.

Prefer separate terminals? The same thing by hand, each terminal first doing
`source logs/gz/session_env.sh` (written by up.sh): T1 `scripts/gz/run_swarm.sh`,
T2 `ros2 launch swarm_bringup swarm_gazebo.launch.py`, T3 `python3 scripts/swarm_status.py`,
T4 `ros2 launch rosbridge_server rosbridge_websocket_launch.xml & (cd gcs && python3 -m http.server 8080)`.

### Ready when the status board shows

```
drone link  armed  mode      FSM      lock  alt m  batt%  phase   executing  hears  seen (10 s)
D1    ok    no     STABILIZE GROUND   -       0.0    100  LANDED  -              4  -
...
```

* **link ok** for every drone (DOWN = that autopilot didn't start: see `logs/gz/D<n>.log`)
* **hears 4** (= every other drone) – the gossip radio works
* wait ~60 s after the swarm tab starts for GPS before the first mission

## 3. Acceptance test (run first, ~10 min)

In the **operator** tab:

```bash
python3 scripts/ros_acceptance.py --formation-timeout 600
```

Watches from outside like an operator: A1 telemetry · A2 radio links · A3 one
drone executes a GOTO · A4 perimeter forms · A5 RTL sticks · A6 the swarm notices
the loss. Must end `ACCEPTANCE: 6/6 passed`. Afterwards: `python3 scripts/mission.py resume ALL`.

## 4. The missions (one at a time)

Positions are metres east,north of the map centre. Between missions:
`python3 scripts/mission.py cancel <TASK-ID>` or let it finish; drones return to their pads by themselves.

### 4.1 Search & rescue

```bash
python3 scripts/mission.py search --at 0,0 --size 700x500
```

* status: phase `SEARCH` on all drones, `seen` shows `person:n` / `vehicle:n` when flying over them
* GCS: the search area fills in (coverage), sightings appear as dots
* mission events / GCS feed: `RESCUE-…` **suggested** → confirm it (GCS click, or
  `python3 scripts/mission.py confirm RESCUE-3-12`) → one drone flies there (`ON_TASK`), then `done`
* pass: every survivor in the area gets one RESCUE task (not one per drone), area ≥ 95 % covered

Tip: people are small from 30–50 m. If YOLO misses them, rebuild the world with
`--cam-w 1280 --cam-h 800` (sharper cameras) and launch with the full model.

### 4.2 Perimeter

```bash
python3 scripts/mission.py perimeter --at 100,50 --radius 120
```

* status: drones go `ENROUTE` → `ON_STATION` with items `SWARM-…/s0..s4`
* events: `PERIMETER_FORMED`, later `RELEASED` (after the hold)
* try `python3 scripts/mission.py rtl D3` while formed → `PERIMETER_DEGRADED`, a free drone refills the slot → `FORMED`

### 4.3 Pursue a moving target

```bash
python3 scripts/mission.py intercept          # the car in the Gazebo world starts driving along streets
```

* Gazebo: the "quarry" car drives on the roads
* status: `seen` shows `vehicle:n` on the drones near it; items `INTERCEPT-…/s*`
* GCS: the target track follows the car, the ring moves with it; parked cars do not pull it away
* events: `PERIMETER_FORMED` on the INTERCEPT task

### 4.4 Perimeter surveillance (patrol + automatic intercept)

```bash
python3 scripts/mission.py patrol --at 0,0 --radius 200
# wait for PERIMETER_FORMED on PATROL-…, then send an intruder:
python3 scripts/mission.py intruder --at 450,0 --to 0,0     # a car drives in along the streets
```

* status: 4 drones on `PATROL-…/s*`, one stays on the pad (reserve)
* nothing happens for parked cars / standing people inside the ring
* when the car drives in: event `INTRUDER`, a new `INTERCEPT-…` appears, the nearest
  drones leave the patrol to ring the car; the remaining patrol keeps flying

### 4.5 Flood recon

The world needs water: rebuild once with a flood and restart the session.

```bash
scripts/swarm_down.sh
python3 scripts/gz/make_world.py --fleet areas/eko/fleet.yaml --victims 8 --flood 0.6
scripts/gz/up.sh eko
python3 scripts/mission.py flood --at 0,0 --size 700x500
```

* status: phase `SEARCH`; `seen` shows `water:n` (the colour-based water detector)
* GCS: blue flood cells fill in on top of the coverage; people in water become RESCUE suggestions
* event: `FLOOD_MAP … ha flooded … people stranded` when the survey completes

## 5. What to look out for

| you see | meaning / what to do |
|---|---|
| `link DOWN` | the autopilot for that drone is not running or the port is wrong: `logs/gz/D<n>.log` |
| FSM stuck in `TAKEOFF`, swarm tab: `Arm: Gyros inconsistent` / `GPS: Bad fix` | autopilot warming up; it retries for 3 min. If it never arms: Gazebo running slower than real time (fewer drones, `--no-camera`) |
| `lock: geofence` / `critical battery` | the safety FSM sent it home; `resume <D>` once the cause is gone |
| `hears 0` | the gossip radio is down for that drone: is its brain running (swarm tab errors)? |
| `seen` stays `-` while flying over people | perception not running (swarm tab: `perception_node` errors), or the model is too weak (step 1) |
| drone sits `IDLE` / `LANDED` with open tasks | it may not have enough battery for task + return; check `batt%` |
| Gazebo real-time factor (bottom right) far below 1.0 | the PC can't keep up: close other apps, fewer drones or cameras |

Logs: `logs/gz/` (Gazebo + autopilots), the swarm tab (all nodes), `~/.ros/log/`.

## 6. Quick check without Gazebo (seconds)

```bash
cd ros2_ws/src/swarm_common && python3 -m swarm_common.sim     # 14 swarm scenarios: all PASS
```

Same swarm software, point-mass physics. Useful after any code change.
