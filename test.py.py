from thread import *


def handle(a,b,c):
	print a,b,c

# import socket 
# print socket.getfqdn()

import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

# print get_ip_address('eth0')  # '192.168.0.110'

import ipgetter
print ipgetter.myip()

start_new_thread(handle ,("A","B","C"));

while True:
	a = 1