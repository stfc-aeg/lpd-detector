'''
Created on 2 July 2012

@author: john coughlan
'''

# Train Builder client.
# Based on FEM client.
# 02/07/12  jac   

# Import Python standard modules
from string import strip, split
import time

# Import Fem modules
#from FemClient import FemClient, FemClientError
#from FemApi.FemTransaction import FemTransaction
#from FemApi.FemConfig import FemConfig
#from FemApi.FemAcquireConfig import FemAcquireConfig
#from FemApi.FemTransaction import FemTransaction
#from FemApi.FemConfig import FemConfig
#from FemApi.FemAcquireConfig import FemAcquireConfig
from FemClient.FemClient import  *

class TBClientv2(FemClient):

# as rs232 splitter is not used yet
# gpio controller mux is used to switch between FPGAs. Master or F1 to F4
# each FPGA F1 to F4 has 2 Xaui 10G channels

    #    """ F1_F4 addresses """
    udp_10g_0     = 0x00000000    #0
    udp_10g_1     = 0x01000000    #1
    data_gen_0    = 0x02000000    #2
    data_chk_0    = 0x03000000    #3
    data_gen_1    = 0x04000000    #4
    data_chk_1    = 0x05000000    #5
    f1_f4_ctrl    = 0x06000000    #6
    llink_mon_0   = 0x07000000    #7
    data_mon_0    = 0x08000000    #8
    llink_mon_1    = 0x09000000    #9  
    data_mon_1    = 0x0a000000    #10
    rsvd_2    = 0x0b000000    #11
    rsvd_3    = 0x0c000000    #12
    rsvd_4    = 0x0d000000    #13
    rsvd_5    = 0x0e000000    #14
    rsvd_6    = 0x0f000000    #15
    
    def __init__(self, hostAddr=None, timeout=None):
        
        # Call superclass initialising function   
        super(TBClient, self).__init__(hostAddr, timeout)
            
    
    def setup_10g_udp_net_block(self, base_addr, net):
        #set up MAC address for SRC & destination
 
        reg1 = (net['fpga_mac'] & 0x00000000FFFFFFFF)
    
        reg2b = ((net['fpga_mac'] & 0x0000FFFF00000000) >> 32)
        reg2t = ((net['nic_mac'] & 0x000000000000FFFF) << 16)
        reg2 = (reg2b | reg2t)
    
        reg3 = (net['nic_mac'] >> 16)

        #print "# fpga_mac_lower_32"
        self.rdmaWrite(base_addr+0, reg1)
        #print "# nic_mac_lower_16 & fpga_mac_upper_16"
        self.rdmaWrite(base_addr+1, reg2)
        #print "# nic_mac_upper_32"
        self.rdmaWrite(base_addr+2, reg3)
        
        #set up IP address for SRC & destination
        #print "Reading IP address for Src & destination.."
        reg6b = self.rdmaRead(base_addr+6, 1)[1]
#        reg6b = 0xA1B2C3D4
        reg6b = (reg6b & 0x0000FFFF)
        reg6 =  ( (net['nic_ip'] << 16)  & 0xFFFFFFFF )
        reg6 =  (reg6 | reg6b)
    
        reg7 =  (net['nic_ip'] >> 16)
        reg7 = ( (reg7 | (net['fpga_ip'] << 16)) & 0xFFFFFFFF )
        
        reg8t = self.rdmaRead(base_addr+8, 1)[1]    # 1 = one 32 bit unsigned integer
#        reg8t = 0x9F8E7D6C
        reg8t = (reg8t & 0xFFFF0000)
        reg8b =  (net['fpga_ip'] >> 16)
        reg8 =  (reg8t | reg8b)

#        print hex(reg6), "\n", hex(reg7), "\n", hex(reg8)        
        #print "Writing to reg6, reg7 & reg8.."
        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
    
        self.rdmaRead(base_addr+9, 1)    

    def setup_10g_udp_block(self, base_addr, udp_pkt_len, udp_frm_sze, eth_ifg):
    
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
        #print "TB UDP Block Packet Size"
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len      
        #print "UDP Block IP Header Length"
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        #print "UDP Block UDP Length"
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # enable & set IFG
        #print "UDP Block IFG"
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)
        
    
    def setup_10g_packet_header(self, base_addr, packet_hdr):
       
        #print "robs udp packet header 10g"
        self.rdmaWrite(base_addr + 11, packet_hdr)

        
    def setup_ll_mux(self, output_data_source):
        # select between data gen and ppc ll data sources
    
        #print "local link mux ouput"
        self.rdmaWrite(TBClient.f1_f4_ctrl+14, 0x00000000)
                
        return 1
        
    
    def toggle_bits(self, reg_addr, bit_pat):
        """ toggle_bits() """
        address= TBClient.f1_f4_ctrl + reg_addr
        
        bits_off = 0
        bits_on  = bit_pat
        
        #print "target_bits() executing rdmaWrite.."
        self.rdmaWrite(address,bits_off)
        self.rdmaWrite(address,bits_on)
        self.rdmaWrite(address,bits_off)
        
        return 1
    
    
    
    def setup_ll_frm_gen(self, base_address, length, data_type, num_ll_frames, hdr_trl_mode):
        """ This function sets up the data Generator & resets """
        
        # frm gen - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2
        #print "DATA GEN Data Length"
        self.rdmaWrite(base_address+1,reg_length)
        
        #print "DATA GEN Nr Frames"
        self.rdmaWrite(base_address+2, num_ll_frames)

        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4

        #turn header/trailer mode on if required
        if hdr_trl_mode == 1:
            control_reg = control_reg | 0x00000001
        else:
            control_reg = control_reg & 0xFFFFFFFE 
        
        #print "DATA GEN Data Type"
        self.rdmaWrite(base_address+4, control_reg)
        
        #print "control reg = $", hex(control_reg)
    
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
    
        #print "DATA GEN Data Init 0"
        self.rdmaWrite(base_address+5,data_0)

        #print "DATA GEN Data Init 1"
        self.rdmaWrite(base_address+6,data_1)
    
        # Data Gen soft reset
        #print "DATA GEN Internal Reset"
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)
    
        
    def clear_ll_monitor(self, base_addr):
        """ clear local link monitor block
             """
        
        #print "Local Link Monitor Counter Reset"
        self.rdmaWrite(base_addr+1,0)
        self.rdmaWrite(base_addr+1,1)
        self.rdmaWrite(base_addr+1,0)
        
        return 1
    
    # Rob Halsall 08-04-2011
    def read_ll_monitor(self, base_addr):
        """ readout a local link monitor block """
        
        mon_addr = base_addr + 16

        print "frm_last_length:\t",         self.rdmaRead(mon_addr+0, 1)[1]
        print "frm_max_length: \t",         self.rdmaRead(mon_addr+1, 1)[1]
        print "frm_min_length: \t",         self.rdmaRead(mon_addr+2, 1)[1]
        print "frm_number:\t\t",            self.rdmaRead(mon_addr+3, 1)[1]
        print "frm_last_cycles:\t",         self.rdmaRead(mon_addr+4, 1)[1]
        print "frm_max_cycles: \t",         self.rdmaRead(mon_addr+5, 1)[1]
        print "frm_min_cycles: \t",         self.rdmaRead(mon_addr+6, 1)[1] 
        total_data = self.rdmaRead(mon_addr+7, 1)[1]
        print "frm_data_total: \t", total_data         
        total_cycles = self.rdmaRead(mon_addr+8, 1)[1]
        print "frm_cycle_total:\t", total_cycles
        print "frm_trig_count: \t",         self.rdmaRead(mon_addr+9, 1)[1]
        print "frm_in_progress:\t",         self.rdmaRead(mon_addr+15, 1)[1]
        
        # data path = 64 bit, clock = 156.25 MHz
        total_time = float(total_cycles) * (1/156.25e6)
        if (total_time):
            rate = (total_data/total_time) * 8
        else:
            rate = 0
            
        print "Data Total = %e" % total_data
        print "Data Time = %e" % total_time
        print "Data Rate = %e" % rate
        
        print ""
        
        return 1       

    def dump_regs_hex(self, base_addr, nr_regs):
        """ hex dump of regs """
        
        print "" 
        print 'rdma base addr = $%08X' %base_addr 
        for i in range(0, nr_regs):
        #    print "reg ", i, hex(self.rdmaRead(base_addr+i, 1)[1])
            print 'reg %2d = $%08X ' %(i, self.rdmaRead(base_addr+i, 1)[1])
            
        print ""  
        
        return 1  

# farm mode
        
    def x10g_net_lut_setup(self, base_addr, net, myTBTest, mac_lut):
        """ Set up the LUTs for 10G Farm Mode  """
        
        i = 0;
        
        for nic in net['nic_list']:
            i = i+1;
            new_nic = nic.split('@')
            nic_port = new_nic[0]
            #print "port ", port
            nic_host = new_nic[1]       
            print "host ", nic_host
            nic_mac = mac_lut[nic_host]              
            print "mac ", nic_mac 
            
            mac = myTBTest.mac_addr_to_uint64(nic_mac)
            mac_low = ((mac &  0xFFFFFFFF0000) >> 16)
            mac_high = ((mac & 0x00000000FFFF) << 16)
            
            ip = myTBTest.ip_addr_to_uint32(nic_host)
            port = int(nic_port)
 
            mac_low = self.swap_endian(mac_low)
            mac_high = self.swap_endian(mac_high)
            ip = self.swap_endian(ip)  

            self.rdmaWrite(base_addr + 0x00010200 + 2*i, mac_low)    # mac lower 32 bits 
            self.rdmaWrite(base_addr + 0x00010200 + 2*i + 1, mac_high)    # mac upper 16 bits 
            self.rdmaWrite(base_addr + 0x00010100 + i, ip)    # ip 32 bits
 
            num_ports = net['num_prts']  
        
            if num_ports == -1:
                self.rdmaWrite(base_addr + 0x00010000 + i, port)    # port 16 bits     
            else:           
                self.rdmaWrite(base_addr + 0x00010000 + i, port + i%num_ports)    # port 16 bits  
                     
        # Example
        # '00-07-43-11-97-90'
        # 192.168.2.1
        # should be like...
        # ip = 0xC0A80201
        # mac_low = 0x43119790
        # mac_high = 0x00000007       
        # port = 61649
       
        # mac_low = self.swap_endian(mac_low)
        # mac_high = self.swap_endian(mac_high)
        # ip = self.swap_endian(ip)  

        # num_ports = net['num_prts']  
        # num_frames = net['num_frames']
        
        # for i in range (0, 256):
# #        for i in range (0, num_frames):   # only set up for max nr of frames in a cycle
            # self.rdmaWrite(base_addr + 0x00010200 + 2*i, mac_low)    # mac lower 32 bits 
            # self.rdmaWrite(base_addr + 0x00010200 + 2*i + 1, mac_high)    # mac upper 16 bits 
            # self.rdmaWrite(base_addr + 0x00010100 + i, ip)    # ip 32 bits
            # self.rdmaWrite(base_addr + 0x00010000 + i, port + i%num_ports)    # port 16 bits           
            
        return 1
        
    def x10g_set_farm_mode(self, base_addr, mode):
        """ Enable or Disable 10G Farm Mode  """
        
        ctrl_reg = self.rdmaRead(base_addr+15, 1)[1]
 
        if mode == 1:
            ctrl_reg = ctrl_reg | 0x00000020
        else:
            ctrl_reg = ctrl_reg & ~0x00000020
            
        self.rdmaWrite(base_addr+15, ctrl_reg)     
            
        return 1
               
    def swap_endian(self, data):  
        swapped = ((data << 24) & 0xff000000) | ((data << 8) & 0x00ff0000) | ((data >>24) & 0x000000ff) | ((data >> 8) & 0x0000ff00)
        return swapped
        
    def x10g_net_lut_clear(self, base_addr):
        """ Zero the Farm Mode LUTs contents """
    
        for i in range (0, 256):   
            self.rdmaWrite(base_addr + 0x00010200 + 2*i, 0)    # mac lower 32 bits 
            self.rdmaWrite(base_addr + 0x00010200 + 2*i + 1, 0)    # mac upper 16 bits 
            self.rdmaWrite(base_addr + 0x00010100 + i, 0)    # ip 32 bits
            self.rdmaWrite(base_addr + 0x00010000 + i, 0)    # port 16 bits           
            
        return 1   