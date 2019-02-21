import os, sys, time, socket, struct

mcast_group = "239.255.16.16"
mcast_port = 10150
mcast_interface = "172.21.25.200"

mcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mcast_socket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
                 socket.inet_aton(mcast_group)+socket.inet_aton(mcast_interface))

mcast_socket.settimeout(1.0)
mcast_socket.bind((mcast_group, mcast_port))

print("EVR timestamp receiver thread listening on MCAST group {} port {} interface {}".format(
    mcast_group, mcast_port, mcast_interface
)) 

evrDatagramHdrFormat = '7I'
evrDatagramHdrSize = struct.calcsize(evrDatagramHdrFormat)

while True:

    try:
        data, address = mcast_socket.recvfrom(1024)
        print len(data), address

        cmdLen = len(data) - evrDatagramHdrSize
        dgFormat = evrDatagramHdrFormat + '%dB' % cmdLen
        unpackedDg = struct.unpack(dgFormat, data)
        (nsecs, secs, low, high, env, evr, ncmds) = unpackedDg[0:7]
        fiducial = high & 0x1ffff
        timestamp = float(secs) + (float(nsecs) / 1.0E9)
        is_event  = True if ((low >> 24)&0xF) == 0xC else False
        is_eventStr = '*' if is_event else ' '
        print '{} {} {:06d}  {:06d}  {:09d}.{:09d}  {:.09f}   {:s}'.format(address, len(data), evr, fiducial, secs, nsecs, timestamp, is_eventStr)
    except socket.timeout:
        print(".")
