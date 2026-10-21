# Published by vehicle_manager (the vehicle authority) for its own brain.
std_msgs/Header header
uint32 drone_id
string label
bool connected
float64 lat
float64 lon
float64 x            # ENU metres from the fleet origin
float64 y
float64 alt          # metres above home
float64 vx           # east m/s
float64 vy           # north m/s
float64 battery_pct
bool armed
string mode          # normalised: GUIDED / RTL / LAND / HOLD / STABILIZE / ...
string fsm_state     # GROUND / TAKEOFF / GUIDED / HOLD / RTL / LAND / ESTOP
string latch         # why mission control is locked out ("" = not latched)
float64 roll         # body FLU / world ENU convention, radians
float64 pitch
float64 yaw_enu      # CCW from east
float64 wind_speed
