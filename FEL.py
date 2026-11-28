# Event Types
ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"

# Performance Tracking
node_times = {i: [] for i in range(1, 8)}
packet_latencies = []
packet_departure_times = []
node3_arrival_attempts = 0
node3_blocked_packets = 0
unfinished_node_times = {i: 0.0 for i in range(1, 8)}

# Simulation State
# simulation.py resets these at the start of every run.
FEL = []
nodes = {}
CURRENT_INPUT_STREAM = None


# FEL Setup.
def schedule_event(FEL, event_time, event_type, packet, node):
    """
    Add an event to the FEL.
    """
    event = (event_time, event_type, packet, node)
    FEL.append(event)
    FEL.sort(key=lambda event: event[0])


# Event Processing Functions
def process_event(event):
    """
    Process an event from the FEL.
    """
    event_time, event_type, packet, node_id = event
    current_time = event_time

    # Identify event type.
    if event_type == ARRIVAL:
        handle_arrival(packet, node_id, current_time)
    elif event_type == DEPARTURE:
        handle_departure(packet, node_id, current_time)


def handle_arrival(packet, node_id, current_time):
    """
    Handle a packet arrival at a Node event.
    """
    node = nodes[node_id]

    # Record packet arrival time at current Node.
    packet.node_arrival_times[node_id] = current_time
    node.update_system_length(current_time)

    # Check whether the Node can accept the packet (For Node 3, shouldn't have arrival event when buffer full).
    if not node.can_accept_packet():
        raise RuntimeError("Packet arrived at a full Node.")

    # Start service if a server is available.
    if node.busy_servers < node.servers:
        node.update_node_busy_time(current_time)
        node.busy_servers += 1

        service_time = CURRENT_INPUT_STREAM["service_times"][packet.id][node_id]
        departure_time = current_time + service_time
        schedule_event(FEL, departure_time, DEPARTURE, packet, node_id)
    else:
        node.update_queue_length(current_time)
        node.queue.append(packet)


def release_server(node_id, current_time):
    """
    Release a server and start service for the next queued packet.
    """
    node = nodes[node_id]
    node.update_node_busy_time(current_time)
    node.update_system_length(current_time)
    node.busy_servers -= 1

    # Start service for the next queued packet.
    if node.queue:
        node.update_queue_length(current_time)
        next_packet = node.queue.pop(0)
        node.busy_servers += 1

        service_time = CURRENT_INPUT_STREAM["service_times"][next_packet.id][node_id]
        departure_time = current_time + service_time

        schedule_event(FEL, departure_time, DEPARTURE, next_packet, node_id)

    # Check whether Node 3 can now accept blocked packets.
    if node_id == 3:
        admit_blocked_packets(current_time)


def admit_blocked_packets(current_time):
    """
    Admit blocked packets when Node 3 has available capacity.
    """
    node3 = nodes[3]

    # Admit blocked packets while Node 3 has capacity.
    while node3.blocked_upstream and node3.can_accept_packet():
        packet, upstream_node_id = node3.blocked_upstream.pop(0)

        # Record time spent at the upstream Node.
        node_times[upstream_node_id].append(current_time - packet.node_arrival_times[upstream_node_id])

        # Admit the packet into Node 3.
        handle_arrival(packet, 3, current_time)

        # Release the upstream server.
        release_server(upstream_node_id, current_time)


def handle_departure(packet, node_id, current_time):
    """
    Handle a packet completing service at a Node.
    """
    global node3_arrival_attempts, node3_blocked_packets

    # Determine the next Node.
    if node_id == 1:
        next_node = 2
    elif node_id == 2:
        if CURRENT_INPUT_STREAM["routing"][packet.id][2]:
            next_node = 3
        else:
            next_node = 6
    elif node_id == 3:
        if CURRENT_INPUT_STREAM["routing"][packet.id][3]:
            next_node = 4
        else:
            next_node = 5
    elif node_id in (4, 5, 6):
        next_node = 7
    elif node_id == 7:
        next_node = 8
    else:
        return

    # Count attempts to enter Node 3 and detect blocking.
    if next_node == 3:
        node3_arrival_attempts += 1

        if not nodes[3].can_accept_packet():
            node3_blocked_packets += 1

    # Apply backpressure if Node 3 cannot accept the packet.
    if next_node == 3 and not nodes[3].can_accept_packet():
        nodes[3].blocked_upstream.append((packet, node_id))
        return

    # Record time spent at the current Node.
    node_times[node_id].append(current_time - packet.node_arrival_times[node_id])

    # Release the current Node's server.
    release_server(node_id, current_time)

    # Admit the packet into Node 3.
    if next_node == 3:
        handle_arrival(packet, 3, current_time)

    # Handle packets reaching the sink.
    elif next_node == 8:
        packet.current_node = 8
        packet.departure_time = current_time
        packet_latencies.append(packet.departure_time - packet.arrival_time)
        packet_departure_times.append(current_time)

    # Schedule arrival at the next Node.
    else:
        packet.current_node = next_node
        schedule_event(FEL, current_time, ARRIVAL, packet, next_node)