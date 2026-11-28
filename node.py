# Imports
import numpy as np


# Packet Class.
class Packet:
    """
    Obj to pass from Node to Node.
    """
    def __init__(self, packet_id, arrival_time):
        self.id = packet_id
        self.arrival_time = arrival_time
        self.current_node = 1
        self.departure_time = None
        self.node_arrival_times = {}


# Node Class.
class Node:
    """
    To store the properties and current state of each Node.
    """
    def __init__(self, name, servers, distribution, parameters, buffer_capacity=None):
        self.name = name
        self.servers = servers
        self.distribution = distribution
        self.parameters = parameters

        # To track the number of busy servers.
        self.busy_servers = 0

        # Queue to store packets waiting for service.
        self.queue = []
        self.queue_area = 0.0
        self.last_queue_update = 0.0

        # Track server utilization.
        self.total_busy_time = 0.0
        self.last_update_time = 0.0

        # Track average number of packets in the Node.
        self.system_area = 0.0
        self.last_system_update = 0.0

        # Packets blocked while waiting to enter Node 3.
        self.buffer_capacity = buffer_capacity
        self.blocked_upstream = []

    def generate_service_time(self):
        """
        Generate a service time based on the Node's distribution.
        """
        if self.distribution == "lognormal":
            # Convert given mean and std of 4.0 and 1.2 to mu and sigma of underlying normal for numpy lognormal distribution.
            mean, std = self.parameters
            sigma = np.sqrt(np.log(1 + (std / mean) ** 2))
            mu = np.log(mean) - sigma ** 2 / 2
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

    def update_queue_length(self, current_time):
        """
        Track the time-weighted queue length.
        """
        elapsed_time = current_time - self.last_queue_update
        self.queue_area += len(self.queue) * elapsed_time
        self.last_queue_update = current_time

    def update_node_busy_time(self, current_time):
        """
        Track cumulative busy server time for a Node.
        """
        elapsed_time = current_time - self.last_update_time
        self.total_busy_time += self.busy_servers * elapsed_time
        self.last_update_time = current_time

    def update_system_length(self, current_time):
        """
        Track the time-weighted number of packets in the Node.
        """
        elapsed_time = current_time - self.last_system_update
        self.system_area += (self.busy_servers + len(self.queue)) * elapsed_time
        self.last_system_update = current_time

    def can_accept_packet(self):
        """
        Check whether the Node has room for another packet.
        """
        if self.busy_servers < self.servers:
            return True

        if self.buffer_capacity is None or len(self.queue) < self.buffer_capacity:
            return True

        return False


# Create Nodes using the server configuration for each scenario.
def create_nodes(node_setup, node_configs):
    """
    Create a set of Nodes using the supplied server counts.
    """
    new_nodes = {}

    for node_id, config in node_configs.items():
        name, distribution, parameters, buffer_capacity = config

        new_nodes[node_id] = Node(
            name,
            node_setup[node_id],
            distribution,
            parameters,
            buffer_capacity
        )

    return new_nodes