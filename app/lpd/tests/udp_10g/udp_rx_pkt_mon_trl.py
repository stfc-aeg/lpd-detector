# X10G Development code
# UDP Receive with Trailer Recognition
# Rob Halsall 23-11-2011

import sys, socket

#from msvcrt import *

if len(sys.argv) == 3:
	ip   = sys.argv[1]
	port = int(sys.argv[2])
else:
	print "use: python udp_rx_ll_mon_trl.py 192.168.9.2 61650"
	exit(0)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 80388608)

print "Receiving on ",ip,":",port

sock.bind((ip, port))

print"Entering packet receive loop - press 's' to exit....\n"

pkt_count = 0

headings = "%8s %8s %8s %8s %23s   %23s %3s" % ('Pkt No' , 'Length','FNUM','PNUM', 'First 8', 'Last 8', 'MKR')
#print headings

chr =""
pkt_num_nxt = 0

try:
        while chr != "s":
 						#receive packet up to 8K Bytes
 						pkt = sock.recv(9000)
 						pkt_len = len(pkt)
 						pkt_top = pkt_len - 8
						frm_num = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
						pkt_num = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
						frm_sof = (pkt_num & 0x80000000) >> 31
						frm_eof = (pkt_num & 0x40000000) >> 30
						pkt_num = pkt_num & 0x3FFFFFFF
						pkt_num_str = "%08X " % (pkt_num)
						frm_num_str = "%08X " % (frm_num)
 						pkt_str_tmp = "%08i %08i " % (pkt_count, pkt_len)
						pkt_str     = pkt_str_tmp + frm_num_str + pkt_num_str
						if frm_sof == 1:
							print headings
 						#print out first 4 bytes of packet
 						for i in range(8):
 						  pkt_str_tmp = "%02X " % ord(pkt[i+8])
 						  pkt_str =  pkt_str + pkt_str_tmp
 						pkt_str =  pkt_str + '- '
 						#print out last 4 bytes of packet
 						for i in range(8):
							pkt_str_tmp = "%02X " % ord(pkt[i+pkt_top])
							pkt_str =  pkt_str + pkt_str_tmp
						if frm_sof == 1:
							pkt_str = pkt_str + "SOF "
						if frm_eof == 1:
							pkt_str = pkt_str + "EOF\n"
						if pkt_num == pkt_num_nxt:
							#pkt_num_nxt = pkt_num_nxt + 1
							pkt_num_nxt = pkt_num + 1
						else:
							#pkt_num_nxt = pkt_num_nxt + 1
							pkt_num_nxt = pkt_num + 1
							pkt_str = pkt_str + "*"
						print pkt_str
						if frm_eof == 1:
							pkt_count = 0
						else:
							pkt_count = pkt_count + 1
						  #chr = getch()
except:
    print "closing socket after exception"
    sock.close()
#finally:
    
print "closing socket at end"
sock.close()
