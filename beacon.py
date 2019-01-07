#!/usr/bin/env python3

# Small sections of this code, namely those dealing with IP_PKTINFO and in_pktinfo have been copied
# from github project https://github.com/etingof/pysnmp, which is subject to the BSD 2-Clause
# "Simplified" License, which allows us to re-use the code, under the condition that the following
# copyright notice included:
#   Copyright (c) 2005-2019, Ilya Etingof <etingof@gmail.com> All rights reserved.
# See https://github.com/etingof/pysnmp/blob/master/LICENSE.rst for the license of the copied code.

import argparse
import ctypes
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

SYMBOLS = {
    'IP_PKTINFO': 8,
    'IP_TRANSPARENT': 19,
    'SOL_IPV6': 41,
    'IPV6_RECVPKTINFO': 49,
    'IPV6_PKTINFO': 50
}

# pylint:disable=invalid-name
uint32_t = ctypes.c_uint32

in_addr_t = uint32_t

class in_addr(ctypes.Structure):
    _fields_ = [('s_addr', in_addr_t)]

class in6_addr_U(ctypes.Union):
    _fields_ = [
        ('__u6_addr8', ctypes.c_uint8 * 16),
        ('__u6_addr16', ctypes.c_uint16 * 8),
        ('__u6_addr32', ctypes.c_uint32 * 4),
    ]

class in6_addr(ctypes.Structure):
    _fields_ = [
        ('__in6_u', in6_addr_U),
    ]

class in_pktinfo(ctypes.Structure):
    _fields_ = [
        ('ipi_ifindex', ctypes.c_int),
        ('ipi_spec_dst', in_addr),
        ('ipi_addr', in_addr),
    ]

for symbol in SYMBOLS:
    if not hasattr(socket, symbol):
        setattr(socket, symbol, SYMBOLS[symbol])

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
    # pylint:disable=no-member
    # We join the multicast group on a particular local interface, identified by local_address.
    # That means multicast packets received on that interface will be accepted. Note, however,
    # that if there are multiple sockets S1, S2, S3, ... that have joined the same multicast group
    # (same multicast address and same port) on different interfaces I1, I2, I3, ... then if we
    # receive a multicast packet on ANY of the interfaces I1, I2, I3... then ALL the sockets S1,
    # S2, S3, ... will be notified that a packet has been received. We use the IP_PKTINFO socket
    # option to determine on which interface I the packet was *really* received and ignore the
    # packet on all other sockets.
    sock.setsockopt(socket.SOL_IP, socket.IP_PKTINFO, 1)
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
    # pylint:disable=too-many-locals
    (sock, interface_name, interface_index) = sock_info
    ancillary_size = socket.CMSG_LEN(MAX_SIZE)
    try:
        message, ancillary_messages, _msg_flags, source = sock.recvmsg(MAX_SIZE, ancillary_size)
    except Exception as exception:
        report("exception {} while receiving on {}".format(exception, interface_name))
    else:
        (address, port) = source
        # We use the IP_PKTINFO ancillary data to determine on which interface the packet was
        # *really* received, and we ignore the packet if this socket is not associated with that
        # particular interface. See comment in create_rx_socket for additional details.
        rx_interface_index = None
        for anc in ancillary_messages:
            # pylint:disable=no-member
            if anc[0] == socket.SOL_IP and anc[1] == socket.IP_PKTINFO:
                packet_info = in_pktinfo.from_buffer_copy(anc[2])
                rx_interface_index = packet_info.ipi_ifindex
        if rx_interface_index and (rx_interface_index != interface_index):
            return
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
        interface_index = socket.if_nametoindex(interface_name)
        rx_sock_infos_by_fd[sock.fileno()] = (sock, interface_name, interface_index)
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
