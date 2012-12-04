'''
Created on Dec 3, 2012

@author: ckd27546
'''

from LpdFemClientLegacy import *  #LpdFemClientLegacy

# Import library for parsing XML fast command files
from LpdCommandSequence.LpdCommandSequenceParser import LpdCommandSequenceParser
from SlowCtrlParams import SlowCtrlParams

class paper_exercise():

    currentSlowCtrlDir = "/"
    currentFastCmdDir = "/"
    
    try:
        myLpdFemClient = LpdFemClientLegacy(('192...', 6969), timeout=10)
    except FemClientError as errString:
        print "Error: FEM connection failed:", errString
        sys.exit(1)

    # --------------------------------------------------------------------------- #
    #            CONFIGURE
    # --------------------------------------------------------------------------- #
    
    ''' See jac's function: config_10g_link() ? '''
    
    femHost                 = '192 ... ...'
    femPort                 = 6969
        
    
    send_ppc_reset          = 1
    fast_ctrl_dynamic       = 1
    setup_slow_control_bram = 1
    
    enable_10g              = 1
    readout_mode            = 'frame'
    data_source_to_10g      = 1
    asic_rx_counting_data   = 0
    asic_module_type        = 2
    asic_pseudo_random      = 0
    load_asic_config_brams  = 0
    asic_rx_start_delay     = 61    # 58
    num_ll_frames           = 1  # nr of local link frames to generate
    trigger_type            = 'a'
    myLpdFemClient.toggle_bits(9, 1)    # Resets dma engines
    fast_cmd_reg_size       = 22
    mask_list               = [0, 0, 0, 0]
    no_asic_cols            = 3   # no_asic_cols = nr triggers or images per train
    no_asic_cols_per_frm    = 3   # no images per local link frame
    eth_ifg                 = 0x00001000  # Ethernet Inter Frame Gap
    udp_pkt_len             = 8000
    udp_pkt_num             = 1
    udp_frm_sze             = (no_asic_cols+1) * 512 * 128 * 2 + 0  # header and trailer removed by ll_rmv
    udp_in_buf_size         = 2048*1024
    asic_gain_override      = 8
    robs_udp_packet_hdr     = 4
    udp_pkt_len             = 8000  #1000
    udp_pkt_num             = 1
    udp_frm_sze             = 262144

    x10g_0, x10g_1          = pcAddressConfig.getStructsVariables()
    # e.g.:
    
    x10g_0 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
              'src_ip'  : self.ip_addr_to_uint32('192.168.7.2'),
              'src_prt' : self.prt_addr_to_uint16('8'),
              # Target PC:
              'dst_mac' : self.mac_addr_to_uint64('00-07-43-10-61-88'),
              'dst_ip'  : self.ip_addr_to_uint32('192.168.7.1'),
              'dst_prt' : self.prt_addr_to_uint16('61649')}
    
    x10g_1 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
              'src_ip'  : self.ip_addr_to_uint32('192.168.8.2'),
              'src_prt' : self.prt_addr_to_uint16('0000'),
              'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),  # in vhdl 10g 
              'dst_ip'  : self.ip_addr_to_uint32('192.168.8.1'),
              'dst_prt' : self.prt_addr_to_uint16('0000')}

    # Set up the UDP IP blocks
    myLpdFemClient.fem_10g_udp_set_up_block0(udp_pkt_len, udp_frm_sze, eth_ifg)
    myLpdFemClient.fem_10g_udp_set_up_block1(udp_pkt_len, udp_frm_sze, eth_ifg)

    # Set MAC, IP Port addresses
    if myLpdFemClient.fem_10g_udp_common(x10g_0, 0):
        # Failed, exiting..
        sys.exit()
    if myLpdFemClient.fem_10g_udp_common(x10g_1, 1):
        # Failed, exiting..
        sys.exit()                
        
    myLpdFemClient.robs_udp_packet_header_10g(robs_udp_packet_hdr)

    #set up data generator 0
    ll_frm_gen_data_type=0

    myLpdFemClient.ll_frm_gen_setup(udp_frm_sze/4, ll_frm_gen_data_type)  # normal operation
    
    # length specifies nr of 64 bit words
    myLpdFemClient.frame_generator_set_up_10g(2, num_ll_frames+1)

    # Send data via 10g 
    if (enable_10g == 1):
        myLpdFemClient.clear_ll_monitor()
        print ""
        myLpdFemClient.read_ll_monitor()

        slowCtrlConfig = SlowCtrlParams( currentSlowCtrlDir + '/slow_control_config.xml', fromFile=True)
        slow_ctrl_data = slowCtrlConfig.encode()
        no_of_bits = 3911

        # fast data
        if asic_pseudo_random:
            # Yes,' fast_random_gaps.txt' really does reside within the "slow control" directory:
            [fast_cmd_data, no_of_words, no_of_nops] = myLpdFemClient.read_fast_cmd_file_jc_new( currentSlowCtrlDir + '/fast_random_gaps.txt', fast_cmd_reg_size)
        else:
            # Real ASIC data selected, load slow control configuration from file
            fileCmdSeq = LpdCommandSequenceParser( currentFastCmdDir + '/fast_readout_replacement_commands.xml', fromFile=True)
            fast_cmd_data = fileCmdSeq.encode() 
            
            no_of_words = fileCmdSeq.getTotalNumberWords()
            no_of_nops = fileCmdSeq.getTotalNumberNops()
                        
        # set up the fast command block
        if fast_ctrl_dynamic == 1:
            # new design with dynamic vetos
            myLpdFemClient.fem_fast_bram_setup(fast_cmd_data, no_of_words)
            myLpdFemClient.fem_fast_cmd_setup_new(no_of_words+no_of_nops)
        else:
            myLpdFemClient.fem_fast_cmd_setup(fast_cmd_data, no_of_words, fast_ctrl_dynamic)            

        # select slow control load mode  jac
        if setup_slow_control_bram == 1:                
            #set up the slow control IP block
            myLpdFemClient.fem_slow_ctrl_setup(slow_ctrl_data, no_of_bits)

        # load mode = 0 for common (2-tile system)    jac
        # load mode = 2 for daisy chain
        myLpdFemClient.select_slow_ctrl_load_mode(0, 0)

        # set up the ASIC RX IP block
        myLpdFemClient.fem_asic_rx_setup(mask_list, no_asic_cols+1, no_asic_cols_per_frm+1)
        
        # data source - self test
        myLpdFemClient.data_source_self_test(asic_rx_counting_data)

        # asic rx gain override
        myLpdFemClient.gain_override(asic_gain_override)

        # top level steering - ie:
        # turn fast & slow buffers on
        # asic serial out readback is from bot sp3 i/o
        # asic start readout delay wrt fast cmd
        myLpdFemClient.top_level_steering(asic_rx_start_delay)
        
        # select asic or llink gen as data source
        myLpdFemClient.fem_local_link_mux_setup(data_source_to_10g)

    
        #--------------------------------------------------------------------
        # send triggers to data generators
        
        if trigger_type is 'all':
            # start asic seq  = reset, slow, fast & asic rx
            print "You selected 'all'"
            myLpdFemClient.toggle_bits(0, 2)
        elif trigger_type is 'a':
            # trigger to local link frame gen 
            print "You selected 'a'"
            myLpdFemClient.toggle_bits(0, 1)
        elif trigger_type is 'b':
            # trigger the asic rx block
            print "You selected 'b'"
            myLpdFemClient.toggle_bits(3, 1)
        elif trigger_type is 's':
            # trigger just the slow contol IP block
            print "You selected 's'"
            myLpdFemClient.toggle_bits(7, 1)
        elif trigger_type is 'f':
            # trigger just the fast cmd block
            print "You selected 'f'"
            myLpdFemClient.toggle_bits(7, 2)
        elif trigger_type is 'x':
            # trigger fastand asic rx  (not slow)
            myLpdFemClient.toggle_bits(7, 2)
            myLpdFemClient.toggle_bits(3, 1)
        else:
            print "No case matching variable trigger_type = ", trigger_type
        #--------------------------------------------------------------------

        # Send data via 10g UDP block
        if enable_10g == 1:
            # Check local link frame statistics
            myLpdFemClient.read_ll_monitor()        


    # --------------------------------------------------------------------------- #
    #        START    
    # --------------------------------------------------------------------------- #
    
    ''' See jac's function: start_10g_link() ? '''


if __name__ == '__main__':
    pass