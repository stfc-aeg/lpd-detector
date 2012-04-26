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
        super(LpdFemClient, self).__init__(hostAddr, timeout)
            
    
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
        
        reg1 = (net['src_mac'] & 0x00000000FFFFFFFF)
    
        reg2b = ((net['src_mac'] & 0x0000FFFF00000000) >> 32)
        reg2t = ((net['dst_mac'] & 0x000000000000FFFF) << 16)
        reg2 = (reg2b | reg2t)
    
        reg3 = (net['dst_mac'] >> 16)

        print "# src_mac_lower_32"
        self.rdmaWrite(base_addr+0, reg1)
        print "# dst_mac_lower_16 & src_mac_upper_16"
        self.rdmaWrite(base_addr+1, reg2)
        print "# dst_mac_upper_32"
        self.rdmaWrite(base_addr+2, reg3)
        
        #set up IP address for SRC & destination
        print "Reading IP address for Src & destination.."
        reg6b = self.rdmaRead(base_addr+6, 1)[1]
#        reg6b = 0xA1B2C3D4
        reg6b = (reg6b & 0x0000FFFF)
        reg6 =  ( (net['dst_ip'] << 16)  & 0xFFFFFFFF )
        reg6 =  (reg6 | reg6b)
    
        reg7 =  (net['dst_ip'] >> 16)
        reg7 = ( (reg7 | (net['src_ip'] << 16)) & 0xFFFFFFFF )
        
        reg8t = self.rdmaRead(base_addr+8, 1)[1]    # 1 = one 32 bit unsigned integer
#        reg8t = 0x9F8E7D6C
        reg8t = (reg8t & 0xFFFF0000)
        reg8b =  (net['src_ip'] >> 16)
        reg8 =  (reg8t | reg8b)

#        print hex(reg6), "\n", hex(reg7), "\n", hex(reg8)        
        print "Writing to reg6, reg7 & reg8.."
        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
    
        self.rdmaRead(base_addr+9, 1)    

    def fem_10g_udp_net_set_up_block1(self, net):
        #set up MAC address for SRC & destination
        base_addr = LpdFemClient.udp_10g_1
        
        reg1 = (net['src_mac'] & 0x00000000FFFFFFFF)
    
        reg2b = ((net['src_mac'] & 0x0000FFFF00000000) >> 32)
        reg2t = ((net['dst_mac'] & 0x000000000000FFFF) << 16)
        reg2 = (reg2b | reg2t)
    
        reg3 = (net['dst_mac'] >> 16)

        print "# src_mac_lower_32"
        self.rdmaWrite(base_addr+0, reg1)
        print "# dst_mac_lower_16 & src_mac_upper_16"
        self.rdmaWrite(base_addr+1, reg2)
        print "# dst_mac_upper_32"
        self.rdmaWrite(base_addr+2, reg3)
        
        #set up IP address for SRC & destination
        print "Reading IP address for Src & destination.."
        reg6b = self.rdmaRead(base_addr+6, 1)[1]
#        reg6b = 0xA1B2C3D4
    
        reg6b = (reg6b & 0x0000FFFF)
        reg6 =  ( (net['dst_ip'] << 16) & 0xFFFFFFFF )
        reg6 =  (reg6 | reg6b)
    
        reg7 =  (net['dst_ip'] >> 16)
        reg7 =  ( (reg7 | (net['src_ip'] << 16)) & 0xFFFFFFFF )
        
        reg8t = self.rdmaRead(base_addr+8, 1)[1]    # 1 = one 32 bit unsigned integer
#        reg8t = 0x9F8E7D6C
        reg8t = (reg8t & 0xFFFF0000)
        reg8b = (net['src_ip'] >> 16)
        reg8 =  (reg8t | reg8b)        
    
#        print hex(reg6), "\n", hex(reg7), "\n", hex(reg8)
        print "Writing to reg6, reg7 & reg8.."
        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
    
        self.rdmaRead(base_addr+9, 1)    
    
    def fem_local_link_mux_setup(self, output_data_source):
        # set up local link mux
        base_addr = LpdFemClient.fem_ctrl_0
    
        reg1 = 0x00000001 | base_addr
    
        if output_data_source == 0:
            print "local link mux ouput 0"
            self.rdmaWrite(reg1, 0x00000000)
        else:
            print "local link mux output 1"
            self.rdmaWrite(reg1, 0x00000001)
        
        return 1
        
    
    def toggle_bits(self, reg_addr, bit_pat):
        """ toggle_bits() """
        address= LpdFemClient.fem_ctrl_0 + reg_addr
        
        bits_off = 0
        bits_on  = bit_pat
        
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
    
    def ll_frm_gen_setup(self, length, data_type):
        """ This function sets up the data Generator & resets """
    
        base_address = LpdFemClient.data_gen_0
        # frm gen - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2
        print "DATA GEN Data Length"
        self.rdmaWrite(base_address+1,reg_length)
    
        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4
    
        print "DATA GEN Data Type"
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
    
        print "DATA GEN Data Init 0"
        self.rdmaWrite(base_address+5,data_0)

        print "DATA GEN Data Init 1"
        self.rdmaWrite(base_address+6,data_1)
    
        # Data Gen soft reset
        print "DATA GEN Internal Reset"
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)
    
    
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
        print "UDP Block Packet Size"
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len      
        print "UDP Block IP Header Length"
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        print "UDP Block UDP Length"
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # enable & set IFG
        print "UDP Block IFG"
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)
    
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
        print "UDP Block Packet Size"
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len
        print "UDP Block IP Header Length"
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        print "UDP Block UDP Length"
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # enable & set IFG
        print "UDP Block IFG"
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)
        
        return 1   

    def robs_udp_packet_header_10g(self, robs_udp_packet_hdr):
        # rob's udp packet headers
        packet_header_10g_0 = (0x0000000 | LpdFemClient.udp_10g_0)
        packet_header_10g_1 = (0x0000000 | LpdFemClient.udp_10g_1)
        
        print "robs udp packet header 10g_0"
        self.rdmaWrite(packet_header_10g_0, robs_udp_packet_hdr)
        print "robs udp packet header 10g_1"
        self.rdmaWrite(packet_header_10g_1, robs_udp_packet_hdr)

    def frame_generator_set_up_10g(self, data_gen_0_offset, num_ll_frames):
        # Original Matlab instruction:
        #rdma_write(    data_gen_0+2, num_ll_frames+1,'rw','DATA GEN Nr Frames');
        # data_gen_0 = LpdFemClient.data_gen_0
        # num_ll_frames = defined in fem_asic_test; +1 added to num_ ll_frame argument when this function is called
        print "DATA GEN Nr Frames"
        #rdma_write(    data_gen_0+data_gen_0_offset, num_ll_frames)
        self.rdmaWrite(LpdFemClient.data_gen_0+data_gen_0_offset, num_ll_frames)

    def recv_image_data_as_packet(self, udp_pkt_num, dudp, packet_size): 
        # loop to read udp frame packet by packet
#        for i in range(0,udp_pkt_num-1, 1):
#             TODO: Will next packet overwrite previous packet?
#            dudp = LpdFemClient.recv()
#             Or use read() function:  ->   #dudp = myFemClient.read(theBus, theWidth, theAddr, theReadLen)    ??
#            print "%4i %8X %8X %8X %8X" % (i, dudp(1),dudp(2),dudp(3),dudp(packet_size))
#            dudp = uint32(fread(u, packet_size, 'uint16'));
#            fprintf('%04i %08X %08X %08X %08X',i, dudp(1),dudp(2),dudp(3),dudp(packet_size));
#        return dudp
        dudp = []
        return dudp
    
    def recv_image_data_as_frame(self, dudp):
#        dudp = LpdFemClient.recv()
#        return dudp
#        return self.recv()
        dudp = []
        return dudp 
    
    def read_slow_ctrl_file(self, filename):
    
        slow_ctrl_file = open(filename, 'r')
        lines = slow_ctrl_file.readlines()
        slow_ctrl_file.close()    
        
        data = []
        for line in lines:
            ivals = [int(val) for val in split(strip(line))]
            data.append(ivals)
            
        i_max = len(data)
#        j_max = len(data[0])
        
        no_words = i_max / 32
        if i_max%32:
            no_words = no_words + 1
            
        slow_ctrl_data = [0L] * no_words
    
        j = 0
        k = 0
        nbits = 0
        data_word = 0L;
        data_mask = 1L;
        
        for i in range(i_max):
            if data[i][1] == 1:
                nbits = nbits + 1
                if data[i][2] == 1:
                    data_word = data_word | data_mask
                if j == 31:
                    slow_ctrl_data[k] = data_word
                    data_word = 0l
                    data_mask = 1L
                    k = k+1
                    j = 0
                else:
                    data_mask = data_mask << 1
                    j = j + 1
        
        slow_ctrl_data[k] = data_word
        no_of_bits = nbits
                
        return slow_ctrl_data, no_of_bits
    


    #def read_fast_cmd_file(self, filename,cmd_reg_size):
    def read_fast_cmd_file_jc_new(self, filename,cmd_reg_size):
        # location:    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian
        # filename:    read_fast_cmd_file_jc.m
        # function:    read_fast_cmd_file()
        # Read fast control file (hex) into an array
        # also adds nops 
    
        # read in command code and nops
        fast_ctrl_file = open(filename, 'r')
        lines = fast_ctrl_file.readlines()
        fast_ctrl_file.close()
    
        data = []
        for line in lines:
            ivals = [val for val in split(strip(line))]
            ivals[0] = int(ivals[0], 16)    # Read hexadecimal
            ivals[1] = int(ivals[1])        # Read decimal (base 10)
            data.append(ivals)
            
        #print data[0][0], data[0][1], data[1][0], data[1][1], data[2][0], data[2][1], data[3][0], data[3][1], data[4][0], data[4][1]
        #print len(data), len(data[0])
        
        i_max = len(data)
        j_max = len(data)
    
        fast_cmd_data = [0L] * i_max
        fast_cmd_nops = [0L] * i_max 
    
        for i in range(i_max):
            fast_cmd_data[i] = data[i][0] 
            fast_cmd_nops[i] = data[i][1] 
    
        nops_total = 0
    
        # new bram format for 22 bit commands
        # nops(31:22) - syncbit(21) - x(20) - cmd(19:12) - padding 0's (11:0)
    
        for j in range(j_max):
    
            fast_cmd_data[j] = (fast_cmd_data[j] & 0x000fffff)
            # special sync_reset 20 bit command?
            if (fast_cmd_data[j] == 0x5a):
                fast_cmd_data[j] = 0x5a5a5                
                fast_cmd_data[j] = self.bitshift(fast_cmd_data[j], cmd_reg_size, 20)
            elif (fast_cmd_data[j] == 0xfffff):  # special tests
                fast_cmd_data[j]= self.bitshift(fast_cmd_data[j], cmd_reg_size, 20)
            else:
                fast_cmd_data[j]= self.bitshift(fast_cmd_data[j], cmd_reg_size, 10)
                fast_cmd_data[j]= (fast_cmd_data[j] | self.bitshift(1, cmd_reg_size, 1) )

            nops_total = nops_total + fast_cmd_nops[j]  
            fast_cmd_data[j]= (fast_cmd_data[j] | (fast_cmd_nops[j] << 22))  
    
        no_of_words = j_max
        no_of_nops = nops_total
    
        return fast_cmd_data, no_of_words, no_of_nops
    
    def bitshift(self, bitVal, arg1, arg2):    
        """ bit shift bitVal according to difference of arg1 - arg2
            (arg1 - arg2) > 0 = bit shift to left (Increase bitVal)
            (arg1 - arg2) < 0 = bit shift to right (Decrease bitVal) """
        if (arg1-arg2 > 0):
            bitVal = (bitVal << arg1-arg2)
        elif (arg1-arg2 < 0):
            bitVal = (bitVal >> arg2-arg1)
        else:
            pass   # If arg1 = arg2, do nothing (bit shift 0 steps)
        return bitVal


    def fem_fast_bram_setup(self, fast_cmd_data, no_of_words):
        # File path:    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian\matlab\matlab
        # Filename:     fem_fast_bram_setup.m
        # Func name:    fem_fast_cmd_setup (!!! function name inside fem_fast_bram_setup.m !!!)
        # fem_asic_test.m calls function:    fem_fast_bram_setup(s, fast_cmd_1, fast_cmd_data, no_of_words);
        #                                    Line:258
        base_addr_1 = LpdFemClient.fast_cmd_1
        #fast cmd set up function blank
        
        max_block_length = 1024
        
        # check length is not greater than FPGA Block RAM
        
        block_length = no_of_words
        
        if block_length > max_block_length:
            block_length =  max_block_length        
        
        # Build tuple of a list of data
        dataTuple = tuple([fast_cmd_data[i] for i in range(block_length)])
        # load fast control pattern memory
        print "Fast Cmd RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
        
        
    ##def fem_fast_cmd_setup(self, no_of_words):
    def fem_fast_cmd_setup_new(self, no_of_words):
        # Location:    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian\matlab\matlab
        # filename:    fem_fast_cmd_setup_new.m
        # func name:    fem_fast_cmd_setup(s, base_addr_0, no_of_words)
        
        base_addr_0 = LpdFemClient.fast_cmd_0
        
        #fast cmd set up function blank
    
        max_block_length = 1024
    
        # check length is not greater than FPGA Block RAM
    
        block_length = no_of_words
    
        if block_length > max_block_length:
            block_length =  max_block_length
    
        # load control registers
        # reset mode  for old behaviour outputting bram , without vetos
    
        print "fast_command_reg_reset_offset"
        self.rdmaWrite(base_addr_0+6, 0)
        print "fast_command_reg_reset_nwords"  
        self.rdmaWrite(base_addr_0+7, no_of_words)
        
    def fem_fast_cmd_setup(self, fast_cmd_data, no_of_words):
    
        base_addr_0 = LpdFemClient.fast_cmd_0
        base_addr_1 = LpdFemClient.fast_cmd_1
            
        #fast cmd set up function blank
    
        max_block_length = 1024
    
        # check length is not greater than FPGA Block RAM
    
        block_length = no_of_words
    
        if block_length > max_block_length:
            block_length =  max_block_length
    
        # Build tuple of a list of data
        dataTuple = tuple([fast_cmd_data+i for i in range(block_length)])
        
        # load fast control pattern memory
        print "Fast Cmd RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
    
        # load control registers
        print "Fast cmd block length"
        self.rdmaWrite(base_addr_0+1, block_length-1)  # was block_length - 1 ? jc
        
    def fem_slow_ctrl_setup(self, slow_ctrl_data, no_of_bits):
    
        base_addr_0 = LpdFemClient.slow_ctr_0
        base_addr_1 = LpdFemClient.slow_ctr_1
        
        #slow control set up function blank
        
        max_block_length = 1024
        
        # load slow control pattern memory
        
        block_length = len(slow_ctrl_data)
        
        if block_length[1] > max_block_length:
            block_length[1] =  max_block_length
        
        dataTuple = tuple([slow_ctrl_data+i for i in range(block_length[1])])
        
        print "Slow Ctrl RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
        
        # load control registers
        
        # set number of bits register
        max_no_of_bits = 32*1024
        if no_of_bits > max_no_of_bits:
            no_of_bits = max_no_of_bits
        
        
        no_of_bits = no_of_bits + 1    # fix added  jc
        
        control_reg_1 = base_addr_0 + 1
        
        print "slow ctrl - no of bits (+1) to reg"
        self.rdmaWrite(control_reg_1, no_of_bits)

        
    def select_slow_ctrl_load_mode(self, address_offset, slow_ctrl_load_mode):
        # select slow control load mode  jac
        
        print "asic load mode"
        self.rdmaWrite(LpdFemClient.slow_ctr_0+address_offset, slow_ctrl_load_mode)
        
    def fem_asic_rx_setup(self, mask_array, no_asic_cols, no_cols_frm):
        
        # called from script as:    fem_asic_rx_setup(s, asic_srx_0, mask_array, no_asic_cols+1,no_asic_cols_per_frm+1)
        # defined in script as:     fem_asic_rx_setup(s, base_addr, mask_array,no_asic_cols,no_cols_frm)
        
        base_addr = LpdFemClient.asic_srx_0        

        #Set up the XFEL FEM ASIC RX IP Block
         
        #setup IP Address register locations
         
        mask_reg0 = (0x00000004 | base_addr)
        mask_reg1 = (0x00000005 | base_addr)
        mask_reg2 = (0x00000006 | base_addr)
        mask_reg3 = (0x00000007 | base_addr)
         
        #gain_override_reg         = (0x0000000 | base_addr)
        #data_source_reg           = (0x00000001 | base_addr)
        no_clk_cyc_dly_reg        = (0x00000002 | base_addr)
        no_asic_cols_cols_frm_reg = (0x00000003 | base_addr)
         
        # setup data values
        no_asic_cols = (no_asic_cols & 0x0000001FF)
        no_cols_frm  = (no_cols_frm & 0x0000001FF)
        no_cols_frm_shft  = (no_cols_frm << 16)
        no_asic_cols_cols_frm = (no_cols_frm_shft | no_asic_cols)

         
        # clkc cycle delay for sof-eof formula 512 * 36 * no cols?
        #no_clk_cyc_dly = 0x00011FDC)
         
        #no_clk_cyc_dly = 512 * 36 * no_asic_cols * no_cols_frm - 1 
         
        # this doesn't match formula in register doc ? jac
        # frame clock length = (no cols * 512 * 36) - 36
        # is this the nr of clocks for payload of each ll frame (or all frames) ?
        # assume headers and footer are not included.
         
        # also fixed bug as above was using bit shifted value of no_cols_frm
        no_clk_cyc_dly = (512 * 36 * no_cols_frm) - 36 
                  
        # set up clk cycle delay
        print "asic rx clk cycle delay"
        self.rdmaWrite(no_clk_cyc_dly_reg,no_clk_cyc_dly)
        
        # set up num asic cols & num cols per frame
        print "asic rx no_cols cols_frm"
        self.rdmaWrite(no_asic_cols_cols_frm_reg,no_asic_cols_cols_frm)
   
        # set up mask registers
        print "asic rx 0"
        self.rdmaWrite(mask_reg0,mask_array[0])
        print "asic rx 1"
        self.rdmaWrite(mask_reg1,mask_array[1])
        print "asic rx 2"
        self.rdmaWrite(mask_reg2,mask_array[2])
        print "asic rx 3"
        self.rdmaWrite(mask_reg3,mask_array[3])
         
  
    def data_source_self_test(self, asic_data_source):
        # data source - self test
        data_source_reg           = (0x00000001 | LpdFemClient.asic_srx_0)
        print "asic rx data source" # 0 = real data ; 1 = test data
        self.rdmaWrite(data_source_reg,asic_data_source)
        
        
    def gain_override(self, asic_gain_override):
        # added override to gain selection 
        # 
        #  bits
        #  0000  normal gain selection     0
        #  1000  force select x100         8
        #  1001  force select x10          9
        #  1011  force select x1          11
        #  1111  force error condition ?  15
        # 
        # Above explanation taken from: 
        #    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian\matlab\matlab\fem_asic_rx_setup.m
        # However, the actual implementation is presumed to be inside:
        #    fem_asic_test.m line 278    (rdma_write(s,gain_override_reg,..))
        gain_override_reg = (0x0000000 | LpdFemClient.asic_srx_0)
        print "asic rx gain override"
        self.rdmaWrite(gain_override_reg,asic_gain_override)
        
        
    def top_level_steering(self, asic_rx_start_delay):
        # turn fast & slow buffers on
        print "asic turn on buffers"
        self.rdmaWrite(LpdFemClient.fem_ctrl_0+5, 0)
        
        print "asic serial out readback is from bot sp3 i/o"
        self.rdmaWrite(LpdFemClient.fem_ctrl_0+2, 1)
        
        print "asic start readout delay wrt fast cmd"
        self.rdmaWrite(LpdFemClient.fem_ctrl_0+4, asic_rx_start_delay)
        
        
    def check_how_much_data_arrived(self, udp_frm_sze):
        """ Check how much UDP data that has arrived """
        print "Amount of UDP data arrived:"
#        count=0
#        while ( (self.bytesavailable != udp_frm_sze) and (count <= 8) ):
#            no_bytes = self.bytesavailable
#            print "%4i" % count, "%8X" % no_bytes
#            count=count+1
#            time.sleep(0.25)
#            time.sleep(0.75)
    
