# Architecture: a leaderless drone swarm

This document explains how the swarm works without any central node, which
guarantees each mechanism gives, and where the honest limits are.

## 1. The rule: every drone is identical and self-sufficient

Each drone runs exactly two processes on its own companion computer:

```
                 radio (/swarm/radio, broadcast, lossy)
                         ▲            │
                         │ packets    ▼
   camera ──► perception ──► drone_brain ──setpoint──► vehicle_manager ──► flight controller
                 (YOLO)      (DroneBrain)  ◄─vehicle_state──  (VehicleFSM)     (ArduPilot/PX4)
                                  │
                                  └──► GCS-facing status (optional observer)
```

* **drone_brain** (`swarm_agents`) wraps `swarm_common.brain.DroneBrain`:
  allocation, gossip, motion, world model, coverage.
* **vehicle_manager** (`swarm_vehicle`) wraps `swarm_common.vehicle_fsm.VehicleFSM`:
  the only code that commands the autopilot.

There is no auctioneer, no leader election, no mesh builder, no task
generator. Nothing exists that "every drone needs". The GCS is an optional
observer and operator uplink: unplug it and the swarm keeps flying its tasks.

The same `DroneBrain` and `VehicleFSM` classes run in the ROS-free simulator
(`swarm_common.sim`), so the scenarios CI runs exercise the code that flies.

## 2. Communication: state-based gossip

Drones broadcast two packet kinds (JSON in a `SwarmPacket`):

| packet | rate | content | used for |
|---|---|---|---|
| beacon `B` | 5 Hz | position, velocity, altitude | collision avoidance (ORCA) |
| state `S` | 1 Hz, plus immediately (≤5 Hz) on change | roster, task registry, CBBA tables, recent observations, coverage bitmaps | everything else |

Everything in a state packet is a **mergeable replicated structure**, so a
packet can be lost, duplicated, delayed or reordered and every drone still
converges. Information travels multi-hop simply because each drone
rebroadcasts its merged state: D1 and D5 don't need to hear each other.

* **Neighbour table**: built from packets actually received, with
  packet-receipt ratio per neighbour from sequence numbers. Links are
  measured, not inferred from GPS distance.
* **Roster**: last-writer-wins map; each drone writes only its own entry.
* **Task registry**: state-based CRDT (`swarm_common/tasks.py`). Definitions
  merge by smallest `(created_t, creator)`; status is a monotone lattice
  `SUGGESTED < OPEN < DONE < CANCELLED < MERGED`.
* **Coverage**: grow-only set of searched cells, sent as a hex bitmap.
* **Observations**: append-only set keyed by `(observer, seq)`.

Measured bandwidth in the scenarios: 2–13 KiB/s per drone.

## 3. Task allocation: CBBA (no auctioneer)

`swarm_common/cbba.py` implements the Consensus-Based Bundle Algorithm
(Choi, Brunet & How, IEEE T-RO 2009).

1. Each drone scores work items with its own state (position, battery, wind)
   using a time-discounted reward, and only if the energy model says it can
   do the work and still get home (`energy.py`).
2. Drones exchange winning bids, winners and info timestamps with neighbours.
   The CBBA decision table resolves every conflict deterministically.
3. Losing a task releases everything added to the bundle after it.

Supporting rules:

* **Claim settle (2.5 s):** a drone acts on a new claim only once it has
  survived a few consensus rounds. This prevents four drones taking off for
  one task while bids propagate.
* **Rebid margin (10%):** stealing a held task needs a clear improvement,
  which avoids chatter.
* **Dead drones:** a claim held by a drone missing from the roster for 10 s
  is reset, and the task is re-bid.

Composite tasks (perimeter rings, intercepts) are stored once as a parent.
Their slots are *derived* deterministically, so every drone agrees on the
slot list without exchanging it. A drone may hold at most one slot per ring.

**Guarantee:** with a connected network (even multi-hop and lossy), CBBA
converges to a conflict-free assignment. **Under a partition** each side
converges on its own, and a task injected on both sides may be executed
twice. That cannot be avoided without communication. On heal, CBBA leaves
exactly one executor (tested in `partition_heal`).

## 4. One energy model

The old code bid with "15 % + 4 %/km" and relinquished with "30 % + 5 %/km",
so drones were assigned and then immediately gave the task up. Now
`EnergyModel` decides both. A drone relinquishes only when reality diverges
from the model (e.g. stronger wind, worn battery). Another drone then
re-bids the task automatically (`battery_handover` scenario).

**In-flight calibration.** `DrainCalibrator` compares each drone's real
battery drop (in the autopilot's whole-percent steps) with what the model
predicted for the flight it actually flew, and scales the model. This came
out of the first SITL run: stock ArduPilot SITL drains about 5× faster than
`fleet.yaml` assumes. The drones had bid on a perimeter they couldn't hold,
relinquished it, and the critical-battery failsafe brought them home. With
calibration, the `miscalibrated_batteries` scenario (every pack 4× worse than
modelled) learns 4.0× on every drone, and no drone ever needs the failsafe.

## 5. Vehicle authority: the safety FSM

`VehicleFSM` sits between brain and autopilot. Priorities:

1. **E-STOP** (operator): land now, latched.
2. **Hard failsafes**: critical battery, geofence. RTL, latched.
3. **Operator RTL / LAND**: latched until RESUME.
4. **Brain watchdog**: setpoints stale for 1.5 s means HOLD; stale for 10 s means RTL.
5. **Mission setpoints**: obeyed only when nothing above applies.

This fixes the old bug where the mission loop re-sent GUIDED gotos and
silently cancelled RTL. The autopilot keeps its own failsafes (RC, GCS
link, battery) underneath. `vehicle_manager` also staggers `RTL_ALT` per
drone so autopilot-level RTLs don't converge at one altitude.

## 6. Motion: altitude layers and ORCA

* Each drone flies its own altitude layer (`base_alt + spacing × ((id−1) mod layers)`).
* Within a layer, **ORCA** (`orca.py`, a port of RVO2) computes the
  collision-free velocity closest to the preferred one, using neighbours'
  beacons. Each drone takes half the avoidance responsibility. A small
  "keep right" bias breaks the symmetric deadlocks ORCA is known for.
* Velocity setpoints stream at 10 Hz, rather than position gotos every 4–10 s.

Tested: 10 drones on a single layer cross through one point with minimum
separation ≥ 12 m (`dense_crossing`), and 12 agents swap across a circle.

**Buildings.** With an OSM area (`area_file` in fleet.yaml) each drone builds a
10 m height grid, dilated by its clearance, and plans with A* + line-of-sight
smoothing *at its own altitude layer* (a 20 m warehouse is no obstacle at 42 m; a
110 m tower is). The route is re-verified from the drone's actual position every
tick (moving ring slots, ORCA nudges), goals inside buildings are replaced by the
nearest free point, and a last-line brake scales down any velocity whose 3 s
look-ahead would enter a building. `city_ops` among 110 m towers: 0 strikes.

## 7. Perception and the shared world model

* `project_bbox` projects a detection's bounding box onto the ground using
  the camera FOV, gimbal pitch, vehicle attitude and altitude. Previously
  the task was placed wherever the spotting drone happened to be.
* Observations gossip. Every drone runs the same deterministic clustering,
  so two drones that see the same survivor agree it is one person. If they
  raced to create two RESCUE tasks, `resolve_duplicates` folds them
  identically everywhere.
* Moving targets (`TargetTracker`): a real detector only says "vehicle", for the
  quarry and every parked car. Every vehicle sighting is associated by global
  nearest neighbour to small alpha-beta tracks (with a least-squares velocity);
  the tracker locks on to the track that *moves* and started near the operator's
  click, and parked cars keep feeding their own tracks. Same observations → same
  lock on every drone. The ring centre follows it, two "cutter" slots lead it.
  (`intercept_with_decoys`: 1 m mean error with 8 look-alikes.)
* Human-in-the-loop: perception tasks are `SUGGESTED` and not allocatable
  until an operator confirms one. A confirmation reaching any drone spreads
  by gossip.

## 8. Decentralized search

`SEARCH` tasks define an area. Idle drones split the *remaining* cells into
contiguous strips by a deterministic rule (same inputs on every drone give
the same split). Each drone sweeps its strip, and searched cells are
gossiped. When a drone leaves or dies, the survivors recompute and the gap
gets covered.

## 9. Missions on the same primitives

* **Perimeter patrol** (`PATROL`): a ring kind that never completes, rotating at
  ~3 m/s; slots bid with a one-shift energy horizon so low batteries hand over.
  `MotionWatch` tracks every person/vehicle inside the perimeter and reports one
  only once it is confirmed *moving*; any drone that sees that spawns an
  `INTERCEPT` (near-duplicates from other drones fold into the oldest). Bundles
  hold one item, so open intercept slots *preempt* patrol duty: the k drones
  nearest the intruder (by the shared roster) drop their patrol slot and bid.
* **Flood recon** (`FLOOD`): a `SEARCH` plus a second G-Set of cells seen under
  water, gossiped like coverage; on completion every drone emits the same
  `FLOOD_MAP` (flooded hectares, people inside flooded cells).

## 10. What is proven where

| layer | how | what |
|---|---|---|
| pure core | `pytest` (in CI) | CBBA convergence (35 randomized lossy multi-hop runs), CRDT merge laws, FSM priorities, ORCA separation, projection geometry, fusion, coverage |
| swarm behaviour | 14 simulator scenarios (in CI), some also at 30% loss | dispatch, perimeter, intercept (+ among decoys), search & rescue, flood recon, patrol + intruder, city ops, battery handover, drone loss + refill, partition + heal, dense crossing, RTL sticks |
| MAVLink backend | tests against a fake ArduCopter over real MAVLink/UDP (in CI) | ACK handling and retries, mode-by-name, pre-arm failure reporting, no re-arm in flight, param set |
| ROS 2 integration | `scripts/ros_acceptance.py` against the live ROS graph (in CI, sim backend) | telemetry, measured mesh, single executor, perimeter, RTL sticks, loss detection |
| ArduPilot SITL | `swarm_sitl.launch.py` + `ros_acceptance.py` | 6/6 |
| ArduPilot SITL in Gazebo physics | `scripts/gz/run_swarm.sh` + `swarm_gazebo.launch.py` + `ros_acceptance.py` | 6/6 (OSM city world) |

## 11. Known limits

* The fast simulator's vehicles are point masses and its radio is a disc model
  with random loss. Gazebo + SITL and real radios are the next levels of truth.
* Clocks: ring rotation and timestamps assume GPS-synchronised clocks
  (true on real drones; trivially true in simulation).
* Gossip state grows with fleet size. Fine to around 20 drones. Beyond that,
  send deltas and digests instead of full state.
* Security: packets are not authenticated. Add signing (e.g. MAVLink 2
  signing at the autopilot, plus SROS2 or HMAC on `SwarmPacket`) before any
  real deployment.
* PX4 support in `MavlinkBackend` is written but untested.
* Building avoidance is only as good as OSM heights; no terrain or manned-aircraft
  avoidance.
