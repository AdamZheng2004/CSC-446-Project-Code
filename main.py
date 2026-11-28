# Imports
from arrivals import generate_input_stream
from simulation import run_simulation
from warmup import welch_warmup
from report import print_baseline_results, print_capacity_results

# Constants
# Simulation Parameters
SIMULATION_TIME = 48000
NUM_RUNS = 8
SEEDS = [1, 2, 3, 4, 5, 6, 7, 8]

# Warm-up Parameters (Welch's Method)
# Pilot runs use their own seeds so they are separate from the eight reported replications.
PILOT_SEEDS = [101, 102, 103, 104, 105, 106, 107, 108]
BUCKET_SIZE = 1000
WINDOW = 5
TOLERANCE = 0.05


# Node Configuration
# The distributions and parameters stay the same across all scenarios, only change server count.
NODE_CONFIGS = {
    1: ("Node 1", "lognormal", (4.0, 1.2), None),
    2: ("Node 2", "exponential", 0.5, None),
    3: ("Node 3", "triangular", (1.0, 2.0, 4.0), 15),
    4: ("Node 4", "weibull", (1.5, 6.0), None),
    5: ("Node 5", "erlang", (3, 8.0), None),
    6: ("Node 6", "gamma", (2.0, 5.0), None),
    7: ("Node 7", "uniform", (2.0, 5.0), None)
}


def main():
    """
    Generate common input streams and run the baseline and capacity scenarios.
    """
    # Baseline Node server configuration.
    baseline_setup = {1: 3, 2: 2, 3: 4, 4: 5, 5: 3, 6: 1, 7: 4}

    # Four Scenarios with added servers.
    scenarios = {
        "Proposed": {1: 5, 2: 2, 3: 4, 4: 5, 5: 3, 6: 1, 7: 4}, # +2 servers at Node 1
        "Alternative 1": {1: 3, 2: 4, 3: 4, 4: 5, 5: 3, 6: 1, 7: 4}, # +2 servers at Node 2
        "Alternative 2": {1: 3, 2: 2, 3: 4, 4: 7, 5: 3, 6: 1, 7: 4}, # +2 servers at Node 4
        "Alternative 3": {1: 4, 2: 2, 3: 4, 4: 6, 5: 3, 6: 1, 7: 4} # +1 server at Node 1 and Node 4
    }

    # 1. Run pilot replications of the baseline network (no warm-up removed).
    print("Running pilot replications for warm-up analysis...")

    pilot_results = []

    for seed in PILOT_SEEDS:
        pilot_stream = generate_input_stream(seed, SIMULATION_TIME, NODE_CONFIGS)

        pilot_results.append(
            run_simulation(
                baseline_setup,
                pilot_stream,
                SIMULATION_TIME,
                NODE_CONFIGS
            )
        )

    # 2. Determine the warm-up period using Welch's method.
    warmup_time = welch_warmup(
        pilot_results,
        SIMULATION_TIME,
        BUCKET_SIZE,
        WINDOW,
        TOLERANCE,
        "welch_plot.png"
    )

    print(f"Warm-up period: {warmup_time:.0f} ms (Welch plot saved to welch_plot.png)")

    # 3. Generate and save the eight common input streams (warm-up period plus the 48 s measured).
    print("\nGenerating common random input streams...")

    input_streams = {}

    for seed in SEEDS:
        input_streams[seed] = generate_input_stream(seed, warmup_time + SIMULATION_TIME, NODE_CONFIGS)

        print(
            f"Input stream for seed {seed} generated "
            f"({len(input_streams[seed]['arrivals'])} arrivals)."
        )

    # 4. Run the baseline network.
    print("\nRunning baseline network...")

    baseline_results = []

    for seed in SEEDS:
        results = run_simulation(
            baseline_setup,
            input_streams[seed],
            SIMULATION_TIME,
            NODE_CONFIGS,
            warmup_time
        )

        baseline_results.append(results)

    # 5. Print baseline results.
    print_baseline_results(baseline_results)

    # 6. Run the four capacity scenarios using the same input streams.
    scenario_results = {}

    for scenario_name, node_setup in scenarios.items():

        print(f"\nRunning {scenario_name}...")

        scenario_results[scenario_name] = []

        for seed in SEEDS:
            results = run_simulation(
                node_setup,
                input_streams[seed],
                SIMULATION_TIME,
                NODE_CONFIGS,
                warmup_time
            )

            scenario_results[scenario_name].append(results)

        print(f"{scenario_name} completed.")

    # 7. Print capacity planning results and paired t-tests.
    print_capacity_results(scenario_results)

    print("\nAll baseline and capacity experiments completed.")

    return baseline_results, scenario_results


if __name__ == "__main__":
    baseline_results, scenario_results = main()