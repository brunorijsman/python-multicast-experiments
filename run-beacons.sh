#!/bin/bash

# Setup the following network namespaces (netns) and virtual ethernet (veth) interface pairs:
#
#    ...................    ............................    ...................
#    . netns-1         .    . netns-2                  .    . netns-3         .
#    .                 .    .                          .    .                 .
#    . veth-1-2        .    . veth-2-1        veth-2-3 .    .     veth-3-2    .
#    .    X----------------------X             X---------------------X        .
#    . 99.1.2.1/24     .    . 99.1.2.2/24  99.2.3.2/24 .    .     99.2.3.3/24 .
#    .                 .    .                          .    .                 .
#    .  veth-1-3a      .    .                          .    .    veth-3-1a    .
#    .  99.1.3.1/24 X  .    .                          .    .  X 99.1.3.3/24  .
#    .              |  .    .                          .    .  |              .
#    . veth-1-3b    |  .    .                          .    .  |  veth-3-1b   .
#    . 88.1.3.1/24  |  .    .                          .    .  |  88.1.3.3/24 .
#    .              |  .    .                          .    .  |              .
#    ...............|...    ............................    ...|...............
#                   |                                          |
#                   +------------------------------------------+

# TODO: Catch INT and cleanup (stop beacons and cleanup netns)

echo "SETUP"
echo "  Create veth pair veth-1-2 and veth-2-1"
ip link add dev veth-1-2 type veth peer name veth-2-1
echo "  Create veth pair veth-2-3 and veth-3-2"
ip link add dev veth-2-3 type veth peer name veth-3-2
echo "  Create veth pair veth-1-3a and veth-3-1a"
ip link add dev veth-1-3a type veth peer name veth-3-1a
echo "  Create veth pair veth-1-3b and veth-3-1b"
ip link add dev veth-1-3b type veth peer name veth-3-1b

echo "  Create netns-1"
ip netns add netns-1
echo "  Move veth-1-2 to netns-1"
ip link set veth-1-2 netns netns-1
echo "  Bring veth-1-2 up"
ip netns exec netns-1 ip link set dev veth-1-2 up
echo "  Assign address 99.1.2.1/24 to veth-1-2"
ip netns exec netns-1 ip addr add 99.1.2.1/24 dev veth-1-2
echo "  Move veth-1-3a to netns-1"
ip link set veth-1-3a netns netns-1
echo "  Bring veth-1-3a up"
ip netns exec netns-1 ip link set dev veth-1-3a up
echo "  Assign address 99.1.3.1/24 to veth-1-3a"
ip netns exec netns-1 ip addr add 99.1.3.1/24 dev veth-1-3a
echo "  Move veth-1-3b to netns-1"
ip link set veth-1-3b netns netns-1
echo "  Bring veth-1-3b up"
ip netns exec netns-1 ip link set dev veth-1-3b up
echo "  Assign address 88.1.3.1/24 to veth-1-3b"
ip netns exec netns-1 ip addr add 88.1.3.1/24 dev veth-1-3b

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

echo "  Create netns-3"
ip netns add netns-3
echo "  Move veth-3-1a to netns-3"
ip link set veth-3-1a netns netns-3
echo "  Bring veth-3-1a up"
ip netns exec netns-3 ip link set dev veth-3-1a up
echo "  Assign address 99.1.3.3/24 to veth-3-1a"
ip netns exec netns-3 ip addr add 99.1.3.3/24 dev veth-3-1a
echo "  Move veth-3-1b to netns-3"
ip link set veth-3-1b netns netns-3
echo "  Bring veth-3-1b up"
ip netns exec netns-3 ip link set dev veth-3-1b up
echo "  Assign address 88.1.3.3/24 to veth-3-1b"
ip netns exec netns-3 ip addr add 88.1.3.3/24 dev veth-3-1b
echo "  Move veth-3-2 to netns-3"
ip link set veth-3-2 netns netns-3
echo "  Bring veth-3-2 up"
ip netns exec netns-3 ip link set dev veth-3-2 up
echo "  Assign address 99.2.3.3/24 to veth-3-2"
ip netns exec netns-3 ip addr add 99.2.3.3/24 dev veth-3-2

echo "TCPDUMP"
echo "  Run tcpdump on each interface"
ip netns exec netns-1 bash -c 'tcpdump -Q in -l -i veth-1-2 udp | sed "s/^/RX veth-1-2: /"' &
ip netns exec netns-1 bash -c 'tcpdump -Q out -l -i veth-1-2 udp | sed "s/^/TX veth-1-2: /"' &
ip netns exec netns-1 bash -c 'tcpdump -Q in -l -i veth-1-3a udp | sed "s/^/RX veth-1-3a: /"' &
ip netns exec netns-1 bash -c 'tcpdump -Q out -l -i veth-1-3a udp | sed "s/^/TX veth-1-3a: /"' &
ip netns exec netns-1 bash -c 'tcpdump -Q in -l -i veth-1-3b udp | sed "s/^/RX veth-1-3b: /"' &
ip netns exec netns-1 bash -c 'tcpdump -Q out -l -i veth-1-3b udp | sed "s/^/TX veth-1-3b: /"' &
ip netns exec netns-2 bash -c 'tcpdump -Q in -l -i veth-2-1 udp | sed "s/^/RX veth-2-1: /"' &
ip netns exec netns-2 bash -c 'tcpdump -Q out -l -i veth-2-1 udp | sed "s/^/TX veth-2-1: /"' &
ip netns exec netns-2 bash -c 'tcpdump -Q in -l -i veth-2-3 udp | sed "s/^/RX veth-2-3: /"' &
ip netns exec netns-2 bash -c 'tcpdump -Q out -l -i veth-2-3 udp | sed "s/^/TX veth-2-3: /"' &
ip netns exec netns-3 bash -c 'tcpdump -Q in -l -i veth-3-1a udp | sed "s/^/RX veth-3-1a: /"' &
ip netns exec netns-3 bash -c 'tcpdump -Q out -l -i veth-3-1a udp | sed "s/^/TX veth-3-1a: /"' &
ip netns exec netns-3 bash -c 'tcpdump -Q in -l -i veth-3-1b udp | sed "s/^/RX veth-3-1b: /"' &
ip netns exec netns-3 bash -c 'tcpdump -Q out -l -i veth-3-1b udp | sed "s/^/TX veth-3-1b: /"' &
ip netns exec netns-3 bash -c 'tcpdump -Q in -l -i veth-3-2 udp | sed "s/^/RX veth-3-2: /"' &
ip netns exec netns-3 bash -c 'tcpdump -Q out -l -i veth-3-2 udp | sed "s/^/TX veth-3-2: /"' &
echo ""

sleep 2

echo "BEACONS"
echo "  Start beacon in netns-1"
ip netns exec netns-1 /host/beacon.py beacon1 veth-1-2 veth-1-3a veth-1-3b &
echo "  Start beacon in netns-2"
ip netns exec netns-2 /host/beacon.py beacon2 veth-2-1 veth-2-3 &
echo "  Start beacon in netns-3"
ip netns exec netns-3 /host/beacon.py beacon3 veth-3-1a veth-3-1b veth-3-2 &

# echo "CLEANUP"
# echo "  Delete veth pair veth-1-2 and veth-2-1"
# ip netns exec netns-1 ip link del veth-1-2
# echo "  Delete veth pair veth-2-3 and veth-3-2"
# ip netns exec netns-2 ip link del veth-2-3
# echo "  Delete veth pair veth-1-3a and veth-3-1a"
# ip netns exec netns-1 ip link del veth-1-3a
# echo "  Delete veth pair veth-1-3b and veth-3-1b"
# ip netns exec netns-1 ip link del veth-1-3a
# echo "  Delete netns-1"
# ip netns del netns-1
# echo "  Delete netns-2"
# ip netns del netns-2
# echo "  Delete netns-3"
# ip netns del netns-3
