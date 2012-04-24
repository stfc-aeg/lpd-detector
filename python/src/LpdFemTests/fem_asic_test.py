'''
Created on 18 Apr 2012

@author: ckd27546
'''

# Import Python standard modules
import sys

# Import Fem modules
#from FemClient import FemClient
from LpdFemClient import *  #LpdFemClient

def set_10g_structs_variables_te2bank():
    """ Construct and return to dictionaries defining to network interfaces
        ..both interfaces same though? """
    
#    myDict = {'field1': 'some val', 'field2': 'some val'}
    x10g_0 = {'src_mac' : mac_addr_to_uint64('62-00-00-00-00-01'),
              'src_ip'  : ip_addr_to_uint32('192.168.0.1'),
              #x10g.src_prt   = prt_addr_to_uint16(prt_addr_to_uint16('0000')); # Typo?
              'src_prt' : prt_addr_to_uint16('0000'),
              'dst_mac' : mac_addr_to_uint64('00-07-43-06-31-A3'),
              'dst_ip'  : ip_addr_to_uint32('192.168.0.13'),
              'dst_prt' : prt_addr_to_uint16('0000')}
    
    x10g_1 = {'src_mac' : mac_addr_to_uint64('62-00-00-00-00-01'),
              'src_ip'  : ip_addr_to_uint32('192.168.0.1'),
              'src_prt' : prt_addr_to_uint16('0000'),
              'dst_mac' : mac_addr_to_uint64('00-07-43-06-31-A3'),  # in vhdl 10g 
              'dst_ip'  : ip_addr_to_uint32('192.168.0.13'),
              'dst_prt' : prt_addr_to_uint16('0000')}

    return x10g_0, x10g_1

def mac_addr_to_uint64(mac_addr_str):
    #convert hex MAC address 'u-v-w-x-y-z' string to integer
    # Convert MAC address into list of 6 elements (and removing the - characters)
    mac_addr_list = mac_addr_str.split('-')
   
    # Reverse the order of the list
    #mac_addr_list.reverse()         DO NOT REVERSE THE ORDER !!
    
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

def ip_addr_to_uint32(ip_addr_str):
    # Convert MAC address into list of 6 elements (and removing the - characters)
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

def prt_addr_to_uint16(prt_addr_str):
    #convert hex prt string to integer

    return int(prt_addr_str)
    
    
# --------------------------------------------------------------------------- #

#femHost = '192.168.0.13'
#femPort = 6969
femHost = '127.0.0.1'
femPort = 5000

try:
    myLpdFemClient = LpdFemClient((femHost, femPort), timeout=10)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)


# enable sending reset to both ppc processors if = 1
send_ppc_reset = 0;

# for new fast controls with optional dynamic vetos if = 1
fast_ctrl_dynamic = 1;

# send data via 10g udp block (needs matlab toolbox license)
enable_10g = 1;

# Read 10g data either by packet or frames
readout_mode = 'frame';

# choose data source to 10g block 
# 0 = llink frame generator
# 1 = direct from asic  
# 2 = PPC
data_source_to_10g = 0

# 1 = dummy counting data from asic rx block
# 0 = real data from asic
asic_data_source = 0;

# for pseudo random frames from asic  (must also set asic_data_source = 0)
asic_pseudo_random = 1;

# steer loading of brams for asic slow and fast configuration data
if (data_source_to_10g == 0 or data_source_to_10g == 2):
    load_asic_config_brams = 0 
else:
    if (asic_data_source == 0):
        load_asic_config_brams = 1  
    else: # skip brams if using asic rx internal data generator
        load_asic_config_brams = 0

# Nr (100 MHz) clock periods delay before start of asic data rx
# tuned for various data runs to capture 1st data bit in stream
# will be replaced later by signal from asic fast block to asic rx
if (asic_pseudo_random) is True:
    asic_rx_start_delay = 59   #uint32(59); 
else:
    asic_rx_start_delay = 1362  #uint32(1362);



num_ll_frames = 2  # nr of local link frames to generate

if (data_source_to_10g == 0 or data_source_to_10g == 2):
    trigger_type = 'a'
else:
    trigger_type = 'all'

#--------------------------------------------------------------------
# Options for configuring LPD ASICs 

# Asic fast cmds 20 or 22 bits format
fast_cmd_reg_size = 22

# Asic Rx 128 bit channel enable masks

# Use list instead of array
mask_list = [0, 0, 0, 0]
if asic_data_source == 1:    # enable all channels for dummy data from asic rx    
    mask_list[0] = 0xffffffff
    mask_list[1] = 0xffffffff
    mask_list[2] = 0xffffffff
    mask_list[3] = 0xffffffff
else: # Enable only relevant channel for single ASIC test module
    mask_list[0] = 0x00000001


#set asic receiver readout size & frame allocation
# valid settings with 16K FIFO
# (more than 3 trigger overflows when going direct to 10 G link)
#  2,2 = 3 triggers with 3 triggers per ll frame ; ie 1 frame
#  1,1 = 2 triggers with 2 triggers per ll frame ; ie 1 frame
# see labbook #19 p191  jac
no_asic_cols         = 1   # no_asic_cols = nr triggers or time slices/images
no_asic_cols_per_frm = 1   # no images per local link frame
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
asic_gain_override = 0

# rob's udp packet headers : 0 to disable ; Nb to enable need correct bit pattern
# Nb this is not the same as asic rx header; Utilised by robs_udp_packet_header_10g()
robs_udp_packet_hdr = 0;

if (data_source_to_10g == 0): # frame generator
    udp_pkt_len = 8000  #1000
    udp_pkt_num = 1
    udp_frm_sze = 1024*1024*8
    udp_in_buf_size =1024*1024*1024*1
    
elif (data_source_to_10g == 2):
    # skip following and by default use same values as asic rx
    pass


if (enable_10g == 1):
    
    #set up the UDP IP blocks
    x10g_0, x10g_1 = set_10g_structs_variables_te2bank()
    
    #set up the UDP IP blocks
    myLpdFemClient.fem_10g_udp_set_up_block0(udp_pkt_len, udp_frm_sze, eth_ifg)
    myLpdFemClient.fem_10g_udp_set_up_block1(udp_pkt_len, udp_frm_sze, eth_ifg)
    
    #set MAC, IP Port addresses
#    myLpdFemClient.fem_10g_udp_net_set_up_block0(x10g_0)
#    myLpdFemClient.fem_10g_udp_net_set_up_block1(x10g_1)

    ''' create a udp record - REMOVED '''
#    u = udp('192.168.0.13', 'LocalPort', 61649,'InputBufferSize', udp_in_buf_size, 'DatagramTerminateMode', 'off')
#    myFemClient = FemClient(hostAddr='192.168.0.13', timeout=10) 

    myLpdFemClient.robs_udp_packet_header_10g(robs_udp_packet_hdr)

#set up data generator 0
ll_frm_gen_data_type=0

# length specifies nr of 64 bit words
myLpdFemClient.ll_frm_gen_setup(udp_frm_sze/4, ll_frm_gen_data_type)  # normal operation

# length specifies nr of 64 bit words
#print "DATA GEN Nr Frames\n"
##rdma_write(    data_gen_0+2, num_ll_frames+1,'rw','DATA GEN Nr Frames');
#LpdFemClient.rdmaWrite(data_gen_0+2, num_ll_frames+1)
myLpdFemClient.frame_generator_set_up_10g(2, num_ll_frames+1)

print "\n"
if (enable_10g == 1):
    myLpdFemClient.clear_ll_monitor()
    print "\n"
    myLpdFemClient.read_ll_monitor()
    print "\n"


#--------------------------------------------------------------------
# configure the ASICs
""" LEAVE THIS SECTION FOR LATER """
if data_source_to_10g == 1:
    
    if load_asic_config_brams == 1:  # only load brams if sending data from asics
        # slow data
        slow_ctrl_data, no_of_bits = myLpdFemClient.read_slow_ctrl_file('SlowControlDefault-1A.txt')
        # fast data
        if (asic_pseudo_random):
            [fast_cmd_data, no_of_words, no_of_nops] = myLpdFemClient.read_fast_cmd_file_jc_new('fast_test1.txt',fast_cmd_reg_size)
        else:
            [fast_cmd_data, no_of_words, no_of_nops] = myLpdFemClient.read_fast_cmd_file_jc_new('fast_readout_4f_gaps.txt',fast_cmd_reg_size)
    
    #set up the fast command block
    if fast_ctrl_dynamic == 1:   # new design with dynamic vetos
        myLpdFemClient.fem_fast_bram_setup(fast_cmd_data, no_of_words)
        myLpdFemClient.fem_fast_cmd_setup_new(no_of_words+no_of_nops)
    else:
        myLpdFemClient.fem_fast_cmd_setup(fast_cmd_data, no_of_words, fast_ctrl_dynamic)
    
    
    #set up the slow control IP block
    myLpdFemClient.fem_slow_ctrl_setup(slow_ctrl_data, no_of_bits)
    
#    # select slow control load mode  jac
#    rdma_write(sCom,slow_ctr_0+0,uint32(2),'rw','asic load mode')
    myLpdFemClient.select_slow_ctrl_load_mode(0, 2)
    
    #set up the ASIC RX IP block
#    fem_asic_rx_setup(mask_array, no_asic_cols+1,no_asic_cols_per_frm+1)
    myLpdFemClient.fem_asic_rx_setup(mask_list, no_asic_cols+1, no_asic_cols_per_frm+1)
    
#    # data source - self test
#    data_source_reg           = (0x00000001 | myLpdFemClient.asic_srx_0)
#    rdma_write(sCom,data_source_reg,asic_data_source,'rw','asic rx data source') # 0 = real data ; 1 = test data
    myLpdFemClient.data_source_self_test()
    
       
#    gain_override_reg = bitor(hex2dec('0000000'))
#    rdma_write(sCom,gain_override_reg,asic_gain_override,'rw','asic rx gain override')
    myLpdFemClient.gain_override()
     
    # top level steering
#    rdma_write(sCom,fem_ctrl_0+5,uint32(0),'rw','asic turn on buffers')   # turn fast & slow buffers on
#    rdma_write(sCom,fem_ctrl_0+2,uint32(1),'rw','asic serial out readback is from bot sp3 i/o')
#    rdma_write(sCom,fem_ctrl_0+4,asic_rx_start_delay,'rw','asic start readout delay wrt fast cmd')
    myLpdFemClient.top_level_steering(asic_rx_start_delay)


# select asic or llink gen as data source
myLpdFemClient.fem_local_link_mux_setup(data_source_to_10g)

#--------------------------------------------------------------------
# send triggers to data generators
#switch trigger_type
#    case 'all'  # start asic seq  = reset, slow, fast & asic rx
#        toggle_bits(sCom,fem_ctrl_0,uint32(0), uint32(2),'rw');
#    case 'a'   # trigger to local link frame gen 
#        toggle_bits(sCom,fem_ctrl_0,uint32(0), uint32(1));
#    case 'b'    # trigger the asic rx block
#        toggle_bits(sCom,fem_ctrl_0,uint32(3), uint32(1));
#    case 's'  # trigger just the slow contol IP block
#        toggle_bits(sCom,fem_ctrl_0,uint32(7), uint32(1));
#    case 'f'  # trigger just the fast cmd block
#        toggle_bits(sCom,fem_ctrl_0,uint32(7), uint32(2));
#    otherwise

#--------------------------------------------------------------------
# send triggers to data generators

# Defined functions utilised by dictionary lookup (switch statement substitution)
def all_asic_seq():
    # start asic seq  = reset, slow, fast & asic rx
    print "You selected 'all'"
    myLpdFemClient.toggle_bits(0, 2)    
    
def alpha():
    print "You selected 'a'"
    # trigger to local link frame gen 
    myLpdFemClient.toggle_bits(0, 1)
    
def bravo():
    print "You selected 'b'"
    # trigger the asic rx block
    myLpdFemClient.toggle_bits(3, 1)

def sierra():
    # trigger just the slow contol IP block
    print "You selected 's'"
    myLpdFemClient.toggle_bits(7, 1)    
    
def foxtrot():
    # trigger just the fast cmd block
    print "You selected 'f'"
    myLpdFemClient.toggle_bits(7, 2)
    
# Substitute switch statement with Python dictionary lookup
options = {'all' : all_asic_seq,
           'a'   : alpha,
           'b'   : bravo,
           's'   : sierra,
           'f'   : foxtrot,
           }

try:
    options[trigger_type]()
except KeyError:
    print "No case matching variable trigger_type!"
#--------------------------------------------------------------------


if enable_10g == 1:
    #Check local link frame statistics
    myLpdFemClient.read_ll_monitor()


# check contents of slow control read back BRAM
# not working yet
#rdma_block_read(slow_ctr_2, 4, 'Read Back Slow Ctrl RAM');


# allow time to trigger ppc dma transfer in sdk app
if data_source_to_10g == 2:
    print "\n paused waiting 2 seconds allowing time to trigger ppc dma transfer in sdk app\n"
    time.sleep(2)   # waits for keyboard input


print "\n ...continuing\n"

if send_ppc_reset == 1:
    # Resets dma engines
    myLpdFemClient.toggle_bits(9, 1)


#--------------------------------------------------------------------
# receive the image data from 10g link

#check how much data has arrived
myLpdFemClient.check_how_much_data_arrived(udp_frm_sze)


# create an array of uint32 to hold the data frame
data_size = udp_frm_sze/2
dudp = [0] * data_size
packet_size = udp_pkt_len/2

print "Receiving the image data from 10g link.."

if  readout_mode is "packet":     
    dudp = myLpdFemClient.recv_image_data_as_packet(udp_pkt_num, dudp, packet_size)
elif readout_mode is "frame":
    dudp = myLpdFemClient.recv_image_data_as_frame(dudp)            
else:
    pass


print "\n"

if enable_10g == 1:
    #Check local link frame statistics
    myLpdFemClient.read_ll_monitor()    
    myLpdFemClient.close()
    print "Closed 10g\n"


#--------------------------------------------------------------------
# process the image data

# 1st arg = 31 is to skip over header
# changed skip to 8 when running with ppc dma 
# 2nd arg is image/trigger nr starting at 1

if (data_source_to_10g == 2):
    image_data_raw = myLpdFemClient.extract_asic_data(1, 1, dudp)
else:
    image_data_raw = myLpdFemClient.extract_asic_data(8, 1, dudp)


# rotate to match ivan's display (isn't matlab clever :) )
#image_data = rot90(image_data_raw);                        # Redundant?

"""                        Plot Data - Sort Later             """
#frame_nr = 1;
## plot the data from the asic
#colormap gray;
#h = imagesc(image_data);
#
#colorbar('location', 'eastoutside');
#title(['frame ',num2str(frame_nr)]);

# report any bytes remaining in buffer
#u.bytesavailable                                    # Redundant?

