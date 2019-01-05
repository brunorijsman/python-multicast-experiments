import datetime
import select
import socket

# TODO: Only one script instead of 3
# TODO: Command line argument: list of interface names on which to beacon
# TODO: Don't hard-code addresses, take it from the interface name
# TODO: Command line argument: node name
# TODO: On interface X send "node name + X"
# TODO: Just infinite loop, send periodically and print everthing sent and received and errors
# TODO: Loopback command-line option
# TODO: IPv4 and IPv6

ADDR_1_2 = "99.1.2.1"
ADDR_2_1 = "99.1.2.2"
ADDR_2_3 = "99.2.3.2"
ADDR_3_2 = "99.2.3.3"
ADDR_1_3 = "99.1.3.1"
ADDR_3_1 = "99.1.3.1"

MULTICAST_ADDR = "224.0.0.120"
MULTICAST_PORT = 911
MULTICAST_LOOPBACK = 0

MAX_SIZE = 1024

TICK_INTERVAL = 1.0

START_ABSOLUTE_TIME = datetime.datetime.now()

def create_multicast_socket(local_address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, MULTICAST_LOOPBACK)
    sock.bind((local_address, MULTICAST_PORT))
    sock.connect((MULTICAST_ADDR, MULTICAST_PORT))
    return sock

def receive(_sock):
    # TODO: Print whatever
    pass

def send(_sock):
    # TODO: Send message
    pass

def secs_since_start():
    # This returns a float with millisecond accuracy.
    absolute_now = datetime.datetime.now()
    time_delta_since_start = absolute_now - START_ABSOLUTE_TIME
    return time_delta_since_start.total_seconds()

def process_tick(socks_by_fd):
    for sock in socks_by_fd.values():
        send(sock)

def main_loop():
    socks_by_fd = {}
    fds = []
    timeout = 1.0
    next_tick_time = secs_since_start() + TICK_INTERVAL
    while True:
        while next_tick_time <= secs_since_start():
            process_tick(socks_by_fd)
            next_tick_time += TICK_INTERVAL
        timeout = next_tick_time - secs_since_start()
        rx_fds, _, _ = select.select(fds, [], [], timeout)
        for rx_fd in rx_fds:
            rx_sock = socks_by_fd[rx_fd]
            receive(rx_sock)
