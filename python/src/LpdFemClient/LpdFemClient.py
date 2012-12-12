'''
LpdFemClient - XFEL LPD class sitting between the API and the FemClient


         
Created 16 October 2012

@Author: ckd



  ADC channels:
    0 = HV volts    1 = 5V volts    2 = 1.2V volts
    3 = HV current  4 = 5V current  5 = 1.2V current
    6 = PSU temp    7 = not used
    8-15  = 2.5V volts (A-H)
    16-23 = 2.5V current (A-H)
    24-31 = Sensor temp (A-H)

  Bits:
    0 = [out] LV control (0=on)
    1 = [out] HV control (0=on)
    2 = unused
    3 = [in] External trip (1=tripped)
    4 = [in] Fault flag (1=tripped)
    5 = [in] Overcurrent (1=fault)
    6 = [in] High temperature (1=fault)
    7 = [in] Low temperature (1=fault)

'''

# Import Python standard modules
from string import strip, split

# log required when calculating temperature
from math import log
import pprint, time

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction

# Import library for parsing XML fast command files
from LpdCommandSequence.LpdCommandSequenceParser import LpdCommandSequenceParser
from LpdFemTests.SlowCtrlParams import SlowCtrlParams

## Test using FemAsicTest class..
#from LpdFemTests.fem_asic_test import *

class LpdFemClient(FemClient):
    '''
    
    '''

    # ADC channel numbers
    HV_VOLTS_CHAN =      0
    V5_VOLTS_CHAN =      1
    V12_VOLTS_CHAN =     2
    HV_AMPS_CHAN =       3
    V5_AMPS_CHAN =       4
    V12_AMPS_CHAN =      5
    PSU_TEMP_CHAN =      6
    V25A_VOLTS_CHAN =    8
    V25B_VOLTS_CHAN =    9
    V25C_VOLTS_CHAN =   10
    V25D_VOLTS_CHAN =   11
    V25E_VOLTS_CHAN =   12
    V25F_VOLTS_CHAN =   13
    V25G_VOLTS_CHAN =   14
    V25H_VOLTS_CHAN =   15
    V25A_AMPS_CHAN =    16
    V25B_AMPS_CHAN =    17
    V25C_AMPS_CHAN =    18
    V25D_AMPS_CHAN =    19
    V25E_AMPS_CHAN =    20
    V25F_AMPS_CHAN =    21
    V25G_AMPS_CHAN =    22
    V25H_AMPS_CHAN =    23
    SENSA_TEMP_CHAN =   24
    SENSB_TEMP_CHAN =   25
    SENSC_TEMP_CHAN =   26
    SENSD_TEMP_CHAN =   27
    SENSE_TEMP_CHAN =   28
    SENSF_TEMP_CHAN =   29
    SENSG_TEMP_CHAN =   30
    SENSH_TEMP_CHAN =   31
    
    # Bit numbers for control bits
    HV_CTRL_BIT    = 0
    LV_CTRL_BIT    = 1

    # Values for control bits
    OFF = 1
    ON  = 0

    # Bit numbers for status bits
    FEM_STATUS_BIT = 2
    EXT_TRIP_BIT   = 3
    FAULT_FLAG_BIT = 4
    OVERCURRENT_BIT =5
    HIGH_TEMP_BIT  = 6
    LOW_TEMP_BIT   = 7
    
    # Values for status bits
    TRIPPED = 1
    FAULT   = 1
    NORMAL  = 0
    
    # Enumarate fault flag as either cleared (0) or tripped (1) 
    flag_message = ["No", "Yes"]

    # Fem has three internal i2c buses, power card uses bus 0x300
    i2cPowerCardBus = 0x300
    
    # i2c device addresses
    AD7998ADDRESS = [0x22, 0x21, 0x24, 0x23]
    
    # Beta is utilised as an argument for calling the calculateTemperature() 
    #    but it's effectively fixed by the hardware design
    Beta = 3474

    # with new addressing using top 4 bits for fpga selection
    #    """ 32 way splitter """
    udp_10g_0     = 0x00000000    #0
    udp_10g_1     = 0x00800000    #1
    data_gen_0    = 0x01000000    #2
    data_chk_0    = 0x01800000    #3
    data_gen_1    = 0x02000000    #4
    data_chk_1    = 0x02800000    #5
    fem_ctrl_0    = 0x03000000    #6
    llink_mon_0   = 0x03800000    #7
    data_mon_1    = 0x04000000    #8
    slow_ctr_2    = 0x04800000    #9
    fast_cmd_0    = 0x05000000    #10
    fast_cmd_1    = 0x05800000    #11
    asic_srx_0    = 0x06000000    #12
    rsvd_13       = 0x06800000    #13
    slow_ctr_0    = 0x07000000    #14
    slow_ctr_1    = 0x07800000    #15
    dma_gen_0    = 0x08000000    #16
    dma_chk_0    = 0x08800000    #17
    dma_gen_1    = 0x09000000    #18
    dma_chk_1    = 0x09800000    #19
    dma_gen_2    = 0x0a000000    #20
    dma_chk_2    = 0x0a800000    #21
    dma_gen_3    = 0x0b000000    #22
    dma_chk_3    = 0x0b800000    #23
    bram_ppc1    = 0x0c000000    #24
    rsvd_25      = 0x0c800000    #25
    rsvd_26      = 0x0d000000    #26
    rsvd_27      = 0x0d800000    #27
    rsvd_28      = 0x0e000000    #28
    rsvd_29      = 0x0e800000    #29
    rsvd_30      = 0x0f000000    #30
    rsvd_31      = 0x0f800000    #31
    
    # file path to the location of the slow control and fast control configuration files
    filePath     = '/u/ckd27546/workspace/xfel_workspace/LpdFemTests/'
    slowCtrlPath = '/u/ckd27546/workspace/xfel_workspace/LpdFemTests/'
    fastCtrlPath = '/u/ckd27546/workspace/xfel_workspace/LpdCommandSequence/'
    
#    # Obtain current working directory for the slow control
#    # The two folders in question are related like this:
#    #    workspace/LpdFemTests
#    #    workspace/LpdCommandSequence
#    currentSlowCtrlDir = os.getcwd()
#    # Is this script executed from the folder containing it or its parent folder?
#    if currentSlowCtrlDir.find("LpdFemTests") == -1:
#        # Script was executed from parent folder
#        
#        # Because we are in the parent folder and not in the subfolder,
#        # the fast control path is straightforward to construct from slow control's:
#        currentFastCmdDir = currentSlowCtrlDir
#        # and then append "/LpdCommandSequence"
#        currentFastCmdDir += "/LpdCommandSequence"
#        
#        # Construct slow control path by appending '/LpdFemTests'
#        currentSlowCtrlDir += "/LpdFemTests" 
#    else:
#        # fem_asic_test executed from the same folder so we can use the parent folder of currentSlowCtrlDir 
#        # however, fast command reside in a different folder:
#        currentFastCmdDir = currentSlowCtrlDir.replace("/LpdFemTests", "") + "/LpdCommandSequence"
    
    def __init__(self, hostAddr=None, timeout=None):
        '''
            Constructor for LpdFemClient class
        '''

        # Call superclass initialising function
        super(LpdFemClient, self).__init__(hostAddr, timeout)

        #TODO: Remove these dummy variables when they become redundant
        #TODO: THIS tenGig0 DICTIONARY IS CURRENTLY NOT BEEN USED !
        #                    PLEASE SEE x10g_0 STRUCTURE INSTEAD
        self.tenGig0 = {'SourceMacDummy'  : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                        'SourceIpDummy'   : self.ip_addr_to_uint32('10.0.0.2'),
                        'SourcePortDummy' : self.prt_addr_to_uint16('0'),
                        # Target PC:
                        'DestMacDummy'  : self.mac_addr_to_uint64('00-07-43-10-65-A0'),
                        'DestIpDummy'   : self.ip_addr_to_uint32('10.0.0.1'),
                        'DestPortDummy' : self.prt_addr_to_uint16('61649')
                        }
        
        self.tenGig1SourceMacDummy = 0
        self.tenGig1SourceIpDummy = 0 
        self.tenGig1SourcePortDummy = 0
        self.tenGig1DestMacDummy = 0  
        self.tenGig1DestIpDummy                = 0
        self.tenGig1DestPortDummy              = 0
        self.tenGigInterframeGapDummy          = 0
        self.tenGigUdpPacketLenDummy           = 0
        self.femSendPpcResetDummy              = 0
        self.femFastCtrlDynamicDummy           = 0
        self.femSetupSlowCtrlBramDummy         = 0
        self.femEnableTenGigDummy              = 0
        self.femDataSourceDummy                = 0
        self.femAsicCountingDataDummy          = 0
        self.femAsicModuleTypeDummy            = 0
        self.femAsicRxStartDelayDummy          = 0
        self.femNumLocalLinkFramesDummy        = 0
        self.femAsicFastCmdRegSizeDummy        = 0
        self.femAsicEnableMaskDummy            = 0
        self.femAsicColumnsDummy               = 0
        self.femAsicColumnsPerFrameDummy       = 0
        self.femAsicGainOverrideDummy          = 0
        self.femAsicSlowControlParamsDummy     = 0
        self.femAsicFastCmdSequenceDummy       = 0
        self.femAsicPixelFeedbackOverrideDummy = 0
        self.femAsicPixelSelfTestOverrideDummy = 0
        self.femReadoutOperatingModeDummy      = 0


        # ------------------ variables utilised by jac's script ------------------

        self.run_params = { 
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

            'asicrx_invert_data' : 1,  # 1 = invert adc output data (by subtracting value from $FFF)

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

        self.x10g_0 = {'fpga_mac'   : self.mac_addr_to_uint64('62-00-00-00-00-01'), # fpga
                       'fpga_ip'    : self.ip_addr_to_uint32('10.0.0.2'),
                       'fpga_prt'   : self.prt_addr_to_uint16('0'),
                       'nic_mac'    : self.mac_addr_to_uint64('00-07-43-10-65-A0'), # burntoak eth6
                       'nic_ip'     : self.ip_addr_to_uint32('10.0.0.1'),
                       'nic_prt'    : self.prt_addr_to_uint16('61649'),
                       'enable'     : 1,        # enable this link
                       'link_nr'    : 1,        # link number
                       'data_gen'   : 1,        # data generator  1 = DataGen 2 = PPC DDR2  (used if run params data source is non asic)  
                       'data_format': 0,        # data format type  (0 for counting data)  
                       'frame_len'  : 0x10000,  #  0xFFFFF0,   #  0x800,    # frame len in bytes
                       'num_frames' : 1,        # number of frames to send in each cycle
                       'num_prts'   : 2,        # number of ports to loop over before repeating
                       'delay'      : 0,        # delay offset wrt previous link in secs
                       'nic_list'   : [ '61649@192.168.3.1' ]
                      }

        # Lpd fem object placeholder
#        self.myLpdFemClient = None
        # FemAsicTest object - to utilise John's new script
#        self.femAsicTest = FemAsicTest()
        # Obtain run parametres and 10 G settings
#        self.run_params, self.x10g_0 = self.femAsicTest.set_10g_structs_variables()
    '''
        --------------------------------------------------------
        Support functions taken from John's version of LpdFemClient.py:
        --------------------------------------------------------
    '''

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
    
    def uint32_to_ip_addr(self, ip_addr):
        ''' Construct IP address (in the form of a 32-bit integer) into a string '''
        ip_list =[ "", "", "", "" ]
        ip_address = (ip_addr & 0xFF000000) >> 24
        ip_list[3] = str(ip_address)
        ip_address = (ip_addr & 0xFF0000) >> 16
        ip_list[2] = str(ip_address)
        ip_address = (ip_addr & 0xFF00) >> 8
        ip_list[1] = str(ip_address)
        ip_address = (ip_addr & 0xFF)
        ip_list[0] = str(ip_address)
        # Add the list's contents into one string
        ip_addr_str = ""
        for idx in range(4):
            ip_addr_str += ip_list[idx] + "."
        return ip_addr_str[0:-1]
    
    def prt_addr_to_uint16(self, prt_addr_str):
        #convert hex prt string to integer
        return int(prt_addr_str)
        
    def init_ppc_bram(self, base_addr, fpga_nr):
        """ This function initialises ppc bram with fpga id """
 
        self.rdmaWrite(base_addr+0, fpga_nr) # fpga id
         
        return 0  

    def toggle_bits(self, reg_addr, bit_nr):
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

    def clear_ll_monitor(self):
        """ readout a local link monitor block
            Rob Halsall 08-04-2011    """
        base_addr = LpdFemClient.llink_mon_0
        #input monitor registers are offset from base address by 16
        
        print "Local Link Monitor Counter Reset"
        self.rdmaWrite(base_addr+1,0)
        self.rdmaWrite(base_addr+1,1)
        self.rdmaWrite(base_addr+1,0)
        
        return 1

    # Rob Halsall 08-04-2011
    def read_ll_monitor(self):
        """ readout a local link monitor block """
        
        #input monitor registers are offset from base address by 16
        mon_addr = LpdFemClient.llink_mon_0 + 16

        print "frm_last_length:\t",         hex( self.rdmaRead(mon_addr+0, 1)[0])
        print "frm_max_length: \t",         hex( self.rdmaRead(mon_addr+1, 1)[0])
        print "frm_min_length: \t",         hex( self.rdmaRead(mon_addr+2, 1)[0])
        print "frm_number:\t\t",            hex( self.rdmaRead(mon_addr+3, 1)[0])
        print "frm_last_cycles:\t",         hex( self.rdmaRead(mon_addr+4, 1)[0])
        print "frm_max_cycles: \t",         hex( self.rdmaRead(mon_addr+5, 1)[0])
        print "frm_min_cycles: \t",         hex( self.rdmaRead(mon_addr+6, 1)[0]) 
        total_data = self.rdmaRead(mon_addr+7, 1)[0]
        print "frm_data_total: \t", total_data         
        total_cycles = self.rdmaRead(mon_addr+8, 1)[0]
        print "frm_cycle_total:\t", total_cycles
        print "frm_trig_count: \t",         hex( self.rdmaRead(mon_addr+9, 1)[0])
        print "frm_in_progress:\t",         hex( self.rdmaRead(mon_addr+15, 1)[0])
        
        # data path = 64 bit, clock = 156.25 MHz
        total_time = float(total_cycles) * (1/156.25e6)
        if (total_time):
 #           rate = (total_data/total_time) * 8
            rate = (total_data/total_time)   #  total data is in bytes already   jac
        else:
            rate = 0
            
        print "Data Total = %e" % total_data
        print "Data Time = %e" % total_time
        print "Data Rate = %e" % rate
        
        print ""
        
        return 1


    def set_asic_clock_freq(self, base_address, clock_sel):
        """ Set the asic clock frequency ; 0 = 100 MHz ; 1 = divided clock """
        # set_asic_clock_freq(self.fem_ctrl_0, self.run_params['asic_local_clock_freq']
        address = base_address + 11
        
        reg_val = self.rdmaRead(address, 1)[0]

        if clock_sel == 1:
            reg_val |= 0x1
        else:
            reg_val &= 0x0

        print "setting asic clock freq sel = %08x" %reg_val

        self.rdmaWrite(address,reg_val)
        
        return 0 

    def setup_ll_frm_gen(self, base_address, length, data_type, num_ll_frames, hdr_trl_mode):
        """ This function sets up the data Generator & resets """
        
        # frm gen - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2
        #print "DATA GEN Data Length"
        self.rdmaWrite(base_address+1,reg_length)
        
        #print "DATA GEN Nr Frames"
        self.rdmaWrite(base_address+2, num_ll_frames)

        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4

        #turn header/trailer mode on if required
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
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)
        
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
    
    def setup_10g_packet_header(self, base_addr, packet_hdr):      
        """robs udp packet header for 10g"""
        
        self.rdmaWrite(base_addr + 11, packet_hdr)
        return 0
 
    def setup_10g_index_cycle(self, base_addr, index_cycle):       
        """ override word in header containing index for 10g port lut"""

        index_cycle &= 0x0000000f
        reg = self.rdmaRead(base_addr+10, 1)[0] 
        reg &= ~0x0000000f
        reg = reg | index_cycle
        self.rdmaWrite(base_addr+10, reg) 
        return 0

    def setup_10g_rx_filter(self, base_addr):
        """ set 10g rx filter to accept any udp packet """     

        reg = self.rdmaRead(base_addr+11, 1)[0]
        reg &= 0xffff00ff
        reg |= 0x0000f300
        self.rdmaWrite(base_addr+11, reg) 
        
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
        print 'ctrl_reg = $%08X' % ctrl_reg         
        
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

    def dump_regs_hex(self, base_addr, nr_regs):
        """ hex dump of regs """
        
        print "" 
        print 'rdma base addr = $%08X' % base_addr 
        for i in range(0, nr_regs):
        #    print "reg ", i, hex(self.rdmaRead(base_addr+i, 1)[0])
            print 'reg %2d = $%08X ' % (i, self.rdmaRead(base_addr+i, 1)[0])
            
        print ""  
        
        return 1      

    def setup_ppc_bram(self, base_addr, length):
        """ This function sets up the bram to provide ppc with run params """
 
        self.rdmaWrite(base_addr+8, 0) # handshaking
        self.rdmaWrite(base_addr+10, 0) # handshaking

        self.rdmaWrite(base_addr+9, 0) # port index
       
        self.rdmaWrite(base_addr+16, length) # for dma tx length in bytes
            
        return 0  

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

    def config_top_level(self):
        """ configure top level of design """
        
        # set asic clock freq
        self.set_asic_clock_freq(self.fem_ctrl_0, self.run_params['asic_local_clock_freq'])    # 0 = 100 Mhz, 1 = div clock 10 MHz
      
        if self.run_params['run_type'] == "asic_data_via_ppc":
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000001)  # asic data via ppc
        elif self.run_params['run_type'] == "asic_data_direct":
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000102)  # aisc direct to 10g
        elif self.run_params['run_type'] == "ll_data_gen":
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000000)  # data generator
        elif self.run_params['run_type'] == "ppc_data_direct":
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000001)  # ppc generated data
        else:
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000001)  # asic data via ppc
                
        return 0

    def config_10g_link(self):
        """ configure 10g link
        """
               
        if self.x10g_0['enable'] == 1:
            print "Configure 10G link nr", self.x10g_0['link_nr']
            
            if self.run_params['debug_level'] > 0:
                pp.pprint(self.x10g_0)
                        
            x10g_base = self.udp_10g_0
            data_gen_base = self.data_gen_0
            ppc_bram_base = self.bram_ppc1
           
            udp_pkt_len = self.run_params['udp_pkt_len']
            udp_frm_sze = self.x10g_0['frame_len']

            eth_ifg = self.run_params['eth_ifg']
            enable_udp_packet_hdr = 4;  # enabled for python = 4  
            
            # legacy non farm mode. (farm mode = 1)
            self.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            self.setup_10g_udp_net_block(x10g_base, self.x10g_0)    
            self.setup_10g_packet_header(x10g_base, enable_udp_packet_hdr)

            self.setup_10g_rx_filter(x10g_base) # accepts any udp packets

            self.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut   
                                 
#            print "Dump of Farm Mode LUT for xaui for Link %d" % self.x10g_0['link_nr']
#            self.dump_regs_hex(x10g_base+0x10000, 16) 
 
            print "Setting up Farm Mode LUT. May take several seconds... "                       
            if self.run_params['10g_farm_mode'] == 2:
                self.x10g_net_lut_setup(x10g_base, self.x10g_0) 
                self.x10g_set_farm_mode(x10g_base, 1)
            elif self.run_params['10g_farm_mode'] == 3:      
                self.x10g_net_lut_setup_from_list(x10g_base, self.x10g_0, self, mac_ip_lut)  
                self.x10g_set_farm_mode(x10g_base, 1)                         
            else: 
                print "Not in Farm Mode."              
                self.x10g_set_farm_mode(x10g_base, 0)

            if self.run_params['debug_level'] > 3:                
                print "Dump of Farm Mode LUT for xaui for Link %d" % self.x10g_0['link_nr']
                self.dump_regs_hex(x10g_base+0x10000, 16) 
                self.dump_regs_hex(x10g_base+0x100f0, 16)                               
                self.dump_regs_hex(x10g_base+0x10100, 16)
                self.dump_regs_hex(x10g_base+0x101f0, 16)  
                self.dump_regs_hex(x10g_base+0x10200, 16)
                self.dump_regs_hex(x10g_base+0x103f0, 16)
                    
            if self.run_params['debug_level'] > 1:
                print "Dump of regs for xaui for Link %d" % self.x10g_0['link_nr']
                self.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % self.x10g_0['link_nr']
                self.dump_regs_hex(data_gen_base, 16)
  
#            if (self.run_params['run_type'] == 0) or (self.run_params['run_type'] == 3):   # data via ppc
#                self.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 
#            else:
#                self.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut 

        
#            if self.x10g_0['data_gen'] == 2:   # data source is ppc
            if (self.run_params['run_type'] == "asic_data_via_ppc") or (self.run_params['run_type'] == "ppc_data_direct"):  # data with PPC ll header
                self.setup_ppc_bram(ppc_bram_base, self.x10g_0['frame_len']) 
                self.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 

                # reset ppc after bram has been set up... moved reset to top level
#                self.reset_ppc()
                 
            else:                       # data source is data gen               
                self.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut   
             
        return 0

    def reset_ppc(self):
        """ reset the ppc
             """                        
        #--------------------------------------------------------------------
        # Resetting the PPC start the DMA test
        # need to get the timing right or add handshaking
                
        # Resets dma engines
        self.toggle_bits(self.fem_ctrl_0+9, 0)
        print "Reset the PPC.."
        
        theDelay = self.run_params['ppc_reset_delay_secs']

        print "Waiting %s seconds.." % theDelay
        time.sleep(theDelay)
        print "Finished waiting %s seconds!" % theDelay
                     
        return 0
#
##-------------------------------------------------------------------------------------    
    def config_data_gen(self):
        """ configure data generator
             """                        
        data_gen_base = self.data_gen_0
                
        # final param to enable data gen headers for farm mode
        self.setup_ll_frm_gen(data_gen_base, self.x10g_0['frame_len']/8, self.x10g_0['data_format'], self.x10g_0['num_frames']-1, 1)
        
        self.override_header_ll_frm_gen(data_gen_base, 0, 0)  # default is not to override index nr in header
                     
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_modules(self):
        """ configure asic modules
             """                        

        self.config_asic_slow()         
        self.config_asic_fast()         
        self.config_asic_datarx()         
             
        print "ENABLE asic Tristate output buffers"
        self.rdmaWrite(self.fem_ctrl_0+5, 0)
                             
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_slow(self):
        """ configure asic slow control parameters
             """                                        
#        slow_ctrl_data, no_of_bits = self.read_slow_ctrl_file( self.filePath + 'SlowControlDefault-1A.txt')
        slowCtrlConfig = SlowCtrlParams( self.slowCtrlPath + 'slow_control_config.xml', fromFile=True)
        slow_ctrl_data = slowCtrlConfig.encode()
        no_of_bits = 3911
  
        load_mode = self.run_params['asic_slow_load_mode']                
                                               
        # load in BRAM 
        self.fem_slow_ctrl_setup(self.slow_ctr_0, self.slow_ctr_1, slow_ctrl_data, no_of_bits, load_mode)

# To Do Fix readback
#        print "asic serial out readback is from bot sp3 i/o"
#        self.rdmaWrite(self.fem_ctrl_0+2, 1)
                     
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_fast(self):
        """ configure asic fast command module
             """                        
        if self.run_params['asic_data_type'] == "asic_pseudo_random":
#                    [fast_cmd_data, no_of_words, no_of_nops] = myLpdFemClient.read_fast_cmd_file_jc_new('/u/ckd27546/workspace/lpd/src/LpdFemTests/fast_random_gaps.txt',fast_cmd_reg_size)
            [fast_cmd_data, no_of_words, no_of_nops] = self.read_fast_cmd_file_jc_new( self.fastCtrlPath + 'fast_random_gaps.txt',fast_cmd_reg_size)
        else:
#            [fast_cmd_data, no_of_words, no_of_nops] = self.read_fast_cmd_file_jc_new( self.fastCtrlPath + 'fast_readout_4f_gaps.txt',fast_cmd_reg_size)
             
            # ''' XML implementation '''
            fileCmdSeq = LpdCommandSequenceParser('/u/ckd27546/workspace/lpd/src/LpdCommandSequence/fast_readout_replacement_commands.xml', fromFile=True)
            # fileCmdSeq = LpdCommandSequenceParser('../LpdCommandSequence/fast_readout_replacement_commands.xml', fromFile=True)
            fast_cmd_data = fileCmdSeq.encode()
            
            no_of_words = fileCmdSeq.getTotalNumberWords()
            no_of_nops = fileCmdSeq.getTotalNumberNops()
                        

        #set up the fast command block
        if self.run_params['asic_fast_dynamic'] == 1:   # new design with dynamic vetos
            self.fem_fast_bram_setup(self.fast_cmd_1, fast_cmd_data, no_of_words)
            self.fem_fast_cmd_setup_new(self.fast_cmd_0, no_of_words+no_of_nops)
        else:
            self.fem_fast_cmd_setup(self.fast_cmd_0, self.fast_cmd_1, fast_cmd_data, no_of_words, fast_ctrl_dynamic)            
                     
        return 0

#-------------------------------------------------------------------------------------    
    def config_asic_datarx(self):
        """ configure asic data rx module
             """                        
        # Asic Rx 128 bit channel enable masks
        
        # Use list instead of array
        mask_list = [0, 0, 0, 0]
        if self.run_params['asic_data_type'] == "asicrx_counting":    # enable all channels for dummy data from asic rx    
            mask_list[0] = 0xffffffff
            mask_list[1] = 0xffffffff
            mask_list[2] = 0xffffffff
            mask_list[3] = 0xffffffff
        else: # Enable only relevant channel for single ASIC test module
            if self.run_params['detector_type'] == "single_asic_module": # Enable 2 channel for single ASIC test module
                mask_list[0] = 0x00000001
            elif self.run_params['detector_type'] == "two_tile_module": #Enable 16 channels for 2-Tile
# new mapping ?
                # Mapping for super module that contains just one ASIC
                mask_list[0] = 0x0f000000   #0x0f0000f0
                mask_list[1] = 0x0f000000   #0x0f0000f0
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

        no_asic_cols = self.run_params['asic_nr_images'] + 1               
        no_asic_cols_per_frm = self.run_params['asic_nr_images_per_frame'] + 1                       
        print "---> no_asic_cols, no_asic_cols_per_frm: ", no_asic_cols, no_asic_cols_per_frm, " <-----"
             
        #set up the ASIC RX IP block
        self.fem_asic_rx_setup(self.asic_srx_0 , mask_list, no_asic_cols, no_asic_cols_per_frm)
        
        # data source - self test
        if self.run_params['asic_data_type'] == "asicrx_counting":            
            self.asicrx_self_test_counting_data_enable()
        else:
            self.asicrx_self_test_counting_data_disable()

        # asic rx gain override
        self.asicrx_override_gain(self.run_params['asicrx_gain_selection'])

        # asic rx invert adc data
        if self.run_params['asicrx_invert_data'] == 1:            
            self.asicrx_invert_data_enable()
        else:
            self.asicrx_invert_data_disable()
        
        if self.run_params['asic_data_type'] == "asic_pseudo_random":
            asic_rx_start_delay = asic_rx_start_pseudo_random
        else: 
            if self.run_params['detector_type'] == "single_asic_module":
                asic_rx_start_delay = asic_rx_start_single_asic
            else:
                asic_rx_start_delay = asic_rx_start_2tile 
            
            if self.run_params['asicrx_capture_asic_header_TEST_ONLY'] == 1:
                asic_rx_start_delay -= asic_rx_hdr_bits

        print "asic_rx_start_delay = %s " % asic_rx_start_delay          
        #print "asic_rx_start_delay = %d ". % asic_rx_start_delay

        if self.run_params['asicrx_start_from_fast_strobe'] == 0:
            self.rdmaWrite(self.fem_ctrl_0+4, asic_rx_start_delay)  # OLD using fixed offsets          
        else: 
            self.rdmaWrite(self.fem_ctrl_0+14, asic_rx_start_delay)   # NEW using strobe from fast command file         
                     
        return 0

    def send_trigger(self):
        """ send triggers
            """                        
        #--------------------------------------------------------------------
        # send triggers to data generators
        #--------------------------------------------------------------------
                                 
        if self.run_params['run_type'] == "ll_data_gen":            
            print "Trigger Data Gen"
            self.toggle_bits(self.fem_ctrl_0+0, 0) # trigger to local link frame gen 
        elif (self.run_params['run_type'] == "asic_data_via_ppc") or (self.run_params['run_type'] == "asic_data_direct"):             
            print "Trigger Asic"
#            print "------------------ > self.fem_ctrl_0 = ", self.fem_ctrl_0
            self.toggle_bits(self.fem_ctrl_0+0, 1)  # start asic seq  = reset, slow, fast & asic rx
        else:
            print "Trigger Asic"
            self.toggle_bits(self.fem_ctrl_0+0, 1)
                    
        return 0

    def dump_registers(self):
        """ dump registers
             """
        print "Dump of FEM Registers : TOP LEVEL CTRL" 
        self.dump_regs_hex(self.fem_ctrl_0, 18)        

        print "Dump of FEM Registers : PPC1 BRAM" 
        self.dump_regs_hex(self.bram_ppc1, 16) 
        
        print "Dump of FEM Registers : XAUI link 1" 
        self.dump_regs_hex(self.udp_10g_0, 16) 

        print "Dump of FEM Registers : DATA GEN on link 1" 
        self.dump_regs_hex(self.data_gen_0, 16) 

        print "Dump of FEM Registers : ASIC RX" 
        self.dump_regs_hex(self.asic_srx_0, 16) 

        print "Dump of FEM Registers : ASIC FAST CTRL" 
        self.dump_regs_hex(self.fast_cmd_0, 16) 

        print "Dump of FEM Registers : ASIC FAST BRAM" 
        self.dump_regs_hex(self.fast_cmd_1, 16) 

        print "Dump of FEM Registers : ASIC SLOW CTRL" 
        self.dump_regs_hex(self.slow_ctr_0, 16) 

        print "Dump of FEM Registers : ASIC SLOW BRAM" 
        self.dump_regs_hex(self.slow_ctr_1, 200) 
                    
        return 0

    def read_slow_ctrl_file(self, filename):
    
        slow_ctrl_file = open(filename, 'r')
        lines = slow_ctrl_file.readlines()
        slow_ctrl_file.close()    
        
        data = []
        for line in lines:
            ivals = [int(val) for val in split(strip(line))]
            data.append(ivals)
            
        i_max = len(data)
#        j_max = len(data[0])
        
        no_words = i_max / 32
        if i_max%32:
            no_words = no_words + 1
            
        slow_ctrl_data = [0L] * no_words
    
        j = 0
        k = 0
        nbits = 0
        data_word = 0L;
        data_mask = 1L;
        
        for i in range(i_max):
            if data[i][1] == 1:
                nbits = nbits + 1
                if data[i][2] == 1:
                    data_word = data_word | data_mask
                if j == 31:
                    slow_ctrl_data[k] = data_word
                    data_word = 0l
                    data_mask = 1L
                    k = k+1
                    j = 0
                else:
                    data_mask = data_mask << 1
                    j = j + 1
        
        slow_ctrl_data[k] = data_word
        no_of_bits = nbits
                
        return slow_ctrl_data, no_of_bits
    
    def fem_slow_ctrl_setup(self, base_addr_0, base_addr_1, slow_ctrl_data, no_of_bits, load_mode):
    
        #base_addr_0 = LpdFemClient.slow_ctr_0
        #base_addr_1 = LpdFemClient.slow_ctr_1
        
        #slow control set up function blank

        # asic slow control load mode
        self.rdmaWrite(base_addr_0+0, load_mode)
        
        max_block_length = 1024
        
        # load slow control pattern memory
        
        block_length = len(slow_ctrl_data)

        if block_length > max_block_length:
            block_length =  max_block_length

        dataTuple = tuple(slow_ctrl_data)   # Do Not construct tuple from list like in fem_fast_.. func
        
        print "Slow Ctrl RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
        
        # load control registers
        
        # set number of bits register
        max_no_of_bits = 32*1024
        if no_of_bits > max_no_of_bits:
            no_of_bits = max_no_of_bits
        
        
        no_of_bits = no_of_bits + 1    # fix added  jc
        
        control_reg_1 = base_addr_0 + 1
        
        print "slow ctrl - no of bits (+1) to reg"
        self.rdmaWrite(control_reg_1, no_of_bits)

    def read_fast_cmd_file_jc_new(self, filename, cmd_reg_size):
        # location:    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian
        # filename:    read_fast_cmd_file_jc.m
        # function:    read_fast_cmd_file()
        # Read fast control file (hex) into an array
        # also adds nops 
    
        # read in command code and nops
        fast_ctrl_file = open(filename, 'r')
        lines = fast_ctrl_file.readlines()
        fast_ctrl_file.close()
    
        data = []
        for line in lines:
            ivals = [val for val in split(strip(line))]
            ivals[0] = int(ivals[0], 16)    # Read hexadecimal
            ivals[1] = int(ivals[1])        # Read decimal (base 10)
            data.append(ivals)
            
        #print data[0][0], data[0][1], data[1][0], data[1][1], data[2][0], data[2][1], data[3][0], data[3][1], data[4][0], data[4][1]
        #print len(data), len(data[0])
        
        i_max = len(data)
        j_max = len(data)
    
        fast_cmd_data = [0L] * i_max
        fast_cmd_nops = [0L] * i_max 
    
        for i in range(i_max):
            fast_cmd_data[i] = data[i][0] 
            fast_cmd_nops[i] = data[i][1] 
    
        nops_total = 0
    
        # new bram format for 22 bit commands
        # nops(31:22) - syncbit(21) - x(20) - cmd(19:12) - padding 0's (11:0)
    
        for j in range(j_max):
    
            fast_cmd_data[j] = (fast_cmd_data[j] & 0x000fffff)
            # special sync_reset 20 bit command?
            if (fast_cmd_data[j] == 0x5a):
                fast_cmd_data[j] = 0x5a5a5                
                fast_cmd_data[j] = self.bitshift(fast_cmd_data[j], cmd_reg_size, 20)
            elif (fast_cmd_data[j] == 0xfffff):  # special tests
                fast_cmd_data[j]= self.bitshift(fast_cmd_data[j], cmd_reg_size, 20)
            else:
                fast_cmd_data[j]= self.bitshift(fast_cmd_data[j], cmd_reg_size, 10)
                fast_cmd_data[j]= (fast_cmd_data[j] | self.bitshift(1, cmd_reg_size, 1) )

            nops_total = nops_total + fast_cmd_nops[j]  
            fast_cmd_data[j]= (fast_cmd_data[j] | (fast_cmd_nops[j] << 22))  
    
        no_of_words = j_max
        no_of_nops = nops_total
    
        return fast_cmd_data, no_of_words, no_of_nops
    
    def bitshift(self, bitVal, arg1, arg2):    
        """ bit shift bitVal according to difference of arg1 - arg2
            (arg1 - arg2) > 0 = bit shift to left (Increase bitVal)
            (arg1 - arg2) < 0 = bit shift to right (Decrease bitVal) """
        if (arg1-arg2 > 0):
            bitVal = (bitVal << arg1-arg2)
        elif (arg1-arg2 < 0):
            bitVal = (bitVal >> arg2-arg1)
        else:
            pass   # If arg1 = arg2, do nothing (bit shift 0 steps)
        return bitVal


    def fem_fast_bram_setup(self, base_addr_1, fast_cmd_data, no_of_words):
        # File path:    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian\matlab\matlab
        # Filename:     fem_fast_bram_setup.m
        # Func name:    fem_fast_cmd_setup (!!! function name inside fem_fast_bram_setup.m !!!)
        # fem_asic_test.m calls function:    fem_fast_bram_setup(s, fast_cmd_1, fast_cmd_data, no_of_words);
        #                                    Line:258
        # base_addr_1 = LpdFemClient.fast_cmd_1
        #fast cmd set up function blank
        
        max_block_length = 1024
        
        # check length is not greater than FPGA Block RAM
        
        block_length = no_of_words
        
        if block_length > max_block_length:
            block_length =  max_block_length        
        
        # Build tuple of a list of data
        dataTuple = tuple([fast_cmd_data[i] for i in range(block_length)])
        # load fast control pattern memory
        print "Fast Cmd RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
        
        
    ##def fem_fast_cmd_setup(self, no_of_words):
    def fem_fast_cmd_setup_new(self, base_addr_0, no_of_words):
        # Location:    \\te9files\ESDGshr\SDG\drop\for_christian\lpd_matlab_for_christian\matlab\matlab
        # filename:    fem_fast_cmd_setup_new.m
        # func name:    fem_fast_cmd_setup(s, base_addr_0, no_of_words)
        
        #base_addr_0 = LpdFemClient.fast_cmd_0
        
        #fast cmd set up function blank
    
        max_block_length = 1024
    
        # check length is not greater than FPGA Block RAM
    
        block_length = no_of_words
    
        if block_length > max_block_length:
            block_length =  max_block_length
    
        # load control registers
        # reset mode  for old behaviour outputting bram , without vetos
    
        print "fast_command_reg_reset_offset"
        self.rdmaWrite(base_addr_0+6, 0)
        print "fast_command_reg_reset_nwords"  
        self.rdmaWrite(base_addr_0+7, no_of_words)
        
    def fem_fast_cmd_setup(self, base_addr_0, base_addr_1, fast_cmd_data, no_of_words):
    
        #base_addr_0 = LpdFemClient.fast_cmd_0
        #base_addr_1 = LpdFemClient.fast_cmd_1
            
        #fast cmd set up function blank
    
        max_block_length = 1024
    
        # check length is not greater than FPGA Block RAM

        block_length = no_of_words
    
        if block_length > max_block_length:
            block_length =  max_block_length
    
        # Build tuple of a list of data
        dataTuple = tuple([fast_cmd_data+i for i in range(block_length)])
        
        # load fast control pattern memory
        print "Fast Cmd RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
    
        # load control registers
        print "Fast cmd block length"
        self.rdmaWrite(base_addr_0+1, block_length-1)  # was block_length - 1 ? jc
        
    def fem_asic_rx_setup(self, base_addr, mask_array, no_asic_cols, no_cols_frm):
        
        #Set up the XFEL FEM ASIC RX IP Block
         
        #setup IP Address register locations
         
        mask_reg0 = (0x00000004 | base_addr)
        mask_reg1 = (0x00000005 | base_addr)
        mask_reg2 = (0x00000006 | base_addr)
        mask_reg3 = (0x00000007 | base_addr)
         
        #gain_override_reg         = (0x0000000 | base_addr)
        #data_source_reg           = (0x00000001 | base_addr)
        no_clk_cyc_dly_reg        = (0x00000002 | base_addr)
        no_asic_cols_cols_frm_reg = (0x00000003 | base_addr)
         
        # setup data values
        no_asic_cols = (no_asic_cols & 0x0000001FF)
        no_cols_frm  = (no_cols_frm & 0x0000001FF)
        no_cols_frm_shft  = (no_cols_frm << 16)
        no_asic_cols_cols_frm = (no_cols_frm_shft | no_asic_cols)

         
        # clkc cycle delay for sof-eof formula 512 * 36 * no cols?
        #no_clk_cyc_dly = 0x00011FDC)
         
        #no_clk_cyc_dly = 512 * 36 * no_asic_cols * no_cols_frm - 1 
         
        # this doesn't match formula in register doc ? jac
        # frame clock length = (no cols * 512 * 36) - 36
        # is this the nr of clocks for payload of each ll frame (or all frames) ?
        # assume headers and footer are not included.
         
        # also fixed bug as above was using bit shifted value of no_cols_frm
        no_clk_cyc_dly = (512 * 36 * no_cols_frm) - 36 
                  
        # set up clk cycle delay
        print "asic rx clk cycle delay"
        self.rdmaWrite(no_clk_cyc_dly_reg, no_clk_cyc_dly)
        
        # set up num asic cols & num cols per frame
        print "asic rx no_cols cols_frm"
        self.rdmaWrite(no_asic_cols_cols_frm_reg,no_asic_cols_cols_frm)
   
        # set up mask registers
        print "asic rx 0"
        self.rdmaWrite(mask_reg0,mask_array[0])
        print "asic rx 1"
        self.rdmaWrite(mask_reg1,mask_array[1])
        print "asic rx 2"
        self.rdmaWrite(mask_reg2,mask_array[2])
        print "asic rx 3"
        self.rdmaWrite(mask_reg3,mask_array[3])
        
        return 0 
        
    def asicrx_self_test_counting_data_enable(self):
        reg_addr = self.asic_srx_0+1
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | 0x00000001
        self.rdmaWrite(reg_addr, new_value)
        return 0

    def asicrx_self_test_counting_data_disable(self):
        reg_addr = self.asic_srx_0+1
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value & ~0x00000001
        self.rdmaWrite(reg_addr, new_value)
        return 0        

    def asicrx_invert_data_enable(self):
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | 0x00000100
        self.rdmaWrite(reg_addr, new_value)
        return 0

    def asicrx_invert_data_disable(self):
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value & ~0x00000100
        self.rdmaWrite(reg_addr, new_value)
        return 0        

    def asicrx_override_gain(self, gain_select):
        # added override to gain selection 
        # 
        #  bits
        #  0000  normal gain selection     0
        #  1000  force select x100         8
        #  1001  force select x10          9
        #  1011  force select x1          11
        #  1111  force error condition ?  15
 
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | (gain_select & 0x0000000f)
        self.rdmaWrite(reg_addr, new_value)
        
        return 0

    def start_10g_link(self):
        """ start a 10g link
        """

        if self.run_params['debug_level'] > 5:
            print "Start 10G link nr", self.x10g_0['link_nr']

        data_gen_base = self.data_gen_0
        ll_mon_base = self.llink_mon_0
        ppc_bram_base = self.bram_ppc1

      
        time.sleep(self.x10g_0['delay'])   # wait before trigger


        if self.run_params['run_type'] == "ll_data_gen": # ll data gen
          
            # check last cycle has completed                
            link_busy = self.status_ll_frm_mon(ll_mon_base) 
            gen_busy = self.status_ll_frm_gen(data_gen_base) 
            i = 0
#            print "\n" 
#            while link_busy == 1:
            while gen_busy == 1:
                i=i+1
#                link_busy = self.status_ll_frm_gen(data_gen_base)                
#                print "Data Gen on 10G link nr %2d has busy flag = %d" %(self.x10g_0['link_nr'], link_busy)
                print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(self.x10g_0['link_nr'],i),
                sys.stdout.flush() 
#                print "1 WARNING Data Gen on 10G link nr %2d is still BUSY" %self.x10g_0['link_nr']
                time.sleep(1)                    
                link_busy = self.status_ll_frm_mon(ll_mon_base) 
                gen_busy = self.status_ll_frm_gen(data_gen_base) 

        if self.run_params['10g_farm_mode'] == 3:
            i = 0
            for nic in self.x10g_0['nic_list']:
                # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
                # don't do this any earlier or won't trigger
                #self.soft_reset_ll_frm_gen(data_gen_base) 
        
                if self.x10g_0['data_gen'] == 1:
                    # check last transfer has completed                
                    link_busy = self.status_ll_frm_mon(ll_mon_base) 
                    gen_busy = self.status_ll_frm_gen(data_gen_base) 
                    t = 0
                    while gen_busy == 1:
                        t=t+1
                        print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' %(self.x10g_0['link_nr'],t),
                        sys.stdout.flush() 
                        time.sleep(1)                    
                        link_busy = self.status_ll_frm_mon(ll_mon_base) 
                        gen_busy = self.status_ll_frm_gen(data_gen_base) 
                      
                    # override the index nr in the data gen ll header output for selecting the 10g port nr in lut
                    index_nr = i
                    self.override_header_ll_frm_gen(data_gen_base, 1, index_nr)
                        
                    if self.run_params['debug_level'] > 5:
                        print "Trigger LL Data Gen"
                    
                    self.toggle_bits(self.fem_ctrl_0+0, 0)   
                    
#                elif self.x10g_0['data_gen'] == 2:
                elif self.run_params['run_type'] == "ppc_data_direct": # ppc dma ddr2 preprogrammed
                    
                    # check previous dma tx has completed
                    busy = self.prev_dma_tx(ppc_bram_base) 
                    t = 0;    
                    while busy == 1:
                        t=t+1
                        print 'Waiting to Trigger Next Cycle : 10G link nr %2d DMA is BUSY ; waiting %d secs\r' %(self.x10g_0['link_nr'],t),
                        sys.stdout.flush() 
                        time.sleep(1)                    
                        busy = self.prev_dma_tx(ppc_bram_base) 
        
                    if self.run_params['debug_level'] > 5:
                        print "Trigger DMA Tx"
                    self.start_dma_tx(ppc_bram_base, i)  # pass index to ppc to select tx descriptor
                    
                i = i + 1
                
        else:
            if self.x10g_0['data_gen'] == 1:
                # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
                # don't do this any earlier or won't trigger
                self.soft_reset_ll_frm_gen(data_gen_base)  
              
                print "Trigger LL Data Gen"
                self.toggle_bits(self.fem_ctrl_0+0, 0)   
         
        return 0

            
    def final_dma_tx(self, base_addr):
        """ flag last dma tx """
  
        self.rdmaWrite(base_addr+10, 0x5678) 
            
        return 0 

    '''
        --------------------------------------------------------
        --------------------------------------------------------
    '''
    
    def configure(self):
        '''
            Placeholder for the future configure() function
        '''
#        femHost = '192.168.2.2' # standalone fem
#        femPort = 6969


        global asic_rx_start_pseudo_random    
        global asic_rx_start_2tile  
        global asic_rx_start_single_asic 
        global asic_rx_hdr_bits   # subtract from values above to capture asic headers

        global fast_cmd_reg_size
   
        global pp

        # new offset with fast command strobe
        asic_rx_start_2tile = 808 # 809   # timed in 26/11/12
        
        asic_rx_hdr_bits = 12   # subtract from values above to capture asic serial headers ($AAA)

        # Asic fast cmds 20 or 22 bits format   (only 22 bit commands work at present)
        fast_cmd_reg_size = 22

        print "=======================================================================" 
  
        pp = pprint.PrettyPrinter(indent=4)
  
        if self.run_params['debug_level'] > 0:
                pp.pprint(self.run_params)


        self.init_ppc_bram(self.bram_ppc1, 0xBEEFFACE)

        self.toggle_bits(self.fem_ctrl_0+9, 8)  # async reset to v5 top level

        self.clear_ll_monitor()

        # set up clocks and connections between modules
        self.config_top_level()         
        
        # set up the 10g link params
        self.config_10g_link()         

        if (self.run_params['run_type'] == "asic_data_via_ppc") or (self.run_params['run_type'] == "ppc_data_direct"):  # runs with ppc
            self.reset_ppc()         

        # set up data gen - not necessary for actual data but leave alone, "just in case"
        self.config_data_gen()         

        # set up asic blocks
        if (self.run_params['run_type'] == "asic_data_via_ppc") or (self.run_params['run_type'] == "asic_data_direct"):  # data from asic
            self.config_asic_modules()
            
            # send_trigger() moved to run() 
            #self.send_trigger(self.run_params, self.myLpdFemClient) 

        else: # data from datagen or ppc ddr2 
                    
#            print "Data Generator disabled for now, exiting.."
            num_cycles = self.run_params['num_cycles']
            print "Starting Run of %d cycles" % self.run_params['num_cycles']
            for i in range (1, num_cycles+1):
#                print "Starting Run Cycle Nr %d" % i
                self.start_10g_link()  
#                self.send_trigger(run_params, myLpdFemClient) 
            
            if self.x10g_0['data_gen'] == 2:
                self.final_dma_tx(self.bram_ppc1)  

        

    def run(self):
        '''
            Placeholder for the future run() function
        '''
        
        print "Executing run().."
        
            
        self.send_trigger()

        # Read out all registers (Required, otherwise .read_ll..() will execute too soon!) 
        self.dump_registers()
        self.read_ll_monitor()


    def sensorATempGet(self):
        '''
            Get temperature from sensor A
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSA_TEMP_CHAN)

    def sensorBTempGet(self):
        '''
            Get temperature from sensor B
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSB_TEMP_CHAN)
    
    def sensorCTempGet(self):
        '''
            Get temperature from Sensor C
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSC_TEMP_CHAN)
    
    def sensorDTempGet(self):
        '''
            Get temperature from Sensor D
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSD_TEMP_CHAN)
    
    
    def sensorETempGet(self):
        '''
            Get temperature from Sensor E
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSE_TEMP_CHAN)

    
    def sensorFTempGet(self):
        '''
            Get temperature from Sensor F
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSF_TEMP_CHAN)

    
    def sensorGTempGet(self):
        '''
            Get temperature from Sensor G
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSG_TEMP_CHAN)

    
    def sensorHTempGet(self):
        '''
            Get temperature from Sensor H
        '''
        
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSH_TEMP_CHAN)

    def powerCardTempGet(self):
        '''
            Get temperature from power card
        '''
        return self.sensorTemperatureRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.PSU_TEMP_CHAN)
    

    def asicPowerEnableGet(self):
        '''
            Get the status of 'ASIC LV Power Enable'
        
            Returns True if OFF; False if ON
        '''
        
        return self.pcf7485ReadOneBit(LpdFemClient.LV_CTRL_BIT)
    
    def asicPowerEnableSet(self, aEnable):
        '''
            Set 'ASIC LV Power Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.pcf7485WriteOneBit(LpdFemClient.LV_CTRL_BIT, value )

    def sensorBiasEnableGet(self):
        '''
            Get the status of 'Sensor HV Bias Enable'
        
            Returns True if OFF; False if ON
        '''
        
        return self.pcf7485ReadOneBit(LpdFemClient.HV_CTRL_BIT)
    
    def sensorBiasEnableSet(self, aEnable):
        '''
            Set 'Sensor LV Bias Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.pcf7485WriteOneBit(LpdFemClient.HV_CTRL_BIT, value )
        
        
    def powerCardFemStatusGet(self):
        '''
            Get power card Fem status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.FEM_STATUS_BIT)) != 0]
    
    def powerCardExtStatusGet(self):
        '''
            Get power card External status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.EXT_TRIP_BIT)) != 0]
    
    def powerCardFaultGet(self):
        '''
            Get power card Fault status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.FAULT_FLAG_BIT)) != 0]
    
    def powerCardOverCurrentGet(self):
        '''
            Get power card Over Current status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.OVERCURRENT_BIT)) != 0]
    
    def powerCardOverTempGet(self):
        '''
            Get power card Over Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.HIGH_TEMP_BIT)) != 0]
    
    def powerCardUnderTempGet(self):
        '''
            Get power card Under Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.LOW_TEMP_BIT)) != 0]
    
    def sensorBiasGet(self):
        '''
            Get Sensor HV Bias Voltage [V]
        '''
        return self.ad5321Read()
    
    def sensorBiasSet(self, aValue):
        '''
            Set Sensor HV Bias Voltage [V]
        '''
        #TODO: Need to to proper scaling aValue -> ADC count
        self.ad55321Write( int(aValue) )
    
    def femVoltageGet(self):
        '''
            Get Fem 5V Supply Voltage [V]
        '''
        return self.sensorSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V5_VOLTS_CHAN)
        
    def femCurrentGet(self):
        '''
            Get Fem 5V Supply Current [A]
        '''
        return self.sensorAmpereRead( LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V5_AMPS_CHAN)

    def digitalVoltageGet(self):
        '''
            Get ASIC 1.2 Digital Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V12_VOLTS_CHAN)

    def digitalCurrentGet(self):
        '''
            Get ASIC 1.2V Digital Supply Current [myA]
        '''
        return self.sensorSevenHundredMilliAmpsScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V12_AMPS_CHAN)

    def sensorAVoltageGet(self):
        '''
            Get Sensor A 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25A_VOLTS_CHAN)

    def sensorACurrentGet(self):
        '''
            Get Sensor A 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25A_AMPS_CHAN)

    def sensorBVoltageGet(self):
        '''
            Get Sensor B 2.5V Supply Voltage [V] 
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25B_VOLTS_CHAN)

    def sensorBCurrentGet(self):
        '''
            Get Sensor B 2.5V Supply Current [A]',
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25B_AMPS_CHAN)

    def sensorCVoltageGet(self):
        '''
            Get Sensor C 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25C_VOLTS_CHAN)

    def sensorCCurrentGet(self):
        '''
            Get Sensor C 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25C_AMPS_CHAN)

    def sensorDVoltageGet(self):
        '''
            Get Sensor D 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25D_VOLTS_CHAN)

    def sensorDCurrentGet(self):
        '''
            Get Sensor D 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25D_AMPS_CHAN)

    def sensorEVoltageGet(self):
        '''
            Get Sensor E 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25E_VOLTS_CHAN)

    def sensorECurrentGet(self):
        '''
            Get Sensor E 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25E_AMPS_CHAN)

    def sensorFVoltageGet(self):
        '''
            Get Sensor F 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25F_VOLTS_CHAN)

    def sensorFCurrentGet(self):
        '''
            Get Sensor F 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25F_AMPS_CHAN)

    def sensorGVoltageGet(self):
        '''
            Get Sensor G 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25G_VOLTS_CHAN)

    def sensorGCurrentGet(self):
        '''
            Get Sensor G 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25G_AMPS_CHAN)

    def sensorHVoltageGet(self):
        '''
            Get Sensor H 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25H_VOLTS_CHAN)

    def sensorHCurrentGet(self):
        '''
            Get Sensor H 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25H_AMPS_CHAN)
    
    def sensorBiasVoltageGet(self):
        '''
            Get Sensor bias voltage readback [V]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.HV_VOLTS_CHAN)
    
    def sensorBiasCurrentGet(self): 
        '''
            Get Sensor bias current readback [uA]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.HV_AMPS_CHAN)
    
    def tenGig0SourceMacGet(self):
        '''
            Get tenGig0SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
#        return self.tenGig0SourceMacDummy
        return self.tenGig0['SourceMacDummy']
    
    def tenGig0SourceMacSet(self, aValue):
        '''
            Set tenGig0SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
#        self.tenGig0SourceMacDummy = aValue
        self.tenGig0['SourceMacDummy'] = aValue
    
    def tenGig0SourceIpGet(self):
        '''
            Get tenGig0SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
#        return self.tenGig0SourceIpDummy
        return self.tenGig0['SourceIpDummy']
    
    def tenGig0SourceIpSet(self, aValue):
        '''
            Set tenGig0SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
#        self.tenGig0SourceIpDummy = aValue
        self.tenGig0['SourceIpDummy'] = aValue

    def tenGig0SourcePortGet(self):
        '''
            Get tenGig0SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
#        return self.tenGig0SourcePortDummy
        return self.tenGig0['SourcePortDummy']
    
    def tenGig0SourcePortSet(self, aValue):
        '''
            Set tenGig0SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
#        self.tenGig0SourcePortDummy = aValue
        self.tenGig0['SourcePortDummy'] = aValue
        
    def tenGig0DestMacGet(self):
        '''
            Get tenGig0DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0['DestMacDummy']
#        return self.tenGig0DestMacDummy

    def tenGig0DestMacSet(self, aValue):
        '''
            Set tenGig0DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0['DestMacDummy'] = aValue
#        self.tenGig0DestMacDummy = aValue

    def tenGig0DestIpGet(self):
        '''
            Get tenGig0DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0['DestIpDummy']
#        return self.tenGig0DestIpDummy

    def tenGig0DestIpSet(self, aValue):
        '''
            Set tenGig0DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0['DestIpDummy'] = aValue
#        self.tenGig0DestIpDummy = aValue

    def tenGig0DestPortGet(self):
        '''
            Get tenGig0DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0['DestPortDummy']
#        return self.tenGig0DestPortDummy

    def tenGig0DestPortSet(self, aValue):
        '''
            Set tenGig0DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0['DestPortDummy'] = aValue
#        self.tenGig0DestPortDummy = aValue

    def tenGig1SourceMacGet(self):
        '''
            Get tenGig1SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1SourceMacDummy

    def tenGig1SourceMacSet(self, aValue):
        '''
            Set tenGig1SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1SourceMacDummy = aValue

    def tenGig1SourceIpGet(self):
        '''
            Get tenGig1SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1SourceIpDummy

    def tenGig1SourceIpSet(self, aValue):
        '''
            Set tenGig1SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1SourceIpDummy = aValue

    def tenGig1SourcePortGet(self):
        '''
            Get tenGig1SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1SourcePortDummy

    def tenGig1SourcePortSet(self, aValue):
        '''
            Set tenGig1SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1SourcePortDummy = aValue

    def tenGig1DestMacGet(self):
        '''
            Get tenGig1DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1DestMacDummy

    def tenGig1DestMacSet(self, aValue):
        '''
            Set tenGig1DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1DestMacDummy = aValue

    def tenGig1DestIpGet(self):
        '''
            Get tenGig1DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1DestIpDummy

    def tenGig1DestIpSet(self, aValue):
        '''
            Set tenGig1DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1DestIpDummy = aValue

    def tenGig1DestPortGet(self):
        '''
            Get tenGig1DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1DestPortDummy

    def tenGig1DestPortSet(self, aValue):
        '''
            Set tenGig1DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1DestPortDummy = aValue

    def tenGigInterframeGapGet(self):
        '''
            Get tenGigInterframeGap
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGigInterframeGapDummy

    def tenGigInterframeGapSet(self, aValue):
        '''
            Set tenGigInterframeGap
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGigInterframeGapDummy = aValue

    def tenGigUdpPacketLenGet(self):
        '''
            Get tenGigUdpPacketLen
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGigUdpPacketLenDummy

    def tenGigUdpPacketLenSet(self, aValue):
        '''
            Set tenGigUdpPacketLen
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGigUdpPacketLenDummy = aValue

    def femSendPpcResetGet(self):
        '''
            Get femSendPpcReset
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femSendPpcResetDummy

    def femSendPpcResetSet(self, aValue):
        '''
            Set femSendPpcReset
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femSendPpcResetDummy = aValue

    def femFastCtrlDynamicGet(self):
        '''
            Get femFastCtrlDynamic
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femFastCtrlDynamicDummy

    def femFastCtrlDynamicSet(self, aValue):
        '''
            Set femFastCtrlDynamic
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femFastCtrlDynamicDummy = aValue

    def femSetupSlowCtrlBramGet(self):
        '''
            Get femSetupSlowCtrlBram
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femSetupSlowCtrlBramDummy

    def femSetupSlowCtrlBramSet(self, aValue):
        '''
            Set femSetupSlowCtrlBram
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femSetupSlowCtrlBramDummy = aValue

    def femEnableTenGigGet(self):
        '''
            Get femEnableTenGig
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femEnableTenGigDummy

    def femEnableTenGigSet(self, aValue):
        '''
            Set femEnableTenGig
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femEnableTenGigDummy = aValue

    def femDataSourceGet(self):
        '''
            Get femDataSource
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femDataSourceDummy

    def femDataSourceSet(self, aValue):
        '''
            Set femDataSource
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femDataSourceDummy = aValue

    def femAsicCountingDataGet(self):
        '''
            Get femAsicCountingData
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicCountingDataDummy

    def femAsicCountingDataSet(self, aValue):
        '''
            Set femAsicCountingData
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicCountingDataDummy = aValue

    def femAsicModuleTypeGet(self):
        '''
            Get femAsicModuleType
        '''
        #TODO: Variable type changed from integer to string ?
        return self.run_params['detector_type']
#        return self.femAsicModuleTypeDummy

    def femAsicModuleTypeSet(self, aValue):
        '''
            Set femAsicModuleType
        '''
        #TODO: Variable type changed from integer to string ?
        self.run_params['detector_type'] = aValue
#        self.femAsicModuleTypeDummy = aValue

    def femAsicRxStartDelayGet(self):
        '''
            Get femAsicRxStartDelay
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicRxStartDelayDummy

    def femAsicRxStartDelaySet(self, aValue):
        '''
            Set femAsicRxStartDelay
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicRxStartDelayDummy = aValue

    def femNumLocalLinkFramesGet(self):
        '''
            Get femNumLocalLinkFrames
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femNumLocalLinkFramesDummy

    def femNumLocalLinkFramesSet(self, aValue):
        '''
            Set femNumLocalLinkFrames
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femNumLocalLinkFramesDummy = aValue

    def femAsicFastCmdRegSizeGet(self):
        '''
            Get femAsicFastCmdRegSize
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicFastCmdRegSizeDummy

    def femAsicFastCmdRegSizeSet(self, aValue):
        '''
            Set femAsicFastCmdRegSize
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicFastCmdRegSizeDummy = aValue

    def femAsicEnableMaskGet(self):
        '''
            Get femAsicEnableMask
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicEnableMaskDummy

    def femAsicEnableMaskSet(self, aValue):
        '''
            Set femAsicEnableMask
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicEnableMaskDummy = aValue

    def femAsicColumnsGet(self):
        '''
            Get femAsicColumns
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicColumnsDummy

    def femAsicColumnsSet(self, aValue):
        '''
            Set femAsicColumns
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicColumnsDummy = aValue

    def femAsicColumnsPerFrameGet(self):
        '''
            Get femAsicColumnsPerFrame
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicColumnsPerFrameDummy

    def femAsicColumnsPerFrameSet(self, aValue):
        '''
            Set femAsicColumnsPerFrame
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicColumnsPerFrameDummy = aValue

    def femAsicGainOverrideGet(self):
        '''
            Get femAsicGainOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicGainOverrideDummy

    def femAsicGainOverrideSet(self, aValue):
        '''
            Set femAsicGainOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicGainOverrideDummy = aValue

    def femAsicSlowControlParamsGet(self):
        '''
            Get femAsicSlowControlParams
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicSlowControlParamsDummy

    def femAsicSlowControlParamsSet(self, aValue):
        '''
            Set femAsicSlowControlParams
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicSlowControlParamsDummy = aValue

    def femAsicFastCmdSequenceGet(self):
        '''
            Get femAsicFastCmdSequence
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicFastCmdSequenceDummy

    def femAsicFastCmdSequenceSet(self, aValue):
        '''
            Set femAsicFastCmdSequence
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicFastCmdSequenceDummy = aValue

    def femAsicPixelFeedbackOverrideGet(self):
        '''
            Get femAsicPixelFeedbackOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicPixelFeedbackOverrideDummy
                    
    def femAsicPixelFeedbackOverrideSet(self, aValue):
        '''
            Set femAsicPixelFeedbackOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicPixelFeedbackOverrideDummy = aValue
            
    def femAsicPixelSelfTestOverrideGet(self):
        '''
            Get femAsicPixelSelfTestOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicPixelSelfTestOverrideDummy
                    
    def femAsicPixelSelfTestOverrideSet(self, aValue):
        '''
            Set femAsicPixelSelfTestOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicPixelSelfTestOverrideDummy = aValue

    def femReadoutOperatingModeGet(self):
        '''
            Get femReadoutOperatingMode
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femReadoutOperatingModeDummy

    def femReadoutOperatingModeSet(self, aValue):
        '''
            Set femReadoutOperatingMode
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femReadoutOperatingModeDummy = aValue


    """ -=-=-=-=-=- Helper Functions -=-=-=-=-=- """

    
    def sensorAmpereRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in  address 'device',
                and converts adc counts into 10 amp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 10.0
        tempVal = (adcVal * scale / 4095.0)
        
        return tempVal

    def sensorSixVoltScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 6 V scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 6.0
        return (adcVal * scale / 4095.0)

    def sensorThreeVoltScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 3 V scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 3.0
        return (adcVal * scale / 4095.0)

    def sensorSevenHundredMilliAmpsScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor  voltage at 'channel' in address 'address',
                and converts adc counts into 700 milliamp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 700.0
        return (adcVal * scale / 4095.0)

    def sensorSixHundredMilliAmpsScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 600 milliamp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 600.0
        return (adcVal * scale / 4095.0)

    def debugDisplay(self, var):
        '''
            Debug function to display decimal and hexadecimal value of 'var'.
        '''
        return var, "0x%X" % var,
        
    def sensorTemperatureRead(self, device, channel):
        '''
            Helper function: Reads sensor temperature at 'channel' in  address 'device',
                and converts adc counts into six volts scale.
            Note: This function will become different from
                    sensorThreeVoltScaleRead(device, channel)
            because this function will later convert into degrees centigrade
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 3.0
        voltage = (adcVal * scale / 4095.0)
        # Calculate resistance from voltage
        resistance = self.calculateResistance(voltage)
        # Calculate temperature from resistance
        temperature = self.calculateTemperature(LpdFemClient.Beta, resistance)
        # Round temperature to 2 decimal points
        return round(temperature, 2)

    def ad7998Read(self, device, channel):
        '''
            Read two bytes from 'channel' in ad7998 at address 'device'
        '''

        # Construct i2c address and ADC channel to be read
        addr = LpdFemClient.i2cPowerCardBus + device
        adcChannel = 0x80 + ((channel & 7) << 4)

        # Write operation, select ADC channel
        ack = self.i2cWrite(addr, adcChannel)
        
        # Read operation, read ADC value
        response = self.i2cRead(addr, 2)
        
        # Extract the received two bytes and return one integer
        value = (int((response[0] & 15) << 8) + int(response[1]))
#        print "[%4i" % value, "]",
        return value

    def ad5321Read(self):
        ''' 
            Read 2 bytes from ad5321 device 
        '''
        
        addr = LpdFemClient.i2cPowerCardBus + 0x0C
        response = -1
        
        response = self.i2cRead(addr, 2)
        high = (response[0] & 15) << 8
        low = response[1]
        return high + low

    def ad55321Write(self, aValue):
        '''
            Write 'aAValue' (2 bytes) to ad5321 device
        '''
    
        response = -1
        # Construct address and payload (as a tuple)
        addr = LpdFemClient.i2cPowerCardBus + 0x0C
        payload = ((aValue & 0xF00) >> 8), (aValue & 0xFF)

        # Write new ADC value to device
        ack = self.i2cWrite(addr, payload)
        
        # Verify write operation
        response = self.ad5321Read()
        return response
    
    def pcf7485ReadOneBit(self, id):
        ''' 
            Read one byte from PCF7485 device and determine if set.
        
            Note: bit 1 = 0, 2 = 1,  3 = 2, 4 = 4, 
                      5 = 8, 6 = 16, 7 = 32 8 = 64
            Therefore, id must be one of the following: [0, 1, 2, 4, 8, 16, 32, 64]
        '''
        
        addr = LpdFemClient.i2cPowerCardBus + 0x38 
        
        response = self.i2cRead(addr, 1)
        
#        print "response = ", response, " type(response) = ", type(response)
        value = response[0]
        return (value & (1 << id)) != 0
        
    def pcf7485ReadAllBits(self):
        ''' 
            Read and return one byte from PCF7485 device
            
            If a bit is set that represents: 
                bit 0-1:    Disabled (HV, LV)
                bit 2-7:    A fault  (Fem Status, Ext trip, fault, etc)
                e.g.    
                    131:    Hv (1) & Lv (2) disabled, low temperature (128) alert

                Beware      bit 0 = 1, bit 1 = 2, bit 2 = 4, etc !!
                therefore   131 = 128 + 2 + 1 (bits: 7, 1, 0)
        '''
        addr = LpdFemClient.i2cPowerCardBus + 0x38
        response = self.i2cRead(addr, 1)
#        print "pcf7485ReadAllBits() response = ", self.debugDisplay(response[0])
        return response[0]

    def pcf7485WriteOneBit(self, id, value):
        ''' 
            Change bit 'id' to 'value' in PCF7485 device
        '''        
        # Read PCF7485's current value
        bit_register = self.pcf7485ReadAllBits()
        # Change bit 'id' to 'value'
        bit_register = (bit_register & ~(1 << id)) | (value << id) | 0xFC

        addr = LpdFemClient.i2cPowerCardBus + 0x38
        response = self.i2cWrite(addr, bit_register)
        
        #TODO: Check ack (i.e.'response') to verify successful write
    
    def adcToTemp(self, adcValue):
        '''
            Convert ADC value into temperature - Redundant?
        '''
        #TODO:Change scale from voltage to degrees Celsius
        scale = 3
        try:
            tempVal = float(adcValue * scale / 4095.0)
        except Exception as e:
            tempVal = -1.0
            print "adcToTemp() Exception: ", e

        return tempVal

    def calculateTemperature(self, Beta, resistanceOne):
        ''' e.g. calculateTemperature(3630, 26000) = 3.304 degrees Celsius '''
        # Define constants since resistance and temperature is already known for one point
        resistanceZero = 10000
        tempZero = 25.0

        invertedTemperature = (1.0 / (273.1500 + tempZero)) + ( (1.0 / Beta) * log(float(resistanceOne) / float(resistanceZero)) )

        # Invert the value to obtain temperature (in Kelvin) and subtract 273.15 to obtain Celsius
        return (1 / invertedTemperature) - 273.15

    def calculateResistance(self, aVoltage):
        '''
            Calculates the resistance for a given voltage (Utilised by the temperature sensors, on board as well as each ASIC module)
        '''
        # Define the supply voltage and the size of resistor inside potential divider
        vCC = 5
        resistance = 15000
        # Calculate resistance of the thermistor
        resistanceTherm = ((resistance * aVoltage) / (vCC-aVoltage))
        return resistanceTherm

    def configureGet(self):
        '''
            TODO: REMOVE OR RATIONALISE THIS FUNCTION AFTER FINISHED TESTING
        '''
        self.configure()

    def runGet(self):
        '''
            TODO: REMOVE OR RATIONALISE THIS FUNCTION AFTER FINISHED TESTING
        '''
        self.run()
