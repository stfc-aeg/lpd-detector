'''
Created on 18 Apr 2012

@author: ckd27546
'''
# Adapted LPD FEM test for Train Builder
# John Coughlan June 2012
# Configured for XFEL Hamburg tests July 2012

# Import Python standard modules
import sys

import pprint

# Import Fem modules
#from FemClient import FemClient
from TBClient import *  #TBClient

            
class TBTest():

    # TBClient myTBClient   # don't know how to have class type as an object, use global instead
 
    def set_10g_structs_variables(self):
       
        run_params = {'run_type' : 2,   # 2 for farm mode ; 1 for legacy non farm mode (only 1 ip and port per link)  
                      'num_cycles'  : 2,
                      'debug_level' : 1,    # higher values more print out
		      'eth_ifg' : 0x200,   # ethernet inter frame gap  ; ensure receiving 10G NIC parameters have been set accordingly
                      'udp_pkt_len' : 8000, # udp packet length in bytes
		      'TBHost' : '192.168.2.2',     # ip address for 1 GbE fem controls
		      'TBPort' : 6969   # udp port nr for 1 GbE fem controls (not to be confused with port nr for 10g links)
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
                    'data_gen' : 1, # data generator type (1 for DataGen)   
                    'data_format' : 0, # data format type  (0 for counting data)  
                    'frame_len'  : 1024,    # frame len in bytes
                    'num_frames' : 1,    # number of frames to send in each cycle
                    'delay' : 0,    # delay offset wrt start of previous link in secs
                    'enable'  : 0,    # enable this link
                    'link_nr' : 1   # link number
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
                        'link_nr' : 2
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
                        'link_nr' : 3
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
                        'link_nr' : 4
                        } 
                        
        x10g_5 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 1, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 125000*8000,    # frame len in bytes
                        'num_frames' : 10,    # number of frames to send
                        'delay' : 5.2,    # delay offset wrt previous link in secs
                        'enable'  : 1,    # enable link
                        'link_nr' : 5
                        } 
                        
        x10g_6 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('61649'),
                        'num_prts' : 1, # number of ports to loop over before repeating
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 20*8000,    # frame len in bytes
                        'num_frames' : 10,    # number of frames to send
                        'delay' : 5.2,    # delay offset wrt previous link in secs
                        'enable'  : 1,    # enable link
                        'link_nr' : 6
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
                        'link_nr' : 7
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
                        'link_nr' : 8
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
     
        #return x10g_params
        return run_params, x10g_params
        #return x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8
       
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
	# TBHost now set in run_params structure
        #TBHost = '192.168.2.2'   # '192.168.0.13'
        #TBPort = 6969          # 6969       
        
        global pp
        
        global myTBClient
        
        global fpga_mux_base
        global fpga_lut
        
        pp = pprint.PrettyPrinter(indent=4)
        
        fpga_mux_base = 0x84000008; # RAW base address of GPIO controlling FPGA RDMA mux
        fpga_term_mux_base = 0x84000000; # RAW base address of GPIO controlling FPGA RDMA mux
       
        # fpga rdma access from master is switched by simple mux under gpio control
        # fpga 1 has links 1&2 ; fpga 2 has links 3&4 ; fpga 3 has links 5&6  ; fpga 4 has links 7&8 ;
        # links start at 1 not 0 (hence first element '0' in fpga_lut
        fpga_lut = [0,1,1,2,2,3,3,4,4]       
            
        #x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8 = self.set_10g_structs_variables_te7redbridge()
        run_params, x10g_params = self.set_10g_structs_variables()
        
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
        response = myTBClient.rdmaWrite(0x0600000f, ppc_nr-1)  
        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_term_mux_base, fpga_nr)  # switch terminal
        print "Switching PPC Terminal output to F%d : PPC#%d:" %(fpga_nr, ppc_nr)
        
        
        print "Dump of Farm Mode LUT for xaui  xaui 0" 
        myTBClient.dump_regs_hex(myTBClient.udp_10g_0+0x10000, 16) 
        myTBClient.dump_regs_hex(myTBClient.udp_10g_0+0x100f0, 16)                               
        myTBClient.dump_regs_hex(myTBClient.udp_10g_0+0x10100, 16)
        myTBClient.dump_regs_hex(myTBClient.udp_10g_0+0x101f0, 16)  
        myTBClient.dump_regs_hex(myTBClient.udp_10g_0+0x10200, 16)
        myTBClient.dump_regs_hex(myTBClient.udp_10g_0+0x103f0, 16) 
        
        #return 0
        
        # for link in x10g_params:       
            # self.clear_10g_link(link, myTBClient)   
            
        # configure from x10g structures
        for link in x10g_params:
        #    pp.pprint(link) 
            self.config_10g_link(run_params, link, myTBClient)         
        
        #return 0 
        
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
                self.start_10g_link(link, myTBClient)  
		#time.sleep(2) 
        
        # display monitor counters etc
        for link in x10g_params:
            self.monitor_10g_link(link, myTBClient)   
        
        return 0 
    
    
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
            
            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
                x10g_base = myTBClient.udp_10g_0
                data_gen_base = myTBClient.data_gen_0
            else:
                x10g_base = myTBClient.udp_10g_1
                data_gen_base = myTBClient.data_gen_1
            
            #udp_pkt_len = x10g['frame_len']
            #udp_frm_sze = x10g['frame_len']
            
            #udp_pkt_len = 8000

            udp_pkt_len = run_params['udp_pkt_len']
            udp_frm_sze = x10g['frame_len']

            #eth_ifg = 0x00001000  # Ethernet Inter Frame Gap
            #eth_ifg = 0x1000  # Ethernet Inter Frame Gap
            eth_ifg = run_params['eth_ifg']
            robs_udp_packet_hdr = 4
            
            # legacy non farm mode
            myTBClient.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            myTBClient.setup_10g_udp_net_block(x10g_base, x10g)    
            myTBClient.setup_10g_packet_header(x10g_base, robs_udp_packet_hdr)
            
            # response = myTBClient.rdmaWrite(x10g_base + 14, 0x000000ab)        
            # response = myTBClient.rdmaRead(x10g_base + 14, 1)
            # print "RDMA read from polarity p/n swapping:", hex(response[1])  
        
            # final param to enable data gen headers for farm mode
            myTBClient.setup_ll_frm_gen(data_gen_base, x10g['frame_len']/8, x10g['data_format'], x10g['num_frames']-1, 1)  
            
            print "Dump of Farm Mode LUT for xaui for Link %d" % x10g['link_nr']
            myTBClient.dump_regs_hex(x10g_base+0x10000, 16) 
            
            if run_params['run_type'] == 2:
                # farm mode
                print "Setting up Farm Mode LUT. May take several seconds... "                       
                myTBClient.x10g_net_lut_setup(x10g_base, x10g)                                      
                myTBClient.x10g_set_farm_mode(x10g_base, 1)

                if run_params['debug_level'] > 3:                
                    print "Dump of Farm Mode LUT for xaui for Link %d" % x10g['link_nr']
                    myTBClient.dump_regs_hex(x10g_base+0x10000, 16) 
                    myTBClient.dump_regs_hex(x10g_base+0x100f0, 16)                               
                    myTBClient.dump_regs_hex(x10g_base+0x10100, 16)
                    myTBClient.dump_regs_hex(x10g_base+0x101f0, 16)  
                    myTBClient.dump_regs_hex(x10g_base+0x10200, 16)
                    myTBClient.dump_regs_hex(x10g_base+0x103f0, 16)                         
            else: 
                print "Disable Farm Mode."              
                myTBClient.x10g_set_farm_mode(x10g_base, 0)
            
            if run_params['debug_level'] > 1:
                #time.sleep(1)
                print "Dump of regs for xaui for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                myTBClient.dump_regs_hex(data_gen_base, 16)
           
        return 0
        
    def start_10g_link(self, x10g, myTBClient):
        """ start a 10g link
             """
        
        if x10g['enable'] == 1:
            print "Start 10G link nr", x10g['link_nr']

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   

            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
                data_gen_base = myTBClient.data_gen_0
                ll_mon_base = myTBClient.llink_mon_0
            else:
                data_gen_base = myTBClient.data_gen_1
                ll_mon_base = myTBClient.llink_mon_1
             
            
            time.sleep(x10g['delay'])   # wait before trigger

            if x10g['data_gen'] == 1:
                
                # check last cycle has completed
                
                link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                i = 0
#                print "\n" 
                while link_busy == 1:
                    i=i+1
#                   link_busy = myTBClient.status_ll_frm_gen(data_gen_base)                
#                   print "Data Gen on 10G link nr %2d has busy flag = %d" %(x10g['link_nr'], link_busy)
                    print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(x10g['link_nr'],i),
                    sys.stdout.flush() 
#                    print "1 WARNING Data Gen on 10G link nr %2d is still BUSY" %x10g['link_nr']
                    time.sleep(1)                    
                    link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
                
                print "Trigger LL Data Gen"
                # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
                # don't do this any earlier or won't trigger
                myTBClient.soft_reset_ll_frm_gen(data_gen_base)  

                if x10g['link_nr']%2:
                    myTBClient.toggle_bits(0, 1)   # xaui chan 0
                else:               
                    myTBClient.toggle_bits(0, 2)   # xaui chan 1
                
                
                # print "After Trigger : Dump of regs for Data Gen for Link %d" % x10g['link_nr']
                # myTBClient.dump_regs_hex(data_gen_base, 32)
                
        return 0

    def init_10g_link(self, x10g, myTBClient):
        """ reset 10g link
             """
        
        if x10g['enable'] == 1:
            print "Clear Monitor on 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
                ll_mon_base = myTBClient.llink_mon_0
            else:
                ll_mon_base = myTBClient.llink_mon_1            
                
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   
            
            myTBClient.clear_ll_monitor(ll_mon_base)
                    
        return 0

    def monitor_10g_link(self, x10g, myTBClient):
        """ monitor 10g link
             """
        
        if x10g['enable'] == 1:
            print "Monitor 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
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
                i = 0
#                print "\n" 
                while link_busy == 1:
                    i=i+1
#                   link_busy = myTBClient.status_ll_frm_gen(data_gen_base)                
#                   print "Data Gen on 10G link nr %2d has busy flag = %d" %(x10g['link_nr'], link_busy)
                    print 'Waiting for Run End : 10G link nr %2d is BUSY ; waiting %d secs \r' %(x10g['link_nr'],i),
                    sys.stdout.flush() 
#                    print "1 WARNING Data Gen on 10G link nr %2d is still BUSY" %x10g['link_nr']
                    time.sleep(1)                    
                    link_busy = myTBClient.status_ll_frm_mon(ll_mon_base) 
             
            print "\n"   
            myTBClient.read_ll_monitor(ll_mon_base)
                    
        return 0
        
    def clear_10g_link(self, x10g, myTBClient):
        """ clear 10g link settings
             """
        
        if x10g['enable'] == 1:
            print "Clear settings on 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
                x10g_base = myTBClient.udp_10g_0
            else:
                x10g_base = myTBClient.udp_10g_1            
                
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   
            
            myTBClient.x10g_net_lut_clear(x10g_base)
                    
        return 0              
        
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