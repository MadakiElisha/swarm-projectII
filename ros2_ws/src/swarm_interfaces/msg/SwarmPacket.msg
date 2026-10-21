# One radio packet between drone brains (the ONLY drone-to-drone channel).
# The payload is versioned JSON produced by swarm_common.brain (beacons,
# gossip state, CBBA bids). sender_x/sender_y (ENU metres) let simulated
# links emulate radio range; real radios simply ignore them.
std_msgs/Header header
uint32 src
uint32 seq
string kind          # "B" beacon, "S" state
float64 sender_x
float64 sender_y
string payload
