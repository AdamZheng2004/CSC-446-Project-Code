# Imports
import numpy as np
from scipy import stats
from simulation import confidence_interval


def print_baseline_results(all_results):
    """
    Print the baseline performance results and confidence intervals.
    """

    # Print individual replication results.
    for run, results in enumerate(all_results, start=1):

        print(f"\nStarting Baseline Run {run}")

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
            if values is not None:
                print(
                    f"Node {node_id}: "
                    f"L = {values['L']:.4f}, "
                    f"Lambda*W = {values['lambda_W']:.4f}, "
                    f"Difference = {values['difference']:.4f}"
                )
            else:
                print(f"Node {node_id}: No visits recorded.")

    # 6. 95% Confidence Intervals
    print("\n6. Baseline 95% Confidence Intervals")

    metrics = {
        "Throughput": "throughput",
        "Mean Latency": "mean_latency",
        "P99 Latency": "p99_latency",
        "Node 3 Average Queue": "node3_average_queue",
        "Node 3 Blocking Probability": "node3_blocking_probability"
    }

    for label, key in metrics.items():
        values = [result[key] for result in all_results]
        mean, lower, upper = confidence_interval(values)
        print(f"{label}: {mean:.4f} (95% CI: {lower:.4f}, {upper:.4f})")

    # Confidence Intervals for Node Utilization
    for node_id in range(1, 8):
        values = [result["utilization"][node_id] for result in all_results]
        mean, lower, upper = confidence_interval(values)

        print(
            f"Node {node_id} Utilization: {mean * 100:.4f}% "
            f"(95% CI: {lower * 100:.4f}%, {upper * 100:.4f}%)"
        )


def print_capacity_results(scenario_results):
    """
    Print the capacity scenario results and compare the designs using paired t-tests.
    """

    print("\n============================================================")
    print("Part 3: Bottleneck Identification & Network Capacity Planning")
    print("============================================================")

    # Print average performance for each scenario.
    for scenario_name, results in scenario_results.items():

        print(f"\n{scenario_name}")

        metrics = {
            "Throughput": "throughput",
            "Mean Latency": "mean_latency",
            "P99 Latency": "p99_latency",
            "Node 3 Average Queue": "node3_average_queue",
            "Node 3 Blocking Probability": "node3_blocking_probability"
        }

        for label, key in metrics.items():
            values = [result[key] for result in results]
            mean, lower, upper = confidence_interval(values)

            print(
                f"{label}: {mean:.4f} "
                f"(95% CI: {lower:.4f}, {upper:.4f})"
            )

        print("Average Node Utilization:")

        for node_id in range(1, 8):
            values = [
                result["utilization"][node_id] for result in results
            ]
            mean, lower, upper = confidence_interval(values)

            print(
                f"Node {node_id}: {mean * 100:.4f}% "
                f"(95% CI: {lower * 100:.4f}%, {upper * 100:.4f}%)"
            )

    # Compare the proposed design against each alternative.
    print("\n\nPAIRED T-TESTS: PROPOSED DESIGN VS ALTERNATIVES")
    print("Metric: 99th Percentile End-to-End Latency")
    print("Significance level: 0.05")

    proposed_results = scenario_results["Proposed"]

    for alternative_name in [
        "Alternative 1",
        "Alternative 2",
        "Alternative 3"
    ]:

        alternative_results = scenario_results[alternative_name]

        proposed_p99 = [
            result["p99_latency"] for result in proposed_results
        ]

        alternative_p99 = [
            result["p99_latency"] for result in alternative_results
        ]

        # Paired differences: Proposed minus Alternative.
        differences = np.array(proposed_p99) - np.array(alternative_p99)

        test_result = stats.ttest_rel(
            proposed_p99,
            alternative_p99
        )

        mean_difference = np.mean(differences)

        print(f"\nProposed vs {alternative_name}")
        print(f"Mean paired difference: {mean_difference:.4f} ms")
        print(f"t-statistic: {test_result.statistic:.4f}")
        print(f"p-value: {test_result.pvalue:.4f}")

        if test_result.pvalue < 0.05:
            print("Result: Statistically significant difference.")
        else:
            print("Result: No statistically significant difference.")

        if mean_difference < 0:
            print("The proposed design had lower average P99 latency.")
        elif mean_difference > 0:
            print("The alternative had lower average P99 latency.")
        else:
            print("The designs had equal average P99 latency.")