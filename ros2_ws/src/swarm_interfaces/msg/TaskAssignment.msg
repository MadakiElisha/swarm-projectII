# Published by a drone when IT starts (or stops) executing a work item.
# There is no central assigner: each drone announces only its own work.
std_msgs/Header header
string task_id        # parent task (e.g. SWARM-3); "" = this drone dropped its task
string item_id        # work item (e.g. SWARM-3/s2)
string assigned_to    # drone label
string kind           # GOTO / RESCUE / FORMATION / INTERCEPT
float64 lat           # parent task location
float64 lon
float32 orbit_radius  # > 0 for ring tasks
