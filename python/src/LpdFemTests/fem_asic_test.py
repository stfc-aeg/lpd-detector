#FEM 10G UDP Test - Instrument Controls tool box
# top level for fem with asic test module
# updated to use Rob's new libraries for 10g, rdma, llink
# jac 25.10.11
# 03/04/12  jac   cleaned up again

# Import Python standard modules
import serial, time
# Force float division:
#from __future__ import division    # Update: do NOT force float division
#import numarray

# Import Fem modules
from FemClient import FemClient

def fem_10g_udp_set_up(s, base_addr, udp_pkt_len, udp_frm_sze, eth_ifg):

    fixed_length = 0
    
    # set up header lengths
    if fixed_length == 1 is True:
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
    rdma_write(s,base_addr + 0x0000000C, data0,         'rw', 'UDP Block Packet Size')
    
    # set IP header length + 64 Bytes
    data1 = 0xDB000000 + ip_hdr_len
    rdma_write(s,base_addr + 0x00000004, data1,         'rw', 'UDP Block IP Header Length')    
    
    # set udp length +64 Bytes
    data2 = 0x0000D1F0 + udp_hdr_len
    rdma_write(s,base_addr + 0x00000009, data2,         'rw', 'UDP Block UDP Length')
    
    # enable & set IFG
    rdma_write(s,base_addr + 0x0000000F, ctrl_reg_val,   'rw', 'UDP Block IFG')
    rdma_write(s,base_addr + 0x0000000D, eth_ifg,        'rw', 'UDP Block IFG')
    
    return 1


def set_10g_structs_variables_te2bank():
    """ Construct and return to dictionaries defining to network interfaces
        ..both interfaces same though? """
    
#    myDict = {'field1': 'some val', 'field2': 'some val'}
    x10g_0 = {'src_mac' : '62-00-00-00-00-01',
              'src_ip'  : '192.168.0.1',
              #x10g.src_prt   = prt_addr_to_uint16('0000'); # Typo?
              'src_prt' : '0000',
              'dst_mac' : '00-07-43-06-31-A3',
              'dst_ip'  : '192.168.0.13',
              'dst_prt' : '0000'}
    
    x10g_1 = {'src_mac' : '62-00-00-00-00-01',
              'src_ip'  : '192.168.0.1',
              'src_prt' : '0000',
              'dst_mac' : '00-07-43-06-31-A3',  # in vhdl 10g 
              'dst_ip'  : '192.168.0.13',
              'dst_prt' : '0000'}

    return x10g_0, x10g_1

#def hex2dec(n): ''' Redundant! '''
#    """ returned the hexadecimal string representation of integer n """
#    try:
#        int(n)
#    except ValueError:
#        print "hex2dec() error: 0x MUST prefix argument!"
#        return
#    else:
#        return "%X" % n


'''
if ispc == 1
    addpath ('C:\Users\jac36\WORKSPACES\common\rdma\tags\release_01\m\');
    addpath ('C:\Users\jac36\WORKSPACES\common\local_link\tags\release_03_beta\m\');
    addpath ('C:\Users\jac36\WORKSPACES\common\X10G\tags\release_01\m\');
#    addpath ('C:\Users\jac36\WORKSPACES\common\X10G\trunk\Matlab\test\');

if isunix == 1
   addpath ('/u/rha73/pc/fpga/library/common/rdma/trunk/m/');
   addpath ('/u/rha73/pc/fpga/library/common/local_link/trunk/m/');
   addpath ('/u/rha73/pc/fpga/library/common/X10G/trunk/m/');
   addpath ('/u/rha73/pc/fpga/library/common/X10G/trunk/matlab/test/');
'''

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
data_source_to_10g = 0;

# 1 = dummy counting data from asic rx block
# 0 = real data from asic
asic_data_source = 0;

# for pseudo random frames from asic  (must also set asic_data_source = 0)
asic_pseudo_random = 1;

# steer loading of brams for asic slow and fast configuration data
if (data_source_to_10g == 0 or data_source_to_10g == 2) is True:
    load_asic_config_brams = 0; 
else:
    if (asic_data_source == 0) is True:
        load_asic_config_brams = 1;  
    else: # skip brams if using asic rx internal data generator
        load_asic_config_brams = 0;

# Nr (100 MHz) clock periods delay before start of asic data rx
# tuned for various data runs to capture 1st data bit in stream
# will be replaced later by signal from asic fast block to asic rx
if (asic_pseudo_random) is True:
    asic_rx_start_delay = 59   #uint32(59); 
else:
    asic_rx_start_delay = 1362  #uint32(1362);  


# FEM UART baud rate   e.g. 9600 / 115200
baud_rate=115200

#Create a serial record for the device parameters
#global sCom;
#sCom=serial('COM1','BaudRate',baud_rate);
try:
    sCom = serial.Serial(port=1, baudrate = baud_rate, timeout = 1)
except Exception as errString:
    print "Unable to open serial connection: ", errString
    print "Terminating program.."
    return

'''
#base addresses of IP blocks in FEM address space
set_fem_base_address_variables;
'''
num_ll_frames = 2;  # nr of local link frames to generate

if (data_source_to_10g == 0 or data_source_to_10g == 2) is True:
    trigger_type = 'a';
else:
    trigger_type = 'all';

#--------------------------------------------------------------------
# Options for configuring LPD ASICs 

# Asic fast cmds 20 or 22 bits format
fast_cmd_reg_size = 22;

# Asic Rx 128 bit channel enable masks
'''
mask_array = zeros(4,1,'uint32'); # disable all
if asic_data_source == 1    # enable all channels for dummy data from asic rx 
    mask_array(1) = uint32(hex2dec('ffffffff'));
    mask_array(2) = uint32(hex2dec('ffffffff'));
    mask_array(3) = uint32(hex2dec('ffffffff'));
    mask_array(4) = uint32(hex2dec('ffffffff'));
else # Enable only relevant channel for single ASIC test module
    mask_array(1) = uint32(hex2dec('00000001'));
'''
# Use list instead of array
mask_list = [0, 0, 0, 0]
if asic_data_source == 1 is True:    # enable all channels for dummy data from asic rx    
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
no_asic_cols         = 1;   # no_asic_cols = nr triggers or time slices/images
no_asic_cols_per_frm = 1;   # no images per local link frame
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
udp_frm_sze = (no_asic_cols+1) * 512 * 128 * 2 + 0;  # header and trailer removed by ll_rmv
udp_in_buf_size = 2048*1024;

#  overrides to asic algorithm gain selection
#  bits
#  0000  normal gain selection     0
#  1000  force select x100         8
#  1001  force select x10          9
#  1011  force select x1          11
#  1111  force error condition ?  15
asic_gain_override = 0;

# rob's udp packet headers : 0 to disable ; Nb to enable need correct bit pattern
# Nb this is not the same as asic rx header
robs_udp_packet_hdr = 0;

if (data_source_to_10g == 0) is True: # frame generator
    udp_pkt_len = 8000  #1000
    udp_pkt_num = 1
    udp_frm_sze = 1024*1024*8
    udp_in_buf_size =1024*1024*1024*1
    
elif (data_source_to_10g == 2) is True:
    # skip following and by default use same values as asic rx
#     udp_pkt_len = uint32(8000);
#     udp_pkt_num = uint32(1);
#     udp_frm_sze = hex2dec('40');
#     udp_in_buf_size =1024*1024*1024*1;
    pass


if (enable_10g == 1) is True:
    
    #set up the UDP IP blocks
    x10g_0, x10g_1 = set_10g_structs_variables_te2bank()
    
    #set up the UDP IP blocks
    fem_10g_udp_set_up(sCom, udp_10g_0, udp_pkt_len, udp_frm_sze, eth_ifg)
    fem_10g_udp_set_up(sCom, udp_10g_1, udp_pkt_len, udp_frm_sze, eth_ifg)
    
    #set MAC, IP Port addresses
    fem_10g_udp_net_set_up(sCom, udp_10g_0, x10g_0)   ''' Function call '''
    fem_10g_udp_net_set_up(sCom, udp_10g_1, x10g_1)   ''' Function call '''

    # create a udp record
#    u = udp('192.168.0.13', 'LocalPort', 61649,'InputBufferSize', udp_in_buf_size, 'DatagramTerminateMode', 'off')
    myFemClient = FemClient(hostAddr='192.168.0.13', timeout=10) 
    # where remote host = 192.168.0.13 and 
    #  PropertyName: 'LocalPort' / 'InputBuffer' / 'DatagramTerminateMode'
    #  assigned values: 61649 / udp_in_buf_size / off
    #  respectively   
#    u.timeout = 10     # Set by FemClient creator
#    u.InputDatagramPacketSize = 8192    # Redundant: recv() receives all available data
    #TODO: Check if byte order change required?
#    u.ByteOrder = 'littleEndian'
    
    # open the udp connection
#    fopen(u)    # Redundant
    
    # rob's udp packet headers
    packet_header_10g_0 = bitor(hex2dec('0000000b'), udp_10g_0)   ''' Function call '''
    packet_header_10g_1 = bitor(hex2dec('0000000b'), udp_10g_1)   ''' Function call '''
    
    rdma_write(sCom,packet_header_10g_0,robs_udp_packet_hdr,'rw','robs udp packet header 10g_0')   ''' Function call '''
    rdma_write(sCom,packet_header_10g_1,robs_udp_packet_hdr,'rw','robs udp packet header 10g_1')   ''' Function call '''
    


#set up data generator 0
ll_frm_gen_data_type=0;

# length specifies nr of 64 bit words
ll_frm_gen_setup(sCom,data_gen_0,udp_frm_sze/4, ll_frm_gen_data_type);  # normal operation   ''' Function call '''

# length specifies nr of 64 bit words
rdma_write(sCom,data_gen_0+2,num_ll_frames+1,'rw','DATA GEN Nr Frames');   ''' Function call '''


#fprintf('\n');
if (enable_10g == 1) is True:
    clear_ll_monitor(sCom, llink_mon_0);   ''' Function call '''
#    fprintf('\n');  
    read_ll_monitor(sCom, llink_mon_0);      ''' Function call '''
#    fprintf('\n\n');   


#--------------------------------------------------------------------
# configure the ASICs
    """ LEAVE THIS SECTION FOR LATER """ '''
if data_source_to_10g == 1
    
    if load_asic_config_brams == 1  # only load brams if sending data from asics
        # slow data
        [slow_ctrl_data, no_of_bits] = read_slow_ctrl_file('SlowControlDefault-1A.txt');
        # fast data
        if (asic_pseudo_random)
            # [fast_cmd_data, no_of_words, no_of_nops] = read_fast_cmd_file_jc_new('fast_random.txt',fast_cmd_reg_size);
            # [fast_cmd_data, no_of_words, no_of_nops] = read_fast_cmd_file_jc_new('fast_random_gaps.txt',fast_cmd_reg_size);
            # [fast_cmd_data, no_of_words, no_of_nops] = read_fast_cmd_file_jc_new('fast_tune.txt',fast_cmd_reg_size);
            [fast_cmd_data, no_of_words, no_of_nops] = read_fast_cmd_file_jc_new('fast_test1.txt',fast_cmd_reg_size);
        else
            # [fast_cmd_data, no_of_words] = read_fast_cmd_file_jc('fast_tune.txt',fast_cmd_reg_size);
            [fast_cmd_data, no_of_words, no_of_nops] = read_fast_cmd_file_jc_new('fast_readout_4f_gaps.txt',fast_cmd_reg_size);
            # [fast_cmd_data, no_of_words] = read_fast_cmd_file_jc('fast_readout_4f_nops.txt',fast_cmd_reg_size);
        
    
    
    #set up the fast command block
    if fast_ctrl_dynamic == 1   # new design with dynamic vetos
        fem_fast_bram_setup(sCom, fast_cmd_1, fast_cmd_data, no_of_words);
        fem_fast_cmd_setup_new(sCom, fast_cmd_0, no_of_words+no_of_nops);
    else
        fem_fast_cmd_setup(sCom, fast_cmd_0, fast_cmd_1, fast_cmd_data, no_of_words, fast_ctrl_dynamic);
    
    
    #set up the slow control IP block
    fem_slow_ctrl_setup(sCom, slow_ctr_0, slow_ctr_1, slow_ctrl_data, no_of_bits);
    
    # select slow control load mode  jac
    rdma_write(sCom,slow_ctr_0+0,uint32(2),'rw','asic load mode');
    
    #set up the ASIC RX IP block
#    fem_asic_rx_setup(sCom, asic_srx_0, mask_array, no_asic_cols+1,no_asic_cols_per_frm+1);
    fem_asic_rx_setup(sCom, asic_srx_0, mask_list, no_asic_cols+1,no_asic_cols_per_frm+1);
    
    # data source - self test
    data_source_reg           = bitor(hex2dec('00000001'), asic_srx_0);
    rdma_write(sCom,data_source_reg,asic_data_source,'rw','asic rx data source'); # 0 = real data ; 1 = test data
    
    gain_override_reg = bitor(hex2dec('0000000'), asic_srx_0);
    rdma_write(sCom,gain_override_reg,asic_gain_override,'rw','asic rx gain override');
     
    # top level steering
    rdma_write(sCom,fem_ctrl_0+5,uint32(0),'rw','asic turn on buffers');   # turn fast & slow buffers on
    rdma_write(sCom,fem_ctrl_0+2,uint32(1),'rw','asic serial out readback is from bot sp3 i/o');
    rdma_write(sCom,fem_ctrl_0+4,asic_rx_start_delay,'rw','asic start readout delay wrt fast cmd');
'''

# select asic or llink gen as data source
fem_local_link_mux_setup(sCom, fem_ctrl_0, data_source_to_10g);   ''' Function call '''

##--------------------------------------------------------------------
## send triggers to data generators
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
#

#--------------------------------------------------------------------
# send triggers to data generators

# Defined functions utilised by dictionary lookup (switch statement substitution)
def all_asic_seq():
    # start asic seq  = reset, slow, fast & asic rx
    print "You selected 'all'"
    toggle_bits(sCom,fem_ctrl_0,0, 2'rw')    ''' Function call '''    
    
def alpha():
    print "You selected 'a'"
    # trigger to local link frame gen 
    toggle_bits(sCom,fem_ctrl_0,0, 1)        ''' Function call '''
    
def bravo():
    print "You selected 'b'"
    # trigger the asic rx block
    toggle_bits(sCom,fem_ctrl_0,3, 1)      ''' Function call '''

def sierra():
    # trigger just the slow contol IP block
    print "You selected 's'"
    toggle_bits(sCom,fem_ctrl_0,7, 1)   ''' Function call '''    
    
def foxtrot():
    # trigger just the fast cmd block
    print "You selected 'f'"
    toggle_bits(sCom,fem_ctrl_0,7, 2)   ''' Function call '''
    
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


if enable_10g == 1 is True:
    #Check local link frame statistics
    read_ll_monitor(sCom, llink_mon_0)   ''' Function call '''


# check contents of slow control read back BRAM
# not working yet
#rdma_block_read(sCom, slow_ctr_2, 4, 'Read Back Slow Ctrl RAM');

if enable_10g == 0 is True:
    sCom.close()
    return


# allow time to trigger ppc dma transfer in sdk app
if data_source_to_10g == 2 is True:
    print "\n paused waiting 2 seconds allowing time to trigger ppc dma transfer in sdk app\n"
    time.sleep(2)   # waits for keyboard input


print "\n ...continuing\n"

if send_ppc_reset == 1 is True:
    # Resets dma engines
    toggle_bits(sCom,fem_ctrl_0, 9, 1)   ''' Function call '''


#--------------------------------------------------------------------
# receive the image data from 10g link

#check how much data has arrived
count=0
while (myFemClient.bytesavailable ~= udp_frm_sze && count <= 8)
    no_bytes = myFemClient.bytesavailable;
    print "\n%4i" % count, "%8X" % no_bytes
    count=count+1;
    time.sleep(0.25)
    time.sleep(0.75)


# create an array of uint32 to hold the data frame
data_size = udp_frm_sze/2
dudp = [0] * data_size
packet_size = udp_pkt_len/2

if  readout_mode is "packet":     
    # loop to read udp frame packet by packet
    for i =0:udp_pkt_num-1
#        dudp = uint32(fread(u, packet_size, 'uint16'));
#        fprintf('\n%04i %08X %08X %08X %08X',i, dudp(1),dudp(2),dudp(3),dudp(packet_size));
        dudp = myFemClient.recv()   # TODO: Understand how to use FemClient receive functionality
                                    # Or use read() function:  
        #dudp = myFemClient.read(theBus, theWidth, theAddr, theReadLen)    ??
        print "\n%4i %8X %8X %8X %8X" % (i, dudp(1),dudp(2),dudp(3),dudp(packet_size))
elif readout_mode is "frame":
#    dudp = uint32(fread(u, data_size, 'uint32'));
    #dudp = myFemClient.recv()    # TODO: Understand how to use FemClient receive functionality    
else:
    pass


#data_rate = udp_frm_sze/time_taken;
#fprintf('\nData Size, Time, Data Rate #8i #4e #4e\n',udp_frm_sze,time_taken,data_rate);
print "\n"

if enable_10g == 1 is True:
    #Check local link frame statistics
    read_ll_monitor(sCom, llink_mon_0)    
    myFemClient.close()
    print "Closed 10g \n"


#--------------------------------------------------------------------
# process the image data

# 1st arg = 31 is to skip over header
# changed skip to 8 when running with ppc dma 
# 2nd arg is image/trigger nr starting at 1

if (data_source_to_10g == 2) is True:
    image_data_raw = extract_asic_data(1, 1, dudp)
else:
    image_data_raw = extract_asic_data(8, 1, dudp)


# rotate to match ivan's display (isn't matlab clever :) )
#image_data = rot90(image_data_raw);                        # Redundant?

                        ''' How Plot Data? '''
#frame_nr = 1;
## plot the data from the asic
#colormap gray;
#h = imagesc(image_data);
#
#colorbar('location', 'eastoutside');
#title(['frame ',num2str(frame_nr)]);

# report any bytes remaining in buffer
#u.bytesavailable                                    # Redundant?

try:
    sCom.close()
except:
    print "Unable to close serial connection before program termination"


