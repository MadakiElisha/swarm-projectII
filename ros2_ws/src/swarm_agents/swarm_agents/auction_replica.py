"""Auction replica: one per drone; lowest-label alive replica leads.
Standbys mirror state so promotion is seamless - true decentralization."""
import time

import rclpy
from std_msgs.msg import String
from swarm_interfaces.msg import TaskAssignment
from swarm_tasks.task_auctioneer import TaskAuctioneer


class AuctionReplica(TaskAuctioneer):
    def __init__(self):
        super().__init__()   # node name overridden by launch name=
        self.declare_parameter('label', 'D1')
        self.label = self.get_parameter('label').value
        self.alive = {}
        self.is_leader = False
        self.hb_pub = self.create_publisher(String, '/swarm/auction_alive', 10)
        self.create_subscription(String, '/swarm/auction_alive', self.on_alive, 10)
        self.create_subscription(TaskAssignment, '/swarm/task_assignments', self.mirror, 10)
        self.create_timer(1.0, self.heartbeat)
        self.get_logger().info(f'{self.label}: auction replica standing by')

    def on_alive(self, m):
        self.alive[m.data] = time.time()

    def heartbeat(self):
        self.alive[self.label] = time.time()
        now = time.time()
        self.alive = {k: v for k, v in self.alive.items() if now - v < 3.0}
        leader = min(self.alive)
        if leader == self.label and not self.is_leader:
            self.get_logger().warn(f'{self.label}: PROMOTED to auction leader')
        elif leader != self.label and self.is_leader:
            self.get_logger().warn(f'{self.label}: demoted - {leader} leads')
        self.is_leader = (leader == self.label)
        self.hb_pub.publish(String(data=self.label))

    def mirror(self, m):
        if m.assigned_to:
            self.auction_results[m.task_id] = m   # idempotency state stays synced
            self.busy_drones[m.assigned_to] = time.time()  # busy-state stays synced

    def on_task_request(self, msg):
        self.task_coords[msg.task_id] = (msg.lat, msg.lon)  # standbys stay warm
        if not self.is_leader:
            return
        super().on_task_request(msg)

    def on_relinquish(self, msg):
        if not self.is_leader:
            return
        super().on_relinquish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = AuctionReplica()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
