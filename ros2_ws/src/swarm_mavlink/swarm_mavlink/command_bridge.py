"""Operator uplink, v3.1: fresh reading session per command;
TAKEOFF uses the canonical GUIDED -> ARM -> TAKEOFF sequence."""
import threading
import time
import rclpy
from rclpy.node import Node
from pymavlink import mavutil
from swarm_interfaces.msg import DroneCommand

FLEET = {
    "D1": "tcp:127.0.0.1:5770", "D2": "tcp:127.0.0.1:5780",
    "D3": "tcp:127.0.0.1:5790", "D4": "tcp:127.0.0.1:5800",
    "D5": "tcp:127.0.0.1:5810",
}


class CommandBridge(Node):
    def __init__(self):
        super().__init__('command_bridge')
        self.create_subscription(DroneCommand, '/swarm/commands', self.on_cmd, 10)
        self.get_logger().info('Command bridge listening on /swarm/commands')

    def on_cmd(self, m):
        url = FLEET.get(m.label)
        if url is None:
            self.get_logger().warning(f'no uplink for {m.label}')
            return
        threading.Thread(target=self._execute,
                         args=(m.label, url, m.command.upper()),
                         daemon=True).start()

    def _execute(self, label, url, cmd):
        try:
            c = mavutil.mavlink_connection(url, source_system=255)
            c.wait_heartbeat(timeout=10)
            for _ in range(2):
                c.mav.heartbeat_send(6, 0, 0, 0, 0)
                time.sleep(0.5)
            if cmd == 'ARM':
                self.long(c, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=1)
            elif cmd == 'DISARM':
                self.long(c, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=0)
            elif cmd == 'TAKEOFF':
                self.long(c, mavutil.mavlink.MAV_CMD_DO_SET_MODE, p1=1, p2=4)  # GUIDED
                time.sleep(1)
                self.long(c, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=1)
                time.sleep(2)
                self.long(c, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, z=30)
            elif cmd == 'RTL':
                self.long(c, mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
            elif cmd == 'LAND':
                self.long(c, mavutil.mavlink.MAV_CMD_NAV_LAND)
            else:
                self.get_logger().warning(f'unknown command {cmd}')
                return
            self.get_logger().info(f'{label}: sent {cmd}')
            t0 = time.time()
            while time.time() - t0 < 5:
                mm = c.recv_match(blocking=True, timeout=0.5)
                if mm is None:
                    continue
                t = mm.get_type()
                if t == 'STATUSTEXT':
                    self.get_logger().info(f'[{label}] {mm.text}')
                elif t == 'COMMAND_ACK':
                    self.get_logger().info(f'[{label}] ACK cmd={mm.command} result={mm.result}')
            c.close()
        except Exception as e:
            self.get_logger().error(f'{label}: {cmd} failed: {e}')

    def long(self, c, command, p1=0.0, p2=0.0, z=0.0):
        c.mav.command_long_send(c.target_system, c.target_component,
                                command, 0, p1, p2, 0, 0, 0, 0, z)


def main(args=None):
    rclpy.init(args=args)
    node = CommandBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
