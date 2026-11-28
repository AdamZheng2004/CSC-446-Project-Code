# Imports
import numpy as np
import FEL as fel
from node import Packet, create_nodes
from warmup import reset_statistics


def run_simulation(node_setup, input_stream, simulation_time, node_configs, warmup_time=0):
    """
    Run one simulation using the supplied Node configuration and input stream.
    The run lasts warmup_time + simulation_time, statistics only cover the last simulation_time.
    """
    # Simulation ends after the warm-up period plus the measured period.
    end_time = warmup_time + simulation_time

    # Set up the Nodes and random input stream.
    fel.nodes = create_nodes(node_setup, node_configs)
    fel.CURRENT_INPUT_STREAM = input_stream

    # Reset trackers.
    fel.node3_arrival_attempts = 0
    fel.node3_blocked_packets = 0

    fel.FEL.clear()
    fel.packet_latencies.clear()
    fel.packet_departure_times.clear()

    for times in fel.node_times.values():
        times.clear()

    for node_id in fel.nodes:
        fel.unfinished_node_times[node_id] = 0.0

    # Schedule external arrivals using the saved input stream.
    arrivals = input_stream["arrivals"]

    for packet_id, arrival_time in enumerate(arrivals, start=1):
        packet = Packet(packet_id, arrival_time)
        fel.schedule_event(fel.FEL, arrival_time, fel.ARRIVAL, packet, 1)

    # Process events until simulation horizon.
    final_time = 0.0
    warmup_done = (warmup_time == 0)

    while fel.FEL:
        if fel.FEL[0][0] > end_time:
            break

        # Clear the statistics once the warm-up period is over.
        if not warmup_done and fel.FEL[0][0] >= warmup_time:
            reset_statistics(warmup_time)
            warmup_done = True

        event = fel.FEL.pop(0)
        fel.process_event(event)
        final_time = event[0]

    # Track unfinished visits at simulation cutoff.
    unfinished_counts = {i: 0 for i in range(1, 8)}

    for node_id, node in fel.nodes.items():

        active_packets = list(node.queue)

        # Packets currently receiving service.
        active_packets += [
            event[2] for event in fel.FEL
            if event[1] == fel.DEPARTURE and event[3] == node_id
        ]

        # Packets blocked at this upstream node.
        active_packets += [
            packet for packet, upstream_id in fel.nodes[3].blocked_upstream
            if upstream_id == node_id
        ]

        for packet in active_packets:
            fel.unfinished_node_times[node_id] += (end_time - packet.node_arrival_times[node_id])
            unfinished_counts[node_id] += 1

    # Update performance measurements.
    for node in fel.nodes.values():
        node.update_node_busy_time(end_time)
        node.update_system_length(end_time)
        node.update_queue_length(end_time)

    # Calculate performance measures.
    # 1. Network Throughput.
    throughput = len(fel.packet_latencies) / simulation_time

    # 2. End-to-End Latency.
    if fel.packet_latencies:
        mean_latency = np.mean(fel.packet_latencies)
        p99_latency = np.percentile(fel.packet_latencies, 99)
    else:
        mean_latency = 0
        p99_latency = 0

    # 3. Node Utilization.
    utilization = {}

    for node_id, node in fel.nodes.items():
        utilization[node_id] = node.total_busy_time / (node.servers * simulation_time)

    # 4. Buffer Congestion.
    node3 = fel.nodes[3]
    average_queue_length = node3.queue_area / simulation_time

    if fel.node3_arrival_attempts > 0:
        blocking_probability = fel.node3_blocked_packets / fel.node3_arrival_attempts
    else:
        blocking_probability = 0

    # 5. Little's Law.
    little_law_results = {}

    for node_id, node in fel.nodes.items():
        L = node.system_area / simulation_time

        completed_count = len(fel.node_times[node_id])
        total_visits = completed_count + unfinished_counts[node_id]

        if total_visits > 0:
            arrival_rate = total_visits / simulation_time
            total_visit_time = (sum(fel.node_times[node_id]) + fel.unfinished_node_times[node_id])
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
        "completed_packets": len(fel.packet_latencies),
        "latencies": list(fel.packet_latencies),
        "departure_times": list(fel.packet_departure_times),
        "external_arrivals": len(arrivals)
    }

    return results


def confidence_interval(values):
    mean = np.mean(values)
    std = np.std(values, ddof=1)

    # 95% CI, using DF = 8 runs - 1.
    t_critical = 2.3646
    margin_of_error = t_critical * std / np.sqrt(len(values))

    lower_bound = mean - margin_of_error
    upper_bound = mean + margin_of_error

    return mean, lower_bound, upper_bound