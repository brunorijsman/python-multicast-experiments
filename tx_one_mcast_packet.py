# Send a single multicast packet on a interface veth-1-2 which has IP address 99.1.2.2
import socket

INTF_ADDR = "99.1.2.2"
MULTICAST_ADDR = "224.0.0.120"
MULTICAST_PORT = 911
MAX_SIZE = 1024
MESSAGE = "hello"

SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
SOCK.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(INTF_ADDR))
SOCK.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
SOCK.bind((INTF_ADDR, MULTICAST_PORT))
SOCK.connect((MULTICAST_ADDR, MULTICAST_PORT))
print("Send {} from {} to {}".format(MESSAGE, SOCK.getsockname(), SOCK.getpeername()))
SOCK.send(MESSAGE.encode())
