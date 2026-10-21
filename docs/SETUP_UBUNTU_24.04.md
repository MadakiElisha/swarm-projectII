# Fresh machine → swarm flying over Lagos in Gazebo

Target machine: **Ubuntu 24.04 (native), Intel i7 13th gen, 16 GB RAM, NVIDIA RTX 5060 8 GB**.
Everything here runs the *real* ArduPilot flight code (SITL) on *real* rigid-body
physics (Gazebo Harmonic), with the drones seeing the world through simulated
cameras and a VisDrone-trained YOLO detector. The swarm software is the same
code that runs on the drones' companion computers.

```
 Gazebo Harmonic ── physics, OSM city, cameras ──► ros_gz_bridge ──► camera_compressor ──► perception_node (YOLO)
      ▲  JSON FDM (9002+10N)                                                                     │ detections
 ArduCopter SITL × N  ◄── MAVLink tcp:5760+10N ──  vehicle_manager (safety FSM)  ◄── setpoints ── drone_brain
                                                                                  gossip ⇅ /swarm/radio
                                                     web GCS (Cesium) ◄── rosbridge ── listens to the radio
```

Time needed: ~1.5 h of mostly unattended installs, plus 2–5 h if you train the detector.

---

## 1. NVIDIA driver (do this first, needs a reboot)

The RTX 50 series (Blackwell) needs a **recent driver with the open kernel modules**
(570 or newer; take the newest `-open` that Ubuntu offers).

```bash
sudo apt update && sudo apt full-upgrade -y
ubuntu-drivers list                       # pick the newest  nvidia-driver-5xx-open
sudo apt install -y nvidia-driver-580-open   # (or the newest -open from the list)
sudo reboot
nvidia-smi                                # must show the RTX 5060 and the driver version
```

If `nvidia-smi` fails after reboot: Secure Boot may be blocking the module. Either
enroll the MOK key when prompted at boot, or disable Secure Boot in the BIOS.

You do **not** need the CUDA toolkit for PyTorch (the wheels bring their own CUDA runtime).

## 2. Everything else: one script

```bash
git clone -b decentralized-swarm https://github.com/MadakiElisha/swarm-projectII.git ~/swarm-projectII
cd ~/swarm-projectII
scripts/setup_ubuntu2404.sh
```

It installs, skipping anything already present:

| step | what |
|---|---|
| `ros` | ROS 2 Jazzy desktop, rosbridge, cv_bridge |
| `gz` | Gazebo Harmonic + `ros_gz` (ROS-supported pairing for Jazzy) + headers for the ArduPilot plugin |
| `ardupilot` | ArduPilot **Copter-4.6.3** in `~/ardupilot`, SITL build (`build/sitl/bin/arducopter`) |
| `apgz` | `~/ardupilot_gazebo` (the ArduPilot ↔ Gazebo JSON plugin) |
| `venv` | `~/swarm_venv` (sees ROS's packages) with pymavlink, pyyaml, pytest |
| `torch` | PyTorch **CUDA 12.8 wheels** (required for RTX 50 / sm_120), Ultralytics, SAHI |
| `build` | `colcon build` of the workspace + the core unit tests |

Run a subset with `STEPS="torch build" scripts/setup_ubuntu2404.sh`.
If the PyTorch site lists a newer CUDA build (e.g. cu130) use it:
`TORCH_INDEX=https://download.pytorch.org/whl/cu130 STEPS=torch scripts/setup_ubuntu2404.sh`.

Then put this in `~/.bashrc` (the script prints it):

```bash
source /opt/ros/jazzy/setup.bash
source ~/swarm_venv/bin/activate
source ~/swarm-projectII/ros2_ws/install/setup.bash
export ARDUPILOT_HOME=~/ardupilot ARDUPILOT_GAZEBO=~/ardupilot_gazebo
```

**Check:**

```bash
python -c "import torch;print(torch.cuda.is_available(), torch.cuda.get_device_capability(0))"   # True (12, 0)
gz sim --version                                    # Gazebo Sim, version 8.x
ls ~/ardupilot/build/sitl/bin/arducopter ~/ardupilot_gazebo/build/libArduPilotPlugin.so
cd ~/swarm-projectII/ros2_ws/src/swarm_common && python -m swarm_common.sim   # 14 scenarios: PASS
```

## 3. Pick the area (Eko / Lagos Island, or anywhere)

```bash
cd ~/swarm-projectII
python3 scripts/make_area.py --list            # eko, victoria-island, lekki-phase1, ajegunle, ikeja, yaba
python3 scripts/make_area.py eko --drones 5    # downloads OSM buildings/water/roads for Lagos Island
# anywhere in the world:
python3 scripts/make_area.py --center 6.4541,3.3947 --size 1800 --name marina --drones 5
```

This writes `areas/eko/area.json` (building footprints + heights, water, roads)
and `areas/eko/fleet.yaml` (origin, 5 launch pads 15 m apart on open ground
found in the OSM data, geofence). The drones plan their routes around exactly
these buildings, and the GCS draws them.

> Building heights come from OSM `height`/`building:levels` tags where mapped,
> otherwise an estimate by building type. Drones fly on altitude layers
> (30 m + 6 m per drone by default, `motion:` in fleet.yaml) and route *around*
> anything taller than their layer, so a missing height tag is the main risk:
> check the tallest towers in the GCS before trusting a route.

5 drones is the sweet spot on 16 GB RAM with cameras on; 7 works with `--no-camera`.

## 4. First flight in Gazebo (real ArduPilot, real physics)

**Terminal 1: world + autopilots**

```bash
python3 scripts/gz/make_world.py --fleet areas/eko/fleet.yaml --victims 6 --cars 10
source sim/gz/eko/env.sh
scripts/gz/run_swarm.sh                 # Gazebo GUI + one ArduCopter SITL per drone
```

Wait for `EKF3 IMU0 is using GPS` in `logs/gz/D*.log` (30–90 s). Add
`--flood 0.6` to `make_world.py` to put the low ground under 0.6 m of water.

**Terminal 2: the swarm**

```bash
source sim/gz/eko/env.sh
export SWARM_FLEET=$PWD/areas/eko/fleet.yaml
ros2 launch swarm_bringup swarm_gazebo.launch.py \
     model:=$HOME/swarm_models/visdrone_yolo11s.pt loss:=0.05
```

Until you have trained weights (section 6) it falls back to the stock `yolo11n.pt`
(COCO: detects people/cars, much weaker from the air).

**Terminal 3: GCS**

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
python3 scripts/fleet_info.py --json > gcs/fleet.json      # includes the area's buildings
cd gcs && python3 -m http.server 8080                       # open http://localhost:8080
```

**Acceptance (Terminal 4)**, before anything else:

```bash
python3 scripts/ros_acceptance.py --formation-timeout 600      # A1–A6 must PASS
```

Stop everything with `scripts/swarm_down.sh` (also stops Gazebo and SITL).

## 5. The GCS: buildings, token, missions

* **⚙ Settings → Cesium ion token** (free: <https://ion.cesium.com> → sign up
  (Community plan, no card) → *Access Tokens* → copy *Default token*). Gives world terrain,
  Cesium OSM Buildings outside your area, and **Photorealistic 3D Tiles** (Google, served
  through ion).
* **Buildings**: *Coloured by height* (default), *Clean white*, *Photorealistic*, *Off*.
  Your area's buildings are drawn from the same OSM footprints the drones avoid, so
  they show even without a token.
* **Operator tools** (live): ◎ Dispatch · ⬢ Perimeter · ◆ Intercept · ⌕ Search ·
  ⛨ Patrol · ≋ Flood recon, plus RTL / LAND / RESUME / E-STOP per drone or ALL.

| mission | how | what the swarm does |
|---|---|---|
| **Search & rescue** | ⌕ Search: click two corners | splits the area, re-covers gaps if a drone is lost; YOLO "person" sightings fused across drones → RESCUE suggestion → you confirm → one drone goes |
| **Perimeter** | ⬢ Perimeter: click centre | ring by consensus, holds, releases; a lost drone's slot is refilled |
| **Pursue target** | ◆ Intercept: click the car | locks on to the vehicle that *moves* away from your click (parked cars ignored), ring follows it, cutters lead it |
| **Perimeter surveillance** | ⛨ Patrol: click centre, give radius | standing patrol ring, one drone in reserve; anything that **moves** inside the perimeter → INTRUDER → nearest patrollers intercept it automatically; tired batteries hand over |
| **Flood recon** | ≋ Flood recon: click two corners | survey + flood map (blue cells) merged across drones, stranded people flagged, `FLOOD_MAP` report |

Recorded versions of these play with no ROS at all:
`gcs/index.html?replay=demos/showcase.json` · `demos/patrol.json` · `demos/flood.json`.
Re-record them among real Lagos buildings:
`python3 scripts/record_demo.py --mission patrol --fleet areas/eko/fleet.yaml`.

## 6. Train the aerial detector (VisDrone)

```bash
source ~/swarm_venv/bin/activate
cd ~/swarm-projectII
python perception/visdrone.py train --model yolo11s.pt --imgsz 640 --batch 16 --epochs 60   # quick: ~1.5 h
python perception/visdrone.py train --model yolo11s.pt --imgsz 1024 --batch 8 --epochs 120  # full: ~3–5 h
python perception/visdrone.py eval --weights runs/visdrone/yolo11s/weights/best.pt --sliced  # SAHI tiles
python perception/visdrone.py install --weights runs/visdrone/yolo11s/weights/best.pt      # -> ~/swarm_models/
```

* Ultralytics downloads VisDrone2019-DET (~2.3 GB) on the first run.
* Close Gazebo while training: the 8 GB of VRAM is the limit. If you hit
  out-of-memory, drop `--batch` (8 → 4) before dropping `--imgsz`.
* Classes are mapped to what the swarm reasons about: pedestrian/people → `person`,
  car/van/truck/bus/motor → `vehicle`.
* For the drones: `export --format engine` on a Jetson (TensorRT), `--format onnx` for
  the Hailo compiler (RPi 5 + Hailo-8L).

## 7. Is it working? Checklist

| check | expected |
|---|---|
| `nvidia-smi` | RTX 5060, driver ≥ 570 |
| `python -m swarm_common.sim` | 14/14 PASS |
| `scripts/ros_acceptance.py` on Gazebo | 6/6 PASS |
| Gazebo GUI | drones on their pads between OSM buildings; they take off together |
| `ros2 topic hz /swarm/D1/camera/compressed` | ~3 Hz |
| `ros2 topic echo /swarm/D1/detections` | people/cars while flying over them |
| GCS | buildings coloured by height, links, consensus slots, coverage filling in |

## 8. Troubleshooting

| symptom | cause / fix |
|---|---|
| `Arm: Gyros inconsistent` / `Accels inconsistent` for a minute | SITL warming up, or the PC is slower than real time. The FSM keeps retrying for 3 min. Check Gazebo's real-time factor (bottom right of the GUI) stays near 1.0; use fewer drones or `--no-camera` if not |
| `GPS 1: Bad fix` | wait 30–60 s after start |
| Gazebo crashes when loading the world | stale world: rerun `make_world.py`. Buildings use box colliders (mesh colliders crash DART) |
| drones never take off | `ros2 topic echo /swarm/D1/vehicle_state` – is `connected: true`? SITL must be up before the launch file |
| `CUDA error: no kernel image is available` | PyTorch built without sm_120: reinstall with the cu128 (or newer) index |
| GCS shows "OFFLINE" | rosbridge not running, or wrong URL in ⚙ |
| `make_area.py` times out | Overpass is busy; retry, or `OVERPASS_URL=https://overpass.kumi.systems/api/interpreter` |

## 9. What is real and what is still simulated here

* **Real**: ArduPilot flight code, MAVLink, the swarm software, Gazebo rigid-body
  physics, cameras rendering the scene, YOLO on those images, OSM buildings.
* **Simulated**: the radio (brains emulate range/loss on one machine; use the Docker
  netem harness for a real network), GPS (perfect unless you add SIM_GPS noise), wind.
* **Flood mapping from the camera**: with `--flood` worlds the perception node uses a
  colour baseline (`water_model:=hsv`, tuned to Gazebo's flood water) to turn image
  patches into "water" detections → the shared flood map. Real floodwater needs a
  segmentation model: train YOLO11-seg on **FloodNet** (UAV imagery of flooded
  Houston) and pass it as `water_model:=<weights>` (any class named *water*/*flood*
  is used). Until then, treat real-world flood maps as unvalidated.
