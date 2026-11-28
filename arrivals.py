# Imports
import numpy as np
from node import Node


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


def generate_arrivals(lam_low, lam_peak, simulation_time):
    """
    Generate NHPP arrival times.
    """
    arrivals = []
    t = 0.0
    T = simulation_time

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


# Generate and save all random inputs for one replication.
def generate_input_stream(seed, simulation_time, node_configs):
    """
    Generate arrivals, service times and routing decisions for one seed.
    These inputs are reused across all capacity scenarios.
    """

    # Generate external arrivals.
    lam_low = 0.1
    lam_peak = 0.2

    np.random.seed(seed)
    arrivals = generate_arrivals(lam_low, lam_peak, simulation_time)

    # Store service times for every packet at every Node.
    service_times = {}

    for packet_id in range(1, len(arrivals) + 1):
        service_times[packet_id] = {}

        for node_id, config in node_configs.items():
            name, distribution, parameters, buffer_capacity = config

            temporary_node = Node(name, 1, distribution, parameters, buffer_capacity)
            service_times[packet_id][node_id] = (temporary_node.generate_service_time())

    # Store routing decisions for every packet.
    routing = {}

    for packet_id in range(1, len(arrivals) + 1):

        # Node 2: True means Node 3, False means Node 6.
        # Node 3: True means Node 4, False means Node 5.
        routing[packet_id] = {
            2: np.random.uniform() < 0.90,
            3: np.random.uniform() < 0.60
        }

    return {
        "arrivals": arrivals,
        "service_times": service_times,
        "routing": routing
    }