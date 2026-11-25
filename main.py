# Imports
import numpy as np

# Constants
# Simulation Parameters
SIMULATION_TIME = 48000  # (48 seconds in ms)
NUM_REPLICATIONS = 8

# Event Types
ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"

# FEL
FEL = []


# Packet Class/Obj to pass from Node to Node.
class Packet:
    def __init__(self, packet_id, arrival_time):
        self.id = packet_id
        self.arrival_time = arrival_time
        self.current_node = 1


# Node Class to store the properties and current state of each Node.
class Node:
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
node1 = Node("Node 1", 3, "lognormal", (4.0, 1.2))
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

# Event Scheduling Function
def schedule_event(FEL, event_time, event_type, packet, node):
    """
    Add an event to the Future Event List.
    """
    event = (event_time, event_type, packet, node)
    FEL.append(event)
    FEL.sort(key=lambda event: event[0])


def main():
    """
    Main function to run the simulation.
    """
    # Initialize simulation.
    current_time = 0.0

    # Define the packet stream.
    # Test with lambda low = 5 packets/sec and lambda peak = 10 packets/sec
    lam_low = 0.005
    lam_peak = 0.010

    arrivals = generate_arrivals(lam_low, lam_peak)

    # Display arrival information.
    print("Expected number of arrivals:",compensator(SIMULATION_TIME, lam_low, lam_peak, SIMULATION_TIME))
    print("Actual number of arrivals:", len(arrivals))
    print("First arrival:", arrivals[0])
    print("Last arrival:", arrivals[-1])

    # Schedule external arrivals at Node 1.
    for packet_id, arrival_time in enumerate(arrivals, start=1):
        packet = Packet(packet_id, arrival_time)
        schedule_event(FEL, arrival_time, ARRIVAL, packet, 1)

    # Check FEL.
    print("\nFuture Event List (FEL):")
    print("Number of scheduled events:", len(FEL))
    print("First scheduled event:", FEL[0])
    print("Last scheduled event:", FEL[-1])

    # Main event-processing loop.


if __name__ == "__main__":
    main()