'''
Created on 18 Apr 2012

@author: ckd27546

mods by jac36
to be compatible with latest 10g libs as used by Train builder
'''

# Import Python standard modules
import sys
import socket, time

import pprint


# Import Fem modules
#from FemClient import FemClient
from LpdFemClient import *  #LpdFemClient
#TODO: Why all of a sudden need to include these two imports: ???
from LpdFemClient.LpdFemClient import LpdFemClient, FemClientError

# Import library for parsing XML fast command files
from LpdCommandSequence.LpdAsicCommandSequence import LpdAsicCommandSequence

class FemAsicTest():

    
    def set_10g_structs_variables(self):
 
        run_params = { 
            'detector_type' : # "fem_standalone", # FEM Standalone 
                        # "single_asic_module",# Single ASIC test module
                         "two_tile_module", # 2-Tile module
                        # "supermodule", # Supermodule
           
            'run_type' :   "asic_data_via_ppc",  # ASIC data (via PPC) [Standard Operation] 
                      # "asic_data_direct",   # ASIC data direct from Rx block
                      # "ll_data_gen",   # LL Data Gen  (simulated data)
                      # "ppc_data_direct", #  preprogrammed data DDR2 (simulated data)

#====== params for run type = "asic_data_via_ppc" or "asic_data_direct"

            'asic_data_type' :   "asic_sensor", # Asic sensor data [Standard Operation Real Data]
                       # "asicrx_counting", # Asic Rx Block internally generated counting data (simulated data)
                        # "asic_pseudo_random", # Asic Pseudo random data (test data from asic)

             # if asic clock is coming from on board FEM 100 MHz Osc
            'asic_local_clock_freq' : 1, # 0 = no scaling = 100 MHz
                                        # 1 = scaled down clock, usually = 10 MHz (set by dcm params)

            'asic_fast_dynamic' : 1, # 1 = New dynamic commands

            'asic_slow_load_mode' : 0, # 0 = parallel load
                                        # 1 = daisy chain
                                        
            'asic_nr_images' : 1, # nr of images to capture per train
            'asic_nr_images_per_frame' : 1, # nr of images put in each local link frame output by data rx

            'asicrx_capture_asic_header_TEST_ONLY' : 0,  # = 0 (NORMAL OPERATION) ignore asic header bits 
                                               # = 1 (TEST ONLY) readout asic header bits to check timing alignment. This will mess up data capture.

            'asicrx_gain_selection' : 8,  # gain algorithm selection
                                    #  0000  normal gain selection     0
                                    #  1000  force select x100         8
                                    #  1001  force select x10          9
                                    #  1011  force select x1          11
                                    #  1111  force error condition ?  15

            'asicrx_invert_data' : 0,  # 1 = invert adc output data (by subtracting value from $FFF)

            'asicrx_start_from_fast_strobe' : 1,  # 1 = Start asic rx data capture using strobe derived from fast command file
                                                    # 0 = Start asic rx data capture using fixed delay value 
#======== params for general steering 
            'ppc_mode' : 0,   # 0 = Single Train Shot with PPC reset 
                      # 1 = Continuous readout (not working yet)

            'ppc_reset_delay_secs' : 5,   # wait after resetting ppc 

            'num_cycles'  : 1, # repeat the test n times
              
            'playback' : 0, # 1 for playback rx (to load files into ddr2 memory)
            'debug_level' : 2,    # higher values more print out

#======== params for GbE Server controls/monitor

#              'GbE_Server_Host' : '192.168.3.2',     # ip address for 1 GbE fem controls
#              'GbE_Server_Port' : 6969,   # udp port nr for 1 GbE fem controls (not to be confused with port nr for 10g links)
 
#======== params for 10G data links

              '10g_farm_mode' : 1,   # 3 for farm mode with nic lists 
                      # 2 for farm mode with fixed ip host and multiple ports
                      # 1 for legacy non farm mode (only 1 ip host and port per link)  
  
              'eth_ifg' : 0x000,   # ethernet inter frame gap  ; ensure receiving 10G NIC parameters have been set accordingly
              'udp_pkt_len' : 8000, # default udp packet length in bytes (can be overriden in asic runs)
              'clear_10g_lut' : 0   # 1 to clear 10g lut tables before start
#========
                    }  
     
        # look up table to match MAC addresses with IP for host NIC
        global mac_ip_lut
        mac_ip_lut = { '192.168.2.1' : '00-07-43-11-97-90',   # redbridge eth2
                    '192.168.3.1' : '00-07-43-11-97-98',   # redbridge eth3
                    '192.168.6.1' : '00-07-43-10-61-80',   # burntoak eth6
                    '192.168.7.1' : '00-07-43-10-61-88',   # burntoak eth7
                    '192.168.8.1' : '00-07-43-10-61-90',   # burntoak eth8
                    '192.168.9.1' : '00-07-43-10-61-98'   # burntoak eth9
            }  
 
        """ Construct and return two dictionaries defining two network interfaces
        """
#following for redbridge        
#        x10g_0 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'), # fpga
#                  'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),
#                  'fpga_prt' : self.prt_addr_to_uint16('0'),
#                  'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'), # redbridge eth2
#                  'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),
#                  'nic_prt' : self.prt_addr_to_uint16('61649'),
#                  'enable'  : 1,    # enable this link
#                  'link_nr' : 1,   # link number
#                  'data_gen' : 1, # data generator  1 = DataGen 2 = PPC DDR2  (used if run params data source is non asic)  
#                  'data_format' : 0, # data format type  (0 for counting data)  
#                  'frame_len'  : 0x10000, #  0xFFFFF0,   #  0x800,    # frame len in bytes
#                  'num_frames' : 1,    # number of frames to send in each cycle
#                  'num_prts' : 2, # number of ports to loop over before repeating
#                  'delay' : 0,    # delay offset wrt previous link in secs
##                       'nic_list' : [ '61649@192.168.3.1', '61650@192.168.3.1', '61652@192.168.3.1', '61654@192.168.3.1' ]
##                        'nic_list' : [ '61649@192.168.3.1', '61650@192.168.3.1' ]
##                 'nic_list' : [ '61649@192.168.3.1', '61649@192.168.3.1' ]
#                 'nic_list' : [ '61649@192.168.3.1' ]
#                    }

# following for te7burntoak
        x10g_0 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'), # fpga
                  'fpga_ip'  : self.ip_addr_to_uint32('192.168.7.2'),
                  'fpga_prt' : self.prt_addr_to_uint16('0'),
                  'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-88'), # burntoak eth6
                  'nic_ip'  : self.ip_addr_to_uint32('192.168.7.1'),
                  'nic_prt' : self.prt_addr_to_uint16('61649'),
                  'enable'  : 1,    # enable this link
                  'link_nr' : 1,   # link number
                  'data_gen' : 1, # data generator  1 = DataGen 2 = PPC DDR2  (used if run params data source is non asic)  
                  'data_format' : 0, # data format type  (0 for counting data)  
                  'frame_len'  : 0x10000, #  0xFFFFF0,   #  0x800,    # frame len in bytes
                  'num_frames' : 1,    # number of frames to send in each cycle
                  'num_prts' : 2, # number of ports to loop over before repeating
                  'delay' : 0,    # delay offset wrt previous link in secs
#                       'nic_list' : [ '61649@192.168.3.1', '61650@192.168.3.1', '61652@192.168.3.1', '61654@192.168.3.1' ]
#                        'nic_list' : [ '61649@192.168.3.1', '61650@192.168.3.1' ]
#                 'nic_list' : [ '61649@192.168.3.1', '61649@192.168.3.1' ]
                 'nic_list' : [ '61649@192.168.3.1' ]
                    }
         
# 2nd link is not used on FEM       
#        x10g_1 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),
#                  'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),
#                  'fpga_prt' : self.prt_addr_to_uint16('0000'),
#                  'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),  # redbridge eth3
#                  'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),
#                  'nic_prt' : self.prt_addr_to_uint16('61649'),
#                  'enable'  : 0,    # enable this link
#                  'link_nr' : 1,   # link number
#                  'data_format' : 0, # data format type  (0 for counting data)  
#                  'frame_len'  : 1024,    # frame len in bytes
#                  'num_frames' : 1    # number of frames to send in each cycle
#                    }
 
#        x10g_params = [ x10g_0, x10g_1 ]

        return run_params, x10g_0     # FEM is only using 1 link

    def mac_addr_to_uint64(self, mac_addr_str):
        #convert hex MAC address 'u-v-w-x-y-z' string to integer
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
  
  # nb command line ip and port are ignored
      
      #  femHost = '192.168.2.2'  # 2-tile fem
        femHost = '192.168.2.2' # standalone fem
        femPort = 6969


        global asic_rx_start_pseudo_random    
        global asic_rx_start_2tile  
        global asic_rx_start_single_asic 
        global asic_rx_hdr_bits   # subtract from values above to capture asic headers

        global fast_cmd_reg_size
   
        global pp

  # measured timing parameters 
  # delay between start signal to fast command output and strobe to asic rx for data capture
  # to do tune to Fast Command Readout strobe

        # old fixed delay offsets
#        asic_rx_start_pseudo_random = 61    
#        asic_rx_start_2tile = 1349 
#        asic_rx_start_single_asic = 1362 


        # new offset with fast command strobe
        #asic_rx_start_pseudo_random = 61    
        asic_rx_start_2tile = 808 # 809   # timed in 26/11/12
        #asic_rx_start_2tile_fast_strobe = 812

        asic_rx_start_supermodule = asic_rx_start_2tile  # assumed same
        
        asic_rx_hdr_bits = 12   # subtract from values above to capture asic serial headers ($AAA)

        # Asic fast cmds 20 or 22 bits format   (only 22 bit commands work at present)
        fast_cmd_reg_size = 22

        print "=======================================================================" 
  
        pp = pprint.PrettyPrinter(indent=4)
 
        run_params, x10g_0 = self.set_10g_structs_variables()
 
        if run_params['debug_level'] > 0:
                pp.pprint(run_params)
 
        #femHost = run_params['GbE_Server_Host']
        #femPort = run_params['GbE_Server_Port']
     
        try:
            myLpdFemClient = LpdFemClient((femHost, femPort), timeout=10)
        except FemClientError as errString:
            print "Error: FEM connection failed (check GbE server is running):", errString
            sys.exit(1)
                 
        #self.dump_registers(run_params, myLpdFemClient)            

#        if run_params['run_type'] == 0:
#          self.reset_ppc(run_params, myLpdFemClient)         

        myLpdFemClient.init_ppc_bram(myLpdFemClient.bram_ppc1, 0xBEEFFACE)

        myLpdFemClient.toggle_bits(myLpdFemClient.fem_ctrl_0+9, 8)  # async reset to v5 top level

        myLpdFemClient.clear_ll_monitor()

        # set up clocks and connections between modules
        self.config_top_level(run_params, myLpdFemClient)         
        
        # set up the 10g link params
        self.config_10g_link(run_params, x10g_0, myLpdFemClient)         

        if (run_params['run_type'] == "asic_data_via_ppc") or (run_params['run_type'] == "ppc_data_direct"):  # runs with ppc
          self.reset_ppc(run_params, myLpdFemClient)         

        # set up data gen
        self.config_data_gen(run_params, x10g_0, myLpdFemClient)         

        # set up asic blocks
        if (run_params['run_type'] == "asic_data_via_ppc") or (run_params['run_type'] == "asic_data_direct"):  # data from asic
          self.config_asic_modules(run_params, myLpdFemClient) 
                  
          self.send_trigger(run_params, myLpdFemClient) 

        else: # data from datagen or ppc ddr2 
                    
          num_cycles = run_params['num_cycles']
          print "Starting Run of %d cycles" % run_params['num_cycles']
          for i in range (1, num_cycles+1):
#              print "Starting Run Cycle Nr %d" % i
              self.start_10g_link(run_params, x10g_0, myLpdFemClient)  
#              self.send_trigger(run_params, myLpdFemClient) 

          if x10g_0['data_gen'] == 2:
            myLpdFemClient.final_dma_tx(myLpdFemClient.bram_ppc1)  

        self.dump_registers(run_params, myLpdFemClient)            
        myLpdFemClient.read_ll_monitor()

        # Close down Fem connection
        try:
            myLpdFemClient.close()
        except Exception as errStr:
            print "Unable to close Fem connection: ", errStr
        else:
            print "Closed Fem connection."
            
        return 0


#================================================

    def dump_registers(self, run_params, myClient):
        """ dump registers
             """
        print "Dump of FEM Registers : TOP LEVEL CTRL" 
        myClient.dump_regs_hex(myClient.fem_ctrl_0, 18)        

        print "Dump of FEM Registers : PPC1 BRAM" 
        myClient.dump_regs_hex(myClient.bram_ppc1, 16) 
        
        print "Dump of FEM Registers : XAUI link 1" 
        myClient.dump_regs_hex(myClient.udp_10g_0, 16) 

        print "Dump of FEM Registers : DATA GEN on link 1" 
        myClient.dump_regs_hex(myClient.data_gen_0, 16) 

        print "Dump of FEM Registers : ASIC RX" 
        myClient.dump_regs_hex(myClient.asic_srx_0, 16) 

        print "Dump of FEM Registers : ASIC FAST CTRL" 
        myClient.dump_regs_hex(myClient.fast_cmd_0, 16) 

        print "Dump of FEM Registers : ASIC FAST BRAM" 
        myClient.dump_regs_hex(myClient.fast_cmd_1, 16) 

        print "Dump of FEM Registers : ASIC SLOW CTRL" 
        myClient.dump_regs_hex(myClient.slow_ctr_0, 16) 

        print "Dump of FEM Registers : ASIC SLOW BRAM" 
        myClient.dump_regs_hex(myClient.slow_ctr_1, 200) 
                    
        return 0

#-------------------------------------------------------------------------------------    
    def config_10g_link(self, run_params, x10g, myClient):
        """ configure 10g link
             """
               
        if x10g['enable'] == 1:
            print "Configure 10G link nr", x10g['link_nr']
            
#            if run_params['debug_level'] > 0:
#                pp.pprint(x10g)
                        
            x10g_base = myClient.udp_10g_0
            data_gen_base = myClient.data_gen_0
            ppc_bram_base = myClient.bram_ppc1
           
            udp_pkt_len = run_params['udp_pkt_len']
            udp_frm_sze = x10g['frame_len']

            eth_ifg = run_params['eth_ifg']
            enable_udp_packet_hdr = 4;  # enabled for python = 4  
            
            # legacy non farm mode. (farm mode = 1)
            myClient.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            myClient.setup_10g_udp_net_block(x10g_base, x10g)    
            myClient.setup_10g_packet_header(x10g_base, enable_udp_packet_hdr)

            myClient.setup_10g_rx_filter(x10g_base) # accepts any udp packets

            myClient.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut   
                                 
#            print "Dump of Farm Mode LUT for xaui for Link %d" % x10g['link_nr']
#            myClient.dump_regs_hex(x10g_base+0x10000, 16) 
 
            print "Setting up Farm Mode LUT. May take several seconds... "                       
            if run_params['10g_farm_mode'] == 2:
                myClient.x10g_net_lut_setup(x10g_base, x10g) 
                myClient.x10g_set_farm_mode(x10g_base, 1)
            elif run_params['10g_farm_mode'] == 3:      
                myClient.x10g_net_lut_setup_from_list(x10g_base, x10g, self, mac_ip_lut)  
                myClient.x10g_set_farm_mode(x10g_base, 1)                         
            else: 
                print "Not in Farm Mode."              
                myClient.x10g_set_farm_mode(x10g_base, 0)

            if run_params['debug_level'] > 3:                
                print "Dump of Farm Mode LUT for xaui for Link %d" % x10g['link_nr']
                myClient.dump_regs_hex(x10g_base+0x10000, 16) 
                myClient.dump_regs_hex(x10g_base+0x100f0, 16)                               
                myClient.dump_regs_hex(x10g_base+0x10100, 16)
                myClient.dump_regs_hex(x10g_base+0x101f0, 16)  
                myClient.dump_regs_hex(x10g_base+0x10200, 16)
                myClient.dump_regs_hex(x10g_base+0x103f0, 16)
                    
            if run_params['debug_level'] > 1:
                print "Dump of regs for xaui for Link %d" % x10g['link_nr']
                myClient.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                myClient.dump_regs_hex(data_gen_base, 16)
  
#            if (run_params['run_type'] == 0) or (run_params['run_type'] == 3):   # data via ppc
#                myClient.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 
#            else:
#                myClient.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut 

        
#            if x10g['data_gen'] == 2:   # data source is ppc
            if (run_params['run_type'] == "asic_data_via_ppc") or (run_params['run_type'] == "ppc_data_direct"):  # data with PPC ll header
                myClient.setup_ppc_bram(ppc_bram_base, x10g['frame_len']) 
                myClient.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 

                # reset ppc after bram has been set up... moved reset to top level
#                self.reset_ppc(run_params, myClient)
                 
            else:                       # data source is data gen               
                myClient.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut   
             
        return 0

#-------------------------------------------------------------------------------------    
    def config_data_gen(self, run_params, x10g, myClient):
        """ configure data generator
             """                        
        data_gen_base = myClient.data_gen_0
                
        # final param to enable data gen headers for farm mode
        myClient.setup_ll_frm_gen(data_gen_base, x10g['frame_len']/8, x10g['data_format'], x10g['num_frames']-1, 1)  
        
        myClient.override_header_ll_frm_gen(data_gen_base, 0, 0)  # default is not to override index nr in header
                     
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_modules(self, run_params, myClient):
        """ configure asic modules
             """                        

        self.config_asic_slow(run_params, myClient)         
        self.config_asic_fast(run_params, myClient)         
        self.config_asic_datarx(run_params, myClient)         
             
        print "ENABLE asic Tristate output buffers"
        myClient.rdmaWrite(myClient.fem_ctrl_0+5, 0)
                             
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_slow(self, run_params, myClient):
        """ configure asic slow control parameters
             """                                        
        slow_ctrl_data, no_of_bits = myClient.read_slow_ctrl_file('SlowControlDefault-1A.txt')
  
        load_mode = run_params['asic_slow_load_mode']                
                                               
        # load in BRAM 
        myClient.fem_slow_ctrl_setup(myClient.slow_ctr_0, myClient.slow_ctr_1, slow_ctrl_data, no_of_bits, load_mode)

# To Do Fix readback
#        print "asic serial out readback is from bot sp3 i/o"
#        self.rdmaWrite(myClient.fem_ctrl_0+2, 1)
                     
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_fast(self, run_params, myClient):
        """ configure asic fast command module
             """                        
        if run_params['asic_data_type'] == "asic_pseudo_random":
#                    [fast_cmd_data, no_of_words, no_of_nops] = myLpdFemClient.read_fast_cmd_file_jc_new('/u/ckd27546/workspace/lpd/src/LpdFemTests/fast_random_gaps.txt',fast_cmd_reg_size)
            [fast_cmd_data, no_of_words, no_of_nops] = myClient.read_fast_cmd_file_jc_new('fast_random_gaps.txt',fast_cmd_reg_size)
        else:
            # [fast_cmd_data, no_of_words, no_of_nops] = myLpdFemClient.read_fast_cmd_file_jc_new('/u/ckd27546/workspace/lpd/src/LpdFemTests/fast_readout_4f_gaps.txt',fast_cmd_reg_size)
            [fast_cmd_data, no_of_words, no_of_nops] = myClient.read_fast_cmd_file_jc_new('fast_readout_4f_gaps.txt',fast_cmd_reg_size)
             
            # ''' XML implementation '''
# #                    fileCmdSeq = LpdAsicCommandSequence('/u/ckd27546/workspace/lpd/src/LpdCommandSequence/fast_readout_replacement_commands.xml', fromFile=True)
            # fileCmdSeq = LpdAsicCommandSequence('../LpdCommandSequence/fast_readout_replacement_commands.xml', fromFile=True)
            # fast_cmd_data = fileCmdSeq.encode()
            
            # no_of_words = fileCmdSeq.getTotalNumberWords()
            # no_of_nops = fileCmdSeq.getTotalNumberNops()
                        

        #set up the fast command block
        if run_params['asic_fast_dynamic'] == 1:   # new design with dynamic vetos
            myClient.fem_fast_bram_setup(myClient.fast_cmd_1, fast_cmd_data, no_of_words)
            myClient.fem_fast_cmd_setup_new(myClient.fast_cmd_0, no_of_words+no_of_nops)
        else:
              myClient.fem_fast_cmd_setup(myClient.fast_cmd_0, myClient.fast_cmd_1, fast_cmd_data, no_of_words, fast_ctrl_dynamic)            
               
                     
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_datarx(self, run_params, myClient):
        """ configure asic data rx module
             """                        
        # Asic Rx 128 bit channel enable masks
        
        # Use list instead of array
        mask_list = [0, 0, 0, 0]
        if run_params['asic_data_type'] == "asicrx_counting":    # enable all channels for dummy data from asic rx    
            mask_list[0] = 0xffffffff
            mask_list[1] = 0xffffffff
            mask_list[2] = 0xffffffff
            mask_list[3] = 0xffffffff
        else: # Enable only relevant channel for single ASIC test module
            if run_params['detector_type'] == "single_asic_module": # Enable 2 channel for single ASIC test module
                mask_list[0] = 0x00000001
            elif run_params['detector_type'] == "two_tile_module": #Enable 16 channels for 2-Tile
# new mapping ?
                mask_list[0] = 0x0f0000f0
                mask_list[1] = 0x0f0000f0
                mask_list[2] = 0x00000000
                mask_list[3] = 0x00000000
# old mapping
#                mask_list[0] = 0x00ff0000
#                mask_list[1] = 0x00000000
#                mask_list[2] = 0x0000ff00
#                mask_list[3] = 0x00000000
# take all channels whilst testing
#                mask_list[0] = 0xffffffff
#                mask_list[1] = 0xffffffff
#                mask_list[2] = 0xffffffff
#                mask_list[3] = 0xffffffff
            else:       # Enable all channels for supermodule
                mask_list[0] = 0xffffffff
                mask_list[1] = 0xffffffff
                mask_list[2] = 0xffffffff
                mask_list[3] = 0xffffffff

        no_asic_cols = run_params['asic_nr_images'] + 1               
        no_asic_cols_per_frm = run_params['asic_nr_images_per_frame'] + 1                       
        print "---> no_asic_cols, no_asic_cols_per_frm: ", no_asic_cols, no_asic_cols_per_frm, " <-----"
             
        #set up the ASIC RX IP block
        myClient.fem_asic_rx_setup(myClient.asic_srx_0 , mask_list, no_asic_cols, no_asic_cols_per_frm)
        
        # data source - self test
        if run_params['asic_data_type'] == "asicrx_counting":            
          myClient.asicrx_self_test_counting_data_enable()
        else:
          myClient.asicrx_self_test_counting_data_disable()

        # asic rx gain override
        myClient.asicrx_override_gain(run_params['asicrx_gain_selection'])

        # asic rx invert adc data
        if run_params['asicrx_invert_data'] == 1:            
          myClient.asicrx_invert_data_enable()
        else:
          myClient.asicrx_invert_data_disable()
        
        if run_params['asic_data_type'] == "asic_pseudo_random":
            asic_rx_start_delay = asic_rx_start_pseudo_random
        else: 
          if run_params['detector_type'] == "single_asic_module":
            asic_rx_start_delay = asic_rx_start_single_asic
          else:           
            asic_rx_start_delay = asic_rx_start_2tile 
            
          if run_params['asicrx_capture_asic_header_TEST_ONLY'] == 1:
            asic_rx_start_delay -= asic_rx_hdr_bits

        print "asic_rx_start_delay = %s " % asic_rx_start_delay          
        #print "asic_rx_start_delay = %d ". % asic_rx_start_delay

        if run_params['asicrx_start_from_fast_strobe'] == 0:  
          myClient.rdmaWrite(myClient.fem_ctrl_0+4, asic_rx_start_delay)  # OLD using fixed offsets          
        else: 
          myClient.rdmaWrite(myClient.fem_ctrl_0+14, asic_rx_start_delay)   # NEW using strobe from fast command file         
                     
        return 0
                
    #-------------------------------------------------------------------------------------    
    def reset_ppc(self, run_params, myClient):
        """ reset the ppc
             """                        
        #--------------------------------------------------------------------
        # Resetting the PPC start the DMA test
        # need to get the timing right or add handshaking
                
        # Resets dma engines
        myClient.toggle_bits(myClient.fem_ctrl_0+9, 0)
        print "Reset the PPC.."
        
        theDelay = run_params['ppc_reset_delay_secs']

        print "Waiting %s seconds.." % theDelay
        time.sleep(theDelay)
        print "Finished waiting %s seconds!" % theDelay
                     
        return 0
        
    def config_top_level(self, run_params, myClient):
        """ configure top level of design
             """
        # set asic clock freq
        myClient.set_asic_clock_freq(myClient.fem_ctrl_0, run_params['asic_local_clock_freq'])    # 0 = 100 Mhz, 1 = div clock 10 MHz
        
        if run_params['run_type'] == "asic_data_via_ppc":
            myClient.rdmaWrite(myClient.fem_ctrl_0+1, 0x00000001)  # asic data via ppc
        elif run_params['run_type'] == "asic_data_direct":
            myClient.rdmaWrite(myClient.fem_ctrl_0+1, 0x00000102)  # aisc direct to 10g
        elif run_params['run_type'] == "ll_data_gen":
            myClient.rdmaWrite(myClient.fem_ctrl_0+1, 0x00000000)  # data generator
        elif run_params['run_type'] == "ppc_data_direct":
            myClient.rdmaWrite(myClient.fem_ctrl_0+1, 0x00000001)  # ppc generated data
        else:
            myClient.rdmaWrite(myClient.fem_ctrl_0+1, 0x00000001)  # asic data via ppc
                   
        return 0

    def send_trigger(self, run_params, myClient):
        """ send triggers
            """                        
        #--------------------------------------------------------------------
        # send triggers to data generators
        #--------------------------------------------------------------------
                                 
        if run_params['run_type'] == "ll_data_gen":            
            print "Trigger Data Gen"
            myClient.toggle_bits(myClient.fem_ctrl_0+0, 0) # trigger to local link frame gen 
        elif (run_params['run_type'] == "asic_data_via_ppc") or (run_params['run_type'] == "asic_data_direct"):             
            print "Trigger Asic"
            myClient.toggle_bits(myClient.fem_ctrl_0+0, 1)  # start asic seq  = reset, slow, fast & asic rx
        else:
            print "Trigger Asic"
            myClient.toggle_bits(myClient.fem_ctrl_0+0, 1)



#        elif trigger_type is 'b':
#            # trigger the asic rx block
#            print "You selected 'b'"
#            myClient.toggle_bits(3, 1)
#        elif trigger_type is 's':
#            # trigger just the slow contol IP block
#            print "You selected 's'"
#            myClient.toggle_bits(7, 1)
#        elif trigger_type is 'f':
#            # trigger just the fast cmd block
#            print "You selected 'f'"
#            myClient.toggle_bits(7, 2)
#        elif trigger_type is 'x':   # trigger fastand asic rx  (not slow)
#            myClient.toggle_bits(7, 2)
#            myClient.toggle_bits(3, 1)
#        else:
#            print "No case matching variable trigger_type = ", trigger_type
#        #--------------------------------------------------------------------
                    
        return 0

#-------------------------------------------------------------------------------------    
    def start_10g_link(self, run_params, x10g, myClient):
      """ start a 10g link
           """
        
      if run_params['debug_level'] > 5:
        print "Start 10G link nr", x10g['link_nr']


      data_gen_base = myClient.data_gen_0
      ll_mon_base = myClient.llink_mon_0
      ppc_bram_base = myClient.bram_ppc1
       
      
      time.sleep(x10g['delay'])   # wait before trigger

#      if x10g['data_gen'] == 1:
      if run_params['run_type'] == "ll_data_gen": # ll data gen
          
          # check last cycle has completed                
          link_busy = myClient.status_ll_frm_mon(ll_mon_base) 
          gen_busy = myClient.status_ll_frm_gen(data_gen_base) 
          i = 0
#                print "\n" 
#                while link_busy == 1:
          while gen_busy == 1:
              i=i+1
#                   link_busy = myClient.status_ll_frm_gen(data_gen_base)                
#                   print "Data Gen on 10G link nr %2d has busy flag = %d" %(x10g['link_nr'], link_busy)
              print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(x10g['link_nr'],i),
              sys.stdout.flush() 
#                    print "1 WARNING Data Gen on 10G link nr %2d is still BUSY" %x10g['link_nr']
              time.sleep(1)                    
              link_busy = myClient.status_ll_frm_mon(ll_mon_base) 
              gen_busy = myClient.status_ll_frm_gen(data_gen_base) 
                          
      if run_params['10g_farm_mode'] == 3: 
          i = 0
          for nic in x10g['nic_list']:
              # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
              # don't do this any earlier or won't trigger
              #myClient.soft_reset_ll_frm_gen(data_gen_base) 

              if x10g['data_gen'] == 1:
                # check last transfer has completed                
                link_busy = myClient.status_ll_frm_mon(ll_mon_base) 
                gen_busy = myClient.status_ll_frm_gen(data_gen_base) 
                t = 0
                while gen_busy == 1:
                    t=t+1
                    print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(x10g['link_nr'],t),
                    sys.stdout.flush() 
                    time.sleep(1)                    
                    link_busy = myClient.status_ll_frm_mon(ll_mon_base) 
                    gen_busy = myClient.status_ll_frm_gen(data_gen_base) 
                  
                # override the index nr in the data gen ll header output for selecting the 10g port nr in lut
                index_nr = i
                myClient.override_header_ll_frm_gen(data_gen_base, 1, index_nr)
                    
                if run_params['debug_level'] > 5:
                    print "Trigger LL Data Gen"

                myClient.toggle_bits(myClient.fem_ctrl_0+0, 0)   
                
#              elif x10g['data_gen'] == 2:
              elif run_params['run_type'] == "ppc_data_direct": # ppc dma ddr2 preprogrammed
                
                # check previous dma tx has completed
                busy = myClient.prev_dma_tx(ppc_bram_base) 
                t = 0;    
                while busy == 1:
                     t=t+1
                     print 'Waiting to Trigger Next Cycle : 10G link nr %2d DMA is BUSY ; waiting %d secs\r' %(x10g['link_nr'],t),
                     sys.stdout.flush() 
                     time.sleep(1)                    
                     busy = myClient.prev_dma_tx(ppc_bram_base) 

                if run_params['debug_level'] > 5:
                   print "Trigger DMA Tx"
                myClient.start_dma_tx(ppc_bram_base, i)  # pass index to ppc to select tx descriptor
                  
              i = i + 1
              
#          if x10g['data_gen'] == 2:
#            myClient.final_dma_tx(ppc_bram_base)  

      else:
        if x10g['data_gen'] == 1:
          # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
          # don't do this any earlier or won't trigger
          myClient.soft_reset_ll_frm_gen(data_gen_base)  
              
          print "Trigger LL Data Gen"
          myClient.toggle_bits(myClient.fem_ctrl_0+0, 0)   
                              
      # if run_params['debug_level'] > 1:
          # print "After Trigger : Dump of regs for Data Gen for Link %d" % x10g['link_nr']
          # myClient.dump_regs_hex(data_gen_base, 32)   
         
      return 0


#########################################
# following needs to be at the end

if __name__ == "__main__":
    femAsicTest = FemAsicTest()
    femAsicTest.execute_tests()

