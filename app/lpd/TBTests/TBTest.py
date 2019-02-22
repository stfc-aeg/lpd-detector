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
import ctypes

import pprint

# Import Fem modules
#from FemClient import FemClient
from TBClient import *  #TBClient

            
class TBTest():

    # TBClient myTBClient   # don't know how to have class type as an object, use global instead

 #register ctrl bit mapping for mux selects 
    LL_MUX_RX_ORIG_SEL     = 0
    LL_MUX_RX_BYPASS_QDR_IN     = 2
    LL_MUX_RX_BYPASS_QDR_OUT     = 4
    LL_MUX_RX_BYPASS_PPC_IN     = 6
    LL_MUX_RX_BYPASS_PPC_OUT     = 8
    LL_MUX_RX_TERM     = 10
    LL_MUX_TX_ORIG_SEL     = 16
    LL_MUX_TX_BYPASS_QDR_IN     = 18
    LL_MUX_TX_BYPASS_QDR_OUT     = 20
    LL_MUX_TX_BYPASS_PPC_IN     = 22
    LL_MUX_TX_BYPASS_PPC_OUT     = 24
    LL_MUX_TX_TERM     = 26


                
    
    def set_10g_structs_variables(self):
       
        run_params = {
            'run_type' :   "10g_test",  # XFEL DAQ tests
                        #"ddr2_test",   # DDR2 memory tests
       
                        '10g_farm_mode' : 0,   
                        # 3 for farm mode with nic lists ; 2 for farm mode with fixed ip host and multiple ports ; # 1 for legacy non farm mode (only 1 ip host and port per link) 
                      'num_cycles'  : 1,
                      'playback' : 0, # 0 for DataGen or PPC  to PC ; 1 for playback rx (to load files into ddr2 memory)
                      'debug_level' : 1,    # higher values more print out
          'eth_ifg' : 0x000,   # ethernet inter frame gap  ; ensure receiving 10G NIC parameters have been set accordingly
                      'udp_pkt_len' : 8000, # udp packet length in bytes
          'TBHost' : '192.168.3.2',    # '192.168.2.2'  # ip address for 1 GbE fem controls  # net = 3 for burntoak ; net = 4 for uxbridge
          'TBPort' : 6969,   # udp port nr for 1 GbE fem controls (not to be confused with port nr for 10g links)
              'clear_10g_lut' : 0,   # 1 to clear 10g lut tables before start
              'using_10g_core' : 0,     # 0 if no xaui generated in F1-F4 design; 
              'using_aurora_core' : 0,     # 0 if no aurora generated in F1-F4 design (need aurora core if using crosspoint); 
              'using_ppc_core' : 1,     # 0 if no ppc generated in F1-F4 design; 
              'ppc_uart_terminal' : 1,    # ppc terminal output; 1 = PPC1 ; 2 = PPC2
              'll_hdr_trl' : 0  # 1 = enable headers and trailers from data gen (needed for ppc, but will generate errors in checker)
                    }  
     
        # look up table to match MAC addresses with IP for host NIC
        global mac_ip_lut
        mac_ip_lut = { '192.168.2.1' : '00-07-43-11-97-90', 
                    '192.168.3.1' : '00-07-43-11-97-98', 
                    '192.168.7.1' : '00-07-43-10-61-88'     # burntoak
            }  
      
    # F1 has links 1&2 , F2 has links 3&4, F3 links 5&6, F4 links 7&8
    # links 2,4,6,8  on FMC chan A's
    # links 1,3,5,7  on FMC chan B's
    # link 1 is at bottom of board
            
#        x10g_1 = {  'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),  # fpga mac address  
#                    'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),     # fpga ip address  
#                    'fpga_prt' : self.prt_addr_to_uint16('0000'),   # fpga port nr
#                    'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),   #  10G NIC channel mac address  
#                    'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),      # 10G NIC channel ip address
#                    'nic_prt' : self.prt_addr_to_uint16('61649'),   # 10G starting port nr for each cycle (increments by 1 for each frame in cycle)
#                    'num_prts' : 4, # number of ports to loop over before repeating
#                    'data_gen' : 1, # data generator type (1 for DataGen ; 2 for PPC/DDR2)   
#                    'data_format' : 0, # data format type  (0 for counting data)  
#                    'frame_len'  : 1024,    # frame len in bytes
#                    'num_frames' : 1,    # number of frames to send in each cycle
#                    'delay' : 0,    # delay offset wrt start of previous link in secs
#                    'enable'  : 0,    # enable this link
#                    'link_nr' : 1,   # link number
#                    'fpga_nr' : 1   # fpga number
#                }

# burntoak
        x10g_1 = {  'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),  # fpga mac address  
                    'fpga_ip'  : self.ip_addr_to_uint32('192.168.7.2'),     # fpga ip address  
                    'fpga_prt' : self.prt_addr_to_uint16('0000'),   # fpga port nr
                    'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-88'),   #  10G NIC channel mac address  
                    'nic_ip'  : self.ip_addr_to_uint32('192.168.7.1'),      # 10G NIC channel ip address
                    'nic_prt' : self.prt_addr_to_uint16('61649'),   # 10G starting port nr for each cycle (increments by 1 for each frame in cycle)
                    'num_prts' : 2, # number of ports to loop over before repeating
                    'data_gen' : 1, # data generator    
                    'data_format' : 0, # data format type   
                    'frame_len'  : 0x20008,    # frame len in bytes
                    'num_frames' : 50010,    # number of frames to send
                    'delay' : 2,    # delay offset wrt previous link in secs
                    'enable'  : 0,    # enable link
                    'link_nr' : 1,   # link number
                    'fpga_nr' : 1   # fpga number
                }

                        
        x10g_2 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.7.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-88'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.7.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x20008,    # frame len in bytes
                        'num_frames' : 50000,    # number of frames to send
                        'delay' : 2,    # delay offset wrt previous link in secs
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
                        'frame_len'  : 0x20008,    # frame len in bytes
                        'num_frames' : 200010,    # number of frames to send
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
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x20008,    # frame len in bytes
                        'num_frames' : 200000,    # number of frames to send
                        'delay' : 2,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 4,   # link number
                        'fpga_nr' : 2   # fpga number
                        } 
                        
        x10g_5 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.8.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'), 
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.8.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),  # 61649
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator      
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x20008,    # frame len in bytes   # 125000*8000
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 1,    # delay offset wrt previous link in secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 5,   # link number
                        'fpga_nr' : 3,   # fpga number                                                
#                       'nic_list' : [ '61649@192.168.2.1', '61650@192.168.2.1', '61652@192.168.2.1', '61654@192.168.2.1' ]
#                        'nic_list' : [ '61649@192.168.2.1', '61650@192.168.2.1' ]
                       'nic_list' : [ '61649@192.168.8.1', '61650@192.168.8.1' ]
                        } 
                        
        x10g_6 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.9.2'),    # ('192.168.7.2')
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-98'),     # ('00-07-43-10-61-88')  
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.9.1'),           # ('192.168.7.1')
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator      
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x20008,    # 0x20008, # 0x88,  # 0x40,    # frame len in bytes   # 125000*8000   # 0x20008 = for qdr lpd alg frame 128 KB
                        # need to set frame len one word bigger when without sop/eop ?
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 2,    # delay offset wrt previous link in secs
                        'enable'  : 1,    # enable link
                        'link_nr' : 6, 
                        'fpga_nr' : 3,   # fpga number                                                
                        #'nic_list' : [ '61649@192.168.3.1', '61650@192.168.3.1' ]
                        'nic_list' : [ '61649@192.168.9.1', '61650@192.168.9.1'  ]  # '192.168.7.1'
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
                        'frame_len'  : 0x20008,    # frame len in bytes
                        'num_frames' : 200010,    # number of frames to send
                        'delay' : 2,    # delay offset wrt previous link in secs
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
                        'num_prts' : 2, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 0x20008,    # frame len in bytes
                        'num_frames' : 200000,    # number of frames to send
                        'delay' : 2,    # delay offset wrt previous link in secs
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
        
        global fpga_mux_base_rdma
        global fpga_lut
        
        global clock_10g
        global clock_ppc
        global clock_rdma

        clock_10g = 156.25e6
        clock_ppc = 200.00e6
        clock_rdma = 100.00e6
        
        frame_gen_32b = 4
        frame_gen_64b = 8
                
        pp = pprint.PrettyPrinter(indent=4)
        
        # gpio mux for rdma address is now selected implicitly by gbe server using upper bits of address

# Move rdma mux base to first gpio output to match lpd fem

        #fpga_mux_base_rdma = 0x85000000      # 0x84000008; # RAW base address of GPIO controlling FPGA RDMA mux

        fpga_mux_base_term = 0x85000008;    # 0x84000000; # RAW base address of GPIO Terminal switch
       
        # fpga rdma access from master is switched by simple mux under gpio control
        # fpga 1 has links 1&2 ; fpga 2 has links 3&4 ; fpga 3 has links 5&6  ; fpga 4 has links 7&8 ;
        # links start at 1 not 0 (hence first element '0' in fpga_lut
        #fpga_lut = [0,1,1,2,2,3,3,4,4]       
        fpga_lut = [0,2,2,3,3,4,4,5,5]   # mapping changed master f/w v0101 , prior to using upper address bits to steer fpga mux    
            
        #x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8 = self.set_10g_structs_variables_te7redbridge()
        run_params, x10g_params, ddr2_params = self.set_10g_structs_variables()

# test reading values from file
        vars = dict()
        if run_params['using_aurora_core'] == 1: 


            with open("tb_config/tb_params3.txt") as f:     
                for line in f:
                    eq_index = line.find('=')
                    var_name = line[:eq_index].strip()
                    #number = float(line[eq_index + 1:].strip())
                    value = line[eq_index + 1:].strip()
                    vars[var_name] = value

            print(vars)

            #XPT_CONFIG_SET = vars['XPT_CONFIG_SET']
            #a = int(vars['xpt_input_long_range'], 16)
            #print "a = $%02x" % a
            #a = int(vars['xpt_input_long_range'], 16)
            #return
        
            # dictionary to associate signal lane names with Xpt I/O port nrs. I/O in port nr order.
            # naming convention is  TX and RX are with respect to Xpt
            xpt = {
            
                # switch output ports

                'X_Z3_TX28': 0,
                'X_Z3_TX29': 1,
                'X_Z3_TX7': 2,
                'X_Z3_TX9': 3,
                'X_Z3_TX14': 4,
                'X_Z3_TX13': 5,
                'X_Z3_TX15': 6,
                'X_Z3_TX21': 7,
                'X_Z3_TX4': 8,
                'X_Z3_TX27': 9,
                'X_Z3_TX25': 10,
                'X_Z3_TX26': 11,
                'X_Z3_TX2': 12,
                'X_Z3_TX16': 13,
                'X_Z3_TX18': 14,
                'X_Z3_TX22': 15,
                'X_Z3_TX8': 16,
                'X_Z3_TX30': 17,
                'X_Z3_TX6': 18,
                'X_Z3_TX10': 19,
                'X_Z3_TX12': 20,
                'X_Z3_TX32': 21,
                'X_Z3_TX11': 22,
                'X_Z3_TX31': 23,
                'X_Z3_TX23': 24,
                'X_Z3_TX5': 25,
                'X_Z3_TX3': 26,
                'X_Z3_TX24': 27,
                'X_Z3_TX20': 28,
                'X_Z3_TX17': 29,
                'X_Z3_TX19': 30,
                'X_Z3_TX1': 31,
                
                'F4_3_XAU_AUR_TX1': 40,
                'F4_3_XAU_AUR_TX0': 41,
                'F4_2_XAU_AUR_TX0': 42,
                'F4_2_XAU_AUR_TX1': 43,
                
                'F4_1_XAU_AUR_TX0': 48,
                'F4_1_XAU_AUR_TX1': 49,
                'F4_0_XAU_AUR_TX1': 50,
                'F4_0_XAU_AUR_TX0': 51,
                'F1_0_XAU_AUR_TX1': 52,
                'F1_0_XAU_AUR_TX0': 53,
                'F1_1_XAU_AUR_TX0': 54,
                'F1_1_XAU_AUR_TX1': 55,
                'F2_2_XAU_AUR_TX0': 56,
                'F2_3_XAU_AUR_TX1': 57,
                'F2_2_XAU_AUR_TX1': 58,
                'F3_0_XAU_AUR_TX1': 59,
                'F2_1_XAU_AUR_TX1': 60,
                'F2_0_XAU_AUR_TX0': 61,
                'F2_1_XAU_AUR_TX0': 62,
                'F2_0_XAU_AUR_TX1': 63,
                'F3_2_XAU_AUR_TX1': 64,
                'F3_3_XAU_AUR_TX0': 65,
                'F3_2_XAU_AUR_TX0': 66,
                'F3_3_XAU_AUR_TX1': 67,
                'F1_2_XAU_AUR_TX0': 68,
                'F1_2_XAU_AUR_TX1': 69,
                'F1_3_XAU_AUR_TX0': 70,
                'F1_3_XAU_AUR_TX1': 71,
                'F3_0_XAU_AUR_TX0': 72,
                'F3_1_XAU_AUR_TX1': 73,
                'F2_3_XAU_AUR_TX0': 74,
                'F3_1_XAU_AUR_TX0': 75,

                
                # switch input ports

                'Z3_X_RX27': 0,
                'Z3_X_RX30': 1,
                'Z3_X_RX29': 2,
                'Z3_X_RX10': 3,
                'F3_1_XAU_AUR_RX1': 4,
                'F3_3_XAU_AUR_RX0': 5,
                'F3_2_XAU_AUR_RX0': 6,
                'F4_2_XAU_AUR_RX1': 7,                        
                'Z3_X_RX7': 8,
                'Z3_X_RX9': 9,
                'Z3_X_RX19': 10,
                'Z3_X_RX20': 11,
                'F3_1_XAU_AUR_RX0': 12,
                'F3_3_XAU_AUR_RX1': 13,
                'F4_0_XAU_AUR_RX0': 14,
                'F4_1_XAU_AUR_RX0': 15,
                'Z3_X_RX25': 16,
                'Z3_X_RX18': 17,
                'Z3_X_RX28': 18,
                'Z3_X_RX8': 19,
                'F2_3_XAU_AUR_RX0': 20,
                'F4_2_XAU_AUR_RX0': 21,
                'F3_2_XAU_AUR_RX1': 22,
                'F4_0_XAU_AUR_RX1': 23,
                'Z3_X_RX16': 24,
                'Z3_X_RX6': 25,
                'Z3_X_RX26': 26,
                'Z3_X_RX17': 27,
                'F2_2_XAU_AUR_RX1': 28,
                'F4_1_XAU_AUR_RX1': 29,
                'F3_0_XAU_AUR_RX1': 30,
                'F3_0_XAU_AUR_RX0': 31,
                'Z3_X_RX4': 32,
                'Z3_X_RX24': 33,
                'Z3_X_RX15': 34,
                'Z3_X_RX5': 35,
                'F2_3_XAU_AUR_RX1': 36,
                'F2_1_XAU_AUR_RX0': 37,
                'F2_1_XAU_AUR_RX1': 38,
                'F2_0_XAU_AUR_RX0': 39,
                'Z3_X_RX14': 40,
                'Z3_X_RX32': 41,
                'Z3_X_RX13': 42,
                'Z3_X_RX23': 43,
                'F2_0_XAU_AUR_RX1': 44,
                'F4_3_XAU_AUR_RX1': 45,
                'F2_2_XAU_AUR_RX0': 46,
                'F1_3_XAU_AUR_RX0': 47,
                'Z3_X_RX3': 48,
                'Z3_X_RX31': 49,
                'Z3_X_RX2': 50,
                'Z3_X_RX22': 51,
                'F1_3_XAU_AUR_RX1': 52,
                'F4_3_XAU_AUR_RX0': 53,
                'F1_1_XAU_AUR_RX0': 54,
                'F1_2_XAU_AUR_RX1': 55,
                'Z3_X_RX12': 56,
                
                'Z3_X_RX1': 58,
                
                'F1_2_XAU_AUR_RX0': 60,
                'F1_0_XAU_AUR_RX1': 61,
                            
                'Z3_X_RX11': 64,

                'F1_0_XAU_AUR_RX0': 68,  

                'Z3_X_RX21': 72,

                'F1_1_XAU_AUR_RX1': 76
                
                }

            NR_AUR_LANES = 4
            SRC = 0
            DST = 1
            OUT = 0
            IN = 1

            CONFIG_XPT = 1
            
            # Crosspoint mappings  ; now read from file
            
            # With blue (ERNI) cable loopback SRC and DST connectors must be the SAME  ; as there is a ONE to ONE mapping on cable
            # With CXP cables loopback must SRC and DST connectors must be DIFFERENT (but same half e.g. U to U or L to L) ; as cable must mate with TWO connectors (which pairs depends how CXP cables are plugged in for loopback!)
            # ie blue cable tests configurations won't work with CXP cables and vice versa
            
            #XPT_CONFIG_SET = 'XPT_CONFIG_F3_A&B_BLUE_CABLE_KA'
            XPT_CONFIG_SET = vars['XPT_CONFIG_SET']
            
            #'XPT_CONFIG_F3_A&B_LOOPBACK'       # F3 loopback chans A and B to themselves Tx to Rx
            #'XPT_CONFIG_F3_A_TO_B_DUPLEX'      # F3 chans A to B  Tx & Rx
            #'XPT_CONFIG_F3_A_BLUE_CABLE'       # F3 chan A loopback via blue cable
            #'XPT_CONFIG_F3_A&B_BLUE_CABLE_KA'       # F3 chans A and B loopback via blue cable connector KA to KA 
            #'XPT_CONFIG_F3_A&B_BLUE_CABLE_KB'       # F3 chans A and B loopback via blue cable connector KB to KB 
            #'XPT_CONFIG_F3_A_BLUE_CABLE_KAUL'       # F3 chan A loopback via blue cable snake one extra loop
            #'XPT_CONFIG_F3_A_BLUE_CABLE_SNAKE_2'       # F3 chan A loopback via blue cable snake test 2 extra loops
            #'XPT_CONFIG_F3_A_BLUE_CABLE_SNAKE_3'       # F3 chan A loopback via blue cable snake test 3  max nr loops 
            #'XPT_CONFIG_F3_A_CXP_LOOPBACK_KAU_KBU'       # F3 chan A loopback using RTM and CXP cable 
            #'XPT_CONFIG_F3_A_CXP_SNAKE_1'       # F3 chan A loopback using RTM and CXP cable 
            
            # tuples of aurora channels ; 1st Outputs , 2nd Inputs
            # NB F4 is physically top FPGA on board
            
            F4A = (
                        ( xpt['F4_2_XAU_AUR_TX0'], xpt['F4_2_XAU_AUR_TX1'], xpt['F4_3_XAU_AUR_TX0'], xpt['F4_3_XAU_AUR_TX1'] ),
                        ( xpt['F4_2_XAU_AUR_RX0'], xpt['F4_2_XAU_AUR_RX1'], xpt['F4_3_XAU_AUR_RX0'], xpt['F4_3_XAU_AUR_RX1'] )
                        )

            F4B = (
                        ( xpt['F4_0_XAU_AUR_TX0'], xpt['F4_0_XAU_AUR_TX1'], xpt['F4_1_XAU_AUR_TX0'], xpt['F4_1_XAU_AUR_TX1'] ),
                        ( xpt['F4_0_XAU_AUR_RX0'], xpt['F4_0_XAU_AUR_RX1'], xpt['F4_1_XAU_AUR_RX0'], xpt['F4_1_XAU_AUR_RX1'] )
                        )

            F3A = (
                        ( xpt['F3_2_XAU_AUR_TX0'], xpt['F3_2_XAU_AUR_TX1'], xpt['F3_3_XAU_AUR_TX0'], xpt['F3_3_XAU_AUR_TX1'] ),
                        ( xpt['F3_2_XAU_AUR_RX0'], xpt['F3_2_XAU_AUR_RX1'], xpt['F3_3_XAU_AUR_RX0'], xpt['F3_3_XAU_AUR_RX1'] )
                        )

            F3B = (
                        ( xpt['F3_0_XAU_AUR_TX0'], xpt['F3_0_XAU_AUR_TX1'], xpt['F3_1_XAU_AUR_TX0'], xpt['F3_1_XAU_AUR_TX1'] ),
                        ( xpt['F3_0_XAU_AUR_RX0'], xpt['F3_0_XAU_AUR_RX1'], xpt['F3_1_XAU_AUR_RX0'], xpt['F3_1_XAU_AUR_RX1'] )
                        )

            F2A = (
                        ( xpt['F2_2_XAU_AUR_TX0'], xpt['F2_2_XAU_AUR_TX1'], xpt['F2_3_XAU_AUR_TX0'], xpt['F2_3_XAU_AUR_TX1'] ),
                        ( xpt['F2_2_XAU_AUR_RX0'], xpt['F2_2_XAU_AUR_RX1'], xpt['F2_3_XAU_AUR_RX0'], xpt['F2_3_XAU_AUR_RX1'] )
                        )

            F2B = (
                        ( xpt['F2_0_XAU_AUR_TX0'], xpt['F2_0_XAU_AUR_TX1'], xpt['F2_1_XAU_AUR_TX0'], xpt['F2_1_XAU_AUR_TX1'] ),
                        ( xpt['F2_0_XAU_AUR_RX0'], xpt['F2_0_XAU_AUR_RX1'], xpt['F2_1_XAU_AUR_RX0'], xpt['F2_1_XAU_AUR_RX1'] )
                        )

            F1A = (
                        ( xpt['F1_2_XAU_AUR_TX0'], xpt['F1_2_XAU_AUR_TX1'], xpt['F1_3_XAU_AUR_TX0'], xpt['F1_3_XAU_AUR_TX1'] ),
                        ( xpt['F1_2_XAU_AUR_RX0'], xpt['F1_2_XAU_AUR_RX1'], xpt['F1_3_XAU_AUR_RX0'], xpt['F1_3_XAU_AUR_RX1'] )
                        )

            F1B = (
                        ( xpt['F1_0_XAU_AUR_TX0'], xpt['F1_0_XAU_AUR_TX1'], xpt['F1_1_XAU_AUR_TX0'], xpt['F1_1_XAU_AUR_TX1'] ),
                        ( xpt['F1_0_XAU_AUR_RX0'], xpt['F1_0_XAU_AUR_RX1'], xpt['F1_1_XAU_AUR_RX0'], xpt['F1_1_XAU_AUR_RX1'] )
                        )


            # CXP connectors K on RTM  A to B  Upper and Lower
            KAU = (
                        ( xpt['X_Z3_TX1'], xpt['X_Z3_TX2'], xpt['X_Z3_TX3'], xpt['X_Z3_TX4'] ),
                        ( xpt['Z3_X_RX1'], xpt['Z3_X_RX2'], xpt['Z3_X_RX3'], xpt['Z3_X_RX4'] )
                        )
            KAL = (
                        ( xpt['X_Z3_TX5'], xpt['X_Z3_TX6'], xpt['X_Z3_TX7'], xpt['X_Z3_TX8'] ),
                        ( xpt['Z3_X_RX5'], xpt['Z3_X_RX6'], xpt['Z3_X_RX7'], xpt['Z3_X_RX8'] )
                        )

            KBU = (
                        ( xpt['X_Z3_TX9'], xpt['X_Z3_TX10'], xpt['X_Z3_TX11'], xpt['X_Z3_TX12'] ),
                        ( xpt['Z3_X_RX9'], xpt['Z3_X_RX10'], xpt['Z3_X_RX11'], xpt['Z3_X_RX12'] )
                        )
            KBL = (
                        ( xpt['X_Z3_TX13'], xpt['X_Z3_TX14'], xpt['X_Z3_TX15'], xpt['X_Z3_TX16'] ),
                        ( xpt['Z3_X_RX13'], xpt['Z3_X_RX14'], xpt['Z3_X_RX15'], xpt['Z3_X_RX16'] )
                        )
                        
            KCU = (
                        ( xpt['X_Z3_TX17'], xpt['X_Z3_TX18'], xpt['X_Z3_TX19'], xpt['X_Z3_TX20'] ),
                        ( xpt['Z3_X_RX17'], xpt['Z3_X_RX18'], xpt['Z3_X_RX19'], xpt['Z3_X_RX20'] )
                        )
            KCL = (
                        ( xpt['X_Z3_TX21'], xpt['X_Z3_TX22'], xpt['X_Z3_TX23'], xpt['X_Z3_TX24'] ),
                        ( xpt['Z3_X_RX21'], xpt['Z3_X_RX22'], xpt['Z3_X_RX23'], xpt['Z3_X_RX24'] )
                        )

            KDU = (
                        ( xpt['X_Z3_TX25'], xpt['X_Z3_TX26'], xpt['X_Z3_TX27'], xpt['X_Z3_TX28'] ),
                        ( xpt['Z3_X_RX25'], xpt['Z3_X_RX26'], xpt['Z3_X_RX27'], xpt['Z3_X_RX28'] )
                        )
            KDL = (
                        ( xpt['X_Z3_TX29'], xpt['X_Z3_TX30'], xpt['X_Z3_TX31'], xpt['X_Z3_TX32'] ),
                        ( xpt['Z3_X_RX29'], xpt['Z3_X_RX30'], xpt['Z3_X_RX31'], xpt['Z3_X_RX32'] )
                        )
                    
        print "===============================================================================" 
        
        if run_params['debug_level'] > 0:
                pp.pprint(run_params)
        try:
            # myTBClient = TBClient((TBHost, TBPort), timeout=10)
            myTBClient = TBClient((run_params['TBHost'], run_params['TBPort']), timeout=10)
        except FEMClientError as errString:
            print "Error: Train Builder connection failed (is Master GbE server running?:", errString
            sys.exit(1)
      

        print "     Master Firmware vers = %08x" % myTBClient.get_master_firmware_vers()
            

        #if CONFIG_XPT == 1:   # crosspoint testing taken from config_xpoint.m
        if run_params['using_aurora_core'] == 1: 
        
            myTBClient.xpoint_reset()
            print "Xpoint Reset"

            #myTBClient.rdmaWrite((myTBClient.master_id<<28) | myTBClient.master_xpoint+13, 0x3e)
            #value = myTBClient.rdmaRead((myTBClient.master_id<<28) | myTBClient.master_xpoint+13, 1)[0]
            #print "xpt ctrl reset reg : = $%08x:" %value
            
            #value = myTBClient.rdmaRead((myTBClient.master_id<<28) | myTBClient.master_xpoint+24, 1)[0]
            #print "xpt ctrl sanity reg : = $%08x:" %value
            
            myTBClient.xpoint_write(0xff, 0x0)  # ms_xpoint_write(s, 255, 0, 1, 'Page 0');

            # general config reg 
            # 0x18 = GRPLNMODE pin ; strobe ASC with pin.xSET ; on with smart power ;  DEFAULT           
            # 0x88 = lane mode ; direct ASC ; on with smart power ;            
            # 0x01 = standby ;
            xpt_general_config = 0x88           
            print "Setting XPt General config reg : = $%02x:" %xpt_general_config                        
            myTBClient.xpoint_write(0x03, xpt_general_config)       # ms_xpoint_write(s, 3, 136, 1, 'Set Lane Mode');
            
            #xpoint_id = myTBClient.xpoint_read(1)
            #print "Crosspoint Device ID : = $%08x:" %xpoint_id
            #xpoint_pagesel = myTBClient.xpoint_read(255)
            #print "Crosspoint pagesel : = %d:" %xpoint_pagesel

            # INPUT buffer config reg 
            # 0xf0 = global ; 100 Ohm   ; DEFAULT
            # 0xb0 = individual equalisation ; 100 Ohm   
            xpt_input_config = 0xf0           
            print "Setting XPt INPUT buffer config reg : = $%02x:" %xpt_input_config
            myTBClient.xpoint_write(0x09, xpt_input_config)      

            # INPUT buffer Global Equalisation reg 
            # 0x00  = 9" ; Dead-Reckoned value from Mindspeed 2xxxx-APP-004-A note ; DEFAULT
            # 0x02  = 20" ; 
            # 0x3d  = 32" ; 
            # 0xed  = 40" ;
            xpt_glob_eq = 0x00           
            print "Setting XPt Global Equalisation reg : = $%02x:" %xpt_glob_eq
            myTBClient.xpoint_write(0x0a, xpt_glob_eq)      

            # OUTPUT buffer config reg 
            # 0xb0 = global ; 800 mV ; 0db de-emphasis  ; DEFAULT
            # 0xb2 = global ; 800 mV ; 2db 
            # 0xb4 = global ; 800 mV ; 4db 
            # 0xb6 = global ; 800 mV ; 6db 
            # 0xc6 = global ; 1000 mV ; 6db 
            # 0x00 = individual output settings
            xpt_output_config = 0xb0           
            print "Setting XPt OUTPUT buffer config reg : = $%02x:" %xpt_output_config
            myTBClient.xpoint_write(0x0b, xpt_output_config)      #ms_xpoint_write(s, 11, 176, 1, '0db');

            # different settings for links to FPGA (SHORT range) and links to connector (LONG range)
            if 1:

                print "INFO: Overriding XPt Global Buffers with Individual Settings "

                xpt_input_config = 0xb0           
                print "Setting XPt INPUT buffer config reg : = $%02x:" %xpt_input_config
                myTBClient.xpoint_write(0x09, xpt_input_config)      

                xpt_output_config = 0x00           
                print "Setting XPt OUTPUT buffer config reg : = $%02x:" %xpt_output_config
                myTBClient.xpoint_write(0x0b, xpt_output_config)     

                xpt_input_short_range = int(vars['xpt_short_range_input_equalisation'], 16)
                #xpt_input_short_range = 0x00           
                print "XPt INPUT setting from FPGA : = $%02x:" %xpt_input_short_range
                xpt_input_long_range = int(vars['xpt_long_range_input_equalisation'], 16)
                #xpt_input_long_range = 0xed           
                print "XPt INPUT setting from Conn : = $%02x:" %xpt_input_long_range

                xpt_output_short_range = int(vars['xpt_short_range_output_swing_deemphasis'], 16)
                #xpt_output_short_range = 0xb0           
                print "XPt OUTPUT setting to FPGA : = $%02x:" %xpt_output_short_range
                xpt_output_long_range = int(vars['xpt_long_range_output_swing_deemphasis'], 16)
                #xpt_output_long_range = 0xc6           
                print "XPt OUTPUT setting to Conn : = $%02x:" %xpt_output_long_range

                for key in xpt: # loop over all xpt ports
                    if "TX" in key:    # xpt outputs                   
                        myTBClient.xpoint_write(0xff, 0x0e) # page:  individual Output buffer control
                        if key[0] == 'F' :  # links to FPGA SHORT
                            myTBClient.xpoint_write(xpt[key], xpt_output_short_range)     
                            #print key, 'Xpt Output SHORT range corresponds to', xpt[key]
                        elif key[0] == 'X' :  # links to Connector LONG
                            myTBClient.xpoint_write(xpt[key], xpt_output_long_range)  
                            #print key, 'Xpt Output LONG range corresponds to', xpt[key]
                        else:
                            print "*** ERROR: Illegal Output Xpt Port Name : = %s:" %key
                            return 1
                    elif "RX" in key:  # xpt inputs
                        myTBClient.xpoint_write(0xff, 0x0c) # page: individual Input buffer control
                        if key[0] == 'F' :  # links to FPGA SHORT
                            myTBClient.xpoint_write(xpt[key], xpt_input_short_range)   
                            #print key, 'Xpt Input SHORT range corresponds to', xpt[key]    
                        elif key[0] == 'Z' :  # links to Connector LONG
                            myTBClient.xpoint_write(xpt[key], xpt_input_long_range)  
                            #print key, 'Xpt Input LONG range corresponds to', xpt[key]
                        else:
                            print "*** ERROR: Illegal Input Xpt Port Name : = %s:" %key
                            return 1
                    else:
                        print "*** ERROR: Illegal Xpt Port Name : = %s:" %key
                        return 1                           
       
                
            # ASC Page :  Configure switch FPGA F3 : loopback chan A and B  each lane Tx back to Rx 

            # get xpoint temperatures
            #myTBClient.xpoint_write(0xff, 0x21)     
            #data = self.xpoint_read(addr)

            myTBClient.xpoint_write(0xff, 0x1)     # ms_xpoint_write(s, 255, 1, 1, 'Page ASC');

            # power down all switch lanes
            for i in range(80):
                myTBClient.xpoint_write(i, 0xff) 
                
            print " Xpt Configuation Set : %s" %XPT_CONFIG_SET
            
            #return

            # if XPT_CONFIG_SET == 'XPT_CONFIG_F3_A&B_LOOPBACK':
                # # # loopback F3 chan A  Tx to Rx
                # # myTBClient.xpoint_write(66, 06) #ms_xpoint_write(s, 66, 06, 1, 'F3_2_XAU_AUR_TX0 ->F3_2_XAU_AUR_RX0');
                # # myTBClient.xpoint_write(64, 22) #ms_xpoint_write(s, 64, 22, 1, 'F3_2_XAU_AUR_TX1 ->F3_2_XAU_AUR_RX1');
                # # myTBClient.xpoint_write(65, 05) #ms_xpoint_write(s, 65, 05, 1, 'F3_3_XAU_AUR_TX0 ->F3_3_XAU_AUR_RX0');
                # # myTBClient.xpoint_write(67, 13) #ms_xpoint_write(s, 67, 13, 1, 'F3_3_XAU_AUR_TX1 ->F3_3_XAU_AUR_RX1');

                # # # loopback F3 chan A  Tx to Rx
                # myTBClient.xpoint_write(xpt['F3_2_XAU_AUR_TX0'], xpt['F3_2_XAU_AUR_RX0']) 
                # myTBClient.xpoint_write(xpt['F3_2_XAU_AUR_TX1'], xpt['F3_2_XAU_AUR_RX1']) 
                # myTBClient.xpoint_write(xpt['F3_3_XAU_AUR_TX0'], xpt['F3_3_XAU_AUR_RX0']) 
                # myTBClient.xpoint_write(xpt['F3_3_XAU_AUR_TX1'], xpt['F3_3_XAU_AUR_RX1']) 
              
            # FPGA F4
            if XPT_CONFIG_SET == 'XPT_CONFIG_F4_A&B_LOOPBACK':
                xpt_map = [(F4A,F4A), (F4B,F4B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F4_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL':
                xpt_map = [(F4A,KAU), (KBU,KAL), (KBL,F4A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F4_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL_KCU_KDU_KCL_KDL':
                xpt_map = [(F4A,KAU), (KBU,KAL), (KBL,KCU), (KDU,KCL), (KDL,F4A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F4_A_KCU_KDU_&_F4_B_KAU_KBU':
                xpt_map = [(F4A,KCU), (KDU,F4A), (F4B,KAU), (KBU,F4B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F4_A_KCU_KDU_KCL_KDL_&_F4_B_KAU_KBU_KAL_KBL':
                xpt_map = [(F4A,KCU), (KDU,KCL), (KDL,F4A), (F4B,KAU), (KBU,KAL), (KBL,F4B)]

            # FPGA F3
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A&B_LOOPBACK':
                xpt_map = [(F3A,F3A), (F3B,F3B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_TO_B_DUPLEX':
                xpt_map = [(F3A,F3B), (F3B,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_BLUE_CABLE':
                xpt_map = [(F3A,KAU), (KAU,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A&B_BLUE_CABLE_KA':
                xpt_map = [(F3A,KAU), (KAU,F3A), (F3B,KAL), (KAL,F3B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A&B_BLUE_CABLE_KB':
                xpt_map = [(F3A,KBU), (KBU,F3A), (F3B,KBL), (KBL,F3B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_BLUE_CABLE_KAUL':
                xpt_map = [(F3A,KAU), (KAU,KAL), (KAL,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_BLUE_CABLE_SNAKE_2':
                xpt_map = [(F3A,KAU), (KAU,KAL), (KAL,KBU), (KBU,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_BLUE_CABLE_SNAKE_3':
                xpt_map = [(F3A,KAU), (KAU,KAL), (KAL,KBU), (KBU,KBL) , (KBL,KCU), (KCU,KCL), (KCL,KDU), (KDU,KDL), (KDL,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_CXP_LOOPBACK_KAU_KBU':
                xpt_map = [(F3A,KAU), (KBU,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_CXP_LOOPBACK_KCU_KDU':
                xpt_map = [(F3A,KCU), (KDU,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL':
                xpt_map = [(F3A,KAU), (KBU,KAL), (KBL,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F3_A_CXP_LOOPBACK_KCU_KDU_KCL_KDL':
                xpt_map = [(F3A,KCU), (KDU,KCL), (KDL,F3A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F3_A_KCU_KDU_&_F3_B_KAU_KBU':
                xpt_map = [(F3A,KCU), (KDU,F3A), (F3B,KAU), (KBU,F3B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F3_A_KCU_KDU_KCL_KDL_&_F3_B_KAU_KBU_KAL_KBL':
                xpt_map = [(F3A,KCU), (KDU,KCL), (KDL,F3A), (F3B,KAU), (KBU,KAL), (KBL,F3B)]

            # FPGA F2
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F2_A&B_LOOPBACK':
                xpt_map = [(F2A,F2A), (F2B,F2B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F2_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL':
                xpt_map = [(F2A,KAU), (KBU,KAL), (KBL,F2A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F2_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL_KCU_KDU_KCL_KDL':
                xpt_map = [(F2A,KAU), (KBU,KAL), (KBL,KCU), (KDU,KCL), (KDL,F2A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F2_A_KCU_KDU_&_F2_B_KAU_KBU':
                xpt_map = [(F2A,KCU), (KDU,F2A), (F2B,KAU), (KBU,F2B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F2_A_KCU_KDU_KCL_KDL_&_F2_B_KAU_KBU_KAL_KBL':
                xpt_map = [(F2A,KCU), (KDU,KCL), (KDL,F2A), (F2B,KAU), (KBU,KAL), (KBL,F2B)]

            # FPGA F1
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F1_A&B_LOOPBACK':
                xpt_map = [(F1A,F1A), (F1B,F1B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F1_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL':
                xpt_map = [(F1A,KAU), (KBU,KAL), (KBL,F1A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_F1_A_CXP_LOOPBACK_KAU_KBU_KAL_KBL_KCU_KDU_KCL_KDL':
                xpt_map = [(F1A,KAU), (KBU,KAL), (KBL,KCU), (KDU,KCL), (KDL,F1A)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F1_A_KCU_KDU_&_F1_B_KAU_KBU':
                xpt_map = [(F1A,KCU), (KDU,F1A), (F1B,KAU), (KBU,F1B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F1_A_KCU_KDU_KCL_KDL_&_F1_B_KAU_KBU_KAL_KBL':
                xpt_map = [(F1A,KCU), (KDU,KCL), (KDL,F1A), (F1B,KAU), (KBU,KAL), (KBL,F1B)]
            elif XPT_CONFIG_SET == 'XPT_CONFIG_CXP_LOOPBACK_F1_A_KAU_KBU_&_F1_B_KCU_KDU':
                xpt_map = [(F1A,KAU), (KBU,F1A), (F1B,KCU), (KDU,F1B)]

            a = 0
            for conn in xpt_map:
                if a%2 == 0:
                    txt = "lane (from fpga to xpt)"
                else:
                    txt = "lane (from xpt to fpga)"
                for lane in range(NR_AUR_LANES):                
                    print " %s # %d ; DST = %d ; SRC = %d" %( txt, lane, conn[DST][OUT][lane], conn[SRC][IN][lane])
                    myTBClient.xpoint_write(conn[DST][OUT][lane], conn[SRC][IN][lane])                
                a=a+1
                                
            if run_params['debug_level'] > 0:
                page = 0x0
                first_reg = 0x0
                last_reg = 0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)
            if run_params['debug_level'] > 0:
                first_reg = 0x40
                last_reg = 0x49
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

            if run_params['debug_level'] > 2:
                page = 0x1
                first_reg = 0  # 0x0
                last_reg = 0x80   # 0x80  0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

            if run_params['debug_level'] > 2:
                page = 0x3
                first_reg = 0x0
                last_reg = 0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

                page = 0x5
                first_reg = 0x0
                last_reg = 0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

                page = 0x7
                first_reg = 0x0
                last_reg = 0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

                page = 0x8
                first_reg = 0x0
                last_reg = 0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

                page = 0xa
                first_reg = 0x0
                last_reg = 0xe
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

            if run_params['debug_level'] > 0:
                page = 0xc
                first_reg = 0x0
                last_reg = 0x04
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

                page = 0xe
                first_reg = 0x0
                last_reg = 0x04
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)

            if run_params['debug_level'] > 2:
                page = 0x21 # temperatures
                first_reg = 0x0
                last_reg = 0xd
                myTBClient.xpoint_dump_regs((myTBClient.master_id<<28) | myTBClient.master_xpoint, page, first_reg, last_reg)
             
            #return

#----------------------------------------------------------------------------------------        
 
    # set FPGA to test here       
        fpga_nr = 3
        print "==================================================" 
        print "===============  TESTING FPGA F%d   ===============" %fpga_nr
        print "==================================================" 
        
        #RDMA switch is OBSOLETE as Embedded code steers GPIO using rdma address.
        #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_nr)   # switch RDMA.  
       
        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_term, fpga_nr)  # switch terminal to fpga
        response = myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.f1_f4_ctrl+15, run_params['ppc_uart_terminal']-1)  # selects either ppc1 or ppc2 term output from selected fpga
        print "Switching PPC Terminal output to F%d : PPC#%d:" %(fpga_nr, run_params['ppc_uart_terminal'])

        print "Dump of regs for TB F1_F4 control"
        myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.f1_f4_ctrl, 20)

        print "     Master Firmware vers = %08x" % myTBClient.get_master_firmware_vers()
        #for i in range(1,4):
        #   print "         F%d Firmware vers = %08x" % (i, myTBClient.get_fe_firmware_vers(i))
        print "         F%d Firmware vers = %08x" % (fpga_nr, myTBClient.get_fe_firmware_vers(fpga_nr))

        #return 0   # return here if just changing terminal output 

        if 0:   # debugging rdma reg writes

            # Resets QDR
            myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+10, 0)   
        
            # QDR test
            #myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.qdr+0, 0x2000) 
            #myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.qdr+1, 0x3000) 
            print "Dump of regs for QDR" 
            myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.qdr, 24)


            #return 0  
 
        if 1:    # test bram comms           
                        
            if run_params['debug_level'] >= 0:
                print "Dump of regs for BRAM on PPC 1"
                myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.bram_ppc1, 32)
      

#============ special ddr2 test ; needs corresponding dma code running on both ppcs

        if (run_params['run_type'] == "ddr2_test") :  

          fpga_nr = 1
          #RDMA switch is OBSOLETE as Embedded code steers GPIO using rdma address.
          #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_nr-1)   # switch RDMA

          print "Starting DDR2 Memory Test..."
          myTBClient.clear_dma_tx((fpga_nr<<28) | myTBClient.bram_ppc1, 0) 
          myTBClient.init_ppc_bram((fpga_nr<<28) | myTBClient.bram_ppc1, 0xbeef0001) 

          myTBClient.clear_dma_tx((fpga_nr<<28) | myTBClient.bram_ppc2, 0) 
          myTBClient.init_ppc_bram((fpga_nr<<28) | myTBClient.bram_ppc2, 0xbeef0002) 

          # Resets ppc bram_ppc1
          myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+9, 0)   
          # Resets ppc bram_ppc2
          myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+9, 1)   

          theDelay = 10
          print "Waiting for PPCs 1&2 to reset %s seconds.." % theDelay
          time.sleep(theDelay)

          myTBClient.clear_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_64b)              
          myTBClient.clear_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_32b)
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_64b, clock_ppc)
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_32b, clock_ppc)              

          myTBClient.clear_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc2_32b)
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc2_32b, clock_ppc)              

          myTBClient.clear_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_tx)
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_tx, clock_ppc)              
           
          # resets the counters start values in the Frame Gens (so ppc knows what's coming!)
          myTBClient.soft_reset_ll_frm_gen((fpga_nr<<28) | myTBClient.data_gen_2)  
          myTBClient.soft_reset_ll_frm_gen((fpga_nr<<28) | myTBClient.data_gen_3)  

          myTBClient.setup_ll_frm_gen((fpga_nr<<28) | myTBClient.data_gen_2, (0x40+frame_gen_32b)/frame_gen_32b, 0, 0, 1)  
          myTBClient.setup_ll_frm_gen((fpga_nr<<28) | myTBClient.data_gen_3, (0x100000+frame_gen_64b)/frame_gen_64b, 0, 0, 1)    

          response = myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_gen_2+7, 0x12345678)  # fix ll frame header
          response = myTBClient.setbit((fpga_nr<<28) | myTBClient.data_gen_2+4, 8)  

          print "Start polling on DMA Rx engine then immediately send Trigger Frame Gen .."
          # use same comms as for Tx , but it's really a Rx this time
          myTBClient.start_dma_tx((fpga_nr<<28) | myTBClient.bram_ppc1, 0) 
          myTBClient.start_dma_tx((fpga_nr<<28) | myTBClient.bram_ppc2, 0) 

# send frames
#          if ppc_nr == 1:
          myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+0, 3) # trigger local link frame gen to ppc1
#          else:
          myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+0, 4) # trigger local link frame gen to ppc2 

# measure rates
          print "Wait for transfer to complete before monitoring .."
          time.sleep(5)
          print "Rates on LL to PPC1 Rx.."
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_64b, clock_ppc)              
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_32b, clock_ppc)              
          print "Rates on LL to PPC2 Rx.."
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc2_32b, clock_ppc)              

          print "Rates on PPC1 Tx .."
          myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.mon_ppc1_tx, clock_ppc)              

          print "Dump of Frame Gen regs for PPC 1 "
          myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_gen_2, 16)
          print "Dump of Frame Gen regs for PPC 2 "
          myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_gen_3, 16)

          print "Dump of LL Checker regs for PPC 1 "
          myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_chk_ppc1_tx, 16)

          return
          
#============
                          
        # initialise

        if 0:
            f1_f4_ctrl_base = (fpga_nr<<28) | myTBClient.f1_f4_ctrl      

            print "Dump of regs for TB F1_F4 control"
            myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)

            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.f1_f4_ctrl+7, 0xbeefface) 

            print "Dump of regs for TB F1_F4 control"
            myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)

            # Resets udp 10g chanA and chanB
           ### myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+1, 0)   
          ###  print " Resetting UDP Chans A & B"

            print "Dump of regs for TB F1_F4 control"
            myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)
            return 0
        else:
            f1_f4_ctrl_base = (fpga_nr<<28) | myTBClient.f1_f4_ctrl      

   # following reset here was causing chipscope on output to trigger spuriously and giving spurious checker errors ?
   # started happening after removing xaui and trying to drive local link channel datagen and checker with system rdma clock
   # Now instead reset checker by s/w after link path is configured.
   
      #### Resets udp 10g chanA and chanB
      ###myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.f1_f4_ctrl+1, 0)   
      ### print "Reset UDP Chans A & B"

            if run_params['debug_level'] > 2:
                print "Checker on Tx Term  Chan A"
                myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_chk_0, 20)
                print "Checker on Tx Term  Chan B"
                myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_chk_1, 20)

            if run_params['debug_level'] > 2:
                print "Dump of regs for TB F1_F4 control"
                myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)

            data_type = 0     # should match datagen setting
            control_reg = data_type & 0x00000003
            control_reg = control_reg << 4

            #turn ll frame header/trailer mode on if required
            if run_params['ll_hdr_trl'] == 1:
                control_reg = control_reg | 0x00000001
            else:
                control_reg = control_reg & 0xFFFFFFFE 

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


            # checker uses same settings read back from data gen
            frame_nr = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_0+2, 1)[0]  # frame nr
            frame_len = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_0+1, 1)[0]  # frame len in samples
            control_reg = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_0+4, 1)[0]  # data type
            data_0 = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_0+5, 1)[0]  # init
            data_1 = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_0+6, 1)[0]  # init

            # link 6 = F3 chan A
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_0+2, frame_nr) # frame nr
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_0+1, frame_len)  # nr of transfers (64 bit)
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_0+4, control_reg) # format (bit 0=1 for sop)
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_0+5, data_0) # init value
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_0+6, data_1) # init value


            # chan B
            frame_nr = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_1+2, 1)[0]  # frame nr
            frame_len = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_1+1, 1)[0]  # frame len in samples
            control_reg = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_1+4, 1)[0]  # data type
            data_0 = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_1+5, 1)[0]  # init
            data_1 = myTBClient.rdmaRead((fpga_nr<<28) | myTBClient.data_gen_1+6, 1)[0]  # init

            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_1+2, frame_nr) # frame nr
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_1+1, frame_len)  # nr of transfers (64 bit)
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_1+4, control_reg) # format (bit 0=1 for sop)
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_1+5, data_0) # init value
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.data_chk_1+6, data_1) # init value


            # QDR
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.qdr+0, 0x4000-1) # chan A frame len   #  0x4000
            myTBClient.rdmaWrite((fpga_nr<<28) | myTBClient.qdr+1, 0x0) # chan B frame len

            ###print "Dump of regs for QDR" 
            #myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.qdr, 24)
            

        for link in x10g_params:       
            self.init(link, myTBClient)   

        print "after init  Dump of regs for TB F1_F4 control"
        myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)

#        return


        # display monitor counters etc
        #for link in x10g_params:
        #    self.dump_registers_10g_link(run_params, link, myTBClient)            

#        return 0

        
        if run_params['clear_10g_lut'] == 1: 
            for link in x10g_params:       
                self.clear_10g_link(link, myTBClient)   

        #print "after clear_10g_link  Dump of regs for TB F1_F4 control"
        #myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)
 
        # configure from x10g structures
        for link in x10g_params:
        #    pp.pprint(link) 
            self.config_10g_link(run_params, link, myTBClient)         

        #print "Configure done. Try chipscope"
        #time.sleep(10)       

        # apply software resets
        print "Apply s/w reset  to Checker A & B to clear spurious counters"
        myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.data_chk_0+0, 0)   # checker A
        myTBClient.toggle_bits_new((fpga_nr<<28) | myTBClient.data_chk_1+0, 0)   # checker B

        #if run_params['debug_level'] >= 0:
        #    print "After s/w reset  Checker on Tx Term  Chan A"
        #    myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_chk_0, 20)

        #return 0
                
        #print "after config_10g_link  Dump of regs for TB F1_F4 control"
        #myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)

############ test only
#        for link in x10g_params:       
#            self.init(link, myTBClient)   
############ test only

        #for link in x10g_params:
        #    self.dump_registers_10g_link(run_params, link, myTBClient)            
            
        #return
         
  
# for receive only tests, do need the 10g set up but don't need to tx triggers
        if run_params['playback'] == 1:      
            return 0 
        
        # reset counters etc
        for link in x10g_params:
            self.init_10g_link(link, myTBClient)   


    # test only
        print "Clear data_mon_0 and data_mon_1" 
        myTBClient.clear_ll_monitor((fpga_nr<<28) | myTBClient.data_mon_0)
        myTBClient.clear_ll_monitor((fpga_nr<<28) | myTBClient.data_mon_1)
        
        # display monitor counters etc
        if run_params['debug_level'] >= 2:
            for link in x10g_params:
                self.monitor_10g_link(link, myTBClient)    


        if run_params['using_ppc_core'] == 1:

            # Prepare for run with PPC
            nrImages = 1
            myTBClient.ppc_prepare_run((fpga_nr<<28) | myTBClient.bram_ppc1, run_params['num_cycles'], nrImages )   # dma buffer params sent to PPC

            time.sleep(2) 
            
            myTBClient.ppc_start_run((fpga_nr<<28) | myTBClient.bram_ppc1)     # start signal to PPC

        if run_params['debug_level'] >= 0:
            print "Dump of regs for BRAM on PPC 1"
            myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.bram_ppc1, 32)

##################################################        
                
        # START SENDING TRIGGERS
        num_cycles = run_params['num_cycles']
        for i in range (1, num_cycles+1):
            # start data transfers on links
            print "Starting Run Cycle Nr %d" % i
            for link in x10g_params:
                self.start_10g_link(run_params, link, myTBClient)  
    
        wait_secs = 10
        print "Waiting %d secs for run to complete" % wait_secs
        time.sleep(wait_secs) # brute force way to ensure test completes before checking data


        # disable next if statement if testing TX only 
        ##if run_params['using_ppc_core'] == 1:
        ##    myTBClient.ppc_stop_run((fpga_nr<<28) | myTBClient.bram_ppc1)     # stop signal to PPC

       
        # display ll monitor stats
        #for link in x10g_params:
        #    self.monitor_10g_link(link, myTBClient) 

        clock_freq = clock_rdma     # clock_ppc   # clock_10g (with xaui)  # clock_rdma (if no XAUI or PPC)
        
        print "Monitor on Rx Origin Chan A"
        myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.data_mon_0, clock_freq) 
        print "Monitor on Tx Term  Chan A"
        myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.llink_mon_0, clock_freq)

        print "Monitor on Rx Origin Chan B"
        myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.data_mon_1, clock_freq)
        print "Monitor on Tx Term  Chan B"
        myTBClient.read_ll_monitor((fpga_nr<<28) | myTBClient.llink_mon_1, clock_freq)

        #f1_f4_ctrl_base = myTBClient.f1_f4_ctrl      
        print "Dump of regs for TB F1_F4 control"
        myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)

        # display registers 
        if run_params['debug_level'] > 0:
            for link in x10g_params:
                self.dump_registers_10g_link(run_params, link, myTBClient)            

        #fpga_nr = 3
        f1_f4_ctrl_base = (fpga_nr<<28) | myTBClient.f1_f4_ctrl      
        ##print "Dump of regs for TB F1_F4 control"
        ##myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)


        print "Checker on Tx Term  Chan A"
        myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_chk_0, 20)
        print "Checker on Tx Term  Chan B"
        myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.data_chk_1, 20)

        ###print "Dump of regs for QDR" 
        ##myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.qdr, 24)

        master_ctrl_base = (0<<28) | myTBClient.master_ctrl      
        ##print "Dump of regs for Master control"
        ##myTBClient.dump_regs_hex((0<<28) | myTBClient.master_ctrl, 20)

        ##print "Dump of regs for Master Xpoint"
        ##myTBClient.dump_regs_hex((0<<28) | myTBClient.master_xpoint, 20)

        if run_params['debug_level'] >= 0:
            print "Dump of regs for BRAM on PPC 1"
            myTBClient.dump_regs_hex((fpga_nr<<28) | myTBClient.bram_ppc1, 32)
                                  

        print "     Master Firmware vers = %08x" % myTBClient.get_master_firmware_vers()
        #for i in range(1,4):
        #   print "         F%d Firmware vers = %08x" % (i, myTBClient.get_fe_firmware_vers(i))
        print "         F%d Firmware vers = %08x" % (fpga_nr, myTBClient.get_fe_firmware_vers(fpga_nr))

 
        print "\n=============================================" 
        print "================ TEST ENDED =================" 
        print "=============================================\n" 
         
        return 0 

#-------------------------------------------------------------------------------------    
    def init(self, x10g, myTBClient):
        """ initialise all links
             """

        # switch mux to fpga 
        fpga_mux = fpga_lut[x10g['link_nr']] - 1
        #print "init fpga_mux = ", fpga_mux
        #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux)   

        if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
            ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc1
        else:
            ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc2  

        fpga_nr = fpga_lut[x10g['link_nr']] - 1
        #print "fpga_nr = ", fpga_nr
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
            #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux)   
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                x10g_base = (fpga_mux<<28) | myTBClient.udp_10g_0
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_0
                ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc1
                ppc_reset_bit = 0
            else:
                x10g_base = (fpga_mux<<28) | myTBClient.udp_10g_1
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_1
                ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc2                
                ppc_reset_bit = 1

            f1_f4_ctrl_base = (fpga_mux<<28) | myTBClient.f1_f4_ctrl
            
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
            
            if run_params['using_10g_core'] != 0: 
             
                myTBClient.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
                myTBClient.setup_10g_udp_net_block(x10g_base, x10g)    
                myTBClient.setup_10g_packet_header(x10g_base, robs_udp_packet_hdr)
                       

                myTBClient.setup_10g_rx_filter(x10g_base) # accepts any udp packets

                #print "after setup_10g_rx_filter  Dump of regs for TB F1_F4 control"
                #myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)
                 
                # response = myTBClient.rdmaWrite(x10g_base + 14, 0x000000ab)        
                # response = myTBClient.rdmaRead(x10g_base + 14, 1)
                # print "RDMA read from polarity p/n swapping:", hex(response[1])  
                     
                if run_params['debug_level'] > 3: 
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

                # final param to enable data gen headers for farm mode
                myTBClient.override_header_ll_frm_gen(data_gen_base, 0, 0)  # default is not to override index nr in header
 
            myTBClient.setup_ll_frm_gen(data_gen_base, x10g['frame_len']/8, x10g['data_format'], x10g['num_frames']-1, run_params['ll_hdr_trl'])  
            
            if run_params['debug_level'] > 1:
                print "Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(data_gen_base, 16)
         
            if x10g['data_gen'] == 2:   # data source is ppc

                myTBClient.setup_ppc_bram(ppc_bram_base, x10g['frame_len'], x10g['data_format'], x10g['num_frames']-1, 1) 
                myTBClient.rdmaWrite(f1_f4_ctrl_base+14, 1) # switch ll mux
                if run_params['using_10g_core'] != 0: 
                    myTBClient.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 

                # Resets ppc 
                myTBClient.toggle_bits_new(f1_f4_ctrl_base+9, ppc_reset_bit)   # xaui chan 0
                theDelay = 10
                print "Waiting for PPC to reset %s seconds.." % theDelay
                time.sleep(theDelay)

            else:                       # data source is data gen               
                myTBClient.rdmaWrite(f1_f4_ctrl_base+14, 0) # switch ll mux
                if run_params['using_10g_core'] != 0: 
                    myTBClient.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut  

            #print "before setting mux sels  Dump of regs for TB F1_F4 control"
            #myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)
 
            if 1: # program mux sels
        #chan A
                # fix chain for DataGen with loopback and bypassing ppc
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_RX_ORIG_SEL) # clr => in from xaui 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_RX_BYPASS_QDR_IN) 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_RX_BYPASS_QDR_OUT) 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_RX_BYPASS_PPC_IN) 
                myTBClient.clrbit(f1_f4_ctrl_base+2, self.LL_MUX_RX_BYPASS_PPC_OUT) 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_RX_TERM)   # clr => out to aurora 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_TX_ORIG_SEL) # clr => in from aurora 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_TX_BYPASS_PPC_IN) 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_TX_BYPASS_PPC_OUT) 
                myTBClient.setbit(f1_f4_ctrl_base+2, self.LL_MUX_TX_TERM)  

                #myTBClient.rdmaWrite(f1_f4_ctrl_base+2, 0x0) 

        #chan B
                # fix chain for DataGen with loopback and bypassing ppc
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_RX_ORIG_SEL) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_RX_BYPASS_QDR_IN) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_RX_BYPASS_QDR_OUT) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_RX_BYPASS_PPC_IN) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_RX_BYPASS_PPC_OUT) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_RX_TERM) # clr => out to aurora 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_TX_ORIG_SEL) # clr => in from aurora 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_TX_BYPASS_PPC_IN) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_TX_BYPASS_PPC_OUT) 
                myTBClient.setbit(f1_f4_ctrl_base+3, self.LL_MUX_TX_TERM) 

                #mask = 0x01410541 # 0x00000541  0x01410541
                #b = self.int32_to_uint32(mask)
                #a = ~b
                #c = self.int32_to_uint32(~mask)
                #print "mask = $%08x ; a = $%08x; b = $%08x; c = $%08x" %(mask,a, b, c)
                #myTBClient.rdmaWrite(f1_f4_ctrl_base+2, 0x01410541) 

            #print "after setting mux sels  Dump of regs for TB F1_F4 control"
            #myTBClient.dump_regs_hex(f1_f4_ctrl_base, 20)
       
            mux_reg_A = myTBClient.rdmaRead(f1_f4_ctrl_base+2, 1)[0] 
            mux_reg_B = myTBClient.rdmaRead(f1_f4_ctrl_base+3, 1)[0] 
            #print 'reg %2d = $%08X ' %(i, self.rdmaRead(base_addr+i, 1)[0])
            print "Mux registers chanA = $%08X; chan B = $%08X" %(mux_reg_A, mux_reg_B)
            
            
        return 0
        
#-------------------------------------------------------------------------------------    
    def start_10g_link(self, run_params, x10g, myTBClient):
        """ start a 10g link
             """
        
        if x10g['enable'] == 1:
            print "Start 10G link nr", x10g['link_nr']

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux)   

            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_0
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_0
                ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc1
            else:
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_1
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_1
                ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc2
             
            f1_f4_ctrl_base = (fpga_mux<<28) | myTBClient.f1_f4_ctrl
            
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
                      if x10g['link_nr']%2 == 0:
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

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux)   
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_0
            else:
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_1            
                
            
            myTBClient.clear_ll_monitor(ll_mon_base)
                    
        return 0

#-------------------------------------------------------------------------------------    
    def monitor_10g_link(self, x10g, myTBClient):
        """ monitor 10g link
             """
        
        if x10g['enable'] == 1:
            print "Monitor 10G link nr", x10g['link_nr']

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux)   
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_0
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_0
            else:
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_1
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_1            
                

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

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux)   
            
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                x10g_base = (fpga_mux<<28) | myTBClient.udp_10g_0
            else:
                x10g_base = (fpga_mux<<28) | myTBClient.udp_10g_1            
                            
            myTBClient.x10g_net_lut_clear(x10g_base)
                    
        return 0   
 
#-------------------------------------------------------------------------------------    
    def dump_registers_10g_link(self, run_params, x10g, myTBClient):
        """ reset 10g link
             """

        if x10g['enable'] == 1:
            print "Dump registers on 10G link nr", x10g['link_nr']
 
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            print "fpga_mux = %d" %fpga_mux
            #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base_rdma, fpga_mux) 
           
            if x10g['link_nr']%2 == 0:  # nb link nr runs from 1 to 8
                x10g_base = (fpga_mux<<28) | myTBClient.udp_10g_0
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_0
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_0
                ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc1
            else:
                x10g_base = (fpga_mux<<28) | myTBClient.udp_10g_1
                ll_mon_base = (fpga_mux<<28) | myTBClient.llink_mon_1
                data_gen_base = (fpga_mux<<28) | myTBClient.data_gen_1
                ppc_bram_base = (fpga_mux<<28) | myTBClient.bram_ppc2             
            
            f1_f4_ctrl_base = (fpga_mux<<28) | myTBClient.f1_f4_ctrl

            if run_params['debug_level'] > 2:
                print "Dump of regs for FE Ctrl Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(f1_f4_ctrl_base, 16)

            if run_params['debug_level'] > 1:
                print "Dump of regs for XAUI for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(x10g_base, 16)
            if run_params['debug_level'] >= 0:
                print "Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(data_gen_base, 16)
            if run_params['debug_level'] >= 2:
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

    def int32_to_uint32(self, i):
        return ctypes.c_uint32(i).value

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
