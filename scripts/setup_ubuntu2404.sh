#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 24.04 machine for the full swarm stack:
#   ROS 2 Jazzy + Gazebo Harmonic + ArduPilot SITL + ardupilot_gazebo + Python venv
#   (+ CUDA PyTorch / Ultralytics for perception when an NVIDIA GPU is present).
#
#   scripts/setup_ubuntu2404.sh            # everything (asks for sudo)
#   STEPS="ros gz" scripts/setup_ubuntu2404.sh     # only some steps
#
# Steps: ros gz ardupilot apgz venv torch build
# The NVIDIA driver is NOT installed here (needs a reboot) - see docs/SETUP_UBUNTU_24.04.md.
# Safe to re-run: every step skips what is already there.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STEPS="${STEPS:-ros gz ardupilot apgz venv torch build}"
AP_REF="${AP_REF:-Copter-4.6.3}"             # ArduPilot release the swarm is tested against
VENV="${SWARM_VENV:-$HOME/swarm_venv}"
say() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
has() { [[ " $STEPS " == *" $1 "* ]]; }

. /etc/os-release
[ "$VERSION_ID" = "24.04" ] || echo "warning: tested on Ubuntu 24.04, this is $PRETTY_NAME"

if has ros; then
  say "ROS 2 Jazzy"
  if [ ! -f /opt/ros/jazzy/setup.bash ]; then
    sudo apt-get update
    sudo apt-get install -y software-properties-common curl git
    sudo add-apt-repository -y universe
    V=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
        | grep -F '"tag_name"' | awk -F'"' '{print $4}')
    curl -L -o /tmp/ros2-apt-source.deb \
      "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${V}/ros2-apt-source_${V}.${VERSION_CODENAME}_all.deb"
    sudo dpkg -i /tmp/ros2-apt-source.deb
    sudo apt-get update
    sudo apt-get install -y ros-jazzy-desktop ros-dev-tools
  fi
  sudo apt-get install -y ros-jazzy-rosbridge-server ros-jazzy-cv-bridge python3-venv python3-pip
  grep -q "/opt/ros/jazzy/setup.bash" ~/.bashrc || echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
fi

if has gz; then
  say "Gazebo Harmonic + ros_gz"
  # ros-jazzy-ros-gz brings Gazebo Harmonic (the ROS-supported pairing for Jazzy)
  sudo apt-get install -y ros-jazzy-ros-gz
  # dev headers for building ardupilot_gazebo, from the OSRF repo
  if [ ! -f /etc/apt/sources.list.d/gazebo-stable.list ]; then
    sudo curl -fsSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable ${VERSION_CODENAME} main" \
      | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
    sudo apt-get update
  fi
  sudo apt-get install -y gz-harmonic libgz-sim8-dev rapidjson-dev libopencv-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad \
    gstreamer1.0-libav gstreamer1.0-gl
fi

if has ardupilot; then
  say "ArduPilot $AP_REF (SITL)"
  if [ ! -d ~/ardupilot ]; then
    git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git ~/ardupilot
  fi
  cd ~/ardupilot
  git fetch --tags -q && git checkout -q "$AP_REF" && git submodule update --init --recursive -q
  if [ ! -f ~/.ardupilot_env_done ]; then
    Tools/environment_install/install-prereqs-ubuntu.sh -y
    touch ~/.ardupilot_env_done
  fi
  # the prereqs script sets up its own venv in ~/.profile
  # shellcheck disable=SC1090
  . ~/.profile || true
  ./waf configure --board sitl
  ./waf copter
  ls -la build/sitl/bin/arducopter
  cd "$ROOT"
fi

if has apgz; then
  say "ardupilot_gazebo (ArduPilot <-> Gazebo plugin)"
  [ -d ~/ardupilot_gazebo ] || git clone https://github.com/ArduPilot/ardupilot_gazebo ~/ardupilot_gazebo
  cd ~/ardupilot_gazebo && mkdir -p build && cd build
  GZ_VERSION=harmonic cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
  make -j"$(nproc)"
  cd "$ROOT"
fi

if has venv; then
  say "Python venv for the swarm ($VENV, sees ROS's system packages)"
  [ -d "$VENV" ] || python3 -m venv --system-site-packages "$VENV"
  # shellcheck disable=SC1091
  . "$VENV/bin/activate"
  pip install -U pip
  # ROS/apt modules are built for NumPy 1.x: every pip install below respects these pins
  export PIP_CONSTRAINT="$ROOT/scripts/venv-constraints.txt"
  pip install pyyaml pymavlink pytest flake8 matplotlib
  pip install -r "$ROOT/scripts/gz/requirements.txt"      # Gazebo world builder
fi

if has torch; then
  say "Perception: PyTorch (CUDA) + Ultralytics + SAHI"
  export PIP_CONSTRAINT="$ROOT/scripts/venv-constraints.txt"
  # shellcheck disable=SC1091
  . "$VENV/bin/activate"
  if command -v nvidia-smi > /dev/null && nvidia-smi > /dev/null 2>&1; then
    # RTX 50-series (Blackwell, sm_120) needs CUDA 12.8+ wheels
    pip install --index-url "${TORCH_INDEX:-https://download.pytorch.org/whl/cu128}" torch torchvision
  else
    echo "no working NVIDIA driver: installing CPU PyTorch (fine for running, slow for training)"
    pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
  fi
  pip install -r "$ROOT/perception/requirements.txt"
  python - <<'EOF'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), "capability", torch.cuda.get_device_capability(0))
    print("matmul ok:", (torch.randn(512, 512, device="cuda") @ torch.randn(512, 512, device="cuda")).shape)
EOF
fi

if has build; then
  say "Build the swarm workspace"
  # shellcheck disable=SC1091
  set +u; source /opt/ros/jazzy/setup.bash; [ -d "$VENV" ] && . "$VENV/bin/activate"; set -u
  cd "$ROOT/ros2_ws" && colcon build --symlink-install
  cd "$ROOT/ros2_ws/src/swarm_common" && python3 -m pytest -q tests -x -k "not scenarios"
fi

say "done"
cat <<EOF
Add to ~/.bashrc (or run in each terminal):
  source /opt/ros/jazzy/setup.bash
  source $VENV/bin/activate
  source $ROOT/ros2_ws/install/setup.bash
  export ARDUPILOT_HOME=~/ardupilot ARDUPILOT_GAZEBO=~/ardupilot_gazebo
Next: docs/SETUP_UBUNTU_24.04.md section 4 (first flight in Gazebo).
EOF
