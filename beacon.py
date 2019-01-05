#!/usr/bin/env python3

import argparse
import datetime
import select
import socket
import sys

import netifaces

# TODO: Command line argument: node name
# TODO: On interface X send "node name + X"
# TODO: Just infinite loop, send periodically and print everthing sent and received and errors
# TODO: Loopback command-line option
# TODO: IPv4 and IPv6

ARGS = None

MULTICAST_ADDR = "224.0.0.120"
MULTICAST_PORT = 911
MULTICAST_LOOPBACK = 0

MAX_SIZE = 1024

TICK_INTERVAL = 1.0

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

def create_multicast_socket(interface_name):
    local_address = interface_ipv4_address(interface_name)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, MULTICAST_LOOPBACK)
    sock.bind((local_address, MULTICAST_PORT))
    sock.connect((MULTICAST_ADDR, MULTICAST_PORT))
    return sock

def receive(interface_info):
    (_rx_sock, _interface_name) = interface_info
    # TODO

def send(interface_info, message):
    (sock, interface_name) = interface_info
    try:
        sock.send(message.encode())
    except Exception as exception:
        report("exception {} while sending {} on {}".format(exception, message, interface_name))
    else:
        report("sent {} on {}".format(message, interface_name))

def secs_since_start():
    # This returns a float with millisecond accuracy.
    absolute_now = datetime.datetime.now()
    time_delta_since_start = absolute_now - START_ABSOLUTE_TIME
    return time_delta_since_start.total_seconds()

def process_tick(interface_infos_by_fd):
    global ARGS, COUNT
    nr_interfaces = len(interface_infos_by_fd)
    interface_info = list(interface_infos_by_fd.values())[COUNT % nr_interfaces]
    (_sock, interface_name) = interface_info
    COUNT += 1
    message = "message-{}-{}-{}".format(ARGS.beacon, interface_name, COUNT)
    send(interface_info, message)

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
    interface_infos_by_fd = {}
    fds = []
    for interface_name in ARGS.interface:
        sock = create_multicast_socket(interface_name)
        interface_infos_by_fd[sock.fileno()] = (sock, interface_name)
        fds.append(sock.fileno())
    next_tick_time = secs_since_start() + TICK_INTERVAL
    while True:
        while next_tick_time <= secs_since_start():
            process_tick(interface_infos_by_fd)
            next_tick_time += TICK_INTERVAL
        timeout = next_tick_time - secs_since_start()
        rx_fds, _, _ = select.select(fds, [], [], timeout)
        for rx_fd in rx_fds:
            interface_info = interface_infos_by_fd[rx_fd]
            receive(interface_info)

def main():
    parse_command_line_arguments()
    beacon_loop()

if __name__ == "__main__":
    main()
