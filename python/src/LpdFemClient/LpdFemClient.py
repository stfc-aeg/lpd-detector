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
# log required when calculating temperature
from math import log, ceil
import pprint, time, sys

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction

# Import library for parsing XML fast command files
from LpdAsicCommandSequence import LpdAsicCommandSequence
from LpdAsicControl import LpdAsicControl


class LpdFemClient(FemClient):
    '''
    
    '''

    # ADC channel numbers
    HV_VOLTS_CHAN   =  0
    V5_VOLTS_CHAN   =  1
    V12_VOLTS_CHAN  =  2
    HV_AMPS_CHAN    =  3
    V5_AMPS_CHAN    =  4
    V12_AMPS_CHAN   =  5
    PSU_TEMP_CHAN   =  6
    V25A_VOLTS_CHAN =  8
    V25B_VOLTS_CHAN =  9
    V25C_VOLTS_CHAN = 10
    V25D_VOLTS_CHAN = 11
    V25E_VOLTS_CHAN = 12
    V25F_VOLTS_CHAN = 13
    V25G_VOLTS_CHAN = 14
    V25H_VOLTS_CHAN = 15
    V25A_AMPS_CHAN  = 16
    V25B_AMPS_CHAN  = 17
    V25C_AMPS_CHAN  = 18
    V25D_AMPS_CHAN  = 19
    V25E_AMPS_CHAN  = 20
    V25F_AMPS_CHAN  = 21
    V25G_AMPS_CHAN  = 22
    V25H_AMPS_CHAN  = 23
    SENSA_TEMP_CHAN = 24
    SENSB_TEMP_CHAN = 25
    SENSC_TEMP_CHAN = 26
    SENSD_TEMP_CHAN = 27
    SENSE_TEMP_CHAN = 28
    SENSF_TEMP_CHAN = 29
    SENSG_TEMP_CHAN = 30
    SENSH_TEMP_CHAN = 31
    
    # Bit numbers for control bits
    HV_CTRL_BIT     =  0
    LV_CTRL_BIT     =  1

    # Values for control bits
    OFF             =  1
    ON              =  0

    # Bit numbers for status bits
    FEM_STATUS_BIT  =  2
    EXT_TRIP_BIT    =  3
    FAULT_FLAG_BIT  =  4
    OVERCURRENT_BIT =  5
    HIGH_TEMP_BIT   =  6
    LOW_TEMP_BIT    =  7
    
    # Values for status bits
    TRIPPED         =  1
    FAULT           =  1
    NORMAL          =  0
    
    # Enumerate fault flag as either cleared (0) or tripped (1) 
    flag_message    = ["No", "Yes"]
    
    # i2c device addresses
    AD7998ADDRESS   = [0x22, 0x21, 0x24, 0x23]
    
    # Beta is utilised as an argument for calling the calculateTemperature() 
    #    but it's effectively fixed by the hardware design
    Beta            = 3474

    # with new addressing using top 4 bits for fpga selection
    #    """ 32 way splitter """
    udp_10g_0       = 0x00000000    #  0
    udp_10g_1       = 0x00800000    #  1
    data_gen_0      = 0x01000000    #  2
    data_chk_0      = 0x01800000    #  3
    data_gen_1      = 0x02000000    #  4
    data_chk_1      = 0x02800000    #  5
    fem_ctrl_0      = 0x03000000    #  6
    llink_mon_0     = 0x03800000    #  7
    data_mon_1      = 0x04000000    #  8
    slow_ctr_2      = 0x04800000    #  9
    fast_cmd_0      = 0x05000000    # 10
    fast_cmd_1      = 0x05800000    # 11
    asic_srx_0      = 0x06000000    # 12
    llink_mon_asicrx= 0x06800000    # 13
    slow_ctr_0      = 0x07000000    # 14
    slow_ctr_1      = 0x07800000    # 15
    dma_gen_0       = 0x08000000    # 16
    dma_chk_0       = 0x08800000    # 17
    dma_gen_1       = 0x09000000    # 18
    dma_chk_1       = 0x09800000    # 19
    dma_gen_2       = 0x0a000000    # 20
    dma_chk_2       = 0x0a800000    # 21
    dma_gen_3       = 0x0b000000    # 22
    dma_chk_3       = 0x0b800000    # 23
    bram_ppc1       = 0x0c000000    # 24
    rsvd_25         = 0x0c800000    # 25
    rsvd_26         = 0x0d000000    # 26
    rsvd_27         = 0x0d800000    # 27
    rsvd_28         = 0x0e000000    # 28
    rsvd_29         = 0x0e800000    # 29
    rsvd_30         = 0x0f000000    # 30
    rsvd_31         = 0x0f800000    # 31
    
    ########## Enumerated values for API variables ##########

    ASIC_MODULE_TYPE_SUPERMODULE    = 0     # (0) Supermodule
    ASIC_MODULE_TYPE_SINGLE_ASIC    = 1     # (1) Single ASIC test module
    ASIC_MODULE_TYPE_TWO_TILE       = 2     # (2) 2-Tile module
    ASIC_MODULE_TYPE_STANDALONE     = 3     # (3) FEM Standalone

    RUN_TYPE_ASIC_DATA_VIA_PPC      = 0     # (0) ASIC data (via PPC) [Standard Operation]
    RUN_TYPE_ASIC_DATA_DIRECT       = 1     # (1) ASIC data direct from Rx block
    RUN_TYPE_LL_DATA_GEN            = 2     # (2) LL Data Gen  (simulated data)
    RUN_TYPE_PPC_DATA_DIRECT        = 3     # (3) preprogrammed data DDR2 (simulated data)
    
    ASIC_DATA_TYPE_ASIC_SENSOR      = 0     # Asic sensor data [Standard Operation Real Data]
    ASIC_DATA_TYPE_RX_COUNTING      = 1     # Asic Rx Block internally generated counting data (simulated data)
    ASIC_DATA_TYPE_PSEUDO_RANDOM    = 2     # Asic Pseudo random data (test data from asic)
    
    def __init__(self, hostAddr=None, timeout=None):
        '''
            Constructor for LpdFemClient class
        '''

        # Call superclass initialising function
        super(LpdFemClient, self).__init__(hostAddr, timeout)

        # Fem has three internal i2c buses
        self.femI2cBus = 0x300                          # 0x200 = RHS Power Card,  0x300 = LHS Power Card

        ######## API variables extracted from jac's functions ########
        self.femAsicEnableMask              = [0, 0, 0, 0]
        self.femAsicSlowControlParams       = ""
        self.femAsicFastCmdSequence         = ""

        ######## API parameters: Functionality to be developed ########
        self.femAsicPixelFeedbackOverride   = 0  #TODO: To be implemented
        self.femAsicPixelSelfTestOverride   = 0  #TODO: To be implemented
        self.femReadoutOperatingMode        = 0  #TODO: To be implemented

        ########### Constants ###########
        self.asicRxPseudoRandomStart       = 61    # asic_rx_start_pseudo_random
        self.asicRx2tileStart              = 810   # asic_rx_start_2tile
        self.asicRxSingleStart             = 0     # asic_rx_start_single_asic
        self.asicRxHeaderBits              = 12    # asic_rx_hdr_bits - subtract this value to capture asic serial headers (0xAAA)
        # offsets in bits for different gains for slow asic readout (Nb first 16 pixels are skipped over)
        self.asicRxOffsetSlowReadout_x100  = 24    # asicrx_offset_slow_readout_x100
        self.asicRxOffsetSlowReadout_x10   = 564   # asicrx_offset_slow_readout_x10
        self.asicRxOffsetSlowReadout_x1    = 564   # asicrx_offset_slow_readout_x1 

        ########## Parameters now (mostly) exposed in API ##########

        self.femAsicModuleType  = self.ASIC_MODULE_TYPE_SUPERMODULE  # (0) Supermodule
        # self.ASIC_MODULE_TYPE_SINGLE_ASIC                          # (1) Single ASIC test module
        # self.ASIC_MODULE_TYPE_TWO_TILE                             # (2) 2-Tile module
        # self.ASIC_MODULE_TYPE_STANDALONE                           # (3) FEM Standalone 

        self.femDataSource      = self.RUN_TYPE_ASIC_DATA_VIA_PPC    # (0) ASIC data (via PPC) [Standard Operation]
        # self.RUN_TYPE_ASIC_DATA_DIRECT                             # (1) ASIC data direct from Rx block
        # self.RUN_TYPE_LL_DATA_GEN                                  # (2) LL Data Gen  (simulated data)
        # self.RUN_TYPE_PPC_DATA_DIRECT                              # (3) preprogrammed data DDR2 (simulated data)

#====== params for run type = self.RUN_TYPE_ASIC_DATA_VIA_PPC or self.RUN_TYPE_ASIC_DATA_DIRECT
        self.femAsicDataType    = self.ASIC_DATA_TYPE_ASIC_SENSOR    # (0) Asic sensor data [Standard Operation Real Data]
        # self.ASIC_DATA_TYPE_RX_COUNTING                            # (1) Asic Rx Block internally generated counting data (simulated data)
        # self.ASIC_DATA_TYPE_PSEUDO_RANDOM                          # (2) Asic Pseudo random data (test data from asic)
        
        self.femAsicLocalClock                      = 0         # 0 = no scaling (100 MHz), 1 = scaled down clock  [10 MHz (set by dcm params)]
        #TODO: False not implemented!
        self.femFastCtrlDynamic                     = True      # True = New dynamic commands
        self.femAsicSlowLoadMode                    = 0         # 0 = parallel load, 1 = daisy chain
        self.femAsicColumns                         = 4         # nr of images to capture per train
        self.asicrx_capture_asic_header_TEST_ONLY   = False     # False = (NORMAL OPERATION) ignore asic header bits 
                                                                # True  = (TEST ONLY) readout asic header bits to check timing alignment. This will mess up data capture.
        self.femAsicGainOverride                    = 8         # gain algorithm selection
        #                                                       #   0000  normal gain selection     0
        #                                                       #   1000  force select x100         8
        #                                                       #   1001  force select x10          9
        #                                                       #   1011  force select x1          11
        #                                                       #   1111  force error condition ?  15
        self.femAsicRxInvertData                    = False     # True  = invert adc output data (by subtracting value from $FFF)
        self.femAsicRxFastStrobe                    = True      # True  = Start asic rx data capture using strobe derived from fast command file
                                                                # False = Start asic rx data capture using fixed delay value 
        self.femAsicRxDelayOddChannels              = True      # True  = delay odd data channels by one clock to fix alignment
        self.femAsicSlowClockPhase                  = 0         # additional phase adjustment of slow clock rsync wrt asic reset
        self.femAsicSlowedClock                     = True      # False = asic readout phase uses same clock as capture phase
                                                                # True  = asic readout phase uses slowed down clock (must use fast cmd file with slow clock command)
        #TODO:  FOR FUTURE USE
        self.femAsicVersion                         = 1         # 1 = version 1, 2 = version 2
        self.femAsicClockSource                     = 0         # 0 = fem local oscillator, 1 =  xfel clock and controls system
        
#======== params for general steering 
        self.femPpcResetDelay       = 5     # wait after resetting ppc 
        self.femNumTestCycles       = 1     # repeat the test n times
        self.debug_level            = 0     # higher values more print out
        #TODO: NEVER USED:
#        self.femPpcMode             = 0     # 0 = Single Train Shot with PPC reset, 1 = Continuous readout (not working yet)
        
#======== params for 10G data links
        self.tenGigFarmMode         = 1     # 1 = non farm mode (1 ip host/port per link), 2 = farm mode (fixed ip host/multiple ports), 3 = farm mode with nic lists
        self.tenGigInterframeGap    = 0x000 # ethernet inter frame gap  ; ensure receiving 10G NIC parameters have been set accordingly
        self.tenGigUdpPacketLen     = 8000  # default udp packet length in bytes (can be overriden in asic runs)

        self.tenGig0 = {'SourceMac'  : '62-00-00-00-00-01',
                       'SourceIp'    : '10.0.0.2',         
                       'SourcePort'  : '0',                
                       'DestMac'     : '00-07-43-10-65-A0',
                       'DestIp'      : '10.0.0.1',         
                       'DestPort'    : '61649',            
                       'femEnable'   : True,                    # enable this link
                       #TODO: Add these to the API?
                       'link_nr'     : 1,                       # link number
                       'data_gen'    : 1,                       # data generator  1 = DataGen 2 = PPC DDR2  (used if run params data source is non asic)  
                       'data_format' : 0,                       # data format type  (0 for counting data)  
                       'frame_len'   : 0x10000,                 # frame len in bytes
                       'num_frames'  : 1,                       # number of frames to send in each cycle
                       'num_prts'    : 2,                       # number of ports to loop over before repeating
                       'delay'       : 0,                       # delay offset wrt previous link in secs
                       'nic_list'    : [ '61649@192.168.3.1' ]  
                      }

        # Placeholder; Not really used..
        self.tenGig1 = {'SourceMac'  : 'X62-00-00-00-00-01',
                       'SourceIp'    : 'X10.0.0.2',          
                       'SourcePort'  : 'X0',                 
                       'DestMac'     : 'X00-07-43-10-65-A0', 
                       'DestIp'      : 'X10.0.0.1',
                       'DestPort'    : 'X61649',
                       'femEnable'   : True,                    # enable this link
                       'link_nr'     : 2,                       # link number
                       'data_gen'    : 1,                       # data generator  1 = DataGen 2 = PPC DDR2  (used if run params data source is non asic)  
                       'data_format' : 0,                       # data format type  (0 for counting data)  
                       'frame_len'   : 0x10000,                 # frame len in bytes
                       'num_frames'  : 1,                       # number of frames to send in each cycle
                       'num_prts'    : 2,                       # number of ports to loop over before repeating
                       'delay'       : 0,                       # delay offset wrt previous link in secs
                       'nic_list'    : [ '61649x@x192.168.3.1' ]
                      }
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

#    def mac_addr_to_string(self, mac_addr_uint64):
#        """ convert uint64 MAC address integer into 'u-v-w-x-y-z' string """
#        mac_address = ""
#        mac_address += "%02X" % ( (mac_addr_uint64 & (0xFF << 0)) >> 0) + "-"
#        mac_address += "%02X" % ( (mac_addr_uint64 & (0xFF << 8)) >> 8) + "-"
#        mac_address += "%02X" % ( (mac_addr_uint64 & (0xFF << 16)) >> 16) + "-"
#        mac_address += "%02X" % ( (mac_addr_uint64 & (0xFF << 24)) >> 24) + "-"
#        mac_address += "%02X" % ( (mac_addr_uint64 & (0xFF << 32)) >> 32) + "-"
#        mac_address += "%02X" % ( (mac_addr_uint64 & (0xFF << 40)) >> 40)
#        return mac_address

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

#    def uint32_to_ip_addr(self, ip_addr):
#        ''' Construct IP address (in the form of a 32-bit integer) into a string '''
#        ip_list =[ "", "", "", "" ]
#        ip_address = (ip_addr & 0xFF000000) >> 24
#        ip_list[3] = str(ip_address)
#        ip_address = (ip_addr & 0xFF0000) >> 16
#        ip_list[2] = str(ip_address)
#        ip_address = (ip_addr & 0xFF00) >> 8
#        ip_list[1] = str(ip_address)
#        ip_address = (ip_addr & 0xFF)
#        ip_list[0] = str(ip_address)
#        # Add the list's contents into one string
#        ip_addr_str = ""
#        for idx in range(4):
#            ip_addr_str += ip_list[idx] + "."
#        return ip_addr_str[0:-1]

    def prt_addr_to_uint16(self, prt_addr_str):
        """ convert hex prt string to integer """
        return int(prt_addr_str)

#    def prt_addr_to_str(self, prt_addr_uint16):
#        """ convert hex prt from integer to string """
#        return str(prt_addr_uint16)
        
    def init_ppc_bram(self, base_addr, fpga_nr):
        """ This function initialises ppc bram with fpga id """
        self.rdmaWrite(base_addr+0, fpga_nr) # fpga id

    def toggle_bits(self, reg_addr, bit_nr):
        """ toggle_bits() """
        prev_value = self.rdmaRead(reg_addr, 1)[0]

        off = prev_value & ~(1 << bit_nr)

        self.rdmaWrite(reg_addr, off)
        on = prev_value | (1 << bit_nr)

        self.rdmaWrite(reg_addr, on)
        off = prev_value & ~(1 << bit_nr)

        self.rdmaWrite(reg_addr, off)
         
    def clear_ll_monitor(self, base):
        """ Reset a local link monitor block
            Rob Halsall 08-04-2011    """
        print "Local Link Monitor Counter Reset"
        self.rdmaWrite(base+1,0)
        self.rdmaWrite(base+1,1)
        self.rdmaWrite(base+1,0)
        
    # Rob Halsall 08-04-2011
    def read_ll_monitor(self, base, clock_freq):
        """ readout a local link monitor block """
        
        mon_addr = base + 16

        print "frm_last_length (bytes):\t",           hex( self.rdmaRead(mon_addr+0, 1)[0])
        print "frm_max_length (bytes): \t",           hex( self.rdmaRead(mon_addr+1, 1)[0])
        print "frm_min_length (bytes): \t",           hex( self.rdmaRead(mon_addr+2, 1)[0])
        print "frm_number:\t\t\t",                    hex( self.rdmaRead(mon_addr+3, 1)[0])
        print "frm_last_cycles:\t\t",                 hex( self.rdmaRead(mon_addr+4, 1)[0])
        print "frm_max_cycles: \t\t",                 hex( self.rdmaRead(mon_addr+5, 1)[0])
        print "frm_min_cycles: \t\t",                 hex( self.rdmaRead(mon_addr+6, 1)[0]) 
        total_data = self.rdmaRead(mon_addr+7, 1)[0]
        print "frm_data_total (bytes): \t", total_data, hex(total_data)         
        total_cycles = self.rdmaRead(mon_addr+8, 1)[0]
        print "frm_cycle_total:\t\t", total_cycles
        print "frm_trig_count: \t\t",                 hex( self.rdmaRead(mon_addr+9, 1)[0])
        print "frm_in_progress:\t\t",                 hex( self.rdmaRead(mon_addr+15, 1)[0])
        
        # data path = 64 bit, clock = 156.25 MHz
#        total_time = float(total_cycles) * (1/156.25e6)
        total_time = float(total_cycles) * (1/clock_freq)
        if (total_time):
            rate = (total_data/total_time)   #  total data is in bytes already   jac
        else:
            rate = 0
            
        print "Data Total = \t\t\t%e"   % total_data
        print "Data Time  = \t\t\t%e"   % total_time
        print "Data Rate  = \t\t\t%e\n" % rate

    def set_asic_clock_freq(self, base_address, clock_sel):
        """ Set the asic clock frequency ; 0 = 100 MHz ; 1 = divided clock """
        address = base_address + 11
        reg_val = self.rdmaRead(address, 1)[0]

        if clock_sel == 1:
            reg_val |= 0x1
        else:
            reg_val &= 0x0
        #print "setting asic clock freq sel = %08x" % reg_val
        self.rdmaWrite(address,reg_val)

    def setup_ll_frm_gen(self, base_address, length, data_type, num_ll_frames, hdr_trl_mode):
        """ This function sets up the data Generator & resets """
        
        # frm gen - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2

        self.rdmaWrite(base_address+1,reg_length)
        
        # DATA GEN Nr Frames
        self.rdmaWrite(base_address+2, num_ll_frames)
        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4

        # Turn header/trailer mode on if required
        if hdr_trl_mode == 1:
            control_reg = control_reg | 0x00000001
        else:
            control_reg = control_reg & 0xFFFFFFFE 
        # DATA GEN Data Type
        self.rdmaWrite(base_address+4, control_reg)
    
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
    
        # DATA GEN Data Init 0
        self.rdmaWrite(base_address+5,data_0)
        # DATA GEN Data Init 1
        self.rdmaWrite(base_address+6,data_1)
        # Data Gen soft reset
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)
        
    def setup_10g_udp_net_block(self, base_addr, net):
        """ Setup MAC address for SRC & destination
            src and dest mac, ip and ports are only used if Farm mode LUT is disabled """
 
        reg1 = ( self.mac_addr_to_uint64(net['SourceMac']) & 0x00000000FFFFFFFF)
    
        reg2b = (( self.mac_addr_to_uint64(net['SourceMac']) & 0x0000FFFF00000000) >> 32)
        reg2t = (( self.mac_addr_to_uint64(net['DestMac']) & 0x000000000000FFFF) << 16)
        reg2 = (reg2b | reg2t)
    
        reg3 = ( self.mac_addr_to_uint64(net['DestMac']) >> 16)

        # fpga_mac_lower_32
        self.rdmaWrite(base_addr+0, reg1)
        # nic_mac_lower_16 & fpga_mac_upper_16
        self.rdmaWrite(base_addr+1, reg2)
        # nic_mac_upper_32
        self.rdmaWrite(base_addr+2, reg3)
        
        # Setup IP address for SRC & destination
        reg6b = self.rdmaRead(base_addr+6, 1)[0]

        reg6b = (reg6b & 0x0000FFFF)
        reg6  = ( (self.ip_addr_to_uint32(net['DestIp']) << 16)  & 0xFFFFFFFF )
        reg6  = (reg6 | reg6b)
    
        reg7  = ( self.ip_addr_to_uint32(net['DestIp']) >> 16)
        reg7  = ( (reg7 | ( self.ip_addr_to_uint32(net['SourceIp']) << 16)) & 0xFFFFFFFF )
        
        reg8t = self.rdmaRead(base_addr+8, 1)[0]    # 1 = one 32 bit unsigned integer

        reg8t = (reg8t & 0xFFFF0000)
        reg8b = (self.ip_addr_to_uint32(net['SourceIp']) >> 16)
        reg8  = (reg8t | reg8b)

        # added jac from rob's latest code

        # set the udp source port
        reg8t = (reg8 & 0x0000FFFF)
        reg8b = (self.prt_addr_to_uint16(net['SourcePort']) << 16)
        # port bytes need to be swapped in xaui register
        reg8bl = reg8b & 0x00ff
        reg8bu = reg8b & 0xff00
        reg8b  = (reg8bl << 8) | (reg8bu >> 8) 
        reg8   = (reg8t | reg8b)
        
        reg9t = self.rdmaRead(base_addr+9, 1)[0]    # nb this was wrong reg in rob's code
        # set the udp destination port
        reg9t = (reg9t & 0xFFFF0000)
        reg9b = ( self.prt_addr_to_uint16(net['DestPort']) & 0x0000FFFF)
        # port bytes need to be swapped in xaui register
        reg9bl = reg9b & 0x00ff
        reg9bu = reg9b & 0xff00
        reg9b  = (reg9bl << 8) | (reg9bu >> 8) 
        reg9   = (reg9t | reg9b)

        self.rdmaWrite(base_addr+6, reg6)    
        self.rdmaWrite(base_addr+7, reg7)
        self.rdmaWrite(base_addr+8, reg8)
        self.rdmaWrite(base_addr+9, reg9)

    def setup_10g_packet_header(self, base_addr, packet_hdr):      
        """ robs udp packet header for 10g """
        self.rdmaWrite(base_addr + 11, packet_hdr)
 
    def setup_10g_index_cycle(self, base_addr, index_cycle):       
        """ override word in header containing index for 10g port lut """
        index_cycle &= 0x0000000f
        reg = self.rdmaRead(base_addr+10, 1)[0] 
        reg &= ~0x0000000f
        reg = reg | index_cycle
        self.rdmaWrite(base_addr+10, reg) 

    def setup_10g_rx_filter(self, base_addr):
        """ set 10g rx filter to accept any udp packet """     
        reg = self.rdmaRead(base_addr+11, 1)[0]
        reg &= 0xffff00ff
        reg |= 0x0000f300
        self.rdmaWrite(base_addr+11, reg) 

    def setup_10g_udp_block(self, base_addr, udp_pkt_len, udp_frm_sze, eth_ifg):
        """ Setup 10G UDP block (?) """
        fixed_length = 0
        
        # Setup header lengths
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
        
        # set 8 x 8 Byte Packets
        data0 = ((udp_pkt_len/8)-2)
        # TB UDP Block Packet Size
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len      
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # enable & set IFG
        # UDP Block IFG
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)


    def x10g_set_farm_mode(self, base_addr, mode):
        """ Enable or Disable 10G Farm Mode  """

        ctrl_reg = self.rdmaRead(base_addr+15, 1)[0]
        #print 'ctrl_reg = $%08X' % ctrl_reg         
        
        if mode == 1:
            ctrl_reg = ctrl_reg | 0x00000020
        else:
            ctrl_reg = ctrl_reg & ~0x00000020
            
        self.rdmaWrite(base_addr+15, ctrl_reg)  
        
        ctrl_reg = self.rdmaRead(base_addr+15, 1)[0]
        #print 'ctrl_reg = $%08X' %ctrl_reg         

    def swap_endian(self, data):  
        swapped = ((data << 24) & 0xff000000) | ((data << 8) & 0x00ff0000) | ((data >>24) & 0x000000ff) | ((data >> 8) & 0x0000ff00)
        return swapped

    def dump_regs_hex(self, base_addr, nr_regs):
        """ hex dump of registers """
        
        print "" 
        print 'rdma base addr = $%08X' % base_addr 
        for i in range(0, nr_regs/2):
            print 'reg %2d = $%08X '   % ((i*2),   self.rdmaRead(base_addr+(i*2),   1)[0]),
            print '\treg %2d = $%08X ' % ((i*2+1), self.rdmaRead(base_addr+(i*2+1), 1)[0])
        print ""  

    def setup_ppc_bram(self, base_addr, length):
        """ This function sets up the bram to provide ppc with run params """
        self.rdmaWrite(base_addr+8, 0)          # handshaking
        self.rdmaWrite(base_addr+10, 0)         # handshaking
        self.rdmaWrite(base_addr+9, 0)          # port index
        self.rdmaWrite(base_addr+16, length)    # for dma tx length in bytes

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

    def config_top_level(self):
        """ configure top level of design """
      
        if self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC:   # asic data via ppc
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000001)
        elif self.femDataSource == self.RUN_TYPE_ASIC_DATA_DIRECT:  # aisc direct to 10g
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000102)
        elif self.femDataSource == self.RUN_TYPE_LL_DATA_GEN:       # data generator
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000000)
        elif self.femDataSource == self.RUN_TYPE_PPC_DATA_DIRECT:   # ppc generated data
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000001)
        else:                                                       # asic data via ppc (yes, the same)
            self.rdmaWrite(self.fem_ctrl_0+1, 0x00000001)

    def config_10g_link(self):
        """ configure 10g link """
               
        if self.tenGig0['femEnable']:
            #print "Configure 10G link nr", self.tenGig0['link_nr']
            
            if self.debug_level > 0:
                self.pp.pprint(self.tenGig0)

            x10g_base = self.udp_10g_0
            data_gen_base = self.data_gen_0
            ppc_bram_base = self.bram_ppc1
           
            udp_pkt_len = self.tenGigUdpPacketLen
            udp_frm_sze = self.tenGig0['frame_len']

            eth_ifg = self.tenGigInterframeGap
            enable_udp_packet_hdr = 4  # enabled for python = 4  
            
            # legacy non farm mode. (farm mode = 1)
            self.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            self.setup_10g_udp_net_block(x10g_base, self.tenGig0)    
            self.setup_10g_packet_header(x10g_base, enable_udp_packet_hdr)

            self.setup_10g_rx_filter(x10g_base)         # accepts any udp packets
            self.setup_10g_index_cycle(x10g_base, 0)    # use 1st word in gen header for 10g index to port lut   
                                 
            #print "Not in Farm Mode."              
            self.x10g_set_farm_mode(x10g_base, 0)

            if self.debug_level > 3:                
                print "Dump of Farm Mode LUT for xaui for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(x10g_base+0x10000, 16) 
                self.dump_regs_hex(x10g_base+0x100f0, 16)                               
                self.dump_regs_hex(x10g_base+0x10100, 16)
                self.dump_regs_hex(x10g_base+0x101f0, 16)  
                self.dump_regs_hex(x10g_base+0x10200, 16)
                self.dump_regs_hex(x10g_base+0x103f0, 16)
                    
            if self.debug_level > 1:
                print "Dump of regs for xaui for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(data_gen_base, 16)
        
            if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_PPC_DATA_DIRECT):
                # data with PPC ll header
                self.setup_ppc_bram(ppc_bram_base, self.tenGig0['frame_len']) 
                self.setup_10g_index_cycle(x10g_base, 3) # use 4th word in ppc header for 10g index to port lut 
            else:
                # data source is data gen               
                self.setup_10g_index_cycle(x10g_base, 0) # use 1st word in gen header for 10g index to port lut   

    def reset_ppc(self):
        """ reset the ppc """

        #-------------------------------------------------
        # Resetting the PPC start the DMA test
        # need to get the timing right or add handshaking
                
        # Resets dma engines
        self.toggle_bits(self.fem_ctrl_0+9, 0)
        print "Reset the PPC.."
        
        theDelay = self.femPpcResetDelay

        print "Waiting %s seconds.." % theDelay,
        sys.stdout.flush()
        time.sleep(theDelay)
        print "\tDone!"

    def config_data_gen(self):
        """ configure data generator """                        
        data_gen_base = self.data_gen_0
                
        # final param to enable data gen headers for farm mode
        self.setup_ll_frm_gen(data_gen_base, self.tenGig0['frame_len']/8, self.tenGig0['data_format'], self.tenGig0['num_frames']-1, 1)
        
        self.override_header_ll_frm_gen(data_gen_base, 0, 0)  # default is not to override index nr in header
                     
    def config_asic_modules(self):
        """ configure asic modules """                        

        # phase delay of sync of slow clock wrt asic reset
        self.rdmaWrite(self.fem_ctrl_0+13, self.femAsicSlowClockPhase)  

        # duration of slowed down asic readout clock
        # duration (in slowed down asic clock cycles) for slow readout clock
        # each image takes ~ 480x22=1056 clocks to read out, plus allowance for setup time

#        asic_slow_readout_duration = self.femAsicColumns * * nr_clocks_to_readout_image + 5000
        asic_slow_readout_duration = 1000000 # 3100
        self.rdmaWrite(self.fem_ctrl_0+12, asic_slow_readout_duration)  

        # Load slow control, Fast Commands, asic module
        self.config_asic_slow_xml()
        self.config_asic_fast_xml()
        self.config_asic_datarx()
             
        #print "ENABLE asic Tristate output buffers"
        self.rdmaWrite(self.fem_ctrl_0+5, 0)

    def config_asic_slow_xml(self):
        """ configure asic slow control parameters from xml """                                        
        
        try:
            #TODO: Temporary hack, filename passed from API (not XML string)
            LpdAsicControlParams = LpdAsicControl( self.femAsicSlowControlParams, preambleBit=6, fromFile=True) #False)
            encodedString = LpdAsicControlParams.encode()
        except Exception as e:
            raise e
            sys.exit()
            
        no_of_bits = 3911
                  
        load_mode = self.femAsicSlowLoadMode

        # load in BRAM
        self.fem_slow_ctrl_setup(self.slow_ctr_0, self.slow_ctr_1, encodedString, no_of_bits, load_mode)
    
    def config_asic_fast_xml(self):
        """ configure asic fast command module """

        #TODO: Temporary hack, filename passed from API (not XML string)
        fileCmdSeq = LpdAsicCommandSequence(self.femAsicFastCmdSequence, fromFile=True) #False)
        xmlString  = fileCmdSeq.encode()
        
        no_of_words = fileCmdSeq.getTotalNumberWords()
        no_of_nops  = fileCmdSeq.getTotalNumberNops()
                        
        #print "fast cmds no_of_words, no_of_nops: ", no_of_words, no_of_nops

        # Setup the fast command block
        if self.femFastCtrlDynamic:   # new design with dynamic vetos
            self.fem_fast_bram_setup(self.fast_cmd_1, xmlString, no_of_words)
            self.fem_fast_cmd_setup_new(self.fast_cmd_0, no_of_words+no_of_nops)
        else:
            #TODO:  Fix this or remove?
            print "femFastCtrlDynamic == False: Need to sort the following block of code! (Exiting..)"
            sys.exit()

    def config_asic_datarx(self):
        """ configure asic data rx module """
        
        # Convert femAsicEnableMask from user format into fem's format
        self.femAsicEnableMask = self.femAsicEnableCalculate(self.femAsicEnableMask)

        no_asic_cols = self.femAsicColumns - 1
        no_asic_cols_per_frm = self.femAsicColumns - 1    # force all images to be in one frame               
             
        # Setup the ASIC RX IP block
        self.fem_asic_rx_setup(self.asic_srx_0, self.femAsicEnableMask, no_asic_cols, no_asic_cols_per_frm)
        
        # data source - self test
        if self.femAsicDataType == self.ASIC_DATA_TYPE_RX_COUNTING:            
            self.asicrx_self_test_counting_data_enable()
        else:
            self.asicrx_self_test_counting_data_disable()

        # asic rx gain override
        self.asicrx_override_gain()

        # asic rx invert adc data
        if self.femAsicRxInvertData:            
            self.asicrx_invert_data_enable()
        else:
            self.asicrx_invert_data_disable()

        # delay odd data channels to fix alignment
        if self.femAsicRxDelayOddChannels:            
            self.rdmaWrite(self.fem_ctrl_0+8, 1)           
        else:
            self.rdmaWrite(self.fem_ctrl_0+8, 0)           
        
        if self.femAsicDataType == self.ASIC_DATA_TYPE_PSEUDO_RANDOM:
            asic_rx_start_delay = self.asicRxPseudoRandomStart
        else:
            if self.femAsicModuleType == self.ASIC_MODULE_TYPE_SINGLE_ASIC:
                asic_rx_start_delay = self.asicRxSingleStart
            else:
                asic_rx_start_delay = self.asicRx2tileStart 
            
            if self.asicrx_capture_asic_header_TEST_ONLY:
                asic_rx_start_delay = asic_rx_start_delay - self.asicRxHeaderBits
            elif self.femAsicSlowedClock:     # following offsets skip 1st row of pixels
                if self.femAsicGainOverride == 8:
                    asic_rx_start_delay = asic_rx_start_delay + self.asicRxOffsetSlowReadout_x100
                elif self.femAsicGainOverride == 9:
                    asic_rx_start_delay = asic_rx_start_delay + self.asicRxOffsetSlowReadout_x10
                elif self.femAsicGainOverride == 11:
                    asic_rx_start_delay = asic_rx_start_delay + self.asicRxOffsetSlowReadout_x1

        #print "asic_rx_start_delay = %s " % asic_rx_start_delay          

        if self.femAsicRxFastStrobe:
            self.rdmaWrite(self.fem_ctrl_0+14, asic_rx_start_delay) # NEW using strobe from fast command file         
        else:
            self.rdmaWrite(self.fem_ctrl_0+4, asic_rx_start_delay)  # OLD using fixed offsets          

    def femAsicEnableCalculate(self, userMask):
        '''  Convert user's femAsicEnableMask selection into fem's own format
            e.g.
                user format: [0] = ASIC1-ASIC32, [1] = 33-64, etc (where 0x1=ASIC1,  0x2=ASIC2, etc)
                fem format:  [0] = ASIC1-4, 17-20, 33-37, etc; [1] = ASIC5-8, 21-24, ..
        '''
        femMask = [0x0, 0x0, 0x0, 0x0]

        femMask[0] = (femMask[0] | (userMask[0]     & 0x0000000F) << 28)
        femMask[1] = (femMask[1] | ( (userMask[0]   & 0x000000F0) << 24) )
        femMask[2] = (femMask[2] | ( (userMask[0]   & 0x00000F00) << 20) )
        femMask[3] = (femMask[3] | ( (userMask[0]   & 0x0000F000) << 16) )
        femMask[0] = (femMask[0] | ( (userMask[0]   & 0x000F0000) <<  8) )
        femMask[1] = (femMask[1] | ( (userMask[0]   & 0x00F00000) <<  4) )
        femMask[2] = (femMask[2] | ( (userMask[0]   & 0x0F000000)      ) )
        femMask[3] = (femMask[3] | ( (userMask[0]   & 0xF0000000) >>  4) )
    
        femMask[0] = (femMask[0] | ( (userMask[1]   & 0x0000000F) << 20) )
        femMask[1] = (femMask[1] | ( (userMask[1]   & 0x000000F0) << 16) )
        femMask[2] = (femMask[2] | ( (userMask[1]   & 0x00000F00) << 12) )
        femMask[3] = (femMask[3] | ( (userMask[1]   & 0x0000F000) <<  8) )
        femMask[0] = (femMask[0] | ( (userMask[1]   & 0x000F0000)      ) )
        femMask[1] = (femMask[1] | ( (userMask[1]   & 0x00F00000) >>  4) )
        femMask[2] = (femMask[2] | ( (userMask[1]   & 0x0F000000) >>  8) )
        femMask[3] = (femMask[3] | ( (userMask[1]   & 0xF0000000) >> 12) )
    
        femMask[0] = (femMask[0] | ( (userMask[2]   & 0x0000000F) << 12) )
        femMask[1] = (femMask[1] | ( (userMask[2]   & 0x000000F0) <<  8) )
        femMask[2] = (femMask[2] | ( (userMask[2]   & 0x00000F00) <<  4) )
        femMask[3] = (femMask[3] | ( (userMask[2]   & 0x0000F000)      ) )
        femMask[0] = (femMask[0] | ( (userMask[2]   & 0x000F0000) >>  8) )
        femMask[1] = (femMask[1] | ( (userMask[2]   & 0x00F00000) >> 12) )
        femMask[2] = (femMask[2] | ( (userMask[2]   & 0x0F000000) >> 16) )
        femMask[3] = (femMask[3] | ( (userMask[2]   & 0xF0000000) >> 20) )

        femMask[0] = (femMask[0] | ( (userMask[3]   & 0x0000000F) <<  4) )
        femMask[1] = (femMask[1] | ( (userMask[3]   & 0x000000F0)      ) )
        femMask[2] = (femMask[2] | ( (userMask[3]   & 0x00000F00) >>  4) )
        femMask[3] = (femMask[3] | ( (userMask[3]   & 0x0000F000) >>  8) )
        femMask[0] = (femMask[0] | ( (userMask[3]   & 0x000F0000) >> 16) )
        femMask[1] = (femMask[1] | ( (userMask[3]   & 0x00F00000) >> 20) )
        femMask[2] = (femMask[2] | ( (userMask[3]   & 0x0F000000) >> 24) )
        femMask[3] = (femMask[3] | ( (userMask[3]   & 0xF0000000) >> 28) )

        if self.debug_level > 2:
            print "userMask => femMask\n==================="
            for idx in range(4):
                print  "%8X    %8X" % (userMask[idx], femMask[idx])
        return femMask

    def send_trigger(self):
        """ send triggers """
                                
        #--------------------------------------------------------------------
        # send triggers to data generators
        #--------------------------------------------------------------------
                                 
        if self.femDataSource == self.RUN_TYPE_LL_DATA_GEN:            
            print "Trigger Data Gen"
            self.toggle_bits(self.fem_ctrl_0+0, 0) # trigger to local link frame gen 
        elif (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_ASIC_DATA_DIRECT):             
            #print "Trigger Asic"
            self.toggle_bits(self.fem_ctrl_0+0, 1)  # start asic seq  = reset, slow, fast & asic rx
        else:
            print "Trigger Asic"
            self.toggle_bits(self.fem_ctrl_0+0, 1)
                    
    def dump_registers(self):
        """ dump registers """
        
        print "Dump of FEM Registers : TOP LEVEL CTRL" 
        self.dump_regs_hex(self.fem_ctrl_0, 18)        

        print "Dump of FEM Registers : PPC1 BRAM" 
        self.dump_regs_hex(self.bram_ppc1, 20) 
        
        print "Dump of FEM Registers : XAUI link 1" 
        self.dump_regs_hex(self.udp_10g_0, 16) 

        print "Dump of FEM Registers : DATA GEN on link 1" 
        self.dump_regs_hex(self.data_gen_0, 16) 

        print "Dump of FEM Registers : ASIC RX" 
        self.dump_regs_hex(self.asic_srx_0, 16) 

        print "Dump of FEM Registers : ASIC FAST CTRL" 
        self.dump_regs_hex(self.fast_cmd_0, 16) 

        print "Dump of FEM Registers : ASIC FAST BRAM" 
        self.dump_regs_hex(self.fast_cmd_1, 50) 

        print "Dump of FEM Registers : ASIC SLOW CTRL" 
        self.dump_regs_hex(self.slow_ctr_0, 16) 

        print "Dump of FEM Registers : ASIC SLOW BRAM" 
        self.dump_regs_hex(self.slow_ctr_1, 130) 
                    
    def fem_slow_ctrl_setup(self, base_addr_0, base_addr_1, slow_ctrl_data, no_of_bits, load_mode):
    
        #slow control set up function blank

        # asic slow control load mode
        self.rdmaWrite(base_addr_0+0, load_mode)
        
        dataTuple = tuple(slow_ctrl_data)   # Do Not construct tuple from list like in fem_fast_.. func
        
        #print "Slow Ctrl RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
        
        # load control registers
        
        # set number of bits register
        max_no_of_bits = 32*1024
        if no_of_bits > max_no_of_bits:
            no_of_bits = max_no_of_bits
        
        no_of_bits = no_of_bits + 1    # fix added  jc
        
        control_reg_1 = base_addr_0 + 1
        
        #print "slow ctrl - no of bits (+1) to reg"
        self.rdmaWrite(control_reg_1, no_of_bits)

    def fem_fast_bram_setup(self, base_addr_1, fast_cmd_data, no_of_words):
        #fast cmd set up function blank
        
        max_block_length = 1024
        
        # check length is not greater than FPGA Block RAM
        
        block_length = no_of_words
        
        if block_length > max_block_length:
            block_length =  max_block_length        
        
        # Build tuple of a list of data
        dataTuple = tuple([fast_cmd_data[i] for i in range(block_length)])
        # load fast control pattern memory
        #print "Fast Cmd RAM"
        self.rdmaWrite(base_addr_1, dataTuple)
        
    def fem_fast_cmd_setup_new(self, base_addr_0, no_of_words):

        #fast cmd set up function blank
    
        # load control registers
        # reset mode  for old behaviour outputting bram , without vetos
    
        #print "fast_command_reg_reset_offset"
        self.rdmaWrite(base_addr_0+6, 0)
        #print "fast_command_reg_reset_nwords"  
        self.rdmaWrite(base_addr_0+7, no_of_words)

    def fem_asic_rx_setup(self, base_addr, mask_array, no_asic_cols, no_cols_frm):
        """ Set up the XFEL FEM ASIC RX IP Block """
         
        # Setup IP Address register locations
        mask_reg0 = (0x00000004 | base_addr)
        mask_reg1 = (0x00000005 | base_addr)
        mask_reg2 = (0x00000006 | base_addr)
        mask_reg3 = (0x00000007 | base_addr)
         
        no_clk_cyc_dly_reg        = (0x00000002 | base_addr)
        no_asic_cols_cols_frm_reg = (0x00000003 | base_addr)
         
        # setup data values
        no_asic_cols          = (no_asic_cols & 0x0000001FF)
        no_cols_frm           = (no_cols_frm & 0x0000001FF)
        no_cols_frm_shft      = (no_cols_frm << 16)
        no_asic_cols_cols_frm = (no_cols_frm_shft | no_asic_cols)

        #TODO: Comment still relevant?         
        # clkc cycle delay for sof-eof formula 512 * 36 * no cols?
        #no_clk_cyc_dly = 0x00011FDC)
         
        #no_clk_cyc_dly = 512 * 36 * no_asic_cols * no_cols_frm - 1 
         
        # this doesn't match formula in register doc ? jac
        # frame clock length = (no cols * 512 * 36) - 36
        # is this the nr of clocks for payload of each ll frame (or all frames) ?
        # assume headers and footer are not included.
         
        # also fixed bug as above was using bit shifted value of no_cols_frm
        no_clk_cyc_dly = (512 * 36 * (no_cols_frm + 1)) - 36       # as no_cols starts from '0'
                  
        # Setup clk cycle delay
        #print "asic rx clk cycle delay"
        self.rdmaWrite(no_clk_cyc_dly_reg, no_clk_cyc_dly)
        
        # Setup num asic cols & num cols per frame
        #print "asic rx no_cols cols_frm"
        self.rdmaWrite(no_asic_cols_cols_frm_reg,no_asic_cols_cols_frm)
   
        # Setup mask registers
        #print "asic rx 0"
        self.rdmaWrite(mask_reg0,mask_array[0])
        #print "asic rx 1"
        self.rdmaWrite(mask_reg1,mask_array[1])
        #print "asic rx 2"
        self.rdmaWrite(mask_reg2,mask_array[2])
        #print "asic rx 3"
        self.rdmaWrite(mask_reg3,mask_array[3])
        
    def asicrx_self_test_counting_data_enable(self):
        """ Enable internal counting data """
        reg_addr = self.asic_srx_0+1
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | 0x00000001
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_self_test_counting_data_disable(self):
        """ Disable internal counting data """
        reg_addr = self.asic_srx_0+1
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value & ~0x00000001
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_invert_data_enable(self):
        """ Invert data by subtracting value from 0xFFF """
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | 0x00000100
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_invert_data_disable(self):
        """ Do not invert data """
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value & ~0x00000100
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_override_gain(self):
        # added override to gain selection 
        # 
        #  bits
        #  0000  normal gain selection     0
        #  1000  force select x100         8
        #  1001  force select x10          9
        #  1011  force select x1          11
        #  1111  force error condition ?  15
        gain_select = self.femAsicGainOverride
        reg_addr    = self.asic_srx_0+0
        prev_value  = self.rdmaRead(reg_addr, 1)[0] 
        new_value   = prev_value | (gain_select & 0x0000000f)
        self.rdmaWrite(reg_addr, new_value)

# new taken from TB script
    def soft_reset_ll_frm_gen(self, base_address):
        """ This function just resets the frame nr in the header """
        # Data Gen soft reset
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)        

    def start_10g_link(self):
        """ start a 10g link """

        if self.debug_level > 5:
            print "Start 10G link nr", self.tenGig0['link_nr']

        data_gen_base = self.data_gen_0
      
        time.sleep(self.tenGig0['delay'])   # wait before trigger

        if self.femDataSource == self.RUN_TYPE_LL_DATA_GEN: # ll data gen
          
            # check last cycle has completed                
            gen_busy  = self.status_ll_frm_gen(data_gen_base) 
            i = 0

            while gen_busy == 1:
                i=i+1
                print 'Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs\r' % (self.tenGig0['link_nr'], i),
                sys.stdout.flush() 
                time.sleep(1)                    
                gen_busy = self.status_ll_frm_gen(data_gen_base) 

        if self.tenGig0['data_gen'] == 1:
            # give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
            # don't do this any earlier or won't trigger
            self.soft_reset_ll_frm_gen(data_gen_base)  
            print "Trigger LL Data Gen"
            self.toggle_bits(self.fem_ctrl_0+0, 0)   
 
    def start_dma_tx(self, base_addr, index):
        """ start dma tx """
        self.rdmaWrite(base_addr+9, index) 
        self.rdmaWrite(base_addr+8, 0x1234) 
    
    def final_dma_tx(self, base_addr):
        """ flag last dma tx """
        self.rdmaWrite(base_addr+10, 0x5678) 

    def prev_dma_tx(self, base_addr):
        """  """  
        busy = 1
        reg = self.rdmaRead(base_addr+8, 1) [1]
        reg &= 0x0000ffff
        if reg == 0:
            busy = 0
        return busy
 
    def ppc_readout_ready_status(self, base_addr):
        """ Check whether PPC reset completed """  
        ready = 0
        
        reg = self.rdmaRead(base_addr+12, 1) [0]
        reg &= 0xffffffff
       
        if reg == 0xFACEFACE:
            ready = 1
        return ready

    def zero_regs(self, base_addr, nr_regs):
        """ zero regs eg bram """
        
        print 'Zero rdma base addr = $%08X ; nr regs = $%08X' %(base_addr, nr_regs)
        for i in range(0, nr_regs):
            self.rdmaWrite(base_addr+i, 0) 

    def register_set_bit(self, reg_addr, bit_nr):
        """ set bit in register """
        prev_value = self.rdmaRead(reg_addr, 1)[0]  
        on = prev_value | (1 << bit_nr)
        self.rdmaWrite(reg_addr, on)
 
    def register_clear_bit(self, reg_addr, bit_nr):
        """ set bit in register """
        prev_value = self.rdmaRead(reg_addr, 1)[0]  
        off = prev_value & ~(1 << bit_nr)
        self.rdmaWrite(reg_addr, off)

    def status_ll_frm_gen(self, base_address):
        """ This function returns busy status of data gen """
        busy = self.rdmaRead(base_address+17, 1)[0]  
        return busy        

    '''
        --------------------------------------------------------
        Rationalised various bits of jac' s code into standalone functions
        --------------------------------------------------------
    '''

    def send_long_asic_reset(self):
        """ Send Long Reset to ASIC pin """
        self.register_set_bit(self.fem_ctrl_0+10, 0)  
        time.sleep(self.femPpcResetDelay)
        self.register_clear_bit(self.fem_ctrl_0+10, 0)  
    
    def resetFwModulesToggleTristateIO(self):
        """ Reset firmware modules, disable and re-enable tri-state asic i/o """
        # reset f/w modules (resets asicrx counters, but also disables tristate outputs to asic fast and slow lines)
        self.toggle_bits(self.fem_ctrl_0+9, 8)  # async reset to v5 top level
        # re-enable v5 tristate i/o to asic 
        self.rdmaWrite(self.fem_ctrl_0+5, 0x0)  

    '''
        --------------------------------------------------------
        --------------------------------------------------------
    '''
    
    def configure(self):
        '''
            Load configuration into Fem
        '''
        #TODO: commented out for now. (28/02/2013)
        # clock downscale factor for slowed down asic readout
        #asic_clock_downscale_factor = 16

        lpd_image_size = 0x20000    # partial image is 128 KB

        #TODO:  commented out for now (28/02/2013)
        #nr_clocks_to_readout_image  = 512 * 36 # * asic_clock_downscale_factor # 512 pixels with 3 gain values each

        # testing timing difference with slowed down readout
        if self.femAsicSlowedClock: #self.run_params['asic_readout_with_slow_clock'] == 1:
            self.asicRx2tileStart = self.asicRx2tileStart - 2

        print "=======================================================================" 
  
        self.pp = pprint.PrettyPrinter(indent=4)

        #TODO: MISSED COPYING THESE TWO LINES ACROSS YESTERDAY? (28/02/2013)
        # moved asic clock selection first
        self.set_asic_clock_freq(self.fem_ctrl_0, self.femAsicLocalClock)    # 0 = 100 Mhz, 1 = div clock 10 MHz
        self.zero_regs(self.bram_ppc1, 20)  # clear ppc ready
  
        self.init_ppc_bram(self.bram_ppc1, 0xBEEFFACE)

        self.resetFwModulesToggleTristateIO()

        #TODO: Is Comment Still Relevant?
        # send Reset to ASIC pin . Shouldn't be necessary? as short reset pulse is sent before trigger sequence.
        print "Send Long Reset to ASIC pin"
        self.send_long_asic_reset()
        
        self.clear_ll_monitor(self.llink_mon_asicrx)
        self.clear_ll_monitor(self.llink_mon_0)

        # Setup clocks and connections between modules
        self.config_top_level()         
        
        # Setup the 10g link params
        self.config_10g_link()         

        # pass readout data length to ppc bram before restarting ppc
        self.setup_ppc_bram(self.bram_ppc1, self.femAsicColumns * lpd_image_size) 

        if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_PPC_DATA_DIRECT):  # runs with ppc
            self.reset_ppc()         

        #TODO: Still needed for  local link generator or redundant?
        # Setup data gen - not necessary for actual data but leave alone, "just in case"
        self.config_data_gen()

        # Setup asic blocks
        if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_ASIC_DATA_DIRECT):  # data from asic
            self.config_asic_modules()

#        else: # data from datagen or ppc ddr2 
##following code won't work with new run() structure , as assumes triggers are sent from withing start_10g_link()
#                    
#            num_cycles = self.femNumTestCycles
#            print "Starting Run of %d cycles" % self.femNumTestCycles
#            for i in range (1, num_cycles+1):
#                print "Starting Run Cycle Nr %d" % i
#                self.start_10g_link()  
#
#            if self.tenGig0['data_gen'] == 2:
#                self.final_dma_tx(self.bram_ppc1)  


    def run(self):
        '''
            Execute run
        '''
        
        print "Executing run().."

        if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource ==  self.RUN_TYPE_PPC_DATA_DIRECT):  # runs with ppc, wait for ppc to be ready to read out
            #if (self.run_params['ppc_reset_delay_secs'] == 0):
            if (self.femPpcResetDelay == 0):
                while self.ppc_readout_ready_status(self.bram_ppc1) == 0:
                    print "Waiting for PPC readout to be ready...\r",
                    sys.stdout.flush()
                    
        self.send_trigger()

        # Read out all registers (Both 2 tile & supermodule run fine without) 
        if self.debug_level > 0:
            self.dump_registers()

        # 10g ll monitor
        self.read_ll_monitor(self.llink_mon_0, 156.25e6)

        print "Asic Rx LLink Monitor"
        self.read_ll_monitor(self.llink_mon_asicrx, 200.0e6)


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
        self.pcf7485WriteOneBit(LpdFemClient.LV_CTRL_BIT, value)

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
        self.pcf7485WriteOneBit(LpdFemClient.HV_CTRL_BIT, value)
        
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
        return self.sensorBiasLevelRead()
    
    def sensorBiasSet(self, aValue):
        '''
            Set Sensor HV Bias Voltage [V]
        '''
        self.ad55321Write( int( ceil( aValue/0.122) ) )
    
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
        return self.tenGig0['SourceMac']

    def tenGig0SourceMacSet(self, aValue):
        '''
            Set tenGig0SourceMac
        '''
        self.tenGig0['SourceMac'] = aValue
    
    def tenGig0SourceIpGet(self):
        '''
            Get tenGig0SourceIp
        '''
        return self.tenGig0['SourceIp']
    
    def tenGig0SourceIpSet(self, aValue):
        '''
            Set tenGig0SourceIp
        '''
        self.tenGig0['SourceIp'] = aValue

    def tenGig0SourcePortGet(self):
        '''
            Get tenGig0SourcePort
        '''
        return self.tenGig0['SourcePort']
    
    def tenGig0SourcePortSet(self, aValue):
        '''
            Set tenGig0SourcePort
        '''
        self.tenGig0['SourcePort'] = aValue
        
    def tenGig0DestMacGet(self):
        '''
            Get tenGig0DestMac
        '''
        return self.tenGig0['DestMac']

    def tenGig0DestMacSet(self, aValue):
        '''
            Set tenGig0DestMac
        '''
        self.tenGig0['DestMac'] = aValue

    def tenGig0DestIpGet(self):
        '''
            Get tenGig0DestIp
        '''
        return self.tenGig0['DestIp']

    def tenGig0DestIpSet(self, aValue):
        '''
            Set tenGig0DestIp
        '''
        self.tenGig0['DestIp'] = aValue

    def tenGig0DestPortGet(self):
        '''
            Get tenGig0DestPort
        '''
        return self.tenGig0['DestPort']

    def tenGig0DestPortSet(self, aValue):
        '''
            Set tenGig0DestPort
        '''
        self.tenGig0['DestPort'] = aValue

    def tenGig1SourceMacGet(self):
        '''
            Get tenGig1SourceMac
        '''
        return self.tenGig1['SourceMac']

    def tenGig1SourceMacSet(self, aValue):
        '''
            Set tenGig1SourceMac
        '''
        self.tenGig1['SourceMac'] = aValue
    
    def tenGig1SourceIpGet(self):
        '''
            Get tenGig1SourceIp
        '''
        return self.tenGig1['SourceIp']
    
    def tenGig1SourceIpSet(self, aValue):
        '''
            Set tenGig1SourceIp
        '''
        self.tenGig1['SourceIp'] = aValue

    def tenGig1SourcePortGet(self):
        '''
            Get tenGig1SourcePort
        '''
        return self.tenGig1['SourcePort']
    
    def tenGig1SourcePortSet(self, aValue):
        '''
            Set tenGig1SourcePort
        '''
        self.tenGig1['SourcePort'] = aValue
        
    def tenGig1DestMacGet(self):
        '''
            Get tenGig1DestMac
        '''
        return self.tenGig1['DestMac']

    def tenGig1DestMacSet(self, aValue):
        '''
            Set tenGig1DestMac
        '''
        self.tenGig1['DestMac'] = aValue

    def tenGig1DestIpGet(self):
        '''
            Get tenGig1DestIp
        '''
        return self.tenGig1['DestIp']

    def tenGig1DestIpSet(self, aValue):
        '''
            Set tenGig1DestIp
        '''
        self.tenGig1['DestIp'] = aValue

    def tenGig1DestPortGet(self):
        '''
            Get tenGig1DestPort
        '''
        return self.tenGig1['DestPort']

    def tenGig1DestPortSet(self, aValue):
        '''
            Set tenGig1DestPort
        '''
        self.tenGig1['DestPort'] = aValue

    def tenGigInterframeGapGet(self):
        '''
            Get tenGigInterframeGap
        '''
        return self.tenGigInterframeGap

    def tenGigInterframeGapSet(self, aValue):
        '''
            Set tenGigInterframeGap
        '''
        self.tenGigInterframeGap = aValue

    def tenGigUdpPacketLenGet(self):
        '''
            Get tenGigUdpPacketLen
        '''
        return self.tenGigUdpPacketLen

    def tenGigUdpPacketLenSet(self, aValue):
        '''
            Set tenGigUdpPacketLen
        '''
        self.tenGigUdpPacketLen = aValue

    def femFastCtrlDynamicGet(self):
        '''
            Get femFastCtrlDynamic
        '''
        return self.femFastCtrlDynamic

    def femFastCtrlDynamicSet(self, aValue):
        '''
            Set femFastCtrlDynamic
        '''
        self.femFastCtrlDynamic = aValue

    def femEnableTenGigGet(self):
        '''
            Get femEnableTenGig
        '''
        return self.tenGig0['femEnable']

    def femEnableTenGigSet(self, aValue):
        '''
            Set femEnableTenGig
        '''
        self.tenGig0['femEnable'] = aValue

    def femDataSourceGet(self):
        '''
            Get femDataSource
        '''
        return self.femDataSource

    def femDataSourceSet(self, aValue):
        '''
            Set femDataSource
        '''
        self.femDataSource = aValue

    def femAsicModuleTypeGet(self):
        '''
            Get femAsicModuleType
        '''
        return self.femAsicModuleType

    def femAsicModuleTypeSet(self, aValue):
        '''
            Set femAsicModuleType
        '''
        self.femAsicModuleType = aValue

    def femAsicEnableMaskGet(self):
        '''
            Get femAsicEnableMask
        '''
        return self.femAsicEnableMask

    def femAsicEnableMaskSet(self, aValue):
        '''
            Set femAsicEnableMask
        '''
        self.femAsicEnableMask = aValue

    def femAsicColumnsGet(self):
        '''
            Get femAsicColumns
        '''
        return self.femAsicColumns

    def femAsicColumnsSet(self, aValue):
        '''
            Set femAsicColumns
        '''
        self.femAsicColumns = aValue

    def femAsicGainOverrideGet(self):
        '''
            Get femAsicGainOverride
        '''
        return self.femAsicGainOverride

    def femAsicGainOverrideSet(self, aValue):
        '''
            Set femAsicGainOverride
        '''
        self.femAsicGainOverride = aValue

    def femAsicSlowControlParamsGet(self):
        '''
            Get femAsicSlowControlParams
        '''
        return self.femAsicSlowControlParams

    def femAsicSlowControlParamsSet(self, aValue):
        '''
            Set femAsicSlowControlParams
        '''
        self.femAsicSlowControlParams = aValue

    def femAsicFastCmdSequenceGet(self):
        '''
            Get femAsicFastCmdSequence
        '''
        return self.femAsicFastCmdSequence

    def femAsicFastCmdSequenceSet(self, aValue):
        '''
            Set femAsicFastCmdSequence
        '''
        self.femAsicFastCmdSequence = aValue

    def femAsicPixelFeedbackOverrideGet(self):
        '''
            Get femAsicPixelFeedbackOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicPixelFeedbackOverride
                    
    def femAsicPixelFeedbackOverrideSet(self, aValue):
        '''
            Set femAsicPixelFeedbackOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicPixelFeedbackOverride = aValue
            
    def femAsicPixelSelfTestOverrideGet(self):
        '''
            Get femAsicPixelSelfTestOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicPixelSelfTestOverride
                    
    def femAsicPixelSelfTestOverrideSet(self, aValue):
        '''
            Set femAsicPixelSelfTestOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicPixelSelfTestOverride = aValue

    def femReadoutOperatingModeGet(self):
        '''
            Get femReadoutOperatingMode
        '''
        return self.femReadoutOperatingMode

    def femReadoutOperatingModeSet(self, aValue):
        '''
            Set femReadoutOperatingMode
        '''
        self.femReadoutOperatingMode = aValue

    def femAsicDataTypeGet(self):
        '''
            Get femAsicDataType
        '''
        return self.femAsicDataType

    def femAsicDataTypeSet(self, aValue):
        '''
            Set femAsicDataType
        '''
        self.femAsicDataType = aValue

    def femAsicLocalClockGet(self):
        '''
            Get femAsicLocalClock
        '''
        return self.femAsicLocalClock

    def femAsicLocalClockSet(self, aValue):
        '''
            Set femAsicLocalClock
        '''
        self.femAsicLocalClock = aValue

    def femAsicSlowLoadModeGet(self):
        '''
            Get femAsicSlowLoadMode
        '''
        return self.femAsicSlowLoadMode

    def femAsicSlowLoadModeSet(self, aValue):
        '''
            Set femAsicSlowLoadMode
        '''
        self.femAsicSlowLoadMode = aValue

    def femAsicRxInvertDataGet(self):
        '''
            Get femAsicRxInvertData
        '''
        return self.femAsicRxInvertData

    def femAsicRxInvertDataSet(self, aValue):
        '''
            Set femAsicRxInvertData
        '''
        self.femAsicRxInvertData = aValue

    def femAsicRxFastStrobeGet(self):
        '''
            Get femAsicRxFastStrobe
        '''
        return self.femAsicRxFastStrobe

    def femAsicRxFastStrobeSet(self, aValue):
        '''
            Set femAsicRxFastStrobe
        '''
        self.femAsicRxFastStrobe = aValue

    def femAsicRxDelayOddChannelsGet(self):
        '''
            Get femAsicRxDelayOddChannels
        '''
        return self.femAsicRxDelayOddChannels

    def femAsicRxDelayOddChannelsSet(self, aValue):
        '''
            Set femAsicRxDelayOddChannels
        '''
        self.femAsicRxDelayOddChannels = aValue

    def femAsicSlowClockPhaseGet(self):
        '''
            Get femAsicSlowClockPhase
        '''
        return self.femAsicSlowClockPhase

    def femAsicSlowClockPhaseSet(self, aValue):
        '''
            Set femAsicSlowClockPhase
        '''
        self.femAsicSlowClockPhase = aValue

    def femAsicSlowedClockGet(self):
        '''
            Get femAsicSlowedClock
        '''
        return self.femAsicSlowedClock

    def femAsicSlowedClockSet(self, aValue):
        '''
            Set femAsicSlowedClock
        '''
        self.femAsicSlowedClock = aValue

    def femAsicVersionGet(self):
        '''
            Get femAsicVersion
        '''
        return self.femAsicVersion

    def femAsicVersionSet(self, aValue):
        '''
            Set femAsicVersion
        '''
        self.femAsicVersion = aValue

    def femAsicClockSourceGet(self):
        '''
            Get femAsicClockSource
        '''
        return self.femAsicClockSource

    def femAsicClockSourceSet(self, aValue):
        '''
            Set femAsicClockSource
        '''
        self.femAsicClockSource = aValue

    def femPpcModeGet(self):
        '''
            Get femPpcMode
        '''
        return self.femPpcMode

    def femPpcModeSet(self, aValue):
        '''
            Set femPpcMode
        '''
        self.femPpcMode = aValue

    def femPpcResetDelayGet(self):
        '''
            Get femPpcResetDelay
        '''
        return self.femPpcResetDelay

    def femPpcResetDelaySet(self, aValue):
        '''
            Set femPpcResetDelay
        '''
        self.femPpcResetDelay = aValue

    def femNumTestCyclesGet(self):
        '''
            Get femNumTestCycles
        '''
        return self.femNumTestCycles

    def femNumTestCyclesSet(self, aValue):
        '''
            Set femNumTestCycles
        '''
        self.femNumTestCycles = aValue

    def tenGigFarmModeGet(self):
        '''
            Get tenGigFarmMode
        '''
        return self.tenGigFarmMode

    def tenGigFarmModeSet(self, aValue):
        '''
            Set tenGigFarmMode
        '''
        self.tenGigFarmMode = aValue

    def femI2cBusGet(self):
        '''
            Get femI2cBus
        '''
        return self.femI2cBus

    def femI2cBusSet(self, aValue):
        '''
            Set femI2cBus
        '''
        self.femI2cBus = aValue

    """ -=-=-=-=-=- Helper Functions -=-=-=-=-=- """

    def sensorBiasLevelRead(self):
        '''
            Helper function: Reads high voltage bias level and converts
                from ADC counts into voltage
        '''
        value = self.ad5321Read()
        return round( float( value * 500 / 4095.0), 2)
    
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

    def sensorTemperatureRead(self, device, channel):
        '''
            Helper function: Reads sensor temperature at 'channel' in  address 'device',
                and converts adc counts into six volts scale.
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
        addr = self.femI2cBus + device
        adcChannel = 0x80 + ((channel & 7) << 4)
        # Write operation, select ADC channel
        self.i2cWrite(addr, adcChannel)
        # Read operation, read ADC value
        response = self.i2cRead(addr, 2)
        # Extract the received two bytes and return one integer
        value = (int((response[0] & 15) << 8) + int(response[1]))
        return value

    def ad5321Read(self):
        ''' 
            Read 2 bytes from ad5321 device 
        '''
        addr = self.femI2cBus + 0x0C
        response = self.i2cRead(addr, 2)
        high = (response[0] & 15) << 8
        low = response[1]
        return high + low

    def ad55321Write(self, aValue):
        '''
            Write 'aValue' (2 bytes) to ad5321 device
        '''
        # Construct address and payload (as a tuple)
        addr = self.femI2cBus + 0x0C
        payload = ((aValue & 0xF00) >> 8), (aValue & 0xFF)
        # Write new ADC value to device
        self.i2cWrite(addr, payload)

    def pcf7485ReadOneBit(self, bitId):
        ''' 
            Read one byte from PCF7485 device and determine if set.
            Note: bit 1 = 0, 2 = 1,  3 = 2, 4 = 4, 
                      5 = 8, 6 = 16, 7 = 32 8 = 64
            Therefore, bitId must be one of the following: [0, 1, 2, 4, 8, 16, 32, 64]
        '''
        addr = self.femI2cBus + 0x38 
        response = self.i2cRead(addr, 1)
        value = response[0]
        return (value & (1 << bitId)) != 0
        
    def pcf7485ReadAllBits(self):
        ''' 
            Read and return one byte from PCF7485 device
            
            If a bit is set, that represents: 
                bit 0-1:    Disabled (HV, LV)
                bit 2-7:    A fault  (Fem Status, Ext trip, fault, etc)
                e.g.    
                    131:    Hv (1) & Lv (2) disabled, low temperature (128) alert

                Beware      bit 0 = 1, bit 1 = 2, bit 2 = 4, etc !!
                therefore   131 = 128 + 2 + 1 (bits: 7, 1, 0)
        '''
        addr = self.femI2cBus + 0x38
        response = self.i2cRead(addr, 1)
        return response[0]

    def pcf7485WriteOneBit(self, bitId, value):
        ''' 
            Change bit 'bitId' to 'value' in PCF7485 device
        '''        
        addr = self.femI2cBus + 0x38
        # Read PCF7485's current value
        bit_register = self.pcf7485ReadAllBits()
        # Change bit 'bitId' to 'value'
        bit_register = (bit_register & ~(1 << bitId)) | (value << bitId) | 0xFC
        self.i2cWrite(addr, bit_register)

    def calculateTemperature(self, Beta, resistanceOne):
        ''' 
            Calculate temperature in thermistor using Beta and resistance
                e.g. calculateTemperature(3630, 26000) = 3.304 degrees Celsius 
        '''
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
