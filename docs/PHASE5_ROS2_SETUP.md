# Phase 5 — ROS2 Setup Guide

IMPORTANT: I could NOT test-run this myself (my sandbox can't reach ROS2's
package servers), so this is the first phase where you're finding out if it
works at the same time I am. If something breaks, paste me the EXACT error
text and we'll debug it together - that's expected and normal for this phase.

## Step 1 — Check your Ubuntu version

```
lsb_release -a
```

- If it says **22.04** → install **ROS2 Humble**
- If it says **24.04** → install **ROS2 Jazzy**

(If you're unsure or it's something else, paste me the output and I'll tell you which to use.)

## Step 2 — Install ROS2 (example shown for Humble / Ubuntu 22.04)

```bash
sudo apt update && sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-desktop python3-colcon-common-extensions python3-rosdep

sudo rosdep init
rosdep update
```

(If you're on 24.04, replace `ros-humble-desktop` with `ros-jazzy-desktop` everywhere above.)

This is a genuinely large install (several GB) — expect it to take a while.

**✅ Verify install worked:**
```bash
source /opt/ros/humble/setup.bash
ros2 --version
```
You should see a version number printed, not an error.

## Step 3 — Install our package's Python dependency

```bash
pip install networkx --break-system-packages
```
(You should already have this from Phase 2 — just confirming.)

## Step 4 — Build our ROS2 package

From your `swarm-project` folder:
```bash
cd ~/swarm-project/ros2_ws
source /opt/ros/humble/setup.bash
colcon build
```

**✅ Verify:** you should see `Summary: 1 package finished` with no red error text. A new `build/`, `install/`, and `log/` folder will appear — that's normal and expected.

## Step 5 — Run everything with one command

```bash
source install/setup.bash
ros2 launch swarm_nodes swarm_launch.py
```

**✅ Verify:** you should see repeating log lines like:
```
[mesh_builder]: Mesh: 5 active drones, 7 links
```
appearing roughly once per second. Leave this running.

## Step 6 — In a SECOND terminal, send a task and check the result

```bash
cd ~/swarm-project/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 topic pub --once /swarm/task_requests std_msgs/String \
  "data: '{\"task_id\": \"T1\", \"lat\": 6.543, \"lon\": 3.398}'"
```

**✅ Verify:** back in Terminal 1 (where the launch is running), you should see a new log line like:
```
[task_auctioneer]: T1 -> D4 (path: D4 -> D3 -> D1)
```

You can also watch the raw result topic directly, in a third terminal:
```bash
ros2 topic echo /swarm/task_assignments
```

## When you're done

Press `Ctrl+C` in Terminal 1 to stop everything.

## What to report back

Tell me exactly which step you got to, and for each step whether it matched
the "✅ Verify" line — and if anything failed, paste the FULL error text, not
just a summary. This phase has more moving parts than the last ones, so
precise error copying will save us both time.
