"""
Phase 3 - Task allocation via auction (Contract Net Protocol style).

No central controller assigns tasks. Instead, each drone calculates
its own "bid" for a task based on factors only it knows about itself
(distance to the task, current battery). The drone with the BEST bid
(lowest cost) wins the task. This is the real algorithm behind most
practical multi-robot task allocation systems.

This builds directly on Phase 2's mesh - in a real deployment, the
"bid" messages would travel over the mesh relay we already proved
works.
"""
import math
from dataclasses import dataclass, field


@dataclass
class Drone:
    drone_id: str
    lat: float
    lon: float
    battery_pct: float
    busy: bool = False

    def distance_km(self, target_lat, target_lon):
        R = 6371.0
        dlat = math.radians(target_lat - self.lat)
        dlon = math.radians(target_lon - self.lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(self.lat)) * math.cos(math.radians(target_lat)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def bid_for_task(self, task):
        """Lower bid = better (this drone is a stronger candidate).
        Returns None if the drone can't/shouldn't take the task at all."""
        if self.busy:
            return None  # already doing something, can't bid

        dist = self.distance_km(task.lat, task.lon)

        # Hard rule: don't bid if battery is too low to safely do the
        # round trip (rough safety margin, not just "can reach it")
        estimated_battery_needed = dist * 4  # rough % per km, toy estimate
        if self.battery_pct < estimated_battery_needed + 15:  # +15% safety reserve
            return None

        # Bid formula: weighted cost - closer and higher-battery = lower (better) bid
        # This is the "utility function" concept from Phase 2's design doc
        cost = (dist * 1.0) + ((100 - self.battery_pct) * 0.05)
        return cost


@dataclass
class Task:
    task_id: str
    lat: float
    lon: float
    description: str


def run_auction(drones, task):
    """Every drone independently calculates its own bid - this is
    decentralized, no drone needs to know the others' internal state,
    only its own. Bids get compared to pick a winner."""
    print(f"\n--- Auction for {task.task_id}: {task.description} ---")
    bids = {}

    for d in drones:
        bid = d.bid_for_task(task)
        if bid is None:
            print(f"  {d.drone_id}: NO BID (busy or insufficient battery)")
        else:
            bids[d.drone_id] = bid
            print(f"  {d.drone_id}: bid = {bid:.2f} (distance-based cost, lower is better)")

    if not bids:
        print(f"  RESULT: No drone available for {task.task_id}. Task unassigned.")
        return None

    winner_id = min(bids, key=bids.get)
    print(f"  RESULT: {winner_id} WINS the task (lowest bid: {bids[winner_id]:.2f})")
    return winner_id


def demo():
    # Reuse the same 5-drone layout from Phase 2's flood zone, now with
    # battery levels varying, some drones already busy
    drones = [
        Drone("D1", 6.5244, 3.3792, battery_pct=95, busy=False),
        Drone("D2", 6.5300, 3.3850, battery_pct=40, busy=False),
        Drone("D3", 6.5360, 3.3910, battery_pct=88, busy=True),   # already on a task
        Drone("D4", 6.5420, 3.3970, battery_pct=70, busy=False),
        Drone("D5", 6.5480, 3.4030, battery_pct=25, busy=False),  # low battery
    ]

    tasks = [
        Task("T1", 6.5430, 3.3980, "Map flooded road segment near D4/D5"),
        Task("T2", 6.5250, 3.3800, "Relay stranded-person message near D1"),
    ]

    assignments = {}
    for task in tasks:
        winner = run_auction(drones, task)
        if winner:
            assignments[task.task_id] = winner
            # mark the winning drone as busy so it can't win a second task
            for d in drones:
                if d.drone_id == winner:
                    d.busy = True

    print("\n=== Final task assignments ===")
    for task_id, drone_id in assignments.items():
        print(f"  {task_id} -> {drone_id}")


if __name__ == "__main__":
    demo()
