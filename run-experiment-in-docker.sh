#!/bin/bash

# Setup the following network namespaces (netns) and virtual ethernet (veth) interface pairs:
#
#    ...............    ............................    ...............
#    . netns-1     .    . netns-2                  .    . netns-3     .
#    .             .    .                          .    .             .
#    . veth-1-1    .    . veth-2-1        veth-2-2 .    . veth-3-1    .
#    .    X------------------X             X-----------------X        .
#    . 99.1.2.1/24 .    . 99.1.2.2/24  99.2.3.2/24 .    . 99.2.3.3/24 .
#    ...............    ............................    ...............

ip link add dev veth-1-1 type veth peer name veth-2-1
ip link add dev veth-2-2 type veth peer name veth-3-1

ip netns add netns-1
ip link set veth-1-1 netns netns-1
ip netns exec netns-1 ip link set dev veth-1-1 up
ip netns exec netns-1 ip addr add 99.1.2.1/24 dev veth-1-1

ip netns add netns-2
ip link set veth-2-1 netns netns-2
ip link set veth-2-2 netns netns-2
ip netns exec netns-2 ip link set dev veth-2-1 up
ip netns exec netns-2 ip addr add 99.1.2.2/24 dev veth-2-1
ip netns exec netns-2 ip link set dev veth-2-2 up
ip netns exec netns-2 ip addr add 99.2.3.2/24 dev veth-2-2

ip netns add netns-3
ip link set veth-3-1 netns netns-3
ip netns exec netns-3 ip link set dev veth-3-1 up
ip netns exec netns-3 ip addr add 99.2.3.3/24 dev veth-3-1

ip netns exec netns-1 python3 /host/experiment_netns1.py &
ip netns exec netns-2 python3 /host/experiment_netns2.py &
ip netns exec netns-2 python3 /host/experiment_netns3.py &

sleep 10
