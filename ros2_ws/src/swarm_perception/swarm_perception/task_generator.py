"""Closes the autonomy loop: person detections become auctioned tasks.

Uses the spotting drone's live SITL position as the task location
(stand-in for full GPS projection of the bounding box).
"""
import time
import rclpy
from rclpy.node import Node
from swarm_interfaces.msg import DetectionArray, DroneTelemetry, TaskRequest
from swarm_common.vision_core import PERSON


class TaskGenerator(Node):
    def __init__(self):
        super().__init__('task_generator')
        self.declare_parameter('cooldown_s', 60.0)
        self.cooldown = self.get_parameter('cooldown_s').value
        self.last_task_at = 0.0
        self.counter = 0
        self.drone_positions = {}

        self.create_subscription(DroneTelemetry, '/swarm/telemetry', self.on_telemetry, 10)
        self.create_subscription(DetectionArray, '/swarm/detections', self.on_detections, 10)
        self.pub = self.create_publisher(TaskRequest, '/swarm/task_requests', 10)
        self.get_logger().info('Task generator listening for person detections...')

    def on_telemetry(self, msg: DroneTelemetry):
        self.drone_positions[msg.label] = (msg.lat, msg.lon)

    def on_detections(self, msg: DetectionArray):
        if not any(d.class_name == PERSON for d in msg.detections):
            return
        now = time.time()
        if now - self.last_task_at < self.cooldown:
            return
        label = msg.header.frame_id
        pos = self.drone_positions.get(label)
        if pos is None:
            self.get_logger().warning(f'person seen by {label}, but no telemetry for it yet')
            return
        self.counter += 1
        self.last_task_at = now
        req = TaskRequest()
        req.task_id = f'RESCUE-{self.counter}'
        req.lat, req.lon = pos
        req.description = f'auto: person(s) seen by {label}'
        self.pub.publish(req)
        self.get_logger().info(f'PERSON SIGHTED by {label} -> requested {req.task_id} at {pos}')


def main(args=None):
    rclpy.init(args=args)
    node = TaskGenerator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
