# Imports
import numpy as np

# Constants
# Simulation Parameters
SIMULATION_TIME = 48000
NUM_RUNS = 8

# Event Types
ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"
SEEDS = [1,2,3,4,5,6,7,8]

# Performance Tracking
node_times = {i: [] for i in range(1, 8)}
packet_latencies = []
node3_arrival_attempts = 0
node3_blocked_packets = 0
unfinished_node_times = {i: 0.0 for i in range(1, 8)}

# Simulation State
FEL = []


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
    def __init__(self, name, servers, distribution, parameters, buffer_capacity=None):
        self.name = name
        self.servers = servers
        self.distribution = distribution
        self.parameters = parameters
        
        # To track the number of busy servers.
        self.busy_servers = 0

        # Queue to store packets waiting for service.
        self.queue = []
        self.queue_area = 0.0
        self.last_queue_update = 0.0

        # Track server utilization.
        self.total_busy_time = 0.0
        self.last_update_time = 0.0

        # Track average number of packets in the Node.
        self.system_area = 0.0
        self.last_system_update = 0.0

        # Packets blocked while waiting to enter Node 3.
        self.buffer_capacity = buffer_capacity
        self.blocked_upstream = []

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
        
    def update_queue_length(self, current_time):
        """
        Track the time-weighted queue length.
        """
        elapsed_time = current_time - self.last_queue_update
        self.queue_area += len(self.queue) * elapsed_time
        self.last_queue_update = current_time

    def update_node_busy_time(self, current_time):
        """
        Track cumulative busy server time for a Node.
        """
        elapsed_time = current_time - self.last_update_time
        self.total_busy_time += self.busy_servers * elapsed_time
        self.last_update_time = current_time

    def update_system_length(self, current_time):
        """
        Track the time-weighted number of packets in the Node.
        """
        elapsed_time = current_time - self.last_system_update
        self.system_area += (self.busy_servers + len(self.queue)) * elapsed_time
        self.last_system_update = current_time

    def can_accept_packet(self):
        """
        Check whether the Node has room for another packet.
        """
        if self.busy_servers < self.servers:
            return True

        if self.buffer_capacity is None or len(self.queue) < self.buffer_capacity:
            return True

        return False


# Create Nodes 1-7 and store in dictionary, node 8 sink handle in main.
node1 = Node("Node 1", 3, "lognormal", (4.0, 1.2)) # Assuming that given mu and sigma represent the underlying normal parameters.
node2 = Node("Node 2", 2, "exponential", 0.5)
node3 = Node("Node 3", 4, "triangular", (1.0, 2.0, 4.0), buffer_capacity=15)
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
    node.update_system_length(current_time)

    # Check whether the Node can accept the packet (For Node 3, shouldn't have arrival event when buffer full).
    if not node.can_accept_packet():
        raise RuntimeError("Packet arrived at a full Node.")

    # Start service if a server is available.
    if node.busy_servers < node.servers:
        node.update_node_busy_time(current_time)
        node.busy_servers += 1
        departure_time = current_time + node.generate_service_time()
        schedule_event(FEL, departure_time, DEPARTURE, packet, node_id)
    else:
        node.update_queue_length(current_time)
        node.queue.append(packet)


def release_server(node_id, current_time):
    """
    Release a server and start service for the next queued packet.
    """
    node = nodes[node_id]
    node.update_node_busy_time(current_time)
    node.update_system_length(current_time)
    node.busy_servers -= 1

    # Start service for the next queued packet.
    if node.queue:
        node.update_queue_length(current_time)
        next_packet = node.queue.pop(0)
        node.busy_servers += 1
        departure_time = current_time + node.generate_service_time()
        schedule_event(FEL, departure_time, DEPARTURE, next_packet, node_id)

    # Check whether Node 3 can now accept blocked packets.
    if node_id == 3:
        admit_blocked_packets(current_time)


def admit_blocked_packets(current_time):
    """
    Admit blocked packets when Node 3 has available capacity.
    """
    node3 = nodes[3]

    # Admit blocked packets while Node 3 has capacity.
    while node3.blocked_upstream and node3.can_accept_packet():
        packet, upstream_node_id = node3.blocked_upstream.pop(0)

        # Record time spent at the upstream Node.
        node_times[upstream_node_id].append(current_time - packet.node_arrival_times[upstream_node_id])

        # Admit the packet into Node 3.
        handle_arrival(packet, 3, current_time)

        # Release the upstream server.
        release_server(upstream_node_id, current_time)


def handle_departure(packet, node_id, current_time):
    """
    Handle a packet completing service at a Node.
    """
    global node3_arrival_attempts, node3_blocked_packets

    # Determine the next Node.
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

    # Count attempts to enter Node 3 and detect blocking.
    if next_node == 3:
        node3_arrival_attempts += 1

        if not nodes[3].can_accept_packet():
            node3_blocked_packets += 1

    # Apply backpressure if Node 3 cannot accept the packet.
    if next_node == 3 and not nodes[3].can_accept_packet():
        nodes[3].blocked_upstream.append((packet, node_id))
        return

    # Record time spent at the current Node.
    node_times[node_id].append(current_time - packet.node_arrival_times[node_id])

    # Release the current Node's server.
    release_server(node_id, current_time)

    # Admit the packet into Node 3.
    if next_node == 3:
        handle_arrival(packet, 3, current_time)

    # Handle packets reaching the sink.
    elif next_node == 8:
        packet.current_node = 8
        packet.departure_time = current_time
        packet_latencies.append(packet.departure_time - packet.arrival_time)

    # Schedule arrival at the next Node.
    else:
        packet.current_node = next_node
        schedule_event(FEL, current_time, ARRIVAL, packet, next_node)


def run_simulation():
    """
    One run of simulation.
    """
    global node3_arrival_attempts, node3_blocked_packets

    # Reset trackers.
    node3_arrival_attempts = 0
    node3_blocked_packets = 0

    FEL.clear()
    packet_latencies.clear()

    for node in nodes.values():
        node.busy_servers = 0
        node.queue.clear()
        node.blocked_upstream.clear()
        node.total_busy_time = 0.0
        node.last_update_time = 0.0
        node.queue_area = 0.0
        node.last_queue_update = 0.0
        node.system_area = 0.0
        node.last_system_update = 0.0

    for times in node_times.values():
        times.clear()

    for node_id in nodes:
        unfinished_node_times[node_id] = 0.0

    # Generate external arrivals.
    lam_low = 0.005
    lam_peak = 0.010
    arrivals = generate_arrivals(lam_low, lam_peak)

    for packet_id, arrival_time in enumerate(arrivals, start=1):
        packet = Packet(packet_id, arrival_time)
        schedule_event(FEL, arrival_time, ARRIVAL, packet, 1)

    # Process events until simulation horizon.
    final_time = 0.0

    while FEL:
        if FEL[0][0] > SIMULATION_TIME:
            break

        event = FEL.pop(0)
        process_event(event)
        final_time = event[0]

    # Track unfinished visits at simulation cutoff.
    unfinished_counts = {i: 0 for i in range(1, 8)}

    for node_id, node in nodes.items():

        active_packets = list(node.queue)

        # Packets currently receiving service.
        active_packets += [
            event[2] for event in FEL
            if event[1] == DEPARTURE and event[3] == node_id
        ]

        # Packets blocked at this upstream node.
        active_packets += [
            packet for packet, upstream_id in nodes[3].blocked_upstream
            if upstream_id == node_id
        ]

        for packet in active_packets:
            unfinished_node_times[node_id] += (SIMULATION_TIME -packet.node_arrival_times[node_id])
            unfinished_counts[node_id] += 1

    # Update performance measurements.
    for node in nodes.values():
        node.update_node_busy_time(SIMULATION_TIME)
        node.update_system_length(SIMULATION_TIME)
        node.update_queue_length(SIMULATION_TIME)

    # Calculate performance measures.
    # 1. Network Throughput.
    throughput = len(packet_latencies) / SIMULATION_TIME

    # 2. End-to-End Latency.
    if packet_latencies:
        mean_latency = np.mean(packet_latencies)
        p99_latency = np.percentile(packet_latencies, 99)
    else:
        mean_latency = 0
        p99_latency = 0

    # 3. Node Utilization.
    utilization = {}

    for node_id, node in nodes.items():
        utilization[node_id] = node.total_busy_time / (node.servers * SIMULATION_TIME)

    # 4. Buffer Congestion.
    node3 = nodes[3]
    average_queue_length = node3.queue_area / SIMULATION_TIME

    if node3_arrival_attempts > 0:
        blocking_probability = (node3_blocked_packets / node3_arrival_attempts)
    else:
        blocking_probability = 0

    # 5. Little's Law.
    little_law_results = {}

    for node_id, node in nodes.items():
        L = node.system_area / SIMULATION_TIME

        completed_count = len(node_times[node_id])
        total_visits = completed_count + unfinished_counts[node_id]

        if total_visits > 0:
            arrival_rate = total_visits / SIMULATION_TIME
            total_visit_time = (sum(node_times[node_id]) + unfinished_node_times[node_id])
            W = total_visit_time / total_visits
            lambda_W = arrival_rate * W

            if L > 0:
                difference = abs(L - lambda_W) / L * 100
            else:
                difference = 0

            little_law_results[node_id] = {
                "L": L,
                "lambda_W": lambda_W,
                "difference": difference
            }

        else:
            little_law_results[node_id] = None

    # Store results to return.
    results = {
        "throughput": throughput,
        "mean_latency": mean_latency,
        "p99_latency": p99_latency,
        "utilization": utilization,
        "node3_average_queue": average_queue_length,
        "node3_blocking_probability": blocking_probability,
        "little_law": little_law_results,
        "completed_packets": len(packet_latencies),
        "external_arrivals": len(arrivals)
    }

    return results


def main():
    """
    Runs the 8 runs of the simulation.
    """
    all_results = []

    for run in range(NUM_RUNS):
        # Set seed, do run, print results.
        np.random.seed(SEEDS[run])  

        print(f"\nStarting Run {run + 1}")

        results = run_simulation()
        all_results.append(results)
        
        print("1. Network Throughput")
        print(f"Throughput: {results['throughput']:.4f} packets/ms")

        print("\n2. End-to-End Latency (System Response Time)")
        print(f"Mean Latency: {results['mean_latency']:.4f} ms")
        print(f"99th Percentile Latency: {results['p99_latency']:.4f} ms")

        print("\n3. Node Utilization")
        for node_id, utilization in results["utilization"].items():
            print(f"Node {node_id}: {utilization * 100:.4f}%")

        print("\n4. Buffer Congestion (Node 3)")
        print(f"Average Queue Length: {results['node3_average_queue']:.4f}")
        print(f"Blocking Probability: {results['node3_blocking_probability']:.4f}")

        print("\n5. Little's Law Verification")
        for node_id, values in results["little_law"].items():
            print(
                f"Node {node_id}: "
                f"L = {values['L']:.4f}, "
                f"Lambda*W = {values['lambda_W']:.4f}, "
                f"Difference = {values['difference']:.4f}"
            )

    print("\nAll runs completed.")

    return all_results


if __name__ == "__main__":
    all_results = main()