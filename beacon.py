#!/usr/bin/env python3

import argparse
import datetime
import select
import socket
import sys

import netifaces

# TODO: Only one script instead of 3
# TODO: Command line argument: list of interface names on which to beacon
# TODO: Don't hard-code addresses, take it from the interface name
# TODO: Command line argument: node name
# TODO: On interface X send "node name + X"
# TODO: Just infinite loop, send periodically and print everthing sent and received and errors
# TODO: Loopback command-line option
# TODO: IPv4 and IPv6

MULTICAST_ADDR = "224.0.0.120"
MULTICAST_PORT = 911
MULTICAST_LOOPBACK = 0

MAX_SIZE = 1024

TICK_INTERVAL = 1.0

START_ABSOLUTE_TIME = datetime.datetime.now()

def fatal_error(message):
    sys.exit(message)

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

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Multicast Beacon')
    parser.add_argument(
        'interface',
        nargs='+',
        help='Interface name')
    args = parser.parse_args()
    return args

def interface_ipv4_address(interface_name):
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        fatal_error("Interface " + interface_name + " not present.")
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET in interface_addresses:
        fatal_error("Interface " + interface_name + " has no IPv4 address.")
    return interface_addresses[netifaces.AF_INET][0]['addr']

def beacon_loop(_interface_names):
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

def main():
    args = parse_command_line_arguments()
    beacon_loop(args.interface)

if __name__ == "__main__":
    main()
