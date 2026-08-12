"""Simulated telemetry source: fake sine-wave flight + battery drain.

Publishes typed DroneTelemetry. Used for simulation/validation before
real SITL hardware is in the loop.
"""
import math

import rclpy
from rclpy.node import Node

from swarm_interfaces.msg import DroneTelemetry
from swarm_common.validation import validate_lat, validate_lon, validate_battery


class TelemetryPublisher(Node):
    def __init__(self):
        super().__init__('telemetry_publisher')
        self.declare_parameter('drone_label', 'D1')
        self.declare_parameter('start_lat', 6.5244)
        self.declare_parameter('start_lon', 3.3792)
        self.label = self.get_parameter('drone_label').value
        self.start_lat = self.get_parameter('start_lat').value
        self.start_lon = self.get_parameter('start_lon').value
        self.battery = 100.0
        self.t = 0
        self.publisher_ = self.create_publisher(DroneTelemetry, '/swarm/telemetry', 10)
        self.timer = self.create_timer(1.0, self.publish_state)
        self.get_logger().info(f'Telemetry publisher started for {self.label}')

    def publish_state(self):
        lat = self.start_lat + 0.0005 * math.sin(self.t / 10)
        lon = self.start_lon + 0.0005 * math.cos(self.t / 10)
        self.battery = max(0.0, self.battery - 0.05)
        self.t += 1

        msg = DroneTelemetry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.label = self.label
        msg.lat = validate_lat(lat)
        msg.lon = validate_lon(lon)
        msg.battery_pct = round(validate_battery(self.battery), 1)
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TelemetryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
