'''
Created June 2012

@author: jac36
'''
# Adapted LPD FEM test for Train Builder
# John Coughlan June 2012
# Configured for XFEL Hamburg tests July 2012

# Added nic list for multiple dest ip and port  jac36  Aug 2012
# Added code for PPC DMA Tx to 10G    jac36 Aug 2012

# Import Python standard modules
import sys

import pprint

# Import Fem modules
#from FemClient import FemClient
from TBClient_v6 import *  #TBClient

            
class TBTest():

    # TBClient myTBClient   # don't know how to have class type as an object, use global instead
 
    def set_10g_structs_variables(self):
       
        run_params = {
            'run_type' :  # "10g_test",  # XFEL DAQ tests
                        "ddr2_test",   # DDR2 memory tests
       
                        '10g_farm_mode' : 0,   
                        # 3 for farm mode with nic lists ; 2 for farm mode with fixed ip host and multiple ports ; # 1 for legacy non farm mode (only 1 ip host and port per link) 
                      'num_cycles'  : 1,
                      'playback' : 0, # 1 for playback rx (to load files into ddr2 memory)
                      'debug_level' : 2,    # higher values more print out
          'eth_ifg' : 0x000,   # ethernet inter frame gap  ; ensure receiving 10G NIC parameters have been set accordingly
                      'udp_pkt_len' : 8000, # udp packet length in bytes
          'TBHost' : '192.168.2.2',     # ip address for 1 GbE fem controls
          'TBPort' : 6969,   # udp port nr for 1 GbE fem controls (not to be confused with port nr for 10g links)
              'clear_10g_lut' : 0   # 1 to clear 10g lut tables before start
                    }  
     
        # look up table to match MAC addresses with IP for host NIC
        global mac_ip_lut
        mac_ip_lut = { '192.168.2.1' : '00-07-43-11-97-90', 
                    '192.168.3.1' : '00-07-43-11-97-98'
            }  
      
    # F1 has links 1&2 , F2 has links 3&4, F3 links 5&6, F4 links 7&8
    # link 1 is at bottom of board when in crate
            
        x10g_1 = {  'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),  # fpga mac address  
                    'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),     # fpga ip address  
                    'fpga_prt' : self.prt_addr_to_uint16('0000'),   # fpga port nr
                    'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),   #  10G NIC channel mac address  
                    'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),      # 10G NIC channel ip address
                    'nic_prt' : self.prt_addr_to_uint16('61649'),   # 10G starting port nr for each cycle (increments by 1 for each frame in cycle)
                    'num_prts' : 4, # number of ports to loop over before repeating
                    'data_gen' : 1, # data generator type (1 for DataGen ; 2 for PPC/DDR2)   
                    'data_format' : 0, # data format type  (0 for counting data)  
                    'frame_len'  : 1024,    # frame len in bytes
                    'num_frames' : 1,    # number of frames to send in each cycle
                    'delay' : 0,    # delay offset wrt start of previous link in secs
                    'enable'  : 0,    # enable this link
                    'link_nr' : 1,   # link number
                    'fpga_nr' : 1   # fpga number
                }

                        
        x10g_2 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 4, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 2,   # link number
                        'fpga_nr' : 1    # fpga number
                        } 
                        
        x10g_3 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 4, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 3,  # link number
                        'fpga_nr' : 2   # fpga number
                        } 
                        
        x10g_4 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 4, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 4,   # link number
                        'fpga_nr' : 2   # fpga number
                        } 
                        
        x10g_5 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'), 
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),  # 61649
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x10000,    # frame len in bytes   # 125000*8000
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 1,    # delay offset wrt previous link in secs
                        'enable'  : 1,    # enable link
                        'link_nr' : 5,   # link number
                        'fpga_nr' : 3,   # fpga number                                                
#                       'nic_list' : [ '61649@192.168.2.1', '61650@192.168.2.1', '61652@192.168.2.1', '61654@192.168.2.1' ]
#                        'nic_list' : [ '61649@192.168.2.1', '61650@192.168.2.1' ]
                       'nic_list' : [ '61649@192.168.2.1' ]
                        } 
                        
        x10g_6 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x4000,    # frame len in bytes   # 125000*8000
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 2,    # delay offset wrt previous link in secs
                        'enable'  : 1,    # enable link
                        'link_nr' : 6, 
                        'fpga_nr' : 3,   # fpga number                                                
                        #'nic_list' : [ '61649@192.168.3.1', '61650@192.168.3.1' ]
                        'nic_list' : [ '61649@192.168.3.1' ]
                        } 
                        
        x10g_7 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 4, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 7,
                        'fpga_nr' : 4   # fpga number 
                        } 
                        
        x10g_8 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 4, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 8,
                        'fpga_nr' : 4   # fpga number 
                        } 
                        
                        
        x10g_params = [ x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8 ]
        
        # xfel tests in level 2 lab
                # x10g_5 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        # 'fpga_ip'  : self.ip_addr_to_uint32('192.168.141.2'),    
                        # 'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        # 'nic_mac' : self.mac_addr_to_uint64('90-E2-BA-0C-54-A4'),    
                        # 'nic_ip'  : self.ip_addr_to_uint32('192.168.141.62'),    
                        # 'nic_prt' : self.prt_addr_to_uint16('61649'),
                        # 'num_prts' : 2, # number of ports to loop over before repeating
                        # 'data_gen' : 1, # data generator    
                        # 'data_format' : 0, # data format type   
                        # 'frame_len'  : 2*8000,    # frame len in bytes
                        # 'num_frames' : 2,    # number of frames to send
                        # 'delay' : 0,    # delay offset wrt previous link in secs
                        # 'enable'  : 1,    # enable link
                        # 'link_nr' : 5
                        # } 
                        
        # x10g_6 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        # 'fpga_ip'  : self.ip_addr_to_uint32('192.168.142.2'),    
                        # 'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        # 'nic_mac' : self.mac_addr_to_uint64('90-E2-BA-0C-54-A5'),    
                        # 'nic_ip'  : self.ip_addr_to_uint32('192.168.142.62'),    
                        # 'nic_prt' : self.prt_addr_to_uint16('61649'),
                        # 'num_prts' : 2, # number of ports to loop over before repeating
                        # 'data_gen' : 1, # data generator    
                        # 'data_format' : 0, # data format type   
                        # 'frame_len'  : 10*8000,    # frame len in bytes
                        # 'num_frames' : 2,    # number of frames to send
                        # 'delay' : 0.2,    # delay offset wrt previous link in secs
                        # 'enable'  : 0,    # enable link
                        # 'link_nr' : 6
                        # } 
                        
        # x10g_nic_params_1 = [{'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        # 'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        # 'nic_prt' : self.prt_addr_to_uint16('0000') },
                        # {'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        # 'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        # 'nic_prt' : self.prt_addr_to_uint16('0000') },
                        # {'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        # 'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        # 'nic_prt' : self.prt_addr_to_uint16('0000') },
                        # {'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        # 'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        # 'nic_prt' : self.prt_addr_to_uint16('0000') }
                        # ]
                        
        # x10g_link_params_1 = {'data_type' : 1, # data type   
                            # 'frame_len'  : 1,    # frame len in bytes
                            # 'num_frames' : 1,    # number of frames to send
                            # 'delay' : 0,    # delay offset wrt previous link in milli-secs
                            # 'enable'  : 1,    # enable link
                            # }                

# parameters for ddr2 tests
        ddr2_1 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 1,
                        'fpga_nr' : 1   # fpga number 
                        } 
        ddr2_2 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 2,
                        'fpga_nr' : 1   # fpga number 
                        } 
        ddr2_3 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 3,
                        'fpga_nr' : 2   # fpga number 
                        } 
        ddr2_4 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 4,
                        'fpga_nr' : 2   # fpga number 
                        } 
        ddr2_5 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 5,
                        'fpga_nr' : 3   # fpga number 
                        } 
        ddr2_6 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 6,
                        'fpga_nr' : 3   # fpga number 
                        } 
        ddr2_7 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 7,
                        'fpga_nr' : 4   # fpga number 
                        } 
        ddr2_8 = {      'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 8,
                        'fpga_nr' : 4   # fpga number 
                        } 

        ddr2_params = [ ddr2_1, ddr2_2, ddr2_3, ddr2_4, ddr2_5, ddr2_6, ddr2_7, ddr2_8 ]
     
        #return x10g_params
        return run_params, x10g_params, ddr2_params
        #return x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8
       
#-------------------------------------------------------------------------------------    
    def mac_addr_to_uint64(self, mac_addr_str):
        # convert hex MAC address 'u-v-w-x-y-z' string to integer
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
    
#-------------------------------------------------------------------------------------    
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
        
#-------------------------------------------------------------------------------------    
    def prt_addr_to_uint16(self, prt_addr_str):
        #convert hex prt string to integer
        return int(prt_addr_str)
        
        
#-------------------------------------------------------------------------------------    
    def execute_tests(self):
  # TBHost now set in run_params structure
        #TBHost = '192.168.2.2'   # '192.168.0.13'
        #TBPort = 6969          # 6969       
        
        global pp
        
        global myTBClient
        
        global fpga_mux_base
        global fpga_lut
        
        global clock_10g
        global clock_ppc

        clock_10g = 156.25e6
        clock_ppc = 200.00e6
        
        frame_gen_32b = 4
        frame_gen_64b = 8
                
        pp = pprint.PrettyPrinter(indent=4)
        
        fpga_mux_base = 0x84000008; # RAW base address of GPIO controlling FPGA RDMA mux
        fpga_term_mux_base = 0x84000000; # RAW base address of GPIO controlling FPGA RDMA mux
       
        # fpga rdma access from master is switched by simple mux under gpio control
        # fpga 1 has links 1&2 ; fpga 2 has links 3&4 ; fpga 3 has links 5&6  ; fpga 4 has links 7&8 ;
        # links start at 1 not 0 (hence first element '0' in fpga_lut
        fpga_lut = [0,1,1,2,2,3,3,4,4]       
            
        #x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8 = self.set_10g_structs_variables_te7redbridge()
        run_params, x10g_params, ddr2_params = self.set_10g_structs_variables()

        print "===============================================================================" 
        
        if run_params['debug_level'] > 0:
                pp.pprint(run_params)
        try:
            # myTBClient = TBClient((TBHost, TBPort), timeout=10)
            myTBClient = TBClient((run_params['TBHost'], run_params['TBPort']), timeout=10)
        except FEMClientError as errString:
            print "Error: Train Builder connection failed (is Master GbE server running?:", errString
            sys.exit(1)
      
         
        fpga_nr = 3
        ppc_nr = 1
        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_nr-1)   # switch RDMA
        response = myTBClient.rdmaWrite(myTBClient.f1_f4_ctrl+15, ppc_nr-1)  # selects either ppc1 or ppc2 term output

        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_term_mux_base, fpga_nr)  # switch terminal
        print "Switching PPC Terminal output to F%d : PPC#%d:" %(fpga_nr, ppc_nr)
        

#============ special ddr2 test ; needs corresponding dma code running on both ppcs

        if (run_params['run_type'] == "ddr2_test") :  

          fpga_nr = 3
          response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_nr-1)   # switch RDMA

          print "Starting DDR2 Memory Test..."
          myTBClient.clear_dma_tx(myTBClient.bram_ppc1, 0) 
          myTBClient.init_ppc_bram(myTBClient.bram_ppc1, 0xbeef0001) 

          myTBClient.clear_dma_tx(myTBClient.bram_ppc2, 0) 
          myTBClient.init_ppc_bram(myTBClient.bram_ppc2, 0xbeef0002) 

          # Resets ppc bram_ppc1
          myTBClient.toggle_bits_new(myTBClient.f1_f4_ctrl+9, 0)   
          # Resets ppc bram_ppc2
          myTBClient.toggle_bits_new(myTBClient.f1_f4_ctrl+9, 1)   

          theDelay = 10
          print "Waiting for PPCs 1&2 to reset %s seconds.." % theDelay
          time.sleep(theDelay)

          myTBClient.clear_ll_monitor(myTBClient.mon_ppc1_64b)              
          myTBClient.clear_ll_monitor(myTBClient.mon_ppc1_32b)
          myTBClient.read_ll_monitor(myTBClient.mon_ppc1_64b, clock_ppc)
          myTBClient.read_ll_monitor(myTBClient.mon_ppc1_32b, clock_ppc)              

          myTBClient.clear_ll_monitor(myTBClient.mon_ppc2_32b)
          myTBClient.read_ll_monitor(myTBClient.mon_ppc2_32b, clock_ppc)              

          myTBClient.clear_ll_monitor(myTBClient.mon_ppc1_tx)
          myTBClient.read_ll_monitor(myTBClient.mon_ppc1_tx, clock_ppc)              
           
          # resets the counters start values in the Frame Gens (so ppc knows what's coming!)
          myTBClient.soft_reset_ll_frm_gen(myTBClient.data_gen_2)  
          myTBClient.soft_reset_ll_frm_gen(myTBClient.data_gen_3)  

          myTBClient.setup_ll_frm_gen(myTBClient.data_gen_2, (0x40+frame_gen_32b)/frame_gen_32b, 0, 0, 1)  
          myTBClient.setup_ll_frm_gen(myTBClient.data_gen_3, (0x100000+frame_gen_64b)/frame_gen_64b, 0, 0, 1)    

          response = myTBClient.rdmaWrite(myTBClient.data_gen_2+7, 0x12345678)  # fix ll frame header
          response = myTBClient.setbit(myTBClient.data_gen_2+4, 8)  

          print "Start polling on DMA Rx engine then immediately send Trigger Frame Gen .."
          # use same comms as for Tx , but it's really a Rx this time
          myTBClient.start_dma_tx(myTBClient.bram_ppc1, 0) 
          myTBClient.start_dma_tx(myTBClient.bram_ppc2, 0) 

# send frames
#          if ppc_nr == 1:
          myTBClient.toggle_bits_new(myTBClient.f1_f4_ctrl+0, 3) # trigger local link frame gen to ppc1
#          else:
          myTBClient.toggle_bits_new(myTBClient.f1_f4_ctrl+0, 4) # trigger local link frame gen to ppc2 

# measure rates
          print "Wait for transfer to complete before monitoring .."
          time.sleep(5)
          print "Rates on LL to PPC1 Rx.."
          myTBClient.read_ll_monitor(myTBClient.mon_ppc1_64b, clock_ppc)              
          myTBClient.read_ll_monitor(myTBClient.mon_ppc1_32b, clock_ppc)              
          print "Rates on LL to PPC2 Rx.."
          myTBClient.read_ll_monitor(myTBClient.mon_ppc2_32b, clock_ppc)              

          print "Rates on PPC1 Tx .."
          myTBClient.read_ll_monitor(myTBClient.mon_ppc1_tx, clock_ppc)              

          print "Dump of Frame Gen regs for PPC 1 "
          myTBClient.dump_regs_hex(myTBClient.data_gen_2, 16)
          print "Dump of Frame Gen regs for PPC 2 "
          myTBClient.dump_regs_hex(myTBClient.data_gen_3, 16)

          print "Dump of LL Checker regs for PPC 1 "
          myTBClient.dump_regs_hex(myTBClient.data_chk_ppc1_tx, 16)

          return
          
#============
                          
        # initialise

        for link in x10g_params:       
            self.init(link, myTBClient)   

#        return


        # display monitor counters etc
        for link in x10g_params:
            self.dump_registers_10g_link(run_params, link, myTBClient)            
#        return 0

        
        if run_params['clear_10g_lut'] == 1: 
            for link in x10g_params:       
                self.clear_10g_link(link, myTBClient)   
 
        # configure from x10g structures
        for link in x10g_params:
        #    pp.pprint(link) 
            self.config_10g_link(run_params, link, myTBClient)         

############ test only
#        for link in x10g_params:       
#            self.init(link, myTBClient)   
############ test only

        for link in x10g_params:
            self.dump_registers_10g_link(run_params, link, myTBClient)            
            
#        return
         
  
# for receive only tests, do need the 10g set up but don't need to tx triggers
        if run_params['playback'] == 1:      
            return 0 
        
        # reset counters etc
        for link in x10g_params:
            self.init_10g_link(link, myTBClient)   
        
        # display monitor counters etc
        for link in x10g_params:
            self.monitor_10g_link(link, myTBClient)    
        
        num_cycles = run_params['num_cycles']
        for i in range (1, num_cycles+1):
            # start data transfers on links
            print "Starting Run Cycle Nr %d" % i
            for link in x10g_params:
                self.start_10g_link(run_params, link, myTBClient)  
    #time.sleep(2) 
        
        # display monitor counters etc
        for link in x10g_params:
            self.monitor_10g_link(link, myTBClient) 

        f1_f4_ctrl_base = myTBClient.f1_f4_ctrl      
        print "Dump of regs for TB F1_F4 control"
        myTBClient.dump_regs_hex(f1_f4_ctrl_base, 16)

        # display monitor counters etc
        for link in x10g_params:
            self.dump_registers_10g_link(run_params, link, myTBClient)            
            
        return 0 

#-------------------------------------------------------------------------------------    
    def init(self, x10g, myTBClient):
        """ initialise all links
             """

        # switch mux to fpga 
        fpga_mux = fpga_lut[x10g['link_nr']] - 1
        print "fpga_mux = ", fpga_mux
        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   

        if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
            ppc_bram_base = myTBClient.bram_ppc1
        else:
            ppc_bram_base = myTBClient.bram_ppc2  

        fpga_nr = fpga_lut[x10g['link_nr']] 
        print "fpga_nr = ", fpga_nr
#        myTBClient.init_ppc_bram(ppc_bram_base, x10g['fpga_nr'])
        myTBClient.init_ppc_bram(ppc_bram_base, fpga_nr)
#        myTBClient.init_ppc_bram(ppc_bram_base, 9)
         
        return 0 
   
#-------------------------------------------------------------------------------------    
    def config_10g_link(self, run_params, x10g, myTBClient):
        """ configure a 10g link
             """
        #pprint(x10g)
               
        if x10g['enable'] == 1:
            print "Configure 10G link nr", x10g['link_nr']
            
            if run_params['debug_level'] > 0:
                pp.pprint(x10g)
            
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            print "fpga_mux = ", fpga_mux
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                x10g_base = myTBClient.udp_10g_0
                data_gen_base = myTBClient.data_gen_0
                ppc_bram_base = myTBClient.bram_ppc1
                ppc_reset_bit = 0
            else:
                x10g_base = myTBClient.udp_10g_1
                data_gen_base = myTBClient.data_gen_1
                ppc_bram_base = myTBClient.bram_ppc2                
                ppc_reset_bit = 1

            f1_f4_ctrl_base = myTBClient.f1_f4_ctrl
            
            #udp_pkt_len = x10g['frame_len']
            #udp_frm_sze = x10g['frame_len']
            
            #udp_pkt_len = 8000

            udp_pkt_len = run_params['udp_pkt_len']
            udp_frm_sze = x10g['frame_len']

            #eth_ifg = 0x00001000  # Ethernet Inter Frame Gap
            #eth_ifg = 0x1000  # Ethernet Inter Frame Gap
            eth_ifg = run_params['eth_ifg']
            robs_udp_packet_hdr = 4; 

            #extract nic params from nic list for farm mode with multiple port@host  (run type = 3)
            # if run_params['10g_farm_mode'] == 3:
                # nic_ip, nic_mac, nic_port = self.get_nic_params(x10g)               
                # x10g['nic_ip'] = nic_ip
                # x10g['nic_mac'] = nic_mac
                # x10g['nic_prt'] = nic_port
            
            # legacy non farm mode. (run type = 1)
            myTBClient.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            myTBClient.setup_10g_udp_net_block(x10g_base, x10g)    
            myTBClient.setup_10g_packet_header(x10g_base, robs_udp_packet_hdr)

            myTBClient.setup_10g_rx_filter(x10g_base) # accepts any udp packets
            
            # response = myTBClient.rdmaWrite(x10g_base + 14, 0x000000ab)        
            # response = myTBClient.rdmaRead(x10g_base + 14, 1)
            # print "RDMA read from polarity p/n swapping:", hex(response[1])  
        
            # final param to enable data gen headers for farm mode
            myTBClient.setup_ll_frm_gen(data_gen_base, x10g['frame_len']/8, x10g['data_format'], x10g['num_frames']-1, 1)  
            
            myTBClient.override_header_ll_frm_gen(data_gen_base, 0, 0)  # default is not to override index nr in header
             
            print "Dump of Farm Mode LUT for xaui for Link %d" % x10g['link_nr']
            myTBClient.dump_regs_hex(x10g_base+0x10000, 16) 
 
            print "Setting up Farm Mode LUT. May take several seconds... "                       
            if run_params['10g_farm_mode'] == 2:
                myTBClient.x10g_net_lut_setup(x10g_base, x10g) 
                myTBClient.x10g_set_farm_mode(x10g_base, 1)
            elif run_params['10g_farm_mode'] == 3:      
                myTBClient.x10g_net_lut_setup_from_list(x10g_base, x10g, self, mac_ip_lut)  
                myTBClient.x10g_set_farm_mode(x10g_base, 1)                         
            else: 
                print "Not in Farm Mode."              
                myTBClient.x10g_set_farm_mode(x10g_base, 0)

            if run_params['debug_level'] > 3:                
                print "Dump of Farm Mode LUT for xaui for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(x10g_base+0x10000, 16) 
                myTBClient.dump_regs_hex(x10g_base+0x100f0, 16)                               
                myTBClient.dump_regs_hex(x10g_base+0x10100, 16)
                myTBClient.dump_regs_hex(x10g_base+0x101f0, 16)  
                myTBClient.dump_regs_hex(x10g_base+0x10200, 16)
                myTBClient.dump_regs_hex(x10g_base+0x103f0, 16)
                    
            if run_params['debug_level'] > 1:
                #time.sleep(1)
                print "Dump of regs for xaui for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(data_gen_base, 16)
 
 
         
            if x10g['data_gen'] == 2:   # data source is ppc

                myTBClient.setup_ppc_bram(ppc_bram_base, x10g['frame_len'], x10g['data_format'], x10g['num_frames']-1, 1) 
                myTBClient.rdmaWrite(f1_f4_ctrl_base+14, 1) # switch ll mux
                myTBClient.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 

                # Resets ppc 
                myTBClient.toggle_bits_new(f1_f4_ctrl_base+9, ppc_reset_bit)   # xaui chan 0
                theDelay = 10
                print "Waiting for PPC to reset %s seconds.." % theDelay
                time.sleep(theDelay)

            else:                       # data source is data gen               
                myTBClient.rdmaWrite(f1_f4_ctrl_base+14, 0) # switch ll mux
                myTBClient.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut   

        return 0
        
#-------------------------------------------------------------------------------------    
    def start_10g_link(self, run_params, x10g, myTBClient):
        """ start a 10g link
             """
        
        if x10g['enable'] == 1:
            print "Start 10G link nr", x10g['link_nr']

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   

            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                data_gen_base = myTBClient.data_gen_0
                ll_mon_base = myTBClient.llink_mon_0
                ppc_bram_base = myTBClient.bram_ppc1
            else:
                data_gen_base = myTBClient.data_gen_1
                ll_mon_base = myTBClient.llink_mon_1
                ppc_bram_base = myTBClient.bram_ppc2
             
            f1_f4_ctrl_base = myTBClient.f1_f4_ctrl
            
            time.sleep(x10g['delay'])   # wait before trigger

            if x10g['data_gen'] == 1:
                
                # check last cycle has completed                
                link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                gen_busy = myTBClient.status_ll_frm_gen(data_gen_base) 
                i = 0
#                print "\n" 
#                while link_busy == 1:
                while gen_busy == 1:
                    i=i+1
#                   link_busy = myTBClient.myTBClientstatus_ll_frm_gen(data_gen_base)                
#                   print "Data Gen on 10G link nr %2d has busy flag = %d" %(x10g['link_nr'], link_busy)
                    print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(x10g['link_nr'],i),
                    sys.stdout.flush() 
#                    print "1 WARNING Data Gen on 10G link nr %2d is still BUSY" %x10g['link_nr']
                    time.sleep(1)                    
                    link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                    gen_busy = myTBClient.status_ll_frm_gen(data_gen_base) 
                                
            if run_params['10g_farm_mode'] == 3: 
                i = 0
                for nic in x10g['nic_list']:
                    # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
                    # don't do this any earlier or won't trigger
                    #myTBClient.soft_reset_ll_frm_gen(data_gen_base) 

                    if x10g['data_gen'] == 1:
                      # check last transfer has completed                
                      link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                      gen_busy = myTBClient.status_ll_frm_gen(data_gen_base) 
                      t = 0
                      while gen_busy == 1:
                          t=t+1
                          print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(x10g['link_nr'],t),
                          sys.stdout.flush() 
                          time.sleep(1)                    
                          link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                          gen_busy = myTBClient.status_ll_frm_gen(data_gen_base) 
                        
                      # override the index nr in the data gen ll header output for selecting the 10g port nr in lut
                      index_nr = i
                      myTBClient.override_header_ll_frm_gen(data_gen_base, 1, index_nr)
                          
                      print "Trigger LL Data Gen"
                      if x10g['link_nr']%0:
                            myTBClient.toggle_bits_new(f1_f4_ctrl_base+0, 0)   # xaui chan 0
                      else:               
                            myTBClient.toggle_bits_new(f1_f4_ctrl_base+0, 1)   # xaui chan 1
                      
                    elif x10g['data_gen'] == 2:
                      
                      # check previous dma tx has completed
                      busy = myTBClient.prev_dma_tx(ppc_bram_base) 
                      t = 0;    
                      while busy == 1:
                           t=t+1
                           print 'Waiting to Trigger Next Cycle : 10G link nr %2d DMA is BUSY ; waiting %d secs\r' %(x10g['link_nr'],t),
                           sys.stdout.flush() 
                           time.sleep(1)                    
                           busy = myTBClient.prev_dma_tx(ppc_bram_base) 

                      myTBClient.start_dma_tx(ppc_bram_base, i)  # pass index to ppc to select tx descriptor
                        
                    i = i + 1
                    
                if x10g['data_gen'] == 2:
                  myTBClient.final_dma_tx(ppc_bram_base)  

            else:
              if x10g['data_gen'] == 1:
                # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
                # don't do this any earlier or won't trigger
                myTBClient.soft_reset_ll_frm_gen(data_gen_base)  
                    
                print "Trigger LL Data Gen"
                if x10g['link_nr']%2 == 0:
                    myTBClient.toggle_bits_new(f1_f4_ctrl_base+0, 0)   # xaui chan 0
                else:               
                    myTBClient.toggle_bits_new(f1_f4_ctrl_base+0, 1)   # xaui chan 1
                                    
            # if run_params['debug_level'] > 1:
                # print "After Trigger : Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                # myTBClient.dump_regs_hex(data_gen_base, 32)   
             
        return 0

#-------------------------------------------------------------------------------------    
    def init_10g_link(self, x10g, myTBClient):
        """ reset 10g link
             """
        
        if x10g['enable'] == 1:
            print "Clear Monitor on 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                ll_mon_base = myTBClient.llink_mon_0
            else:
                ll_mon_base = myTBClient.llink_mon_1            
                
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   
            
            myTBClient.clear_ll_monitor(ll_mon_base)
                    
        return 0

#-------------------------------------------------------------------------------------    
    def monitor_10g_link(self, x10g, myTBClient):
        """ monitor 10g link
             """
        
        if x10g['enable'] == 1:
            print "Monitor 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                ll_mon_base = myTBClient.llink_mon_0
                data_gen_base = myTBClient.data_gen_0
            else:
                ll_mon_base = myTBClient.llink_mon_1
                data_gen_base = myTBClient.data_gen_1            
                
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   

            if x10g['data_gen'] == 1:                
                link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                gen_busy = myTBClient.status_ll_frm_gen(data_gen_base) 
                i = 0
#                print "\n"
                while gen_busy == 1: 
#                while link_busy == 1:
                    i=i+1
#                   link_busy = myTBClient.status_ll_frm_gen(data_gen_base)                
#                   print "Data Gen on 10G link nr %2d has busy flag = %d" %(x10g['link_nr'], link_busy)
                    print 'Waiting for Run End : 10G link nr %2d is BUSY ; waiting %d secs \r' %(x10g['link_nr'],i),
                    sys.stdout.flush() 
#                    print "WARNING Data Gen on 10G link nr %2d is still BUSY" %x10g['link_nr']
                    time.sleep(1)                    
                    link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                    gen_busy = myTBClient.status_ll_frm_gen(data_gen_base) 
                    if i > 5:
                        print "ATTENTION Data Gen on 10G link nr %2d TIMED OUT waiting on BUSY" %x10g['link_nr']
                        break
             
            print "\n"   
            myTBClient.read_ll_monitor(ll_mon_base, clock_10g)              
                    
        return 0
        
#-------------------------------------------------------------------------------------    
    def clear_10g_link(self, x10g, myTBClient):
        """ clear 10g link settings
             """
        
        if x10g['enable'] == 1:
            print "Clear settings on 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                x10g_base = myTBClient.udp_10g_0
            else:
                x10g_base = myTBClient.udp_10g_1            
                
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   
            
            myTBClient.x10g_net_lut_clear(x10g_base)
                    
        return 0   
 
    def dump_registers_10g_link(self, run_params, x10g, myTBClient):
        """ reset 10g link
             """

        if x10g['enable'] == 1:
            print "Clear Monitor on 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                x10g_base = myTBClient.udp_10g_0
                ll_mon_base = myTBClient.llink_mon_0
                data_gen_base = myTBClient.data_gen_0
                ppc_bram_base = myTBClient.bram_ppc1
            else:
                x10g_base = myTBClient.udp_10g_1
                ll_mon_base = myTBClient.llink_mon_1
                data_gen_base = myTBClient.data_gen_1
                ppc_bram_base = myTBClient.bram_ppc2             
    
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   
            
            if run_params['debug_level'] > 1:
                print "Dump of regs for XAUI for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(data_gen_base, 16)
                print "Dump of regs for PPC BRAM %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(ppc_bram_base, 32)
                    
        return 0
        
#-------------------------------------------------------------------------------------    
    def get_nic_params(self, x10g):
              
        #nic = '61649@192.168.2.1'
        
        # mac_ip_lut = { '192.168.2.2' : '62-00-00-00-00-04', 
                    # '192.168.2.3' : '62-00-00-00-00-05',
                    # '192.168.2.4' : '62-00-00-00-00-06'
                    # }                       
        
        nic_list = x10g['nic_list']                
        port1 = nic_list[0]
        
        port1 = port1.split('@')
        nic_ip = self.ip_addr_to_uint32(port1[1])
        nic_port = port1[0]
        nic_mac = self.mac_addr_to_uint64(mac_ip_lut[port1[1]]) 
        
        # for nic in nic_list:
            # new_nic = nic.split('@')
            # port = new_nic[0]
            # print "port ", port
            # host = new_nic[1]       
            # print "host ", host
            # mac = mac_lut[host]              
            # print "host ", mac
            
        return nic_ip, nic_mac, nic_port
            
#-------------------------------------------------------------------------------------    
if __name__ == "__main__":
    TBTest = TBTest()
    TBTest.execute_tests()

    

    # --------------------------------------------------------------------------- #
    # test code
    #
    # for x in range(10): 
            # print '\rDownloading: %s (%d%%)' % ("|"*(x/2), x), 
            # sys.stdout.flush() 
            # time.sleep(0.1)  
    
        # for x in range(10): 
            # print '\r%s'%x, 
            # sys.stdout.flush() 
            # time.sleep(1)
        
        # print "\n"           
        # x = 2
        # for i in range(10): 
            # print 'WARNING Data Gen on 10G link nr %2d is BUSY counting %d \r' %(x,i), 
            # sys.stdout.flush() 
            # time.sleep(0.5)
        # print "\n"
        
        # return 1   
    # --------------------------------------------------------------------------- #            
