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


# Packet Object to pass from Node to Node.
class Packet:
    def __init__(self, packet_id, arrival_time):
        self.id = packet_id
        self.arrival_time = arrival_time
        self.current_node = 1


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


def schedule_event(FEL, event_time, event_type, packet, node):
    """
    Add an event to the Future Event List.
    """
    event = (event_time, event_type, packet, node)
    FEL.append(event)
    FEL.sort(key=lambda event: event[0])


# Nodes, returns a service time following the distribution except Node 8 which is a sink.
def node_1():
    """
    Ingress Edge Router.
    """
    # Parameters
    servers = 3
    mu = 4.0
    sigma = 1.2

    # Assumption: mu and sigma represent the underlying normal distribution.
    service_time = np.random.lognormal(mu, sigma)

    # To Node 2

    return service_time


def node_2():
    """
    Deep Packet Inspection.
    """
    # Parameters
    servers = 2
    lam = 0.5

    # Generate exponential service time.
    service_time = np.random.exponential(1/lam)

    # 90% to Node 3, 10% to Node 6

    return service_time


def node_3():
    """
    Central Load Balancer.
    """
    # Parameters
    buffer_capacity = 15
    servers = 4
    min_time = 1.0
    mode = 2.0
    max_time = 4.0

    # Generate triangular service time.
    service_time = np.random.triangular(min_time, mode, max_time)

    # 60% to Node 4, 40% to Node 5
    
    return service_time


def node_4():
    """
    Compute Cluster A (Standard).
    """
    # Parameters
    servers = 5
    alpha = 1.5
    beta = 6.0

    # Generate Weibull service time.
    service_time = beta * np.random.weibull(alpha)

    # To Node 7
    
    return service_time


def node_5():
    """
    Compute Cluster B (GPU Heavy).
    """
    # Parameters
    servers = 3
    k = 3
    mean = 8.0

    # Generate Erlang-k service time.
    scale = mean / k
    service_time = np.random.gamma(k, scale)

    # To Node 7

    return service_time


def node_6():
    """
    Security Quarantine.
    """
    # Parameters
    servers = 1
    alpha = 2.0
    beta = 5.0

    # Generate Gamma service time.
    service_time = np.random.gamma(alpha, beta)

    # To Node 7

    return service_time


def node_7():
    """
    Database Ingestion.
    """
    # Parameters
    servers = 4
    min_time = 2.0
    max_time = 5.0

    # Generate uniform service time.
    service_time = np.random.uniform(min_time, max_time)

    # To Node 8

    return service_time


def node_8():
    """
    Sink.
    """
    # Report Stats
    return


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

        schedule_event(
            FEL,
            arrival_time,
            ARRIVAL,
            packet,
            1
        )

    # Check FEL.
    print("\nFuture Event List (FEL):")
    print("Number of scheduled events:", len(FEL))
    print("First scheduled event:", FEL[0])
    print("Last scheduled event:", FEL[-1])

    # Main event-processing loop.


if __name__ == "__main__":
    main()