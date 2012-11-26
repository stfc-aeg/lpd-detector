'''
Created on 18 Apr 2012

@author: ckd27546
'''

# Import Python standard modules
import sys, os, string 
import socket
#from socket import gethostname

# Import Fem modules
#from FemClient import FemClient
from LpdFemClientLegacy import *  #LpdFemClientLegacy

# Import library for parsing XML fast command files
from LpdCommandSequence.LpdCommandSequenceParser import LpdCommandSequenceParser
from SlowCtrlParams import SlowCtrlParams

class FemAsicTest():

    # Dictionary of hostname -> 1g IP address
    one1gAddress = {'te7burntoak'  : '192.168.2.2',
                    'te7kiribati'  : '192.168.3.2',
                    'devgpu02'     : '192.168.3.2',}


    def set_10g_structs_variables_te2bank(self):
        """ Construct and return two dictionaries defining two network interfaces
        """
        
        x10g_0 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.7.2'),
                  'src_prt' : self.prt_addr_to_uint16('0000'),
                  # PC TARGET:
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.0.13'),
                  'dst_prt' : self.prt_addr_to_uint16('0000')}
        
        x10g_1 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-09'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.0.100'),
                  'src_prt' : self.prt_addr_to_uint16('0000'),
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),  # in vhdl 10g 
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.0.13'),
                  'dst_prt' : self.prt_addr_to_uint16('0000')}
        return x10g_0, x10g_1

    def set_10g_structs_variables_te7burntoak(self):
        """ Construct and return two dictionaries defining two network interfaces
        """
        
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
    
        return x10g_0, x10g_1
    
    def mac_addr_to_uint64(self, mac_addr_str):
        """ convert hex MAC address 'u-v-w-x-y-z' string to integer """
        # Convert MAC address into list of 6 elements (and removing the - characters)
        mac_addr_list = mac_addr_str.split('-')   
        # Convert hexadecimal values into the decimals
        mac_addr_list = [int(val, 16) for val in mac_addr_list]
        # combine the 6 elements into a single 48 bit MAC value
        mac_address = 0
        mac_address = (mac_address | mac_addr_list[0])
        mac_address = (mac_address | (mac_addr_list[1] << 8))
        mac_address = (mac_address | (mac_addr_list[2] << 16))
        mac_address = (mac_address | (mac_addr_list[3] << 24))
        mac_address = (mac_address | (mac_addr_list[4] << 32))
        mac_address = (mac_address | (mac_addr_list[5] << 40))
        return mac_address
    
    def ip_addr_to_uint32(self, ip_addr_str):
        # Convert IP address into list of 4 elements (and removing the - characters)
        ip_addr_list = ip_addr_str.split('.') 
        # Convert hexadecimal values into the decimals
        ip_addr_list = [int(val) for val in ip_addr_list]    
        # combine the 4 elements into a single 32 bit value 
        ip_address = 0
        ip_address = (ip_address | ip_addr_list[0])
        ip_address = (ip_address | (ip_addr_list[1] << 8))
        ip_address = (ip_address | (ip_addr_list[2] << 16))
        ip_address = (ip_address | (ip_addr_list[3] << 24))
        return ip_address 
    
    def prt_addr_to_uint16(self, prt_addr_str):
        #convert hex prt string to integer
        return int(prt_addr_str)
        
        
    # --------------------------------------------------------------------------- #
    
    def execute_tests(self):

        # Determine name of current machine
        fullDomainName = socket.gethostname()
        # Only need hostname, not domain part
        hostName = fullDomainName.partition('.')[0]
        # Locate corresponding IP address
        femHost = FemAsicTest.one1gAddress[hostName]
#        print "Debug info: machine = '%s', IP = '%s'." % (hostName, femHost)
        
        
#        femHost = '192.168.2.2'    # Burntoak
        #femHost = '192.168.3.2'     # Kiribati
        femPort = 6969
        
        print "~+~+~+~+~+~+~+~+~+~+~+~+~ Connecting to host: %s, port: %i ~+~+~+~+~+~+~+~+~+~+~+~+~" % (femHost, femPort)
        
        
        try:
            myLpdFemClient = LpdFemClientLegacy((femHost, femPort), timeout=10)
        except FemClientError as errString:
            print "Error: FEM connection failed:", errString
            sys.exit(1)
        
       
        # -------------------------------------------------
        # Enable readback of every rdmaWrite function call
        myLpdFemClient.set_rdma_read_back(True)
        # -------------------------------------------------
       
        # enable sending reset to both ppc processors if = 1
        send_ppc_reset = 1
        
        # for new fast controls with optional dynamic vetos if = 1
        fast_ctrl_dynamic = 1
        
        # (Skip loading slow control block)
        # 0 = disable, 1 = enable filling slow control bram
        # ON Cold Start:
        setup_slow_control_bram = 1
        # Once ASICs programmed:
#        setup_slow_control_bram = 0
        
        # send data via 10g udp block
        enable_10g = 1
        
        # Read 10g data either by packet or frames
        readout_mode = 'frame'
        
        # choose data source to 10g block 
        # 0 = llink frame generator
        # 1 = direct from asic  
        # 2 = PPC
        data_source_to_10g = 1
        
        # 1 = dummy counting data from asic rx block
        # 0 = real data from asic
        asic_rx_counting_data = 0
        
        # 1 = single asic module
        # 2 = 2-Tile box
        asic_module_type = 2
        
        # for pseudo random frames from asic  (must also set asic_rx_counting_data = 0)
        asic_pseudo_random = 0
        
        # steer loading of brams for asic slow and fast configuration data
        # if data_source_to_10g is llink frame generator (0) or PPC (2), set to 0
        if (data_source_to_10g == 0 or data_source_to_10g == 2):
            load_asic_config_brams = 0 
        else:
            # data source is 'direct from asic'; is it real or dummy data? 
            if (asic_rx_counting_data == 0):
                # real data; want to load slow control
                load_asic_config_brams = 1  
            else: # skip brams if using asic rx internal data generator
                load_asic_config_brams = 0
        
        # Nr (100 MHz) clock periods delay before start of asic data rx
        # tuned for various data runs to capture 1st data bit in stream
        # will be replaced later by signal from asic fast block to asic rx
        if asic_pseudo_random:
            asic_rx_start_delay = 61    # 58
        else:
            # real data
            if asic_module_type == 2:
                # 2-Tile box selected
                asic_rx_start_delay = 1361  #1360
            else:
                # single asic module
                # 20/09/2012: Presume this should be 1363?
                asic_rx_start_delay = 1362  #uint32(1362)
        
        
        num_ll_frames = 1  # nr of local link frames to generate
        
        # trigger_type, 'a'=trigger local link frame generator,
        # 'all'=start asic seq, 'b'=trigger of asic rx block, 
        # 's'=trigger only the slow control IP block, 'f'=trigger the fast cmd block,
        # 'x'=trigger fast and asic rx (not slow)
        
        # if data source is 'llink frame generator' or 'PPC'
        if (data_source_to_10g == 0 or data_source_to_10g == 2):
            trigger_type = 'a'
        else:
            # On cold start:
            trigger_type = 'all'    # trigger FEM to load slow ctrl into ASICs    (Keep setup_slow_control_bram = 1)
            # Once ASICs configured once:
#            trigger_type = 'x'      # skip loading slow ctrl into ASICs - set setup_slow_control_bram = 0 in addition
        
        
        #--------------------------------------------------------------------
        # Resetting the PPC start the DMA test
        # need to get the timing right or add handshaking
                
        if send_ppc_reset == 1:
            # Resets dma engines
            myLpdFemClient.toggle_bits(9, 1)
        
        theDelay = 1
        print "Waiting %s seconds.." % theDelay
        time.sleep(theDelay)
        print "Finished waiting %s seconds!" % theDelay
        
        #--------------------------------------------------------------------
        # Options for configuring LPD ASICs 
        
        # Asic fast cmds 20 or 22 bits format
        fast_cmd_reg_size = 22
        
        # Asic Rx 128 bit channel enable masks
        
        # mask_list - which asics to be enabled (1) or disabled (0)
        mask_list = [0, 0, 0, 0]
        if asic_rx_counting_data == 1:
            # enable all channels for dummy data from asic rx    
            mask_list[0] = 0xffffffff
            mask_list[1] = 0xffffffff
            mask_list[2] = 0xffffffff
            mask_list[3] = 0xffffffff
        else: 
            # Enable only relevant channel for single ASIC test module
            if asic_module_type == 1: 
                # Enable 2 channel for single ASIC test module
                mask_list[0] = 0x00000001
            elif asic_module_type == 2: 
                #Enable 16 channels for single ASIC test module
                mask_list[0] = 0x00ff0000
                mask_list[1] = 0x00000000
                mask_list[2] = 0x0000ff00
                mask_list[3] = 0x00000000
            else:
                # Enable all channels for supermodule
                mask_list[0] = 0xffffffff
                mask_list[1] = 0xffffffff
                mask_list[2] = 0xffffffff
                mask_list[3] = 0xffffffff
        
        
        #set asic receiver readout size & frame allocation
        # valid settings with 16K FIFO
        # (more than 3 trigger overflows when going direct to 10 G link)
        #  2,2 = 3 triggers with 3 triggers per ll frame ; ie 1 frame
        #  1,1 = 2 triggers with 2 triggers per ll frame ; ie 1 frame
        # see labbook #19 p191  jac
        no_asic_cols         = 3   # no_asic_cols = nr triggers or images per train
        no_asic_cols_per_frm = 3   # no images per local link frame
#        no_asic_cols         = 0   # set to zero means 1 image per trigger (because +1 added wherever no_asic_cols used)
#        no_asic_cols_per_frm = 0   # set to zero means 1 image per trigger (because +1 added wherever no_asic_cols_per_frm used)

        
        
        #
        print "---> no_asic_cols, no_asic_cols_per_frm: ", no_asic_cols, no_asic_cols_per_frm, " <-----"
        #--------------------------------------------------------------------
        
        # Set up 10G UDP packet length, number & frame size
        eth_ifg = 0x00001000  # Ethernet Inter Frame Gap
        udp_pkt_len = 8000
        udp_pkt_num = 1
        
        # udp frame size in bytes should match data to be transferred
        # no_asic_cols = nr triggers ; Nb min nr triggers = 2  ?
        # 512 pixels per asic
        # 128 asics per fem
        # 2 bytes per pixel (after gain selection)
        # + 64 byte for asic rx header and trailer (each 8 x 32 bits) but removed by ll_rmv )
        udp_frm_sze = (no_asic_cols+1) * 512 * 128 * 2 + 0  # header and trailer removed by ll_rmv
        udp_in_buf_size = 2048*1024
        
        #  overrides to asic algorithm gain selection
        #  bits
        #  0000  normal gain selection     0
        #  1000  force select x100         8
        #  1001  force select x10          9
        #  1011  force select x1          11
        #  1111  force error condition ?  15
#        asic_gain_override = 0
        asic_gain_override = 8
        
        # rob's udp packet headers : 0 to disable ; set bit 2 to enable, ie = 4 (decimal = 100b, binary) 
        # Disable for Matlab ; Enable for Python
        # Nb to enable need correct bit pattern
        # Nb this is not the same as asic rx header; Utilised by robs_udp_packet_header_10g()
        # Won't generate header
        #robs_udp_packet_hdr = 0
        # Generate header with 10g data
        robs_udp_packet_hdr = 4

        # if data source is 'llink frame generator'        
        if (data_source_to_10g == 0):
            udp_pkt_len = 8000  #1000
            udp_pkt_num = 1
#            udp_frm_sze = 1024*1024*8
            udp_frm_sze = 262144
            udp_in_buf_size =1024*1024*1024*1
            
            # if data source is 'PPC':
        elif (data_source_to_10g == 2):
            # Default to use same values as asic rx
            pass
        
        # Setup the UDP IP blocks sending data via 10g udp block
        if (enable_10g == 1):
            
            # Which PC is running the script?
            thisHost = socket.gethostname()
            # Remove domain name from hostname
            hostname = thisHost.split(".", 1)[0]
            # Construct function name to be called from hostname
            print "Use excaliburPowerGuiMain.py and getattr() to construct and call the appropriate .set_10g_.dot() function"
            print "\nThat it, exiting for now..\n"
            
            sys.exit()
            # Set up the UDP IP blocks
            x10g_0, x10g_1 = self.set_10g_structs_variables_te7burntoak()
            
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
        
        # length specifies nr of 64 bit words
        myLpdFemClient.ll_frm_gen_setup(udp_frm_sze/4, ll_frm_gen_data_type)  # normal operation
        
        # length specifies nr of 64 bit words
        ##rdma_write(    data_gen_0+2, num_ll_frames+1,'rw','DATA GEN Nr Frames');
        myLpdFemClient.frame_generator_set_up_10g(2, num_ll_frames+1)
        
        print ""
        # Send data via 10g 
        if (enable_10g == 1):
            myLpdFemClient.clear_ll_monitor()
            print ""
            myLpdFemClient.read_ll_monitor()
            print ""
        
        
        #--------------------------------------------------------------------
        # configure the ASICs
        
        # Obtain current working directory for the slow control
        # The two folders in question are related like this:
        #    workspace/LpdFemTests
        #    workspace/LpdCommandSequence
        currentSlowCtrlDir = os.getcwd()
        # Is this script executed from the folder containing it or its parent folder?
        if currentSlowCtrlDir.find("LpdFemTests") == -1:
            # Script was executed from parent folder
            
            # Because we are in the parent folder and not in the subfolder,
            # the fast control path is straightforward to construct from slow control's:
            currentFastCmdDir = currentSlowCtrlDir
            # and then append "/LpdCommandSequence"
            currentFastCmdDir += "/LpdCommandSequence"
            
            # Construct slow control path by appending '/LpdFemTests'
            currentSlowCtrlDir += "/LpdFemTests" 
        else:
            # fem_asic_test executed from the same folder so we can use the parent folder of currentSlowCtrlDir 
            # however, fast command reside in a different folder:
            currentFastCmdDir = currentSlowCtrlDir.replace("/LpdFemTests", "") + "/LpdCommandSequence"
            
#        print currentFastCmdDir, "\n", currentSlowCtrlDir
        
        # if the data source is 'direct from asic'
        if data_source_to_10g == 1:
            
            # Load slow control and potentially fast control commands?
            if load_asic_config_brams == 1:  # only load brams if sending data from asics
                # slow data
#                slow_ctrl_data, no_of_bits = myLpdFemClient.read_slow_ctrl_file( currentSlowCtrlDir + '/SlowControlDefault-1A.txt')
                
                slowCtrlConfig = SlowCtrlParams( currentSlowCtrlDir + '/slow_control_config.xml', fromFile=True)
                slow_ctrl_data = slowCtrlConfig.encode()
                no_of_bits = 3911
#                sys.exit()
                
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
        
        # check contents of slow control read back BRAM
        # not working yet
        #rdma_block_read(slow_ctr_2, 4, 'Read Back Slow Ctrl RAM');
        
        
        # if data source is PPC, allow time to trigger ppc dma transfer in sdk app
        if data_source_to_10g == 2:
            print " paused waiting 2 seconds allowing time to trigger ppc dma transfer in sdk app"
            time.sleep(2)
        
        
        print " ...continuing"

        #--------------------------------------------------------------------
        # receive the image data from 10g link
        
        
        # check how much data has arrived - Function call does nothing, redundant
        myLpdFemClient.check_how_much_data_arrived(udp_frm_sze)
        
        
        # create an array of uint32 to hold the data frame
        data_size = udp_frm_sze/2
        dudp = [0] * data_size
        packet_size = udp_pkt_len/2
        
        print "Receiving the image data from 10g link.."
        
        # Neither of the two functions actually do anything
        if  readout_mode is "packet":
            # Currently redundant:
            dudp = myLpdFemClient.recv_image_data_as_packet(udp_pkt_num, dudp, packet_size)
        elif readout_mode is "frame":
            # Currently redundant:
            dudp = myLpdFemClient.recv_image_data_as_frame(dudp)            
        else:
            pass
        
        
        print ""
        
        # Send data via 10g UDP block
        if enable_10g == 1:
            # Check local link frame statistics
            myLpdFemClient.read_ll_monitor()    
        
        # Close down Fem connection
        try:
            myLpdFemClient.close()
        except Exception as errStr:
            print "Unable to close Fem connection: ", errStr
        else:
            print "Closed Fem connection."
            
        #--------------------------------------------------------------------
        # process the image data
        
        # 1st arg = 31 is to skip over header
        # changed skip to 8 when running with ppc dma 
        # 2nd arg is image/trigger nr starting at 1
        
        #if (data_source_to_10g == 2):
        #    image_data_raw = myLpdFemClient.extract_asic_data(1, 1, dudp)
        #else:
        #    image_data_raw = myLpdFemClient.extract_asic_data(8, 1, dudp)
        
        
        # rotate to match ivan's display (isn't matlab clever :) )
        #image_data = rot90(image_data_raw);                        # Redundant?
        
        """                        Plot Data - See Python script: receiveTengTest.py             """
        #frame_nr = 1;
        ## plot the data from the asic
        #colormap gray;
        #h = imagesc(image_data);
        #
        #colorbar('location', 'eastoutside');
        #title(['frame ',num2str(frame_nr)]);

if __name__ == "__main__":
    femAsicTest = FemAsicTest()
    femAsicTest.execute_tests()
