#!/bin/bash

# Setup the following network namespaces (netns) and virtual ethernet (veth) interface pairs:
#
#    ...............    ............................    ...............
#    . netns-1     .    . netns-2                  .    . netns-3     .
#    .             .    .                          .    .             .
#    . veth-1-2    .    . veth-2-1        veth-2-3 .    . veth-3-2    .
#    .    X------------------X             X-----------------X        .
#    . 99.1.2.1/24 .    . 99.1.2.2/24  99.2.3.2/24 .    . 99.2.3.3/24 .
#    .             .    .                          .    .             .
#    . veth-1-3    .    .                          .    . veth-3-1    .
#    . 99.1.3.1/24 .    .                          .    . 99.1.3.3/24 .
#    .    X        .    .                          .    .    X        .
#    .....|.........    ............................    .....|.........
#         |                                                  |
#         +--------------------------------------------------+

# TODO: Catch INT and cleanup (stop beacons and cleanup netns)

echo "SETUP"
echo "  Create veth pair veth-1-2 and veth-2-1"
ip link add dev veth-1-2 type veth peer name veth-2-1
echo "  Create veth pair veth-2-3 and veth-3-2"
ip link add dev veth-2-3 type veth peer name veth-3-2
echo "  Create veth pair veth-1-3 and veth-3-1"
ip link add dev veth-1-3 type veth peer name veth-3-1

echo "  Create netns-1"
ip netns add netns-1
echo "  Move veth-1-2 to netns-1"
ip link set veth-1-2 netns netns-1
echo "  Bring veth-1-2 up"
ip netns exec netns-1 ip link set dev veth-1-2 up
echo "  Assign address 99.1.2.1/24 to veth-1-2"
ip netns exec netns-1 ip addr add 99.1.2.1/24 dev veth-1-2
echo "  Move veth-1-2 to netns-1"
ip link set veth-1-3 netns netns-1
echo "  Bring veth-1-3 up"
ip netns exec netns-1 ip link set dev veth-1-3 up
echo "  Assign address 99.1.3.1/24 to veth-1-3"
ip netns exec netns-1 ip addr add 99.1.3.1/24 dev veth-1-3

echo "  Create netns-2"
ip netns add netns-2
echo "  Move veth-2-1 to netns-2"
ip link set veth-2-1 netns netns-2
echo "  Bring veth-2-1 up"
ip netns exec netns-2 ip link set dev veth-2-1 up
echo "  Assign address 99.1.2.2/24 to veth-2-1"
ip netns exec netns-2 ip addr add 99.1.2.2/24 dev veth-2-1
echo "  Move veth-2-3 to netns-2"
ip link set veth-2-3 netns netns-2
echo "  Bring veth-2-3 up"
ip netns exec netns-2 ip link set dev veth-2-3 up
echo "  Assign address 99.2.3.2/24 to veth-2-3"
ip netns exec netns-2 ip addr add 99.2.3.2/24 dev veth-2-3

echo "  Create netns-2"
ip netns add netns-3
echo "  Move veth-3-1 to netns-3"
ip link set veth-3-1 netns netns-3
echo "  Bring veth-3-1 up"
ip netns exec netns-3 ip link set dev veth-3-1 up
echo "  Assign address 99.1.3.3/24 to veth-3-1"
ip netns exec netns-3 ip addr add 99.1.3.3/24 dev veth-3-1
echo "  Move veth-3-2 to netns-3"
ip link set veth-3-2 netns netns-3
echo "  Bring veth-3-2 up"
ip netns exec netns-3 ip link set dev veth-3-2 up
echo "  Assign address 99.2.3.3/24 to veth-3-2"
ip netns exec netns-3 ip addr add 99.2.3.3/24 dev veth-3-2

# TODO: Change this to beacons
# ip netns exec netns-1 python3 /host/experiment_netns1.py &
# ip netns exec netns-2 python3 /host/experiment_netns2.py &
# ip netns exec netns-3 python3 /host/experiment_netns3.py &

wait

echo "CLEANUP"
echo "  Delete veth pair veth-1-2 and veth-2-1"
ip netns exec netns-1 ip link del veth-1-2
echo "  Delete veth pair veth-2-3 and veth-3-2"
ip netns exec netns-2 ip link del veth-2-3
echo "  Delete veth pair veth-1-3 and veth-3-1"
ip netns exec netns-1 ip link del veth-1-3
echo "  Delete netns-1"
ip netns del netns-1
echo "  Delete netns-2"
ip netns del netns-2
echo "  Delete netns-3"
ip netns del netns-3
