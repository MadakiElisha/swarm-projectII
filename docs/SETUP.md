# Swarm Disaster Response Project — Setup Guide

This gets Phase 1 (MAVLink telemetry) and Phase 2 (mesh relay simulation)
running on YOUR OWN computer, so you can see and verify it yourself.

## Step 0 — What you need first

You need Python 3 installed. Check if you already have it:

**On Mac or Linux:** open Terminal and type:
```
python3 --version
```
If you see something like `Python 3.10.x` or higher, you're good.

**On Windows:** the easiest path is to install WSL (Windows Subsystem for Linux),
which gives you a real Linux environment inside Windows — this matters because
almost all drone/robotics tooling (ROS2, ArduPilot, Gazebo) assumes Linux, so
setting this up now saves pain later.

To install WSL:
1. Open PowerShell as Administrator
2. Run: `wsl --install`
3. Restart your computer when prompted
4. After restart, an Ubuntu terminal will open — set a username/password
5. Inside that Ubuntu terminal, check Python: `python3 --version`

If Python isn't there (rare, but possible): `sudo apt update && sudo apt install python3 python3-pip -y`

## Step 1 — Get the project files

Unzip the file I gave you (`swarm-project.zip`) into a folder, for example:
- Mac/Linux: `~/swarm-project`
- Windows (inside WSL): `~/swarm-project`

Then move into that folder in your terminal:
```
cd ~/swarm-project
```

Verify the files are there:
```
ls
```
You should see folders: `sim`, `gcs`, `mesh`, `firmware`, `docs`, `vision`, `tests`

## Step 2 — Install the two required libraries

```
pip install pymavlink networkx --break-system-packages
```

(If that flag causes an error on your system, just drop it: `pip install pymavlink networkx`)

**Verify it installed correctly:**
```
python3 -c "import pymavlink; import networkx; print('Both libraries installed OK')"
```
You should see: `Both libraries installed OK`
If you see an error instead, the install didn't work — copy the exact error message if you need help debugging it.

## Step 3 — Run Phase 1 (MAVLink telemetry)

This needs TWO terminal windows open at the same time, both inside `~/swarm-project`.

**In Terminal window 1** (this starts the simulated drone, it will run continuously):
```
python3 sim/fake_drone.py --id 1 --port 14550
```
You won't see much output here — that's normal, it's just broadcasting.

**In Terminal window 2** (this is the "ground station" that listens and decodes):
```
python3 gcs/ground_station.py --port 14550 --duration 10
```

**What you should see in Terminal 2, within a few seconds:**
```
[GCS] Listening on UDP port 14550 for 10s...

[GCS] Heartbeat received from system 1 - autopilot type 3, mode flags 216
[GCS] Position update: lat=6.524499, lon=3.379690, alt=50.0m
[GCS] Battery: 99%
...
[GCS] SUCCESS: real MAVLink telemetry pipeline confirmed working.
```

**✅ Verification:** if you see that final `SUCCESS` line, Phase 1 is confirmed working on your machine. If you see `FAILURE: no messages received`, go back to Terminal 1 and make sure `fake_drone.py` is actually still running.

Once confirmed, go to Terminal 1 and press `Ctrl+C` to stop the fake drone.

## Step 4 — Run Phase 2 (mesh relay simulation)

Only needs ONE terminal window:
```
python3 mesh/mesh_sim.py
```

**What you should see:**
```
=== Mesh topology (who can directly talk to who) ===
  D1 <-> D2  (distance: 0.89 km)
  D1 <-> D3  (distance: 1.83 km)
  ...

=== Testing message relay: D5 (stranded person) -> D1 (edge, has signal) ===
SUCCESS: message relayed via path: D5 -> D3 -> D1
That's 2 hop(s) - D5 and D1 are NOT in direct range, but the mesh got the message through anyway.
```

**✅ Verification:** the key line is `SUCCESS: message relayed via path: ...` — that confirms the mesh routing logic works on your machine, independently of mine.

## Troubleshooting

- **`command not found: python3`** → Python isn't installed or isn't in your PATH. Reinstall following Step 0.
- **`ModuleNotFoundError: No module named 'pymavlink'`** → the pip install didn't work, retry Step 2, read the error output.
- **Terminal 2 shows `FAILURE`** → Terminal 1's drone script isn't running, or you used different `--port` numbers in each — they must match (both `14550` unless you change both).
- **Nothing happens / permission errors** → tell me the exact error text and which OS you're on, and we'll fix it together.

## Once both are verified working

Report back with what you saw (or any errors) — that confirms you have a real, independent, working copy of the project on your own machine, not just something that ran on mine. That's the actual foundation we build Phase 3 onward on top of.
