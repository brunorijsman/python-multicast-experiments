import socket

PREFIX_1_2 = "99.1.2."
PREFIX_2_3 = "99.2.3."
UNICAST_PORT = 50000
MULTICAST_ADDR = "224.0.0.120"
MULTICAST_PORT = 911
MAX_SIZE = 1024

def open_unicast_socket(local_address, remote_address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((local_address, UNICAST_PORT))
    sock.connect((remote_address, UNICAST_PORT))
    return sock

def unicast_send(sock, sent_str):
    sock.send(sent_str.encode())

def unicast_expect(sock, expected_address, expected_str, ignore_str=None):
    while True:
        actual_data, address_and_port = sock.recvfrom(MAX_SIZE)
        (actual_address, actual_port) = address_and_port
        assert actual_address == expected_address
        assert actual_port == UNICAST_PORT
        if (ignore_str is not None) and (actual_data == ignore_str.encode()):
            continue
        assert actual_data == expected_str.encode()
        return

def make_address(link_prefix, node_id):
    return link_prefix + str(node_id)

def sync(link_prefix, local_id, remote_id, sync_point_name):
    local_address = make_address(link_prefix, local_id)
    remote_address = make_address(link_prefix, remote_id)
    if local_id > remote_id:
        sync_initiate(local_address, remote_address, sync_point_name)
    else:
        sync_expect(local_address, remote_address, sync_point_name)

def sync_initiate(local_address, remote_address, sync_point_name):
    sock = open_unicast_socket(local_address, remote_address)
    sock.settimeout(0.5)
    while True:
        try:
            unicast_send(sock, sync_point_name + "-req")
        except ConnectionRefusedError:
            # This happens when we try to send a packet from the remote node, but the remote
            # node is not running yet. Just continue trying to send .
            continue
        print("INIT: sent req")
        try:
            unicast_expect(sock, remote_address, sync_point_name + "-ack")
        except socket.timeout:
            # If we sent the req before the remote node was up, we will timeout waiting for the
            # ack. Just sent the req again.
            pass
    print("INIT: got ack")
    # Complete the 3-way handshake by sending a conf
    unicast_send(sock, sync_point_name + "-conf")
    print("INIT: sent conf")

def sync_expect(local_address, remote_address, sync_point_name):
    sock = open_unicast_socket(local_address, remote_address)
    while True:
        try:
            print("EXP: expect req")
            unicast_expect(sock, remote_address, sync_point_name + "-req")
        except ConnectionRefusedError:
            # This happens when we try to receive a packet from the remote node, but the remote
            # node is not running yet. Just continue trying to receive.
            pass
    print("EXP: got req")
    # The send should not fail, because we know for a fact that the remote node is running and
    # ready to receive the ack.
    unicast_send(sock, sync_point_name + "-ack")
    print("EXP: sent ack")
    # Now, wait for the conf that completes the 3-way handshake. While waiting for the conf, we
    # could see some retransmitted reqs that we should ignore
    unicast_expect(sock, remote_address, sync_point_name + "-conf", sync_point_name + "-req")
    print("EXP: got conf")
