#!/usr/bin/env python3
"""Preflight: is this machine ready to run the swarm in Gazebo? Prints a fix for every ✗.

    source ~/swarm_venv/bin/activate && source /opt/ros/jazzy/setup.bash
    python3 scripts/check.py [eko]
"""
import glob
import importlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
AREA = ARGS[0] if ARGS else "eko"
GAZEBO = "--gazebo" in sys.argv          # the heavy mode needs Gazebo + the plugin + a world
G, Y, R, X = "\033[32m✓\033[0m", "\033[33m!\033[0m", "\033[31m✗\033[0m", "\033[0m"
bad = 0


def ok(msg, *_):
    print(f" {G} {msg}")


def warn(msg, fix=""):
    print(f" {Y} {msg}" + (f"\n      → {fix}" if fix else ""))


def fail(msg, fix):
    global bad
    bad += 1
    print(f" {R} {msg}\n      → {fix}")


def run(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


print("\n== machine")
smi = run("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader")
if smi:
    ok(f"GPU: {smi}")
else:
    warn("no working NVIDIA driver (perception will run on CPU, slowly)", "docs/SETUP_UBUNTU_24.04.md §1")

print("\n== Python environment")
venv = os.environ.get("VIRTUAL_ENV", "")
(ok if venv else warn)(f"venv: {venv or 'none active'}", "" if venv else "source ~/swarm_venv/bin/activate")
for mod, fix in [("yaml", "pip install pyyaml"), ("pymavlink", "pip install pymavlink"),
                 ("cv2", "pip install -c scripts/venv-constraints.txt opencv-python"),
                 ("trimesh", "pip install -r scripts/gz/requirements.txt"),
                 ("shapely", "pip install -r scripts/gz/requirements.txt")]:
    try:
        importlib.import_module(mod)
        ok(mod)
    except Exception as e:
        fail(f"{mod}: {str(e)[:80]}", fix)
try:
    import numpy
    if int(numpy.__version__.split(".")[0]) >= 2:
        fail(f"numpy {numpy.__version__} (ROS/Ubuntu modules need 1.x)",
             'pip install -c scripts/venv-constraints.txt "numpy<2" "opencv-python<4.12"')
    else:
        ok(f"numpy {numpy.__version__}")
except Exception as e:
    fail(f"numpy: {e}", "pip install 'numpy<2'")
try:
    import torch
    if torch.cuda.is_available():
        cap = torch.cuda.get_device_capability(0)
        x = torch.randn(256, 256, device="cuda")
        (x @ x).sum().item()
        ok(f"torch {torch.__version__} on {torch.cuda.get_device_name(0)} (sm_{cap[0]}{cap[1]})")
    else:
        warn(f"torch {torch.__version__} without CUDA", "STEPS=torch scripts/setup_ubuntu2404.sh")
except Exception as e:
    fail(f"torch: {str(e)[:100]}", "STEPS=torch scripts/setup_ubuntu2404.sh")
try:
    import ultralytics
    ok(f"ultralytics {ultralytics.__version__}")
except Exception:
    fail("ultralytics missing", "pip install -c scripts/venv-constraints.txt -r perception/requirements.txt")

print("\n== detector")
model = os.path.expanduser("~/swarm_models/visdrone_yolo11s.pt")
if os.path.isfile(model):
    ok(f"VisDrone model {model}")
else:
    warn("no VisDrone model yet - drones will use stock COCO yolo11n (weak from the air)",
         "python3 perception/visdrone.py train --quick   (≈1-1.5 h on the RTX 5060; installs itself)")

print("\n== ROS 2 / Gazebo / ArduPilot")
(ok if os.environ.get("ROS_DISTRO") == "jazzy" else fail)(
    f"ROS_DISTRO={os.environ.get('ROS_DISTRO', 'unset')}", "source /opt/ros/jazzy/setup.bash")
gz = run("gz sim --versions") or run("gz sim --version")
(ok if gz else (fail if GAZEBO else warn))(f"gazebo: {gz.splitlines()[0] if gz else 'not found'}",
                                           "STEPS=gz scripts/setup_ubuntu2404.sh")
ap = os.path.expanduser(os.environ.get("ARDUPILOT_HOME", "~/ardupilot"))
(ok if os.path.isfile(f"{ap}/build/sitl/bin/arducopter") else fail)(
    f"ArduCopter SITL in {ap}", "STEPS=ardupilot scripts/setup_ubuntu2404.sh")
apgz = os.path.expanduser(os.environ.get("ARDUPILOT_GAZEBO", "~/ardupilot_gazebo"))
(ok if glob.glob(f"{apgz}/build/libArduPilotPlugin.so") else (fail if GAZEBO else warn))(
    f"ardupilot_gazebo plugin in {apgz}", "STEPS=apgz scripts/setup_ubuntu2404.sh")
if GAZEBO:
    for pkg, fix in (("ros_gz_bridge", "sudo apt install ros-jazzy-ros-gz"),
                     ("rosapi", "sudo apt install ros-jazzy-rosbridge-suite")):
        (ok if run(f"ros2 pkg prefix {pkg}") else fail)(f"ROS package {pkg}", fix)
(ok if run("ros2 pkg prefix rosbridge_server") else warn)(
    "rosbridge (web GCS live mode)", "sudo apt install ros-jazzy-rosbridge-server")

rmw = os.environ.get("RMW_IMPLEMENTATION", "")
if "zenoh" in rmw:
    warn(f"RMW_IMPLEMENTATION={rmw}: nodes can't see each other without a Zenoh router",
         "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp   (scripts/gz/up.sh does this for you)")
else:
    ok(f"ROS 2 middleware: {rmw or 'default (Fast DDS)'}")

print("\n== workspace")
vm = os.path.join(ROOT, "ros2_ws/install/swarm_vehicle/lib/swarm_vehicle/vehicle_manager")
if not os.path.isfile(vm):
    fail("workspace not built", "cd ros2_ws && python3 -m colcon build && source install/setup.bash")
else:
    shebang = open(vm).readline().strip()
    if "env python3" in shebang or (venv and venv in shebang):
        ok(f"workspace built ({shebang})")
    else:
        fail(f"nodes run with {shebang[2:]} (not your venv: pymavlink/torch invisible)",
             "cd ros2_ws && rm -rf build install log && python3 -m colcon build && source install/setup.bash")
pref = run("ros2 pkg prefix swarm_vehicle")
(ok if pref.startswith(ROOT) else fail)(
    "workspace sourced", "source ros2_ws/install/setup.bash")

print(f"\n== area '{AREA}'")
fleet = os.path.join(ROOT, "areas", AREA, "fleet.yaml")
(ok if os.path.isfile(fleet) else fail)(f"{fleet}", f"python3 scripts/make_area.py {AREA} --drones 5")
world = os.path.join(ROOT, "sim/gz", AREA, "worlds/swarm.sdf")
if os.path.isfile(world):
    newest = max(os.path.getmtime(p) for p in glob.glob(os.path.join(ROOT, "scripts/gz/make_world.py")))
    if os.path.getmtime(world) < newest:
        warn("Gazebo world is older than the world builder (rebuild for the latest look)",
             f"python3 scripts/gz/make_world.py --fleet areas/{AREA}/fleet.yaml")
    else:
        ok(world)
else:
    (fail if GAZEBO else warn)("no Gazebo world (only needed for --gazebo)",
                               f"python3 scripts/gz/make_world.py --fleet areas/{AREA}/fleet.yaml")
tok = os.path.join(ROOT, "gcs/config.local.js")
if os.path.isfile(tok):
    ok("Cesium ion token (gcs/config.local.js)")
else:
    warn("no Cesium ion token file", "echo \"window.SW_ION_TOKEN = '<token>';\" > gcs/config.local.js")
if shutil.which("gnome-terminal") is None and shutil.which("tmux") is None:
    warn("neither gnome-terminal nor tmux: scripts/gz/up.sh can't open terminals", "sudo apt install tmux")

print("\n" + ("\033[32mREADY\033[0m  ->  scripts/gz/up.sh " + AREA + (" --gazebo" if GAZEBO else "") if not bad else
              f"\033[31m{bad} problem(s)\033[0m - fix the ✗ lines above, then run this again"))
sys.exit(1 if bad else 0)
