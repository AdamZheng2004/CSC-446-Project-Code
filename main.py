# Imports
import numpy as np

# Constants
# Simulation Parameters
SIMULATION_TIME = 48000  # (48 seconds in ms)
NUM_REPLICATIONS = 8

# Event Types
ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"


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


# Nodes
def node_1():
    """
    Ingress Edge Router.
    """
    # Parameters
    servers = 3
    service_time = (4.0, 1.2) # Log-Normal

    # To Node 2

    return


def node_2():
    """
    Deep Packet Inspection.
    """
    # Parameters
    servers = 2
    service_time = (0.5) # Exponential

    # 90% to Node 3, 10% to Node 6

    return


def node_3():
    """
    Central Load Balancer.
    """
    # Parameters
    buffer_capacity = 15
    servers = 4
    service_time = (1.0, 2.0, 4.0) # Triangular

    # 60% to Node 4, 40% to Node 5
    
    return


def node_4():
    """
    Compute Cluster A (Standard).
    """
    # Parameters
    servers = 5
    service_time = (1.5, 6.0) # Weibull

    # To Node 7
    
    return


def node_5():
    """
    Compute Cluster B (GPU Heavy).
    """
    # Parameters
    servers = 3
    service_time = (3, 8.0) # Erlang-k

    # To Node 7

    return


def node_6():
    """
    Security Quarantine.
    """
    servers = 1
    service_time = (2.0, 5.0) # Gamma

    # To Node 7

    return


def node_7():
    """
    Database Ingestion.
    """
    # Parameters
    servers = 4
    service_time = (2.0, 5.0) # Uniform

    # To Node 8

    return


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
    # Future Event List Stuff
    current_time = 0.0
    events = []  

    # Define the packet stream.
    # Test with lambda low = 5 packets/sec and lambda peak = 10 packets/sec
    lam_low = 0.005
    lam_peak = 0.010

    arrivals = generate_arrivals(lam_low, lam_peak)
    print("Expected number of arrivals:", compensator(SIMULATION_TIME, lam_low, lam_peak, SIMULATION_TIME))
    print("First arrival:", arrivals[0])
    print("Last arrival:", arrivals[-1])
    
    # Main loop 

    # Display results
    packet = Packet(1, 0.0)
    print(packet.id, packet.arrival_time, packet.current_node)


if __name__ == "__main__":
    main()