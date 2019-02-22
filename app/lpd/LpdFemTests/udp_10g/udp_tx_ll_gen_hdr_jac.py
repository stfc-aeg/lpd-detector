#Generates pseudo local link frames using udp packet protocol in header mode
#Does not include padding or partial packets
#Rob Halsall - 04-07-2012
#John Coughlan - 07-09-2012  - reduce packet size
import sys, socket

if len(sys.argv) == 6:
	ip   = sys.argv[1]
	port = int(sys.argv[2])
	len_frm  = int(sys.argv[3])
	num_frm = int(sys.argv[4])
	len_pkt = int(sys.argv[5])
else:
	print "use: python udp_tx_ll_test_hdr.py ip port frm_len frm_num pkt_len"
	exit(0)

print "sending to: ", ip, port

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('192.168.2.1', 61649))

data=""
i=0
j=0
while i != 16: #  64:
	if j>252:
		j=0
	else:
		data = data+chr(j)+chr(j+1)+chr(j+2)+chr(j+3)
		#print i,j, len(data)
		j=j+4
	i=i+1

num_pkt = len_frm/len_pkt

print num_pkt

for frm_num in range(num_frm):
	frm_0 = (frm_num >>  0) & 0xFF
	frm_1 = (frm_num >>  8) & 0xFF
	frm_2 = (frm_num >> 16) & 0xFF
	frm_3 = (frm_num >> 24) & 0xFF
	frm_hdr = chr(frm_0)+chr(frm_1)+chr(frm_2)+chr(frm_3)
	for pkt_num in range(num_pkt):
		if pkt_num == 0:
			flg_hdr = chr(0x80)
		else:
			flg_hdr = chr(0x00)
		if pkt_num == num_pkt-1:
			flg_hdr = chr(0x40 | ord(flg_hdr))
 
		pkt_0 = (pkt_num >>  0) & 0xFF
		pkt_1 = (pkt_num >>  8) & 0xFF
		pkt_2 = (pkt_num >> 16) & 0xFF
		pkt_3 = (pkt_num >> 24) & 0xFF
		pkt_hdr = chr(pkt_0)+chr(pkt_1)+chr(pkt_2)
		header = frm_hdr + pkt_hdr + flg_hdr
		pkt = header + data
		print len(pkt)
		sock.sendto(pkt, (ip, port))

sock.close()
