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
from FemApi.FemAcquireConfig import FemAcquireConfig
from FemApi.FemTransaction import FemTransaction
#from FemApi.FemConfig import FemConfig
#from FemApi.FemAcquireConfig import FemAcquireConfig
from FemClient.FemClient import  *

class TBClient(FemClient):

# rdma mux is controlled implcitly by high address bits by gbe server on ppc.
# each FPGA F1 to F4 has 2 Xaui 10G channels

    master_id = 0
    #f1-4 id = 1-4
    mmc_id = 5

# FPGA N(=1-4) on rdma base address 0xNxxxxxxx
# following are offsets from that base
   
    #    """ F1_F4 addresses """            # 32 way rdma bus splitter
    
    udp_10g_0         = 0x00000000    #0
    udp_10g_1         = 0x00800000    #1
    data_gen_0        = 0x01000000    #2
    data_chk_0        = 0x01800000    #3
    data_gen_1        = 0x02000000    #4
    data_chk_1        = 0x02800000    #5
    f1_f4_ctrl        = 0x03000000    #6
    llink_mon_0       = 0x03800000    #7
    data_mon_0        = 0x04000000    #8
    llink_mon_1       = 0x04800000    #9  
    data_mon_1        = 0x05000000    #10
    mon_ppc1_64b    = 0x05800000    #11  64 bit mon from frame gen to dma2
    data_gen_2        = 0x06000000    #12   data gen to ppc1 dma
    data_gen_3        = 0x06800000    #13   data gen to ppc2 dma
    bram_ppc1         = 0x07000000    #14    comms to ppc1
    bram_ppc2         = 0x07800000    #15    comms to ppc2
    mon_ppc1_32b    = 0x08000000    #16  32 bit mon into dma2 on ppc1
    mon_ppc2_32b    = 0x08800000    #17  32 bit mon into dma2 on ppc2
    data_chk_ppc1_tx    = 0x09000000    #18  
    mon_ppc1_tx    = 0x09800000    #19  
    aur_ctrl    = 0x0a000000    #20  
    aur_gen    = 0x0a800000    #21  
    aur_chk    = 0x0b000000    #22  
    qdr    = 0x0b800000    #23  
    rsvd8    = 0x0c000000    #24  
    rsvd9    = 0x0c800000    #25  
    rsvd10    = 0x0d000000    #26  
    rsvd11    = 0x0d800000    #27  
    rsvd12    = 0x0e000000    #28  
    rsvd13    = 0x0e800000    #29  
    rsvd14    = 0x0f000000    #30  
    rsvd15    = 0x0f800000    #31  

    # Master FPGA on rdma address 0x0xxxxxxx   ;  4 way rdma bus splitter
    
    master_ctrl      = 0x00000000    #0        
    master_xpoint    = 0x04000000    #1 
    
    comms_bram_ppc      = 0x10  # start of area in ppc comms bram for ppc to write
    comms_bram_python   = 0x10  # start of area in ppc comms bram for python to write


#==================================================================================      
    
    def __init__(self, hostAddr=None, timeout=None):
        
        # Call superclass initialising function   
        super(TBClient, self).__init__(hostAddr, timeout)
            
    
    def setup_10g_udp_net_block(self, base_addr, net):
        #set up MAC address for SRC & destination
        # src and dest mac, ip and ports are only used if Farm mode LUT is disabled
 
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
        reg6b = self.rdmaRead(base_addr+6, 1)[0]
#        reg6b = 0xA1B2C3D4
        reg6b = (reg6b & 0x0000FFFF)
        reg6 =  ( (net['nic_ip'] << 16)  & 0xFFFFFFFF )
        reg6 =  (reg6 | reg6b)
    
        reg7 =  (net['nic_ip'] >> 16)
        reg7 = ( (reg7 | (net['fpga_ip'] << 16)) & 0xFFFFFFFF )
        
        reg8t = self.rdmaRead(base_addr+8, 1)[0]    # 1 = one 32 bit unsigned integer
#        reg8t = 0x9F8E7D6C
        reg8t = (reg8t & 0xFFFF0000)
        reg8b =  (net['fpga_ip'] >> 16)
        reg8 =  (reg8t | reg8b)

        # added jac from rob's latest code

        # set the udp source port
        reg8t = (reg8 & 0x0000FFFF)
        reg8b = (net['fpga_prt'] << 16)
        # port bytes need to be swapped in xaui register
        reg8bl = reg8b & 0x00ff
        reg8bu = reg8b & 0xff00
        reg8b = (reg8bl << 8) | (reg8bu >> 8) 
        reg8 = (reg8t | reg8b)
        
        reg9t = self.rdmaRead(base_addr+9, 1)[0]    # nb this was wrong reg in rob's code
        # set the udp destination port
        reg9t = (reg9t & 0xFFFF0000)
        reg9b = (net['nic_prt'] & 0x0000FFFF)
        # port bytes need to be swapped in xaui register
        reg9bl = reg9b & 0x00ff
        reg9bu = reg9b & 0xff00
        reg9b = (reg9bl << 8) | (reg9bu >> 8) 
        reg9 = (reg9t | reg9b)
        
#        print hex(reg6), "\n", hex(reg7), "\n", hex(reg8), "\n", hex(reg9)        
        #print "Writing to reg6, reg7 & reg8 & reg9.."
        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
        self.rdmaWrite(base_addr+9, reg9)

        return 0

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
        """robs udp packet header for 10g"""
        self.rdmaWrite(base_addr + 11, packet_hdr)

 
    def setup_10g_index_cycle(self, base_addr, index_cycle):       
        """ override word in header containing index for 10g port lut"""

        index_cycle &= 0x0000000f
        reg = self.rdmaRead(base_addr+10, 1)[0] 
        reg &= ~0x0000000f
        reg = reg | index_cycle
        self.rdmaWrite(base_addr+10, reg) 

       
    def setup_ll_mux(self, output_data_source):
        """select between data gen and ppc ll data sources"""
    
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
    
    def toggle_bits_new(self, reg_addr, bit_nr):
        """ toggle_bits() """

        prev_value = self.rdmaRead(reg_addr, 1)[0]         
        #print "prev: %08x" % prev_value
        off = prev_value & ~(1 << bit_nr)
        #print "off: %08x" % off
        self.rdmaWrite(reg_addr, off)
        on = prev_value | (1 << bit_nr)
        #print "on: %08x" % on
        self.rdmaWrite(reg_addr, on)
        off = prev_value & ~(1 << bit_nr)
        #print "off: %08x" % off
        self.rdmaWrite(reg_addr, off)
         
        return 0
    
    
    def setup_ll_frm_gen(self, base_address, length, data_type, num_ll_frames, hdr_trl_mode):
        """ This function sets up the data Generator & resets """

        # Data Gen soft reset
        #print "DATA GEN Internal Reset"
#        self.rdmaWrite(base_address+0,0x00000000)    
#        self.rdmaWrite(base_address+0,0x00000001)
#        self.rdmaWrite(base_address+0,0x00000000)
        
        # frm gen - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2
        #print "DATA GEN Data Length"
        self.rdmaWrite(base_address+1,reg_length)
        
        #print "DATA GEN Nr Frames"
        self.rdmaWrite(base_address+2, num_ll_frames)

        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4

        #turn ll frame header/trailer mode on if required
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
#        self.rdmaWrite(base_address+0,0x00000000)    
#        self.rdmaWrite(base_address+0,0x00000001)
#        self.rdmaWrite(base_address+0,0x00000000)

    def soft_reset_ll_frm_gen(self, base_address):
        """ This function just resets the frame nr in the header """
            
        # Data Gen soft reset
        #print "DATA GEN Internal Reset"
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)        

    def override_header_ll_frm_gen(self, base_address, enable_override, index_nr):
        """ This function overrides the index nr sent in the ll header (for steeting the port nr in 10g tx) """
        
        self.rdmaWrite(base_address+7, index_nr)   # set index nr 
        
        # override default behaviour         
        format_reg = self.rdmaRead(base_address+4, 1)[0] 
        if enable_override == 1:
            format_reg = format_reg | 0x00000100
        else:
            format_reg = format_reg & 0xFFFFFEFF 
        self.rdmaWrite(base_address+4, format_reg) 

        return 0       
        
    def status_ll_frm_gen(self, base_address):
        """ This function returns busy status of data gen """
            
        busy = self.rdmaRead(base_address+17, 1)[0]  
        return busy        

    def status_ll_frm_mon(self, base_address):
        """ This function returns busy status of link monitor """ 
        busy = self.rdmaRead(base_address+16+15, 1)[0]  
        return busy  
        
    def clear_ll_monitor(self, base_addr):
        """ clear local link monitor block
             """
        
        #print "Local Link Monitor Counter Reset"
        self.rdmaWrite(base_addr+1,0)
        self.rdmaWrite(base_addr+1,1)
        self.rdmaWrite(base_addr+1,0)
        
        return 0
   
    # Rob Halsall 08-04-2011
    def read_ll_monitor(self, base_addr, clock_freq):
        """ readout a local link monitor block  """
        
        mon_addr = base_addr + 16

        print "frm_last_length:\t",         self.rdmaRead(mon_addr+0, 1)[0]
        print "frm_max_length: \t",         self.rdmaRead(mon_addr+1, 1)[0]
        print "frm_min_length: \t",         self.rdmaRead(mon_addr+2, 1)[0]
        print "frm_number:\t\t",            self.rdmaRead(mon_addr+3, 1)[0]
        print "frm_last_cycles:\t",         self.rdmaRead(mon_addr+4, 1)[0]
        print "frm_max_cycles: \t",         self.rdmaRead(mon_addr+5, 1)[0]
        print "frm_min_cycles: \t",         self.rdmaRead(mon_addr+6, 1)[0] 
        total_data = self.rdmaRead(mon_addr+7, 1)[0]
        print "frm_data_total: \t", total_data         
        total_cycles = self.rdmaRead(mon_addr+8, 1)[0]
        print "frm_cycle_total:\t", total_cycles
        print "frm_trig_count: \t",         self.rdmaRead(mon_addr+9, 1)[0]
        print "frm_in_progress:\t",         self.rdmaRead(mon_addr+15, 1)[0]

        total_time = float(total_cycles) * (1/clock_freq)
          
        if (total_time):
 #           rate = (total_data/total_time) * 8
            rate = (total_data/total_time)   #  total data is in bytes already   jac
        else:
            rate = 0
            
        print "Data Total = %e" % total_data
        print "Data Time = %e" % total_time
        print "Data Rate = %e" % rate
        
        print ""
        
        return 0       

    def dump_regs_hex(self, base_addr, nr_regs):
        """ hex dump of regs """
        
        print "" 
        print 'rdma base addr = $%08X' %base_addr 
        for i in range(0, nr_regs):
        #    print "reg ", i, hex(self.rdmaRead(base_addr+i, 1)[0])
            print 'reg %2d = $%08X ' %(i, self.rdmaRead(base_addr+i, 1)[0])
            
        print ""  
        
        return 0  

# farm modes
        
    def x10g_net_lut_setup(self, base_addr, net):
        """ Set up the LUTs for 10G Farm Mode  """
        
        mac_low = ((net['nic_mac'] &  0xFFFFFFFF0000) >> 16)
        mac_high = ((net['nic_mac'] & 0x00000000FFFF) << 16) 
        ip = net['nic_ip']
        port = net['nic_prt']        

        # Example
        # '00-07-43-11-97-90'
        # 192.168.2.1
        # should be like...
        # ip = 0xC0A80201
        # mac_low = 0x43119790
        # mac_high = 0x00000007       
        # port = 61649
       
        mac_low = self.swap_endian(mac_low)
        mac_high = self.swap_endian(mac_high)
        ip = self.swap_endian(ip)  

        num_ports = net['num_prts']  
        print "num ports =", num_ports
        num_frames = net['num_frames']
        
 #       for i in range (0, 256):
        nr_lut_entries = num_frames
#        nr_lut_entries = num_frames*num_cycles
        if nr_lut_entries > 256 :
            nr_lut_entries = 256
        for i in range (0, nr_lut_entries):   # only set up for max nr of frames in a cycle 
            self.rdmaWrite(base_addr + 0x00010200 + 2*i, mac_low)    # mac lower 32 bits 
            self.rdmaWrite(base_addr + 0x00010200 + 2*i + 1, mac_high)    # mac upper 16 bits 
            self.rdmaWrite(base_addr + 0x00010100 + i, ip)    # ip 32 bits 
            self.rdmaWrite(base_addr + 0x00010000 + i, port + i%num_ports)         
            
        return 0

    def x10g_net_lut_setup_from_list(self, base_addr, net, myTBTest, mac_ip_lut):
        """ Set up the LUTs for 10G Farm Mode from list of NIC port@host """
        
        i = 0;
        
        for nic in net['nic_list']:
            new_nic = nic.split('@')
            nic_port = new_nic[0]
            #print "port ", port
            nic_host = new_nic[1]       
            print "host ", nic_host
            nic_mac = mac_ip_lut[nic_host]              
            print "mac ", nic_mac 
            
            mac = myTBTest.mac_addr_to_uint64(nic_mac)
            mac_low = ((mac &  0xFFFFFFFF0000) >> 16)
            mac_high = ((mac & 0x00000000FFFF) << 16)
            
            ip = myTBTest.ip_addr_to_uint32(nic_host)
            port = int(nic_port)
                  
            print "port ", port
 
            mac_low = self.swap_endian(mac_low)
            mac_high = self.swap_endian(mac_high)
            ip = self.swap_endian(ip)  

            self.rdmaWrite(base_addr + 0x00010200 + 2*i, mac_low)    # mac lower 32 bits 
            self.rdmaWrite(base_addr + 0x00010200 + 2*i + 1, mac_high)    # mac upper 16 bits 
            self.rdmaWrite(base_addr + 0x00010100 + i, ip)    # ip 32 bits
 
            self.rdmaWrite(base_addr + 0x00010000 + i, port)    # port 16 bits       
            
            i = i+1;
            
        return 0
        
    def x10g_set_farm_mode(self, base_addr, mode):
        """ Enable or Disable 10G Farm Mode  """
        
        ctrl_reg = self.rdmaRead(base_addr+15, 1)[0]
        #print 'ctrl_reg = $%08X' %ctrl_reg         
        
        if mode == 1:
            ctrl_reg = ctrl_reg | 0x00000020
        else:
            ctrl_reg = ctrl_reg & ~0x00000020
            
        self.rdmaWrite(base_addr+15, ctrl_reg)  
        
        ctrl_reg = self.rdmaRead(base_addr+15, 1)[0]
        print 'ctrl_reg = $%08X' %ctrl_reg         
            
        return 0
               
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
            
        return 0   

    def init_ppc_bram(self, base_addr, fpga_nr):
        """ This function initialises ppc comms bram """
 
        #print 'init_ppc_bram: rdma base addr = $%08X ; fpga = %d' %(base_addr, fpga_nr)
        self.rdmaWrite(base_addr + self.comms_bram_python + 0, 0xbeef0001)  # sanity value from python
         
        return 0  

    def setup_ppc_bram(self, base_addr, length, data_type, num_ll_frames, hdr_trl_mode):
        """ This function sets up the bram to provide ppc with run params. Legacy code """
 
        self.rdmaWrite(base_addr+8, 0) # handshaking
        self.rdmaWrite(base_addr+10, 0) # handshaking

        self.rdmaWrite(base_addr+9, 0) # port index
       
        self.rdmaWrite(base_addr+16, length) # for dma tx length in bytes
            
        return 0  

    def ppc_prepare_run(self, base_addr, numberTrains, numberImages ):
        """ This function fills ppc bram with dma params before run start.  """

        # BRAM comms mimics FEM mailbox comms when running with variant of Matt's code.
        # Data structure for mailbox messages
        #typedef struct
        #{
	    #    u32 cmd;
	    #    u32 buffSz;
	    #    u32 buffCnt;
	    #    u32 param;
	    #    u32 mode;
	    #    u32 bdCoalesceCnt;
        #} mailMsg;
               
        print "Configure PPC1 Readout for CMD_ACQ_CONFIG."

        # compute the DMA buffer sizes based on the numberImages in the Train(s)
        # whole nr of Trains must fit in the BD ring buffers 

        maxNrImagesPerBD = 127  # limit the nr of images in a BD (physical limit is 127)
        nrTrainsInMemory = 4   # allow for N Trains worth in BDs

        nrBufsPerTrain = (numberImages / maxNrImagesPerBD) + 1
        if ((numberImages % maxNrImagesPerBD) == 0):
            nrBufsPerTrain -= 1
        BufCount = nrBufsPerTrain * nrTrainsInMemory   # ensure whole nr of Trains in BD ring
        #BufCount = 10   

        lpd_image_size = 0x20000    # 0x100    # 0x20000    # 128 KB for lpd frame  , must set datagen size to match

        BufSize = (maxNrImagesPerBD * lpd_image_size)    
        NumAcqs = numberTrains * nrBufsPerTrain    # number of BDs to process
        Coalesce = numberImages    # for LPD use this param instead to pass the nr of images to set up Tx descriptors
        
        AcqMode = FemTransaction.ACQ_MODE_TX_ONLY   # TEST
        #AcqMode = FemTransaction.ACQ_MODE_NORMAL
        if (AcqMode == FemTransaction.ACQ_MODE_TX_ONLY):
             print "*** WARNING TESTING  FemTransaction.ACQ_MODE_TX_ONLY " 
        
        ##  mailbox call   # self.acquireSend(FemTransaction.CMD_ACQ_CONFIG, AcqMode, BufSize, BufCount, NumAcqs, Coalesce)

        print "CMD_ACQ_CONFIG. Total Nr BDs = %d ; Nr BD per Train = %d " % (BufCount, nrBufsPerTrain)
        print "CMD_ACQ_CONFIG. Nr BDs to Process this Run = %d ; Length of BD = $%08x bytes" % ( NumAcqs, BufSize)

        self.rdmaWrite(base_addr + self.comms_bram_python + 4, FemTransaction.CMD_ACQ_CONFIG) 
        self.rdmaWrite(base_addr + self.comms_bram_python + 5, BufSize) 
        self.rdmaWrite(base_addr + self.comms_bram_python + 6, BufCount) 
        self.rdmaWrite(base_addr + self.comms_bram_python + 7, NumAcqs)     # param    
        self.rdmaWrite(base_addr + self.comms_bram_python + 8, AcqMode) 
        self.rdmaWrite(base_addr + self.comms_bram_python + 9, Coalesce) 
        
        self.rdmaWrite(base_addr + self.comms_bram_python + 12, 0xface1234) # signal to PPC that run params are ready to read

        return 0  

    def ppc_start_run(self, base_addr):
        """ This function sends start run signal to PPC """
 
        self.rdmaWrite(base_addr + self.comms_bram_python + 4, FemTransaction.CMD_ACQ_START) 
        #self.rdmaWrite(base_addr + self.comms_bram_python + 16, FemTransaction.CMD_ACQ_START)  
        self.rdmaWrite(base_addr + self.comms_bram_python + 12, 0xface1234) # signal to PPC that param is ready
         
        return 0  

    def ppc_stop_run(self, base_addr):
        """ This function sends stop run signal to PPC """
 
        self.rdmaWrite(base_addr + self.comms_bram_python + 4, FemTransaction.CMD_ACQ_STOP) 
        #self.rdmaWrite(base_addr + self.comms_bram_python + 16, FemTransaction.CMD_ACQ_STOP)  
        self.rdmaWrite(base_addr + self.comms_bram_python + 12, 0xface1234) # signal to PPC that param is ready
         
        return 0  

    def ppc_ready_for_run(self, base_addr):
        """ This function checks whether PPC is ready for next run """
 
        reg = self.rdmaRead(base_addr + self.comms_bram_ppc + 0, 1) [0] 
         
        return reg  

    def ppc_watchdog(self, base_addr):
        """ This function checks whether PPC is alive """
 
        # tbd 
         
        return status  
        
    def start_dma_tx(self, base_addr, index):
        """ start dma tx """
  
        self.rdmaWrite(base_addr+9, index) 
        self.rdmaWrite(base_addr+8, 0x1234) 
            
        return 0 

    def clear_dma_tx(self, base_addr, index):
        """ init dma tx """
  
        self.rdmaWrite(base_addr+8, 0) 
        self.rdmaWrite(base_addr+9, 0) 
        self.rdmaWrite(base_addr+10, 0) 
            
        return 0 
            
    def final_dma_tx(self, base_addr):
        """ flag last dma tx """
  
        self.rdmaWrite(base_addr+10, 0x5678) 
            
        return 0 
        
    def clear_final_dma_tx(self, base_addr):
        """ flag last dma tx """
  
        self.rdmaWrite(base_addr+10, 0) 
            
        return 0 
        
    def prev_dma_tx(self, base_addr):
        """  """  
        busy = 1
        
        reg = self.rdmaRead(base_addr+8, 1) [0]
        reg &= 0x0000ffff
        
        if reg == 0:
          busy = 0
            
        return busy
        
    def setup_10g_rx_filter(self, base_addr):
        """ set 10g rx filter to accept any udp packet """     

        reg = self.rdmaRead(base_addr+11, 1)[0]
        reg &= 0xffff00ff
        reg |= 0x0000f300
        self.rdmaWrite(base_addr+11, reg) 
        
        return reg   

    def setbit(self, addr, bit):
        """ set bit in register """     

        reg = self.rdmaRead(addr, 1)[0]
        reg |= (1 << bit)
        self.rdmaWrite(addr, reg) 
        
        return reg   

    def clrbit(self, addr, bit):
        """ set bit in register """     

        reg = self.rdmaRead(addr, 1)[0]
        reg &= ~(1 << bit)
        self.rdmaWrite(addr, reg) 
        
        return reg   

    def get_master_firmware_vers(self):
        ''' Gets the firmware version loaded in Master FPGA [READONLY]   '''
        return self.rdmaRead((self.master_id<<28) | self.master_ctrl+17, 1)[0]

    def get_fe_firmware_vers(self, fpga_nr):
        ''' Gets the firmware version loaded in FE FPGAs [READONLY]   '''
        return self.rdmaRead((fpga_nr<<28) | self.f1_f4_ctrl+17, 1)[0]
        
    def xpoint_reset(self):
        ''' Reset crosspoint. Bit 0 of register connected directly to reset line. Active Low.  '''
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+13, 0) 
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+13, 1)         
        #print 'Toggled Xpoint Reset line.'        
        return 0
        
    def xpoint_write(self, addr, data):
        ''' Write data to crosspoint register addr. Via Serial Interface. From matlab ms_xpoint_write.m   '''
       
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+10, addr) 
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+11, data)  
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+9, 2)  # write strobe       
        #print 'Write to Xpoint reg: addr = $%08x ; data = $%08x' %( addr, data )    
        
        return 0

    def xpoint_read(self, addr):
        ''' Write data to crosspoint register addr. Via Serial Interface. From matlab ms_xpoint_read.m   '''
       
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+10, addr) 
        self.rdmaWrite((self.master_id<<28) | self.master_xpoint+9, 1)  # read strobe  
        data =  self.rdmaRead((self.master_id<<28) | self.master_xpoint+19, 1)[0]    
        #print 'Read from Xpoint reg: addr = $%08x ; data = $%08x' %( addr, data )     
        
        return data

    def xpoint_dump_regs(self, base, page, first_reg, last_reg):
        ''' Display the contents of Xpoint registers for given page  '''

        if page == 0x00 or page == 0x01 or page == 0x03 or page == 0x05 or page == 0x07 or page == 0x08 or page == 0x0a or page == 0x0c or page == 0x0e or page == 0x21:
            self.xpoint_write(255,page) # select legal page
        else:
            print '*** WARNING: xpoint_dump_regs(): Illegal Xpoint page nr = %d' %page     
            return 99

        page = self.xpoint_read(255)
        print '=========== XPoint Page Nr = %02x   ==============' %page     
        for i in range(first_reg, last_reg+1):
            addr = base + i
            data = self.xpoint_read(addr)
            print '@addr offset = %03d ($%02x) ; data = %03d ($%02x)' %( addr&0xff, addr&0xff, data, data )   # 256 x 8 bit locations on each page 
                
        return 0
