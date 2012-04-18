'''
Created on 18 Apr 2012

@author: ckd27546
'''

#FEM 10G UDP Test - Instrument Controls tool box
# top level for fem with asic test module
# updated to use Rob's new libraries for 10g, rdma, llink
# jac 25.10.11
# 03/04/12  jac   cleaned up again

# Import Python standard modules
import serial, time
# Force float division:
#from __future__ import division    # Update: do NOT force float division
#import numarray

# Import Fem modules
from FemClient import FemClient
#from FemApi.FemTransaction import FemTransaction
#from FemApi.FemConfig import FemConfig
#from FemApi.FemAcquireConfig import FemAcquireConfig
#from FemApi.FemTransaction import FemTransaction
#from FemApi.FemConfig import FemConfig
#from FemApi.FemAcquireConfig import FemAcquireConfig
from FemClient.FemClient import  *

import ExcaliburFemTests.defaults as defaults

class LpdFemClient(FemClient):

    #    """ 32 way splitter """
    udp_10g_0     = 0x00000000    #0
    udp_10g_1     = 0x08000000    #1
    data_gen_0    = 0x10000000    #2
    data_chk_0    = 0x18000000    #3
    data_gen_1    = 0x20000000    #4
    data_chk_1    = 0x28000000    #5
    fem_ctrl_0    = 0x30000000    #6
    llink_mon_0   = 0x38000000    #7
    data_mon_1    = 0x40000000    #8
    slow_ctr_2    = 0x48000000    #9
    fast_cmd_0    = 0x50000000    #10
    fast_cmd_1    = 0x58000000    #11
    asic_srx_0    = 0x60000000    #12
    rsvd_13       = 0x68000000    #13
    slow_ctr_0    = 0x70000000    #14
    slow_ctr_1    = 0x78000000    #15
    dma_gen_0    = 0x80000000    #16
    dma_chk_0    = 0x88000000    #17
    dma_gen_1    = 0x90000000    #18
    dma_chk_1    = 0x98000000    #19
    dma_gen_2    = 0xa0000000    #20
    dma_chk_2    = 0xa8000000    #21
    dma_gen_3    = 0xb0000000    #22
    dma_chk_3    = 0xb8000000    #23
    rsvd_24      = 0xc0000000    #24
    rsvd_25      = 0xc8000000    #25
    rsvd_26      = 0xd0000000    #26
    rsvd_27      = 0xd8000000    #27
    rsvd_28      = 0xe0000000    #28
    rsvd_29      = 0xe8000000    #29
    rsvd_30      = 0xf0000000    #30
    rsvd_31      = 0xf8000000    #31
    
    def __init__(self, hostAddr=None, timeout=None):
        
        # Call superclass initialising function   
        try:
#            super(LpdFemClient.self).__init__(((defaults.femHost, defaults.femPort), defaults.femTimeout))
            super(LpdFemClient.self).__init__(hostAddr, timeout)
        except FemClientError as errString:
            print "Error: FEM connection failed:", errString
            sys.exit(1)
    
    def extract_asic_data(self, asic_no, column_no, asic_data):
        # Rob Halsall 12-04-2011
        # Extract Image data from 1 ASIC, 1 time slice
        # extract for specified time slice = column_no  jac
        
        start = asic_no + ((column_no-1) * 128 * 511);
        stop = (asic_no + 128 * 511) + ((column_no-1) * 128 * 511);
        
        #image_data = reshape(asic_data(start:128:stop), 16, 32); # rob's
        # reshape(A, rows, columns) = Turn matrix matrix (rows*columns) sized matrix
        
        # Matlab matrix: matrix = [3 4 5 6 7 8]
        # display all elements:   matrix(1:6)
        # Python List:   List =   [3, 4, 5, 6, 7, 8]
        # display all elements:   List[0:6]
        
        # Copy sub list of asic_data,
        # starting from (including) start until stop =    
        # asic_data[(start-1):stop]
        
        counter = start
        image_data = []
        while counter < stop:
            image_data.append(asic_data[counter-1])
            counter += 128
                            
        return image_data
    
    def clear_ll_monitor(self):
        """ readout a local link monitor block
            Rob Halsall 08-04-2011    """
        base_addr = LpdFemClient.llink_mon_0
        #input monitor registers are offset from base address by 16
        
    #    rdma_write(sCom,base_addr+1,0,'rw','Local Link Monitor Counter Reset')
    #    rdma_write(sCom,base_addr+1,1,'rw','Local Link Monitor Counter Reset')
    #    rdma_write(sCom,base_addr+1,0,'rw','Local Link Monitor Counter Reset')
        print "Local Link Monitor Counter Reset"
        self.rdmaWrite(base_addr+1,0)
        self.rdmaWrite(base_addr+1,1)
        self.rdmaWrite(base_addr+1,0)
        
        return 1
    
    def fem_10g_udp_net_set_up_block0(self, net):
        #set up MAC address for SRC & destination
        base_addr = LpdFemClient.udp_10g_0
        
        reg1 = (net.src_mac & 0x00000000FFFFFFFF)
    
        reg2b = ((net.src_mac & 0x0000FFFF000000) >> 32)
        reg2t = ((net.dst_mac & 0x000000000000FF) << 16)
        reg2 = (reg2b | reg2t)
    
        reg3 = (net.dst_mac >> 16)

        print "# src_mac_lower_32\n"
        self.rdmaWrite(base_addr+0, reg1)
        print "# dst_mac_lower_16 & src_mac_upper_16\n"
        self.rdmaWrite(base_addr+1, reg2)
        print "# dst_mac_upper_32\n"
        self.rdmaWrite(base_addr+2, reg3)
        
        #set up IP address for SRC & destination
        print "Reading IP address for Src & destination..\n"
        reg6b = self.rdmaRead(base_addr+6, 1)
    
        reg6b = (reg6b & 0x0000FF)
        reg6 =  (net.dst_ip << 16)
        reg6 =  (reg6 | reg6b)
    
        reg7 =  (net.dst_ip >> 16)
        reg7 =  (reg7 | (net.src_ip << 16))
        reg8t = self.rdmaRead(base_addr+8, 1)    # 1 = 1 32 bit unsigned integer?
    
        reg8t = (reg8t & 0xFFFF00)
        reg8b =  (net.src_ip >> 16)
        reg8 =  (reg8t | reg8b)
    
        print "Writing to reg6, reg7 & reg8..\n"
        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
    
        self.rdmaRead(base_addr+9, 1)    
        return 1

    def fem_10g_udp_net_set_up_block1(self, net):
        #set up MAC address for SRC & destination
        base_addr = LpdFemClient.udp_10g_1
        
        reg1 = (net.src_mac & 0x00000000FFFFFFFF)
    
        reg2b = ((net.src_mac & 0x0000FFFF000000) >> 32)
        reg2t = ((net.dst_mac & 0x000000000000FF) << 16)
        reg2 = (reg2b | reg2t)
    
        reg3 = (net.dst_mac >> 16)

        print "# src_mac_lower_32\n"
        self.rdmaWrite(base_addr+0, reg1)
        print "# dst_mac_lower_16 & src_mac_upper_16\n"
        self.rdmaWrite(base_addr+1, reg2)
        print "# dst_mac_upper_32\n"
        self.rdmaWrite(base_addr+2, reg3)
        
        #set up IP address for SRC & destination
        print "Reading IP address for Src & destination..\n"
        reg6b = self.rdmaRead(base_addr+6, 1)
    
        reg6b = (reg6b & 0x0000FF)
        reg6 =  (net.dst_ip << 16)
        reg6 =  (reg6 | reg6b)
    
        reg7 =  (net.dst_ip >> 16)
        reg7 =  (reg7 | (net.src_ip << 16))
        reg8t = self.rdmaRead(base_addr+8, 1)    # 1 = 1 32 bit unsigned integer?
    
        reg8t = (reg8t & 0xFFFF00)
        reg8b =  (net.src_ip >> 16)
        reg8 =  (reg8t | reg8b)
    
        print "Writing to reg6, reg7 & reg8..\n"
        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
    
        self.rdmaRead(base_addr+9, 1)    
        return 1
    
    def fem_local_link_mux_setup(self, output_data_source):
        # set up local link mux
        base_addr = LpdFemClient.fem_ctrl_0
    
        reg1 = 0x00000001 | base_addr
    
        if output_data_source == 0:          
            print "local link mux ouput 0\n"
            self.rdmaWrite(reg1, 0x00000000)
        else:
    #        rdma_write(sCom,reg1,0x00000001, 'rw','local link mux output 1');
            print "local link mux output 1\n"
            self.rdmaWrite(reg1, 0x00000001)
        
        return 1
        
    
    def toggle_bits(self, reg_addr, bit_pat):
        """ toggle_bits() """
        address= LpdFemClient.fem_ctrl_0 + reg_addr
        
        bits_off = 0
        bits_on  = bit_pat
        
    #    rdma_write(s,address,bits_off,'rw','')
    #    rdma_write(s,address,bits_on, 'rw','')
    #    rdma_write(s,address,bits_off,'rw','')
        print "target_bits() executing rdmaWrite.."
        self.rdmaWrite(address,bits_off)
        self.rdmaWrite(address,bits_on)
        self.rdmaWrite(address,bits_off)
        
        return 1
    
    
    # Rob Halsall 08-04-2011
    def read_ll_monitor(self):
        """ readout a local link monitor block """
        
        #input monitor registers are offset from base address by 16
        mon_addr = LpdFemClient.llink_mon_0 + 16
        
    #    rdma_read(s,mon_addr+0,'r','frm_last_length')
    #    rdma_read(s,mon_addr+1,'r','frm_max_length')
    #    rdma_read(s,mon_addr+2,'r','frm_min_length')
    #    rdma_read(s,mon_addr+3,'r','frm_number')
    #    rdma_read(s,mon_addr+4,'r','frm_last_cycles')
    #    rdma_read(s,mon_addr+5,'r','frm_max_cycles')
    #    rdma_read(s,mon_addr+6,'r','frm_min_cycles')
    #    total_data = rdma_read(s,mon_addr+7,'r','frm_data_total')
    #    total_cycles = rdma_read(s,mon_addr+8,'r','frm_cycle_total')
    #    rdma_read(s,mon_addr+9,'r','frm_trig_count')
    #    rdma_read(s,mon_addr+15,'r','frm_in_progress')
        
        print "frm_last_length"
        self.rdmaWrite(mon_addr+0)
        print "frm_max_length"
        self.rdmaWrite(mon_addr+1)
        print "frm_min_length"
        self.rdmaWrite(mon_addr+2)
        print "frm_number"
        self.rdmaWrite(mon_addr+3)
        print "frm_last_cycles"
        self.rdmaWrite(mon_addr+4)
        print "frm_max_cycles"
        self.rdmaWrite(mon_addr+5)
        print "frm_min_cycles"
        self.rdmaWrite(mon_addr+6)
        print "frm_data_total"
        total_data = self.rdmaWrite(mon_addr+7)
        print "frm_cycle_total"
        total_cycles = self.rdmaWrite(mon_addr+8)
        print "frm_trig_count"
        self.rdmaWrite(mon_addr+9)
        print "frm_in_progress"
        self.rdmaWrite(mon_addr+15)
           
        # data path = 64 bit, clock = 156.25 MHz
        total_time = total_cycles * (1/156.25e6)
        rate = (total_data/total_time) * 8
        
        print "\nData Total = %e" % total_data
        print "\nData Time = %e" % total_time
        print "\nData Rate = %e" % rate
        
        print "\n\n"
        
        return 1
    
    def ll_frm_gen_setup(self, base_address, length, data_type):
        """ This function sets up the data Generator & resets """
    
        # frm gen - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2
        #rdma_write(s,    base_address+1, reg_length,'rw','DATA GEN Data Length')
        #rdma_write(sCom, address,        data,      type,description)
        print "DATA GEN Data Length\n"
        self.rdmaWrite(base_address+1,reg_length)
    
        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4
    
        #rdma_write(s,        base_address+4, control_reg,'rw','DATA GEN Data Type')
        print "DATA GEN Data Type\n"
        self.rdmaWrite(base_address+4, control_reg)
    
        if data_type == 0:
            data_0 = 0x00000000
            data_1 = 0x00000001
        elif data_type == 1:
            data_0 = 0x03020100
            data_1 = 0x07060504
        elif data_type == 2:
            data_0 = 0x00000000
            data_1 = 0x00000000
        else:
            data_0 = 0xFFFFFFFF
            data_1 = 0xFFFFFFFF
    
        #rdma_write(s,        base_address+5,data_0,'rw','DATA GEN Data Init 0')
        print "DATA GEN Data Init 0"
        self.rdmaWrite(base_address+5,data_0)
        #rdma_write(s,        base_address+6,data_1,'rw','DATA GEN Data Init 1')
        print "DATA GEN Data Init 1"
        self.rdmaWrite(base_address+6,data_1)
    
        # Data Gen soft reset
        #rdma_write(s,        base_address+0,0x00000000,'rw','DATA GEN Internal Reset')
        #rdma_write(s,        base_address+0,0x00000001,'rw','DATA GEN Internal Reset')
        #rdma_write(s,        base_address+0,0x00000000,'rw','DATA GEN Internal Reset')
        print "DATA GEN Internal Reset\n"
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)
    
        return 1
    
    
    def fem_10g_udp_set_up_block0(self, udp_pkt_len, udp_frm_sze, eth_ifg):
    
        base_addr = LpdFemClient.udp_10g_0
        fixed_length = 0
        
        # set up header lengths
        if fixed_length == 1:
            ip_hdr_len   = 28 + udp_pkt_len
            udp_hdr_len  = 8 + udp_pkt_len
            ctrl_reg_val = 0x00000009
            
            udp_hdr_len1 = udp_hdr_len & 0x000000FF
            udp_hdr_len2 = udp_hdr_len & 0x0000FF00
            udp_hdr_len  = (udp_hdr_len1 << 8) + (udp_hdr_len2 >> 8)
        
            ip_hdr_len1 = ip_hdr_len & 0x000000FF
            ip_hdr_len2 = ip_hdr_len & 0x0000FF00
            ip_hdr_len  = (ip_hdr_len1 << 8) + (ip_hdr_len2 >> 8)
        else:
            ip_hdr_len   = 28
            udp_hdr_len  = 8
            ctrl_reg_val = 0x00000001    
        
        #set udp checksum = zero
        ctrl_reg_val = ctrl_reg_val | 0x00000010
        
        #shift udp header length up to the top two bytes
        udp_hdr_len  = (udp_hdr_len << 16)
        
        # set up frame generator size 
        gen_frm_cyc = (udp_frm_sze >> 2)        # Never utilised by Matlab script..
        
        # set 8 x 8 Byte Packets
        data0 = ((udp_pkt_len/8)-2)
        print "UDP Block Packet Size\n"
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len
        print "UDP Block IP Header Length\n"
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        print "UDP Block UDP Length\n"
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # enable & set IFG
        print "UDP Block IFG\n"
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)
        
        return 1
    
    def fem_10g_udp_set_up_block1(self, udp_pkt_len, udp_frm_sze, eth_ifg):
    
        base_addr = LpdFemClient.udp_10g_1
        fixed_length = 0
        
        # set up header lengths
        if fixed_length == 1:
            ip_hdr_len   = 28 + udp_pkt_len
            udp_hdr_len  = 8 + udp_pkt_len
            ctrl_reg_val = 0x00000009
            
            udp_hdr_len1 = udp_hdr_len & 0x000000FF
            udp_hdr_len2 = udp_hdr_len & 0x0000FF00
            udp_hdr_len  = (udp_hdr_len1 << 8) + (udp_hdr_len2 >> 8)
        
            ip_hdr_len1 = ip_hdr_len & 0x000000FF
            ip_hdr_len2 = ip_hdr_len & 0x0000FF00
            ip_hdr_len  = (ip_hdr_len1 << 8) + (ip_hdr_len2 >> 8)
        else:
            ip_hdr_len   = 28
            udp_hdr_len  = 8
            ctrl_reg_val = 0x00000001    
        
        #set udp checksum = zero
        ctrl_reg_val = ctrl_reg_val | 0x00000010
        
        #shift udp header length up to the top two bytes
        udp_hdr_len  = (udp_hdr_len << 16)
        
        # set up frame generator size 
        gen_frm_cyc = (udp_frm_sze >> 2)        # Never utilised by Matlab script..
        
        # set 8 x 8 Byte Packets
        data0 = ((udp_pkt_len/8)-2)
        print "UDP Block Packet Size\n"
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len
        print "UDP Block IP Header Length\n"
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        print "UDP Block UDP Length\n"
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # enable & set IFG
        print "UDP Block IFG\n"
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)
        
        return 1   

    
    #def hex2dec(n): ''' Redundant! '''
    #    """ returned the hexadecimal string representation of integer n """
    #    try:
    #        int(n)
    #    except ValueError:
    #        print "hex2dec() error: 0x MUST prefix argument!"
    #        return
    #    else:
    #        return "%X" % n

    

if __name__ == "__main__":
    # Execute actual program
#    app = QtGui.QApplication(sys.argv)
    client = LpdFemClient()
#    sys.exit(app.exec_())


    