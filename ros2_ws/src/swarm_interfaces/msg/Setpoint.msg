# Brain -> vehicle_manager. The vehicle FSM decides whether to obey.
std_msgs/Header header
uint32 drone_id
string kind          # IDLE / VEL / POS / HOLD / RTB / LAND
float64 vx           # east m/s
float64 vy           # north m/s
float64 vz
float64 x            # ENU metres (POS)
float64 y
float64 alt          # target altitude above home
