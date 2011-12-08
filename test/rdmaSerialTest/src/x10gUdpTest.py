'''
Created on Aug 12, 2011

@author: tcn45
'''
import socket
import threading
from time import sleep, time

from RdmaSerial import * 

class RxThread(threading.Thread):
    
    def run(self):

        print "RxThread opening socket"
        
        # Open socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Set socket rcv buffer - assumes system level max buffer is set appropriately
        # e.g. by sudo /sbin/sysctl -w net.core.rmem_max=8388608 
        # Default values of this (net.core.rmem_max = 131072) cause significant
        # packet loss
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8388608)
        
        # Set socket timeout so thread can loop cleanly
        sock.settimeout(1)

        # Bind socket to address and port        
        sock.bind(('10.0.2.2', 61649))

        # Set up local variables
        self.running = 1
        self.verbose = 0
                
        pkt_count = 0
        pkt_total = 0
        first = 1
        start_time = 0.0
        last_time = 0.0

        # Enter loop while running flag is set        
        while self.running == 1:

            try:
                pkt = sock.recv(8192)
                if first == 1:
                    start_time = time()
                    first = 0
                last_time = time()
                pkt_len = len(pkt)
                pkt_top= pkt_len - 4
                if self.verbose:
                    pkt_str = "PACKET RX: %08i %08i " % (pkt_count, pkt_len)
                    #print out first 4 bytes of packet
                    for i in range(4):
                        pkt_str_tmp = "%02X " % ord(pkt[i])
                        pkt_str =  pkt_str + pkt_str_tmp
                    pkt_str =  pkt_str + '- '
                    #print out last 4 bytes of packet
                    for i in range(4):
                        pkt_str_tmp = "%02X " % ord(pkt[i+pkt_top])
                        pkt_str =  pkt_str + pkt_str_tmp
                    print pkt_str
                pkt_count = pkt_count + 1
                pkt_total = pkt_total + pkt_len
            except socket.timeout:
                pass
            except:
                sock.close()
                self.running = 0
                    
        sock.close()
        deltaT = last_time - start_time
        rate = pkt_total / deltaT
        print "*** Received %d packets, total data %d bytes in %e secs, rate = %e bytes/sec" % (pkt_count, pkt_total, deltaT, rate )
        
# Create UDP receive thread
rxThread = RxThread()
rxThread.start()

x10g_rdma = RdmaSerial('/dev/ttyUSB0', 115200, 1)

x10g_rdma.setDebug(True);

# Set up UDP IP block 0
print "Set up UDP block 0"
x10g_rdma.write(0x00000000, 0x00000062, 'UDP Block 0 MAC Source Lower 32')
x10g_rdma.write(0x00000001, 0x07001000, 'UDP Block 0 MAC Source Upper 16/Dest Lower 16')
x10g_rdma.write(0x00000002, 0x205F1043, 'UDP Block 0 MAC Dest Upper 32')
x10g_rdma.write(0x00000006, 0x000A77B8, 'UPB Block 0 IP Dest Addr / Checksum')
x10g_rdma.write(0x00000007, 0x000A0202, 'UPB Block 0 IP Dest Addr / Srd Addr')
x10g_rdma.write(0x00000008, 0x08000102, 'UPB Block 0 IP Src Addr / Port')
x10g_rdma.write(0x0000000C, 0x000003E6, 'UDP Block 0 Packet Size')    
x10g_rdma.write(0x00000004, 0xDB00001C, 'UDP Block 0 IP Header Length')
x10g_rdma.write(0x00000009, 0x0008D1F0, 'UDP Block 0 UDP Length')
x10g_rdma.write(0x0000000F, 0x00000001, 'UDP Block 0 IFG')
x10g_rdma.write(0x0000000D, 0x00000008, 'UDP Block 0 IFG')
print ""

# Set up UDP IP block 1
print "Set up UDP block 1"
x10g_rdma.write(0x10000000, 0x00000062, 'UDP Block 1 MAC Source Lower 32')
x10g_rdma.write(0x10000001, 0x07001000, 'UDP Block 1 MAC Source Upper 16/Dest Lower 16')
x10g_rdma.write(0x10000002, 0x205F1043, 'UDP Block 1 MAC Dest Upper 32')
x10g_rdma.write(0x10000006, 0x000A77B8, 'UPB Block 1 IP Dest Addr / Checksum')
x10g_rdma.write(0x10000007, 0x000A0202, 'UPB Block 1 IP Dest Addr / Srd Addr')
x10g_rdma.write(0x10000008, 0x08000102, 'UPB Block 1 IP Src Addr / Port')
x10g_rdma.write(0x1000000C, 0x000003E6, 'UDP Block 1 Packet Size')    
x10g_rdma.write(0x10000004, 0xDB00001C, 'UDP Block 1 IP Header Length')
x10g_rdma.write(0x10000009, 0x0008D1F0, 'UDP Block 1 UDP Length')
x10g_rdma.write(0x1000000F, 0x00000001, 'UDP Block 1 IFG')
x10g_rdma.write(0x1000000D, 0x00000008, 'UDP Block 1 IFG')
print""

# Set up LocalLink frame generator 0
print "Set up LocalLink frame generator 0"
x10g_rdma.write(0x20000001, 0x001FFFFE, 'DATA GEN 0 Data Length')
#x10g_rdma.write(0x20000001, 0x00000FFE, 'DATA GEN 0 Data Length')
x10g_rdma.write(0x20000000, 0x00000001, 'DATA GEN 0 Data Type')
print ""

# Set up LocalLink frame generator 1
print "Set up LocalLink frame generator 1"
x10g_rdma.write(0x40000001, 0x001FFFFE, 'DATA GEN 0 Data Length')
#x10g_rdma.write(0x40000001, 0x00000FFE, 'DATA GEN 0 Data Length')
x10g_rdma.write(0x40000000, 0x00000001, 'DATA GEN 0 Data Type')
print ""

# Clear local link monitor
print "Clear LocalLink monitor"
x10g_rdma.write(0xD0000001, 0x00000000, 'Local Link Monitor Reset')
x10g_rdma.write(0xD0000001, 0x00000001, 'Local Link Monitor Reset')
x10g_rdma.write(0xD0000001, 0x00000000, 'Local Link Monitor Reset')
print ""

# Read local link monitor
print "Read LocalLink Monitor"
x10g_rdma.read(0xD0000010, 'frm_last_length')
x10g_rdma.read(0xD0000011, 'frm_max_length')
x10g_rdma.read(0xD0000012, 'frm_min_length')
x10g_rdma.read(0xD0000013, 'frm_number')
x10g_rdma.read(0xF0000014, 'frm_last_cycles')
x10g_rdma.read(0xD0000015, 'frm_max_cycles')
x10g_rdma.read(0xD0000016, 'frm_min_cycles')
total_data   = x10g_rdma.read(0xD0000017, 'frm_data_total')
total_cycles = x10g_rdma.read(0xD0000018, 'frm_cycle_total')
x10g_rdma.read(0xD0000019, 'frm_trig_count')
x10g_rdma.read(0xD000001F, 'frm_in_progress')
print ""

total_time = float(total_cycles) * (1.0 / 300E6)
try:
    rate       = (float(total_data) / total_time) * 4.0
except:
    rate = 0.0
    
print "Data total = %e" % (float(total_data) * 4)
print "Data time  = %e" % total_time
print "Data rate  = %e" % rate
print ""

# Trigger data generator
print "Triggering data generator"
x10g_rdma.write(0x60000000, 0x00000000, "Trigger data generator")
x10g_rdma.write(0x60000000, 0x00000001, "Trigger data generator")
x10g_rdma.write(0x60000000, 0x00000000, "Trigger data generator")
print ""

# Allow RX thread to run then shut it down
sleep(10.0)
rxThread.running = 0
sleep(1.0)

# Read local link monitor
print ""
print "Read LocalLink Monitor"
x10g_rdma.read(0xD0000010, 'frm_last_length')
x10g_rdma.read(0xD0000011, 'frm_max_length')
x10g_rdma.read(0xD0000012, 'frm_min_length')
x10g_rdma.read(0xD0000013, 'frm_number')
x10g_rdma.read(0xF0000014, 'frm_last_cycles')
x10g_rdma.read(0xD0000015, 'frm_max_cycles')
x10g_rdma.read(0xD0000016, 'frm_min_cycles')
total_data   = x10g_rdma.read(0xD0000017, 'frm_data_total')
total_cycles = x10g_rdma.read(0xD0000018, 'frm_cycle_total')
x10g_rdma.read(0xD0000019, 'frm_trig_count')
x10g_rdma.read(0xD000001F, 'frm_in_progress')
print ""

total_time = float(total_cycles) * (1.0 / 300E6)
try:
    rate       = (float(total_data) / total_time) * 4.0
except:
    rate = 0.0
    
print "Data total = %e" % (float(total_data) * 4)
print "Data time  = %e" % total_time
print "Data rate  = %e" % rate
print ""
