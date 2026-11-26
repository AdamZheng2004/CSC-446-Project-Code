# Imports
import numpy as np

# Constants
# Simulation Parameters
SIMULATION_TIME = 48000
NUM_REPLICATIONS = 8

# Event Types
ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"

# Performance Tracking
node_times = {i: [] for i in range(1, 8)}
packet_latencies = []

# Simulation State
FEL = []

# Seed
np.random.seed(42)


# Packet Class.
class Packet:
    """
    Obj to pass from Node to Node.
    """
    def __init__(self, packet_id, arrival_time):
        self.id = packet_id
        self.arrival_time = arrival_time
        self.current_node = 1
        self.departure_time = None
        self.node_arrival_times = {}


# Node Class.
class Node:
    """
    To store the properties and current state of each Node.
    """
    def __init__(self, name, servers, distribution, parameters):
        self.name = name
        self.servers = servers
        self.distribution = distribution
        self.parameters = parameters

        # To track the number of busy servers.
        self.busy_servers = 0

        # Queue to store packets waiting for service.
        self.queue = []

    def generate_service_time(self):
        """
        Generate a service time based on the Node's distribution.
        """
        if self.distribution == "lognormal":
            mu, sigma = self.parameters
            return np.random.lognormal(mu, sigma)

        elif self.distribution == "exponential":
            lam = self.parameters
            return np.random.exponential(1 / lam)

        elif self.distribution == "triangular":
            min_time, mode, max_time = self.parameters
            return np.random.triangular(min_time, mode, max_time)

        elif self.distribution == "weibull":
            alpha, beta = self.parameters
            return beta * np.random.weibull(alpha)

        elif self.distribution == "erlang":
            k, mean = self.parameters
            return np.random.gamma(k, mean / k)

        elif self.distribution == "gamma":
            alpha, beta = self.parameters
            return np.random.gamma(alpha, beta)

        elif self.distribution == "uniform":
            min_time, max_time = self.parameters
            return np.random.uniform(min_time, max_time)

        else:
            raise ValueError("Invalid service time distribution.")


# Create Nodes 1-7 and store in dictionary, node 8 sink handle in main.
node1 = Node("Node 1", 3, "lognormal", (4.0, 1.2)) # Assuming that given mu and sigma represent the underlying normal parameters.
node2 = Node("Node 2", 2, "exponential", 0.5)
node3 = Node("Node 3", 4, "triangular", (1.0, 2.0, 4.0))
node4 = Node("Node 4", 5, "weibull", (1.5, 6.0))
node5 = Node("Node 5", 3, "erlang", (3, 8.0))
node6 = Node("Node 6", 1, "gamma", (2.0, 5.0))
node7 = Node("Node 7", 4, "uniform", (2.0, 5.0))

nodes = {1: node1, 2: node2, 3: node3, 4: node4, 5: node5, 6: node6, 7: node7}


# NHPP Arrival Process Generation from Notes (3.4.4)
def compensator(t, lam_low, lam_peak, T):
    """
    Compensator function for piecewise NHPP.
    """
    interval = T / 3

    if t < interval:
        return lam_low * t
    elif t < 2 * interval:
        return (lam_low * interval) + (lam_peak * (t - interval))
    else:
        return (lam_low * interval) + (lam_peak * interval) + (lam_low * (t - 2 * interval))


def inverse_compensator(t, lam_low, lam_peak, T):
    """
    Inverse compensator function for piecewise NHPP.
    """
    interval = T / 3

    first_boundary = compensator(interval, lam_low, lam_peak, T)
    second_boundary = compensator(2 * interval, lam_low, lam_peak, T)

    if t < first_boundary:
        return t / lam_low
    elif t < second_boundary:
        return interval + (t - first_boundary) / lam_peak
    else:
        return (2 * interval) + (t - second_boundary) / lam_low


def generate_arrivals(lam_low, lam_peak):
    """
    Generate NHPP arrival times.
    """
    arrivals = []
    t = 0.0
    T = SIMULATION_TIME

    # Calculate maximum transformed time.
    max_transformed_time = compensator(T, lam_low, lam_peak, T)

    while True:
        # Step 1: Generate uniform random variable.
        u = np.random.uniform()

        # Step 2: Generate next transformed arrival time.
        t += -np.log(u)

        # Check if transformed time exceeds simulation horizon.
        if t > max_transformed_time:
            break

        # Step 3: Convert transformed time to actual time.
        arrival_time = inverse_compensator(t, lam_low, lam_peak, T)
        arrivals.append(arrival_time)

    return arrivals


# FEL Setup.
def schedule_event(FEL, event_time, event_type, packet, node):
    """
    Add an event to the FEL.
    """
    event = (event_time, event_type, packet, node)
    FEL.append(event)
    FEL.sort(key=lambda event: event[0])


# Event Processing Functions
def process_event(event):
    """
    Process an event from the FEL.
    """
    event_time, event_type, packet, node_id = event
    current_time = event_time

    # Identify event type.
    if event_type == ARRIVAL:
        handle_arrival(packet, node_id, current_time)
    elif event_type == DEPARTURE:
        handle_departure(packet, node_id, current_time)


def handle_arrival(packet, node_id, current_time):
    """
    Handle a packet arrival at a Node event.
    """
    node = nodes[node_id]

    # Record packet arrival time at current Node.
    packet.node_arrival_times[node_id] = current_time

    # Check if a server is available.
    if node.busy_servers < node.servers:
        node.busy_servers += 1
        departure_time = current_time + node.generate_service_time()
        schedule_event(FEL, departure_time, DEPARTURE, packet, node_id)
    else:
        node.queue.append(packet)


def handle_departure(packet, node_id, current_time):
    """
    Handle a packet completing service at a Node, schedules the next arrival event.
    """
    node = nodes[node_id]
    node.busy_servers -= 1

    # Record time spent at this Node.
    node_times[node_id].append(
        current_time - packet.node_arrival_times[node_id]
    )

    # Start service for the next queued packet.
    if node.queue:
        next_packet = node.queue.pop(0)
        node.busy_servers += 1
        departure_time = current_time + node.generate_service_time()
        schedule_event(FEL, departure_time, DEPARTURE, next_packet, node_id)

    # Route completed packet to the next Node.
    if node_id == 1:
        next_node = 2
    elif node_id == 2:
        next_node = 3 if np.random.uniform() < 0.90 else 6
    elif node_id == 3:
        next_node = 4 if np.random.uniform() < 0.60 else 5
    elif node_id in (4, 5, 6):
        next_node = 7
    elif node_id == 7:
        next_node = 8
    else:
        return

    # Schedule arrival event for the next Node.
    if next_node == 8:
        packet.current_node = 8
        packet.departure_time = current_time
        packet_latencies.append(packet.departure_time - packet.arrival_time)
    else:
        packet.current_node = next_node
        schedule_event(FEL, current_time, ARRIVAL, packet, next_node)


def main():
    """
    Main function to run the simulation.
    """
    # Initialize simulation, reset trackers.
    FEL.clear()
    packet_latencies.clear()

    for node in nodes.values():
        node.busy_servers = 0
        node.queue.clear()

    for times in node_times.values():
        times.clear()

    # Define the packet stream.
    lam_low = 0.005
    lam_peak = 0.010
    arrivals = generate_arrivals(lam_low, lam_peak)

    # Schedule external arrivals at Node 1.
    for packet_id, arrival_time in enumerate(arrivals, start=1):
        packet = Packet(packet_id, arrival_time)
        schedule_event(FEL, arrival_time, ARRIVAL, packet, 1)

    # Process events until the simulation horizon.
    final_time = 0.0

    while FEL:
        event = FEL.pop(0)

        if event[0] > SIMULATION_TIME:
            break

        process_event(event)
        final_time = event[0]

    # Display basic simulation results.
    print("\nSimulation Results")
    print("------------------")
    print("Total external arrivals:", len(arrivals))
    print("Completed packets:", len(packet_latencies))
    print("Final simulation time:", final_time)

    # Calculate latency statistics.
    if packet_latencies:
        mean_latency = np.mean(packet_latencies)
        percentile_99 = np.percentile(packet_latencies, 99)

        print("Mean end-to-end latency:", mean_latency, "ms")
        print("99th percentile latency:", percentile_99, "ms")

    # Display average time spent at each Node.
    for node_id, times in node_times.items():
        if times:
            print(f"Node {node_id} average time: {np.mean(times):.2f} ms")


if __name__ == "__main__":
    main()