#!/usr/bin/env python3

import argparse
import datetime
import random
import select
import socket
import struct
import sys

import netifaces

ARGS = None

MULTICAST_ADDR = "224.0.0.120"
MULTICAST_PORT = 911

MAX_SIZE = 1024

# Relatively slow, to avoid things getting confusing when too much stuff happens at the same time.
TICK_INTERVAL = 5.0

START_ABSOLUTE_TIME = datetime.datetime.now()

COUNT = 0

def fatal_error(message):
    sys.exit(message)

def report(message):
    global ARGS
    print("{}: {}".format(ARGS.beacon, message))

def interface_ipv4_address(interface_name):
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        fatal_error("Interface " + interface_name + " not present.")
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET in interface_addresses:
        fatal_error("Interface " + interface_name + " has no IPv4 address.")
    return interface_addresses[netifaces.AF_INET][0]['addr']

def create_rx_socket(interface_name):
    local_address = interface_ipv4_address(interface_name)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        pass
    sock.bind((MULTICAST_ADDR, MULTICAST_PORT))
    report("join group {} on {} for local address {}".format(MULTICAST_ADDR, interface_name,
                                                             local_address))
    req = struct.pack("=4s4s", socket.inet_aton(MULTICAST_ADDR), socket.inet_aton(local_address))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    return sock

def create_tx_socket(interface_name):
    local_address = interface_ipv4_address(interface_name)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        pass
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_address))
    # Disable the loopback of sent multicast packets to listening sockets on the same host. We don't
    # want this to happen because each beacon is listening on the same port and the same multicast
    # address on potentially multiple interfaces. Each receive socket should only receive packets
    # that were sent by the host on the other side of the interface, and not packet that were sent
    # from the same host on a different interface. IP_MULTICAST_IF is enabled by default, so we have
    # to explicitly disable it)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    sock.bind((local_address, MULTICAST_PORT))
    sock.connect((MULTICAST_ADDR, MULTICAST_PORT))
    return sock

def receive(sock_info):
    (sock, interface_name) = sock_info
    try:
        message, from_address_and_port = sock.recvfrom(MAX_SIZE)
    except Exception as exception:
        report("exception {} while receiving on {}".format(exception, interface_name))
    else:
        (address, port) = from_address_and_port
        message_str = message.decode()
        report("received {} on {} from {}:{}".format(message_str, interface_name, address, port))

def send(sock_info, message):
    (sock, interface_name) = sock_info
    try:
        report("send {} on {} from {} to {}".format(message, interface_name, sock.getsockname(),
                                                    sock.getpeername()))
        sock.send(message.encode())
    except Exception as exception:
        report("exception {} while sending {} on {}".format(exception, message, interface_name))

def secs_since_start():
    # This returns a float with millisecond accuracy.
    absolute_now = datetime.datetime.now()
    time_delta_since_start = absolute_now - START_ABSOLUTE_TIME
    return time_delta_since_start.total_seconds()

def process_tick(tx_sock_infos_by_fd):
    global ARGS, COUNT
    nr_interfaces = len(tx_sock_infos_by_fd)
    sock_info = list(tx_sock_infos_by_fd.values())[COUNT % nr_interfaces]
    (_sock, interface_name) = sock_info
    COUNT += 1
    message = "{}-message-{}-to-{}".format(ARGS.beacon, COUNT, interface_name)
    send(sock_info, message)

def parse_command_line_arguments():
    global ARGS
    parser = argparse.ArgumentParser(description='Multicast Beacon')
    parser.add_argument(
        'beacon',
        help='Beacon name')
    parser.add_argument(
        'interface',
        nargs='+',
        help='Interface name')
    ARGS = parser.parse_args()

def beacon_loop():
    # Create TX sockets
    tx_sock_infos_by_fd = {}
    for interface_name in ARGS.interface:
        sock = create_tx_socket(interface_name)
        tx_sock_infos_by_fd[sock.fileno()] = (sock, interface_name)
    # Create RX sockets
    rx_sock_infos_by_fd = {}
    rx_fds = []
    for interface_name in ARGS.interface:
        sock = create_rx_socket(interface_name)
        rx_sock_infos_by_fd[sock.fileno()] = (sock, interface_name)
        rx_fds.append(sock.fileno())
    # Random start tick time, to avoid all beacons being synchronized
    next_tick_time = secs_since_start() + random.uniform(0.0, TICK_INTERVAL)
    while True:
        while next_tick_time <= secs_since_start():
            process_tick(tx_sock_infos_by_fd)
            next_tick_time += TICK_INTERVAL
        timeout = next_tick_time - secs_since_start()
        active_rx_fds, _, _ = select.select(rx_fds, [], [], timeout)
        for active_rx_fd in active_rx_fds:
            sock_info = rx_sock_infos_by_fd[active_rx_fd]
            receive(sock_info)

def main():
    parse_command_line_arguments()
    beacon_loop()

if __name__ == "__main__":
    main()
