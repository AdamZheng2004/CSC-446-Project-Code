# Imports
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import FEL as fel


# Welch's Method for Warm-up Determination.
def welch_warmup(pilot_results, simulation_time, bucket_size, window, tolerance, plot_file):
    """
    Use Welch's method on the pilot replications to find the warm-up time.
    """
    # Step 1: Average the latency of the packets leaving in each time bucket, for every replication.
    # Only the first third of the run is used, because the arrival rate is constant there.
    num_buckets = int(simulation_time / 3 / bucket_size)
    bucket_means = np.full((len(pilot_results), num_buckets), np.nan)

    for run, results in enumerate(pilot_results):
        departure_times = np.array(results["departure_times"])
        latencies = np.array(results["latencies"])

        for bucket in range(num_buckets):
            in_bucket = (departure_times >= bucket * bucket_size) & (departure_times < (bucket + 1) * bucket_size)

            if in_bucket.any():
                bucket_means[run, bucket] = latencies[in_bucket].mean()

    # Step 2: Average across the replications.
    average_curve = np.nanmean(bucket_means, axis=0)

    # Step 3: Moving average with window w (shrinks near the start of the curve).
    smoothed_curve = []

    for i in range(num_buckets - window):
        half_width = min(i, window)
        smoothed_curve.append(np.mean(average_curve[i - half_width: i + half_width + 1]))

    smoothed_curve = np.array(smoothed_curve)

    # Step 4: Warm-up ends at the first bucket where the curve reaches the steady-state level (within the tolerance).
    # Steady-state level is taken as the average of the second half of the smoothed curve.
    steady_level = np.mean(smoothed_curve[len(smoothed_curve) // 2:])
    close_enough = np.abs(smoothed_curve - steady_level) <= tolerance * steady_level
    warmup_bucket = int(np.where(close_enough)[0][0])

    # The warm-up is at least one bucket, since that is the smallest period this analysis can resolve.
    warmup_time = max(warmup_bucket, 1) * bucket_size

    # Save the plot for the report.
    plt.figure(figsize=(8, 4.5))
    plt.plot(np.arange(num_buckets) * bucket_size, average_curve, color="lightgray", label="Average across replications")
    plt.plot(np.arange(len(smoothed_curve)) * bucket_size, smoothed_curve, color="blue", label=f"Moving average (w = {window})")
    plt.axhline(steady_level, color="green", linestyle=":", label="Steady-state level")
    plt.axvline(warmup_time, color="red", linestyle="--", label=f"Warm-up = {warmup_time:.0f} ms")
    plt.xlabel("Time (ms)")
    plt.ylabel("Mean End-to-End Latency (ms)")
    plt.title("Welch's Method")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_file, dpi=150)
    plt.close()

    return warmup_time


# Clear the statistics when the warm-up period ends.
def reset_statistics(warmup_time):
    """
    Clear all performance measurements at the end of the warm-up period.
    Packets already in the network stay where they are, only their measured time starts now.
    """
    # Bring the Node trackers up to date, then clear them.
    for node in fel.nodes.values():
        node.update_node_busy_time(warmup_time)
        node.update_system_length(warmup_time)
        node.update_queue_length(warmup_time)

        node.total_busy_time = 0.0
        node.system_area = 0.0
        node.queue_area = 0.0

    # Clear the recorded packet results.
    fel.packet_latencies.clear()
    fel.packet_departure_times.clear()
    fel.node3_arrival_attempts = 0
    fel.node3_blocked_packets = 0

    for times in fel.node_times.values():
        times.clear()

    # Packets already in a Node only count the time spent there from now on.
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
            packet.node_arrival_times[node_id] = warmup_time