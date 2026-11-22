# Imports
import numpy as np

# Simulation Parameters
SIMULATION_TIME = 48000  # (48 seconds in ms)
NUM_REPLICATIONS = 8

# Nodes
def node_1():
    """
    Ingress Edge Router
    """
    # Parameters
    arrival = "NHPP"
    servers = 3
    service_time = (4.0, 1.2) # Log-Normal

    # To Node 2

    return


def node_2():
    """
    Deep Packet Inspection
    """
    # Parameters
    servers = 2
    service_time = (0.5) # Exponential

    # 90% to Node 3, 10% to Node 6

    return


def node_3():
    """
    Central Load Balancer
    """
    # Parameters
    buffer_capacity = 15
    servers = 4
    service_time = (1.0, 2.0, 4.0) # Triangular

    # 60% to Node 4, 40% to Node 5
    
    return


def node_4():
    """
    Compute Cluster A (Standard)
    """
    # Parameters
    servers = 5
    service_time = (1.5, 6.0) # Weibull

    # To Node 7
    
    return


def node_5():
    """
    Compute Cluster B (GPU Heavy)
    """
    # Parameters
    servers = 3
    service_time = (3, 8.0) # Erlang-k

    # To Node 7

    return


def node_6():
    """
    Security Quarantine
    """
    servers = 1
    service_time = (2.0, 5.0) # Gamma

    # To Node 7

    return


def node_7():
    """
    Database Ingestion
    """
    # Parameters
    servers = 4
    service_time = (2.0, 5.0) # Uniform

    # To Node 8

    return


def node_8():
    """
    Sink
    """
    # Report Stats
    return


def main():
    """
    Main
    """
    # Define the packet stream.
    
    # Main loop 

    # Display results
    print("Hello World.")


if __name__ == "__main__":
    main()