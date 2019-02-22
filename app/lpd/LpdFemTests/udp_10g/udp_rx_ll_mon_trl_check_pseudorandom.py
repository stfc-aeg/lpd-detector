# X10G Development code
# UDP Receive with Trailer Recognition
# Rob Halsall 23-11-2011
# added printout of payload  jac
# checking asic pseudorandom values jac

import sys, socket
import pprint

#from msvcrt import *


if len(sys.argv) == 3:
  ip   = sys.argv[1]
  port = int(sys.argv[2])
else:
  print "use: python udp_rx_ll_mon_trl.py 192.168.9.2 61650"
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

nr_asics = 128
nr_pix = 512
nr_samples_per_image = nr_asics * nr_pix

headings = "%8s %8s %8s %8s %8s" % ('Frame No' ,'FNUM','PNUM', 'Length', 'Errors')
#print headings

chr =""
pkt_num_nxt = 0

loop = 0
sample = 0	# 16 bit value from asic

samples_checked = 0

# enabled asics to check :  mask order 0,1,2,3 ; mask 0 = (lsb) 1-32 (msb) ; mask 1 = 33-64 ; mask 3 = 65-96 ; mask 4 = 97-128
asic_enable = [ 0xff000000, 0x000000, 0x000000, 0x000000 ]	# 2-tile with LHS sensor only 

# pseudo random number output.  
#psrandom_out0 = 0x967   # First value is not repeated.
# Remaining values repeat every 32 values.
psrandom_out = [0x967, 0xC6E, 0xA12, 0xCF8, 0xDD4, 0x259, 0xF1B, 0xA84, 0xB3E, 0x375, 0x96, 0x7C6, 0xEA1, 0x2CF, 0x8DD, 0x425, 0x9F1, 0xBA8, 0x4B3, 0xE37, 0x509, 0x67C, 0x6EA, 0x12C, 0xF8D, 0xD42, 0x59F, 0x1BA, 0x84B, 0x3E3, 0x750]
nr_pseudorandom_values = len(psrandom_out)

gain = 100

udp_pkt_num = 0

nprint_err_max = 64
nprint_ok_max = 16

nok = 0
nerr = 0

trailer_len = 8


print "====================================================================="            

#print 'nr_pseudorandom_values = %3d ' %(nr_pseudorandom_values)

try:
        while chr != "s":
            #receive packet up to 8K Bytes  (may be less!)
            pkt = sock.recv(8192)
            udp_pkt_num += 1
            udp_pkt_len = len(pkt)
            #print 'pkt nr = %3d ; pkt length = %6d bytes' %(udp_pkt_num, udp_pkt_len)

# 64 bit
#            if loop < 1:
#              for i in range(0, 4*256, 4):
#                  data = (ord(pkt[i+3]) << 24) + (ord(pkt[i+2]) << 16) + (ord(pkt[i+1]) << 8) + ord(pkt[i+0])
#                  print 'byte nr = %3d data = $%08X ' %(i, data)
#              loop+=1

# 32 bit
#            if loop < 1:
#              for i in range(0, 2*256, 2):
#                  data =(ord(pkt[i+1]) << 8) + ord(pkt[i+0])
#                  print 'byte nr = %3d data = $%04X ' %(i, data)
#              loop+=1

# compare readout with expected pseudo random values
# all 128 (enabled) asics should have same value for each pixel
# pseudo random value sequence is dependent on gain selection   

#            if udp_pkt_num < 2:
            if 1:
              for i in range(0, udp_pkt_len - trailer_len, 2):  # loop over bytes in this udp packet, careful to ignore the trailer          
#              for i in range(0, 800, 2): # loop over bytes in this udp packet
                sample = sample + 1
                data = (0xfff & ((ord(pkt[i+1]) << 8) + ord(pkt[i+0]))) 
                asic_nr = (sample-1) % nr_asics + 1
                pix_nr = ((sample-1) / nr_asics ) % nr_pix + 1 
                image_nr = (sample-1) / nr_samples_per_image + 1
                
#                if (image_nr == 1 and pix_nr == 1): # 1st value doesn't repeat
#                  expected = psrandom_out0
#                else:                    
#                  expected = psrandom_out[(3*pix_nr-4) % (nr_pseudorandom_values)]

# if all 32 values are in fact repeated 
                expected = psrandom_out[3*((((image_nr-1)*nr_pix + pix_nr)-1)) % (nr_pseudorandom_values)]

                # only check asic chans expecting data
                if ((asic_enable[(asic_nr-1)/32] & (1 << ((asic_nr-1)%32))) != 0) :
#                if 1:
#                  if i < 400:
                    samples_checked += 1
                    if (data != expected):
                      nerr += 1
                      if (nerr < nprint_err_max):
                        print '**ERROR: i = %5d ; sample = %5d ; image nr = %3d ; pix nr = %3d ; asic nr = %3d data = $%04X, expected = $%04X' %(i, sample, image_nr, pix_nr, asic_nr, data, expected)
                    else:
                      nok += 1
                      if (nok < nprint_ok_max):
                        print '     OK: i = %5d ; sample = %5d ; image nr = %3d ; pix nr = %3d ; asic nr = %3d data = $%04X, expected = $%04X' %(i, sample, image_nr, pix_nr, asic_nr, data, expected)
                                                                 


#=================
            if (udp_pkt_num == 1):
              print headings

            pkt_len = len(pkt)
            frame_length = frame_length + pkt_len
            pkt_top = pkt_len - 8
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

    print '================= End ==============================================' 
    print 'Summary : Total nr of samples = %6d (%6d ($%08x) bytes ); Total nr inspected = %6d ; Total nr of errors = %6d' %(sample, sample*2, sample*2, samples_checked, nerr)


#    pp = pprint.PrettyPrinter(indent=4)
#        pp.pprint(pkt)

#    for i in range(0, 10):
#        data = ord(pkt[i])
#        print 'reg %2d = $%08X ' %(i, data)
    
print "closing socket at end"
sock.close()
