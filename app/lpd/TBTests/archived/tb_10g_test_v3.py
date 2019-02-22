'''
Created on 18 Apr 2012

@author: ckd27546
'''
# Adapted LPD FEM test for Train Builder
# John Coughlan June 2012

# Import Python standard modules
import sys

import pprint

# Import Fem modules
#from FemClient import FemClient
from TBClient import *  #TBClient

            
class TBTest():

    # TBClient myTBClient   # don't know how to have class type as an object, use global instead

    def set_10g_structs_variables_te7burntoak(self):
        """ Construct and return to dictionaries defining to network interfaces
            ..both interfaces same though? """
            
        
    #    myDict = {'field1': 'some val', 'field2': 'some val'}
    
        x10g_0 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'), # fpga   
                  'fpga_ip'  : self.ip_addr_to_uint32('192.168.6.2'),    # fpga
                  'fpga_prt' : self.prt_addr_to_uint16('0000'),
                  'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-80'),    # 10g nic    eth6
                  'nic_ip'  : self.ip_addr_to_uint32('192.168.6.1'),    # 10g nic  eth6
                  'nic_prt' : self.prt_addr_to_uint16('0000')}
        
        x10g_1 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),     # doesn't matter for tx from fpga
                  'fpga_ip'  : self.ip_addr_to_uint32('192.168.8.2'),    # fpga   doesn't matter for tx from fpga
                  'fpga_prt' : self.prt_addr_to_uint16('0000'),
                  'nic_mac' : self.mac_addr_to_uint64('00-07-43-10-61-90'),  # 10g nic  eth8
                  'nic_ip'  : self.ip_addr_to_uint32('192.168.8.1'),    # 10g nic  eth8
                  'nic_prt' : self.prt_addr_to_uint16('0000')}  # 10g nic port only matters in farm mode
    
        return x10g_0, x10g_1

    # def set_10g_structs_variables_te7redbridge(self):
        # """ Construct and return to dictionaries defining to network interfaces
            # ..both interfaces same though? """
            
        
       #myDict = {'field1': 'some val', 'field2': 'some val'}
    
        # x10g_0 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'), # fpga   
                  # 'src_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    # fpga
                  # 'src_prt' : self.prt_addr_to_uint16('0000'),
                  # 'dst_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    # 10g nic    eth6
                  # 'dst_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    # 10g nic  eth6
                  # 'dst_prt' : self.prt_addr_to_uint16('0000')}
 
        # x10g_1 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),     # doesn't matter for tx from fpga
                  # 'src_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    # fpga   doesn't matter for tx from fpga
                  # 'src_prt' : self.prt_addr_to_uint16('0000'),
                  # 'dst_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),  # 10g nic  eth8
                  # 'dst_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    # 10g nic  eth8
                  # 'dst_prt' : self.prt_addr_to_uint16('0000')}  # 10g nic port only matters in farm mode
    
        # return x10g_0, x10g_1
     
     
    def set_10g_structs_variables_te7redbridge(self):
    # F1 has links 1&2 , F2 has links 3&4, F3 links 5&6, F4 links 7&8
    # link 1 is bottom of board
            
        x10g_1 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 1
                        }
                        
        x10g_2 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 2
                        } 
                        
        x10g_3 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 3
                        } 
                        
        x10g_4 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 4
                        } 
                        
        x10g_5 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 5,    # delay offset wrt previous link in milli-secs
                        'enable'  : 1,    # enable link
                        'link_nr' : 5
                        } 
                        
        x10g_6 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 10,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 6
                        } 
                        
        x10g_7 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-03'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.2.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-90'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.2.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 7
                        } 
                        
        x10g_8 = {'fpga_mac' : self.mac_addr_to_uint64('62-00-00-00-00-04'),   
                        'fpga_ip'  : self.ip_addr_to_uint32('192.168.3.2'),    
                        'fpga_prt' : self.prt_addr_to_uint16('0000'),
                        'nic_mac' : self.mac_addr_to_uint64('00-07-43-11-97-98'),    
                        'nic_ip'  : self.ip_addr_to_uint32('192.168.3.1'),    
                        'nic_prt' : self.prt_addr_to_uint16('0000'),
                        'data_gen' : 1, # data generator    
                        'data_format' : 0, # data format type   
                        'frame_len'  : 1024,    # frame len in bytes
                        'num_frames' : 1,    # number of frames to send
                        'delay' : 0,    # delay offset wrt previous link in milli-secs
                        'enable'  : 0,    # enable link
                        'link_nr' : 8
                        } 
                        
                        
        x10g_params = [ x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8 ]
        
        
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
     
        
    
        return x10g_params
        #return x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8
       
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
        TBHost = '192.168.2.2'   # '192.168.0.13'
        TBPort = 6969          # 6969       
        
        global pp
        
        global myTBClient
        
        global fpga_mux_base
        global fpga_lut
        
        pp = pprint.PrettyPrinter(indent=4)
        
        fpga_mux_base = 0x84000008; # RAW base address of GPIO controlling FPGA RDMA mux
        
        # fpga rdma access from master is switched by simple mux under gpio control
        # fpga 1 has links 1&2 ; fpga 2 has links 3&4 ; fpga 3 has links 5&6  ; fpga 4 has links 7&8 ;
        # links start at 1 not 0 (hence first element '0' in fpga_lut
        fpga_lut = [0,1,1,2,2,3,3,4,4]       
            
        #x10g_1, x10g_2, x10g_3, x10g_4, x10g_5, x10g_6, x10g_7, x10g_8 = self.set_10g_structs_variables_te7redbridge()
        x10g_params = self.set_10g_structs_variables_te7redbridge()
        
        try:
            myTBClient = TBClient((TBHost, TBPort), timeout=10)
        except FEMClientError as errString:
            print "Error: Train Builder connection failed (is Master GbE server running?:", errString
            sys.exit(1)
     
        # configure from x10g structures
        for link in x10g_params:
        #    pp.pprint(link) 
            self.config_10g_link(link, myTBClient)         
        
        # reset counters etc
        for link in x10g_params:
            self.init_10g_link(link, myTBClient)     
        
        # display monitor counters etc
        for link in x10g_params:
            self.monitor_10g_link(link, myTBClient)    
         
        # start data transfers on links
        for link in x10g_params:
            self.start_10g_link(link, myTBClient)   
        
        # display monitor counters etc
        for link in x10g_params:
            self.monitor_10g_link(link, myTBClient)   
        
        return 0
                       
        
        # Set up 10G UDP packet length, number & frame size
        eth_ifg = 0x00001000  # Ethernet Inter Frame Gap
       
 
        # rob's udp packet headers : 0 to disable   4 to enable ; Nb to enable need correct bit pattern
        # Nb this is not the same as asic rx header; Utilised by robs_udp_packet_header_10g()
        robs_udp_packet_hdr = 4
        
        if (data_source_to_10g == 0): # frame generator
            udp_pkt_len = 1024  #1000
            udp_pkt_num = 1
            udp_frm_sze = 1024
            udp_in_buf_size =1024*1024*1024*1
            
        
        # some sanity checks for rdma access
        
        print "Sanity Checks now..."

        #response = myTBClient.rawWrite(0x84000008, 0x4)    # connect RDMA to Master
        #response = myTBClient.rawRead(0x84000008, 1)
        #print "Raw read of GPIO register for RDMA Mux select reads:", hex(response[1])
        
        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, 0x84000000, 0x3) 
        print "Switching PPC Term output F3:"
        
        #return 0
                
        # as no rawWrite defined function yet
        #bus = FemTransaction.BUS_RAW_REG    # Raw access for GPIO reg
        #width = FemTransaction.WIDTH_LONG
        #response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, 0x84000008, 0x4)    
       
        # response = myTBClient.rdmaRead(0x00000014, 1)
        # print "RDMA read from Master register addr 0x00000014 (should read 0xBEEFACE):", hex(response[1])   # to connect RDMA to Master
                
        response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, 0x84000008, 0x2)   # connect RDMA to F3
        
        response = myTBClient.rdmaRead(0x06000010, 1)
        print "RDMA read from F1_F4 register addr 0x00000010 (should read 0x00010004):", hex(response[1])   
        
        response = myTBClient.rdmaWrite(0x0600000f, 0)
        print "Switched term output to PPC1:"
        
        time.sleep(5)   # waits for keyboard input
        
        response = myTBClient.rdmaWrite(0x0600000f, 1)
        print "Switched term output to PPC2:"
       
        response = myTBClient.rdmaWrite(0x0600000e, 0)  # bit 0 for PPC1 DMA to XAUI0 ; bit 1 for PPC2 DMA to XAUI1
        #print "Mux Local Link output from PPC DMA:"
        print "Set up Local Link Mux:"
        
        # response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, 0x84000008, 0x1)   # connect RDMA to F2       
        # myTBClient.toggle_bits(0, 3)
        # print "Trigger DataGen to PPC1:"
        
        response = myTBClient.rdmaRead(0x0600001e, 1)
        print "RDMA read from F1_F4 register addr 0x0600001e :", hex(response[1])  
        
        #return 0
    
        
       
    
        if (enable_10g == 1):
            
            #set up the UDP IP blocks
            #x10g_0, x10g_1 = self.set_10g_structs_variables_te7burntoak()
            #x10g_1, x10g_0 = self.set_10g_structs_variables_te7burntoak()
            x10g_0, x10g_1 = self.set_10g_structs_variables_te7redbridge()
            
            #set up the UDP IP blocks
            myTBClient.setup_10g_udp_block(myTBClient.udp_10g_0, udp_pkt_len, udp_frm_sze, eth_ifg)
            myTBClient.setup_10g_udp_block(myTBClient.udp_10g_1, udp_pkt_len, udp_frm_sze, eth_ifg)
            
            #set MAC, IP Port addresses
            myTBClient.setup_10g_udp_net_block(myTBClient.udp_10g_0, x10g_0)
            myTBClient.setup_10g_udp_net_block(myTBClient.udp_10g_1, x10g_1)
        
            ''' create a udp record - REMOVED '''
        #    u = udp('192.168.0.13', 'LocalPort', 61649,'InputBufferSize', udp_in_buf_size, 'DatagramTerminateMode', 'off')
        #    myFemClient = FemClient(hostAddr='192.168.0.13', timeout=10) 
        
        # enable headers
            myTBClient.setup_10g_packet_header(myTBClient.udp_10g_0, robs_udp_packet_hdr)
            myTBClient.setup_10g_packet_header(myTBClient.udp_10g_1, robs_udp_packet_hdr)
        
        response = myTBClient.rdmaRead(0x0000000e, 1)
        print "RDMA read from polarity p/n swapping in 10g_0 (should read 0x000000ab):", hex(response[1])   
        response = myTBClient.rdmaRead(0x0100000e, 1)
        print "RDMA read from polarity p/n swapping in 10g_1 (should read 0x000000aa):", hex(response[1])   
        
        response = myTBClient.rdmaWrite(0x0000000e, 0x000000ab)
        print "fix polarity p/n swapping in 10g core  ONLY override xaui 0"
        
        response = myTBClient.rdmaRead(0x0000000e, 1)
        print "RDMA read from polarity p/n swapping in 10g_0 (should read 0x000000ab):", hex(response[1])   
    
    
        #set up data generator 0
        ll_frm_gen_data_type=0
        
        # length specifies nr of 64 bit words
        myTBClient.setup_ll_frm_gen(myTBClient.data_gen_0, udp_frm_sze/8, ll_frm_gen_data_type, num_ll_frames+1)  # trigger chan 0
        myTBClient.setup_ll_frm_gen(myTBClient.data_gen_1, udp_frm_sze/8, ll_frm_gen_data_type, num_ll_frames+1)  # trigger chan 1
               
        print ""
        if (enable_10g == 1):
            myTBClient.clear_ll_monitor(myTBClient.llink_mon_0)
            myTBClient.clear_ll_monitor(myTBClient.llink_mon_1)
            print ""
            myTBClient.read_ll_monitor(myTBClient.llink_mon_0)
            myTBClient.read_ll_monitor(myTBClient.llink_mon_1)
            print ""
        
        
        # select asic or llink gen as data source
        #myTBClient.fem_local_link_mux_setup(data_source_to_10g)
    
        #--------------------------------------------------------------------
        # send triggers to data generators
        #--------------------------------------------------------------------
        # send triggers to data generators
        if trigger_type is 'all':
            # start asic seq  = reset, slow, fast & asic rx
            print "You selected 'all'"
            myTBClient.toggle_bits(0, 2)
        elif trigger_type is 'a':
            # trigger to local link frame gen 
            print "You selected 'a'"
            #myTBClient.toggle_bits(0, 1)
            #myTBClient.toggle_bits(0, 2)
            myTBClient.toggle_bits(0, 3)   # both data gens
        elif trigger_type is 'b':
            # trigger the asic rx block
            print "You selected 'b'"
            myTBClient.toggle_bits(3, 1)
        elif trigger_type is 's':
            # trigger just the slow contol IP block
            print "You selected 's'"
            myTBClient.toggle_bits(7, 1)
        elif trigger_type is 'f':
            # trigger just the fast cmd block
            print "You selected 'f'"
            myTBClient.toggle_bits(7, 2)
        else:
            print "No case matching variable trigger_type = ", trigger_type
        #--------------------------------------------------------------------
        
        if enable_10g == 1:
            #Check local link frame statistics
            myTBClient.read_ll_monitor(myTBClient.llink_mon_0)  
            myTBClient.read_ll_monitor(myTBClient.llink_mon_1)       
        
        # check contents of slow control read back BRAM
        # not working yet
        #rdma_block_read(slow_ctr_2, 4, 'Read Back Slow Ctrl RAM');
        
        
        # allow time to trigger ppc dma transfer in sdk app
        if data_source_to_10g == 2:
            print " paused waiting 2 seconds allowing time to trigger ppc dma transfer in sdk app"
            time.sleep(2)   # waits for keyboard input
        
        
        print " ...continuing"
        
        
        
        print "Receiving the image data from 10g link.."
        
        
        
        print ""
        
        # if enable_10g == 1:
        #    Check local link frame statistics
            # myTBClient.read_ll_monitor(xaui_id)  
    
    
    def config_10g_link(self, x10g, myTBClient):
        """ configure a 10g link
             """
        #pprint(x10g)
               
        if x10g['enable'] == 1:
            print "Configure 10G link nr", x10g['link_nr']
            
            pp.pprint(x10g)
            
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            print "fpga_mux = ", fpga_mux
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   # connect RDMA to F3
            
            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
                x10g_base = myTBClient.udp_10g_0
                data_gen_base = myTBClient.data_gen_0
            else:
                x10g_base = myTBClient.udp_10g_1
                data_gen_base = myTBClient.data_gen_1
            
            #return 1
            
            udp_pkt_len = x10g['frame_len']
            udp_frm_sze = x10g['frame_len']
            eth_ifg = 0x00001000  # Ethernet Inter Frame Gap
            robs_udp_packet_hdr = 4
            
            myTBClient.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            myTBClient.setup_10g_udp_net_block(x10g_base, x10g)    
            myTBClient.setup_10g_packet_header(x10g_base, robs_udp_packet_hdr)
            
            # response = myTBClient.rdmaWrite(x10g_base + 14, 0x000000ab)        
            # response = myTBClient.rdmaRead(x10g_base + 14, 1)
            # print "RDMA read from polarity p/n swapping:", hex(response[1])  
        
            # extra param to enable data gen headers for farm mode
            myTBClient.setup_ll_frm_gen(data_gen_base, x10g['frame_len']/8, x10g['data_format'], x10g['num_frames']-1, 1)  
        
            #data_gen = x10g['data_gen']
            #print "datagen =", data_gen

            print "Dump of 10g regs for xaui"
            myTBClient.dump_regs_hex(x10g_base, 16)
            
            print "Dump of 10g regs for data gen"
            myTBClient.dump_regs_hex(data_gen_base, 16)
            
        return 1
        
    def start_10g_link(self, x10g, myTBClient):
        """ start a 10g link
             """
        
        if x10g['enable'] == 1:
            print "Start 10G link nr", x10g['link_nr']

            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   # connect RDMA to F3
            
            time.sleep(x10g['delay'])   # wait before trigger

            if x10g['data_gen'] == 1:
                print "Trigger LL Data Gen"
                if x10g['link_nr']%2:
                    myTBClient.toggle_bits(0, 1)   # xaui chan 0
                else:               
                    myTBClient.toggle_bits(0, 2)   # xaui chan 1
                
        return 1

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
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   # connect RDMA to F3
            
            myTBClient.clear_ll_monitor(ll_mon_base)
                    
        return 1

    def monitor_10g_link(self, x10g, myTBClient):
        """ monitor 10g link
             """
        
        if x10g['enable'] == 1:
            print "Monitor 10G link nr", x10g['link_nr']
            
            if x10g['link_nr']%2 == 1:  # nb link nr runs from 1 to 8
                ll_mon_base = myTBClient.llink_mon_0
            else:
                ll_mon_base = myTBClient.llink_mon_1            
                
            # switch mux to fpga 
            fpga_mux = fpga_lut[x10g['link_nr']] - 1
            response = myTBClient.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, fpga_mux_base, fpga_mux)   # connect RDMA to F3
            
            myTBClient.read_ll_monitor(ll_mon_base)
                    
        return 1
                
        
if __name__ == "__main__":
    TBTest = TBTest()
    TBTest.execute_tests()
