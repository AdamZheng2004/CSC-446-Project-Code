# Adam Zheng
# V01005151
# CSC 446
# 2026-11-27

# CSC 446 Project Option B
Discrete event simulation of a multi-tier edge-to-cloud packet processing network, written in Python.

## How to run
Please download all the .py files and have them in the same folder.
Install the required libraries listed in requirements.txt (skip if you already have numpy, scipy, and matplotlib).
Run main.py:

    python main.py

This will first run 8 warmup runs for Welch's.
Then it will run 8 more runs with warmup considered as the baseline (printing out all the stats in the terminal). 
Finally, it will run 8 runs per scenario for Part 3: Bottleneck Identification & Network Capacity Planning and print the t-tests.

The run takes around 15min on my laptop to complete.

## Files
- main.py: Constants, node configuration, scenario setup, Welch's graph, and the main run.
- arrivals.py: NHPP arrival generation, plus service times and routing for each replication.
- node.py: Packet and Node classes.
- FEL.py: Future Event List and all event handling (arrivals, departures, blocking).
- simulation.py: Runs one replication, computes the performance metrics, and the confidence interval function.
- report.py: Prints the results, confidence intervals, and paired t-tests.
- warmup.py: Runs Welch's method to create a graph for what to count as warmup.
- welch_plot.png: Plot from warmup.py.
- requirements.txt: Library versions used
 