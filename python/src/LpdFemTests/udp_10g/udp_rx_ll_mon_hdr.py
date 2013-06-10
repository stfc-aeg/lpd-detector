# X10G Development code
# UDP Receive with Header Recognition
# Rob Halsall 22-06-2012

import sys, socket

#from msvcrt import *

if len(sys.argv) == 3:
	ip   = sys.argv[1]
	port = int(sys.argv[2])
else:
	print "use: python udp_rx_ll_mon_hdr.py 192.168.9.2 61650"
	exit(0)
 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 80388608)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, (8*1024+8)*1024*128)

print "Receiving on ",ip,":",port

sock.bind((ip, port))

print"Entering packet receive loop - press 's' to exit....\n"

pkt_count = 0
frame_count = 0
pkt_num_err = 0
frame_length = 0

pkt_size_min = 9000
pkt_size_max = 0

headings = "%8s %8s %8s %8s %8s" % ('Frame No' ,'FNUM','PNUM', 'Length', 'Errors')
print headings

chr =""
pkt_num_nxt = 0

try:
        while chr != "s":
 						#receive packet up to 8K Bytes
 						pkt = sock.recv(9000)
 						pkt_len = len(pkt)
 						frame_length = frame_length + pkt_len
 						pkt_top = 0
						frm_num = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
						pkt_num = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
						frm_sof = (pkt_num & 0x80000000) >> 31
						frm_eof = (pkt_num & 0x40000000) >> 30
						pkt_num = pkt_num & 0x3FFFFFFF		 
						if pkt_num == pkt_num_nxt:
							pkt_num_nxt = pkt_num + 1
						else:
							pkt_num_nxt = pkt_num + 1
							pkt_num_err = pkt_num_err + 1
						if frm_eof == 1:
 							pkt_str_tmp = "%08X %08X %08X %08X %08X" % (frame_count, frm_num, pkt_num, frame_length, pkt_num_err)
							pkt_str     = pkt_str_tmp
							print pkt_str
							pkt_count = 0
							pkt_num_nxt = 0
							pkt_num_err = 0
							frame_length = 0
							pkt_size_min = 9000
							pkt_size_max = 0
							frame_count = frame_count + 1
						else:
							pkt_count = pkt_count + 1
except:
    print "closing socket after exception"
    sock.close()
#finally:
    
print "closing socket at end"
sock.close()
