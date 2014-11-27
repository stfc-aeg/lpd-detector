'''
LpdFemClient - XFEL LPD class sitting between the API and the FemClient
         
Created 16 October 2012

@Author: ckd    -    TRUNK VERSION

'''

# Import Python standard modules
# log required when calculating temperature
from math import log#, ceil
import pprint, time, sys, os
from functools import partial

from datetime import datetime

# for keyboard interrupts
import select
import tty
import termios

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction
from LpdPowerCard import *

# Import library for parsing XML asic files
from LpdAsicCommandSequence import *
from LpdAsicSetupParams import *

# Import library for parsing XML ccc veto patterns
from LpdAsicBunchPattern import *

# next lines for ESC key interrupt
def isData():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
old_settings = termios.tcgetattr(sys.stdin)


class LpdFemClient(FemClient):
    '''
        Handles all the low-level fem interactions
    '''

    # with new addressing using top 4 bits for fpga selection
    #        32 way splitter
    udp_10g_0           = 0x00000000    #  0
    udp_10g_1           = 0x00800000    #  1
    data_gen_0          = 0x01000000    #  2
    data_chk_0          = 0x01800000    #  3
    data_gen_1          = 0x02000000    #  4
    data_chk_1          = 0x02800000    #  5
    fem_ctrl_0          = 0x03000000    #  6
    llink_mon_0         = 0x03800000    #  7
    data_mon_1          = 0x04000000    #  8
    slow_ctr_2          = 0x04800000    #  9
    fast_cmd_0          = 0x05000000    # 10
    fast_cmd_1          = 0x05800000    # 11    Tx bram
    asic_srx_0          = 0x06000000    # 12
    llink_mon_asicrx    = 0x06800000    # 13
    slow_ctr_0          = 0x07000000    # 14
    slow_ctr_1          = 0x07800000    # 15
    dma_gen_0           = 0x08000000    # 16
    dma_chk_0           = 0x08800000    # 17
    dma_gen_1           = 0x09000000    # 18
    dma_chk_1           = 0x09800000    # 19
    dma_gen_2           = 0x0a000000    # 20
    dma_chk_2           = 0x0a800000    # 21
    dma_gen_3           = 0x0b000000    # 22
    dma_chk_3           = 0x0b800000    # 23
    bram_ppc1           = 0x0c000000    # 24
    trig_strobe         = 0x0c800000    # 25
    ccc_delay_reg       = 0x0d000000    # 26
    ccc_pattern_bram    = 0x0d800000    # 27 - which bunch(s) to read
    ccc_pattern_id      = 0x0e000000    # 28 
    ccc_cmd_gen_bram    = 0x0e800000    # 29 - sim of C&C system (testing, generate cc cmds, vetos, etc)
    ccc_cmd_gen_reg     = 0x0f000000    # 30
    rsvd_31             = 0x0f800000    # 31
 
# Spartan 3 devices 
# needs new gbe embedded software with rs232 mux control
    bot_sp3_ctrl        = 0x10000000    #  0
    top_sp3_ctrl        = 0x20000000    #  0
    cfg_sp3_ctrl        = 0x30000000    #  0

   
    ########## Enumerated values for API variables ##########

    ASIC_MODULE_TYPE_SUPER_MODULE   = 0     # (0) Supermodule
    ASIC_MODULE_TYPE_SINGLE_ASIC    = 1     # (1) Single ASIC test module
    ASIC_MODULE_TYPE_TWO_TILE       = 2     # (2) 2-Tile module
    ASIC_MODULE_TYPE_STAND_ALONE    = 3     # (3) FEM Standalone
    ASIC_MODULE_TYPE_RAW_DATA       = 4     # (4) Super Module Raw Data

    RUN_TYPE_ASIC_DATA_VIA_PPC      = 0     # (0) ASIC data (via PPC) [Standard Operation]
    RUN_TYPE_ASIC_DATA_DIRECT       = 1     # (1) ASIC data direct from Rx block
    RUN_TYPE_LL_DATA_GEN            = 2     # (2) LL Data Gen  (simulated data)
    RUN_TYPE_PPC_DATA_DIRECT        = 3     # (3) preprogrammed data DDR2 (simulated data)
    
    ASIC_DATA_TYPE_ASIC_SENSOR      = 0     # Asic sensor data [Standard Operation Real Data]
    ASIC_DATA_TYPE_RX_COUNTING      = 1     # Asic Rx Block internally generated counting data (simulated data)
    ASIC_DATA_TYPE_PSEUDO_RANDOM    = 2     # Asic Pseudo random data (test data from asic)
    
    ########## femAsicGain Lookup Table ##########
    
    FEM_ASIC_GAIN_LOOKUP = {0: 0,   # Default 
                            3: 8,   # x100
                            2: 9,   # x10
                            1: 11}  # x1
    
    def __init__(self, hostAddr=None, timeout=None, asicModuleType=0):
        '''
            Constructor for LpdFemClient class
        '''

        # Call superclass initialising function
        super(LpdFemClient, self).__init__(hostAddr, timeout)

        ######## API variables extracted from jac's functions ########
        self.femAsicEnableMask              = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF]

        self.femAsicSetupParams             = ""
        self.femAsicCmdSequence             = ""

        ######## API parameters: Functionality to be developed ########
        self.femAsicPixelFeedbackOverride   = -1                # Default -1 = "Don't Care"
        self.femAsicPixelSelfTestOverride   = -1                # Default -1 = "Don't Care"
        self.femReadoutOperatingMode        = 0                 #TODO: To be implemented

        ########### Constants ###########
        self.nr_clocks_to_readout_image     = (512 * 3 * 12)    # * asic_clock_downscale_factor # 512 pixels with 3 gain values each. this is time for asic data streams to enter asicrx (output takes longer)
        self.nr_clocks_to_readout_row       = (16 * 3 * 12)     # row of image 16 pixels

        self.lpd_image_size                 = 0x20000           # size of buffer in ppc for partial image is 128 KB

        self.nr_asics_per_sensor = 8

        self.asicRxPseudoRandomStart        = (80+50+1)         # asic_rx_start_pseudo_random  ; this is now fixed wrt start asic seq (it is not using readout cmd word), also need extra clock for sensor delay FF
        self.asicRx2tileStart               = (810+1+1)         # asic_rx_start_2tile ; added 1 clock delay to compensate for new delay of sensor groups ; add another clock step after fixing clock distribution timing in sp3 io v0109
        self.asicRxSingleStart              = 0                 # asic_rx_start_single_asic
        self.asicRxHeaderBits               = 12                # asic_rx_hdr_bits - subtract this value to capture asic serial headers (0xAAA)
        # offsets in bits for different gains for slow asic readout 
        self.asicRxOffsetSlowReadout_x100   = (24 - 16*3*12)    #  NB first row of 16 pixels to be ignored  # 24   # skips first row of 16 pixels for x100
        self.asicRxOffsetSlowReadout_x10    = -12               # keep first row of 16 pixels # 564 (skip first row of 16 pixels)
        self.asicRxOffsetSlowReadout_x1     = -12               # keep first row of 16 pixels # 564 (skip first row of 16 pixels) 

        self.asic_readout_clock_div         = 16                # factor to divide asic clock for slow readout of asic v1

        ########## Parameters now (mostly) exposed in API ##########

        self.femAsicModuleType  = self.ASIC_MODULE_TYPE_SUPER_MODULE        # (0) Supermodule
        self.femDataSource      = self.RUN_TYPE_ASIC_DATA_VIA_PPC   # (0) ASIC data (via PPC) [Standard Operation]
        self.femAsicDataType    = self.ASIC_DATA_TYPE_ASIC_SENSOR   # (0) Asic sensor data [Standard Operation Real Data]
        
        self.femAsicLocalClock                      = 0         # 0 = no scaling (100 MHz), 1 = scaled down clock  [10 MHz (set by dcm params)]
        self.femAsicSetupLoadMode                   = 0         # 0 = parallel load, 1 = daisy chain
        self.numberImages                           = 4         # Number of images to capture per train
        self.femAsicGain                            = 8         # Gain    algorithm selection     F/W value, API correspodning value 
        #                                                       #   0000  normal gain selection     0,        0
        #                                                       #   1000  force select x100         8,        3
        #                                                       #   1001  force select x10          9,        2
        #                                                       #   1011  force select x1          11,        1
        #                                                       #   1111  force error condition ?  15,        #TODO: Implement?
        self.femInvertAdcData                       = False     # True  = invert adc output data (by subtracting value from $FFF)
        self.femAsicRxCmdWordStart                  = True      # True  = Start asic rx data capture using strobe derived from fast command file
                                                                # False = Start asic rx data capture using fixed delay value 
        self.femAsicSetupClockPhase                 = 0         # Additional phase adjustment of slow clock rsync wrt asic reset
        self.femAsicSlowedClock                     = False     # False = asic readout phase uses same clock as capture phase
                                                                # True  = asic readout phase uses slowed down clock (must use fast cmd file with slow clock command)
        #TODO:  FOR FUTURE USE
        self.femAsicVersion                         = 2         # 1 = version 1, 2 = version 2
        self.femAsicClockSource                     = 0         # 0 = Fem local oscillator, 1 = xfel, 2 = petra, 3 = Diamond

        self.femStartTrainSource                    = 1         # 0 = XFEL clock and controls system, 1 = Software, 2 = LCLS, 3 = PETRAIII, 4 = Diamond

        self.ext_trig_strobe_delay                  = 10 # test  #   512 #  (2+88)    # Delay of ext trigger strobe (in asic clock periods)
        self.ext_trig_strobe_polarity               = 0         # 1 = use inverted signal 
        self.petra_shutter_polarity                 = 0         # 1 = use inverted signal

        self.femDelaySensors                        = 0xffff    # delay timing of 16 sensors ; bit = 1 adds 1 clock delay ; sensor mod 1 is lsb
        self.femAsicGainOverride                    = False     # False = asicrx gain sel fixed by register, True =  asicrx gain sel taken from fast cmd file commands on the fly

#=======================
# minimum length of inhibit is time to read out asic data. this is ok for LCLS  where train rate is fixed 120 Hz
# but for Petra use this inhibit to adjust "train rate" ;  E.g set inhibit to 100 msec for 10 Hz ; Nb with petra clock as input the asic clock period is 192 / 22 nsec ~ 8.7 nsec
# 

############################
##   ext_trig_strobe_inhibit is now overridden by value set in readoutConfiguration.xml
#
#        self.ext_trig_strobe_inhibit  = (22*200 + self.nr_clocks_to_readout_image * self.numberImages + self.asicRx2tileStart)       # length of inhibit after ext strobe enough to read out all data (in asic clock periods) ; allow for 100 fast cmds each 22 clocks to inhibit during fast commands from file before readout starts
# At PETRA for Trigger Rate = N Hz set ext_trig_strobe_inhibit = N x 10**7 x 22 / 192
#        self.ext_trig_strobe_inhibit    = (100000000*22/192)  # 100 msec for 10Hz     # see comments above

# for 10 Hz triggers rate  (with ARB asic clock period = 12 nsec)
#        self.ext_trig_strobe_inhibit    = (100000000*22/12)  


#############################################


#======== params for general steering 
        self.femPpcResetDelay           = 5     # wait after resetting ppc 
        self.numberTrains               = 1     # Number of trains to be readout
        self.femDebugLevel              = 0     # higher values more print out
        #TODO: To be implemented: ??
        self.femPpcMode                 = 1     # 0 = Single Train Shot with PPC reset, 1 = Continuous readout (not working yet)

#=========================================================================================================              
#  john c

        self.FAST_BRAM_SIZE_BYTES = 2048 

        self.femIgnorePetraShutter = 0    # 0 = use the Petra Shutter, 1 = ignore the Petra shutter


# CCC stuff for Xfel C&C

# 2 Fast Asic command sequences for new CCC
        self.femAsicCmdSequenceStart  = 'Config/CmdSequence/Command_LongExposure_Start.xml'
        self.femAsicCmdSequenceStop  = 'Config/CmdSequence/Command_LongExposure_4Images_Stop.xml'

#        ccc_system_mode ;  (32 bits) 
#           = 0  ;  without c&c system  ; old style external trigger or s/w to load single fast xml cmd file
#           = 1  ;  with c&c system  ;  using start, stop cmds   (single fast cmd file)
#           = 2  ;  with c&c system  ;  using start, stop cmds  AND  vetos   (start and stop fast cmd files)
        self.cccSystemMode = 1   
        
        self.cccEmulationMode = True;  #  =1 to emulate c&c commands (for testing if no c&c system connected)

#   ccc_override_nr_images_to_readout ; 
#   Only For ccc_system_mode = 2
#       =1 ; read out actual nr triggers sent to asic
#       =0 ; use numberImages param to override nr images to readout  
        self.cccProvideNumberImages = True;

# ccc delays
        self.cccVetoStartDelay = 0 #;  32 bits ; used to adjust timing of veto arrival (in steps of N clocks) ; needs to be TUNED with beam vetos
        self.cccStopDelay = 0       #;  32 bits ; used to adjust timing of stop (in steps of N clocks)   ; optional
        self.cccResetDelay = 0      #;  32 bits ; used to adjust timing of reset (in steps of N clocks)  ; optional

        self.cccVetoPatternFile     = "UNDEFINED.xml"
        
        self.NR_BUNCHES_IN_TRAIN = 3072   # as expected by CCC veto logic
        
        self.CCC_CMD_GEN_XRAY_DELAY = 1024  # nr of clocks between emulated xfel c&c start and arrival of xrays

        self.TRAIN_ID_LENGTH = 64   # nr bits

        self.femModuleId = [0] * 16; # module ID for header

        self.NR_CLOCKS_PER_FAST_CMD = 22
        
        self.CCC_PATTERN_VETO_BRAM_SIZE_BYTES = 1024

        self.NR_CCC_VETO_PATTERNS = 10
        self.NR_WORDS_PER_CCC_VETO_PATTERN = 96  # size of pattern in bram words


#----       
        self.sp3_io_bot_firmware_modules = 0
        
        self.STOP_RUN_ON_ESC_KEY = False    # Set False if running with Gui ; True

#=========================================================================================================              
       
#======== params for 10G data links
        self.tenGigFarmMode             = 1     # 1 = non farm mode (1 ip host/port per link), 2 = farm mode (fixed ip host/multiple ports), 3 = farm mode with nic lists
        self.tenGigInterframeGap        = 0x000 # ethernet inter frame gap  ; ensure receiving 10G NIC parameters have been set accordingly
        self.tenGigUdpPacketLen         = 8000  # default udp packet length in bytes (can be overriden in asic runs)

        self.tenGig0 = {'SourceMac'  : '62-00-00-00-00-01',
                        'SourceIp'    : '10.0.0.2', 
                        'SourcePort'  : '0',
                        'DestMac'     : '00-07-43-10-65-A0',
                        'DestIp'      : '10.0.0.1',
                        'DestPort'    : '61649',
                        'femEnable'   : True,                    # enable this link
                        'link_nr'     : 1,                       # link number
                        'data_gen'    : 1,                       # data generator  1=DataGen, 2=PPC DDR2  (Used if femDataSource=2)  
                        'data_format' : 0,                       # data format type  (0 for counting data)  
                        'frame_len'   : 0x10000,                 # frame len in bytes
                        'num_frames'  : 1,                       # number of frames to send in each cycle
                        #TODO: Add these to the API?
                        'num_prts'    : 2,                       # number of ports to loop over before repeating
                        'delay'       : 0,                       # delay offset wrt previous link in secs
                        'nic_list'    : [ '61649@192.168.3.1' ]
                        }
        
        # Supermodule has two power cards, everything else only one
        if (asicModuleType ==  LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE) or (asicModuleType ==  LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA):
            numberPowerCards= 2
            numberSensorsPerCard = 8
            powerCardI2cBus = [3, 2]
            sensorMapping = []
            
            # Generate mapping for temperature sensors
            for cardIdx in range(numberPowerCards):
                for sensor in range(8):
                    sensorIdx = sensor if cardIdx == 0 else (numberSensorsPerCard  - (sensor+1))
                    sensorMapping.append([cardIdx, sensorIdx])
            
        else:
            numberPowerCards= 1
            powerCardI2cBus = [3]
            sensorMapping = [[0,1], [0, 6]]
        
        self.powerCards = []
        for idx in range(numberPowerCards):
            self.powerCards.append(LpdPowerCard(self, powerCardI2cBus[idx]))

        paramTypes = ['Temp', 'Voltage', 'Current']
        
        for sensor in range(len(sensorMapping)):
            
            for paramType in paramTypes:
                
                getMethodName = 'sensor' + str(sensor) + paramType + 'Get'
                targetMethodName = 'sensor' + paramType + 'Get'
                
                [cardIdx, sensorIdx] = sensorMapping[sensor]
                
                setattr(self, getMethodName,
                        partial(self._sensorParamGet, cardIdx=cardIdx, sensorIdx=sensorIdx, method=targetMethodName))

        # Add 'misc' quantities
        miscMethodNames = ['sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus',
                           'powerCardExtStatus', 'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']

        for name in miscMethodNames:
            for cardIdx in range(len(self.powerCards)):
                
                getMethodName = name + str(cardIdx) + 'Get'
                targetMethodName = name + 'Get'
                
                setattr(self, getMethodName,
                        partial(self._powerCardParamGet, cardIdx=cardIdx, method=targetMethodName))
        
        powerMethodNames = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent']
        
        for name in powerMethodNames:
            for cardIdx in range(len(self.powerCards)):
                
                getMethodName = name + str(cardIdx) + 'Get'
                targetMethodName = name + 'Get'
                
                setattr(self, getMethodName,
                        partial(self._powerCardParamGet, cardIdx=cardIdx, method=targetMethodName))

        # Add 'misc' Set functions
        setMethodNames = ['sensorBias', 'sensorBiasEnable', 'asicPowerEnable']

        for name in setMethodNames:
            for cardIdx in range(len(self.powerCards)):
                
                setMethodName = name + str(cardIdx) + 'Set'
                targetMethodName = name + 'Set'
                
                setattr(self, setMethodName,
                        partial(self._powerCardParamSet, cardIdx=cardIdx, method=targetMethodName))

    def _powerCardParamSet(self, value, cardIdx, method):

        return getattr(self.powerCards[cardIdx], method)(value)

    def _sensorParamGet(self, cardIdx, sensorIdx, method):
        
        return getattr(self.powerCards[cardIdx], method)(sensorIdx)
        
    def _powerCardParamGet(self, cardIdx, method):
        
        return getattr(self.powerCards[cardIdx], method)()
    
    '''
        --------------------------------------------------------
        Support functions taken from John's version of LpdFemClient.py:
        --------------------------------------------------------
    '''

    def mac_addr_to_uint64(self, mac_addr_str):
        ''' convert hex MAC address 'u-v-w-x-y-z' string to integer '''
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
        ''' Convert IP address into list of 4 elements (remove the - characters) '''
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
        ''' convert hex port from string to integer '''
        return int(prt_addr_str)

    def init_ppc_bram(self, base_addr, fpga_nr):
        ''' This function initialises ppc bram with fpga id '''
        self.rdmaWrite(base_addr+0, fpga_nr) # fpga id

    def toggle_bits(self, reg_addr, bit_nr):
        ''' Toggle bit 'bit_nr' in register 'reg_addr' off, on, and off '''
        prev_value = self.rdmaRead(reg_addr, 1)[0]

        off = prev_value & ~(1 << bit_nr)

        self.rdmaWrite(reg_addr, off)
        on = prev_value | (1 << bit_nr)

        self.rdmaWrite(reg_addr, on)
        off = prev_value & ~(1 << bit_nr)

        self.rdmaWrite(reg_addr, off)
         
    def clear_ll_monitor(self, base):
        ''' Reset a local link monitor block
            Rob Halsall 08-04-2011    '''
        self.rdmaWrite(base+1,0)
        self.rdmaWrite(base+1,1)
        self.rdmaWrite(base+1,0)
        
    # Rob Halsall 08-04-2011
    def read_ll_monitor(self, base, clock_freq):
        ''' readout a local link monitor block '''
        
        mon_addr = base + 16

        print "frm_last_length (bytes):      %s" % hex( self.rdmaRead(mon_addr+0, 1)[0])
        print "frm_max_length (bytes):       %s" % hex( self.rdmaRead(mon_addr+1, 1)[0])
        print "frm_min_length (bytes):       %s" % hex( self.rdmaRead(mon_addr+2, 1)[0])
        print "frm_number:                   %s" % hex( self.rdmaRead(mon_addr+3, 1)[0])
        print "frm_last_cycles:              %s" % hex( self.rdmaRead(mon_addr+4, 1)[0])
        print "frm_max_cycles:               %s" % hex( self.rdmaRead(mon_addr+5, 1)[0])
        print "frm_min_cycles:               %s" % hex( self.rdmaRead(mon_addr+6, 1)[0]) 
        total_data = self.rdmaRead(mon_addr+7, 1)[0]
        print "frm_data_total (bytes):       %d %s" % (total_data, hex(total_data))         
        total_cycles = self.rdmaRead(mon_addr+8, 1)[0]
        print "frm_cycle_total:              %d" % total_cycles
        print "frm_trig_count:               %s" % hex( self.rdmaRead(mon_addr+9, 1)[0])
        print "frm_in_progress:              %s" % hex( self.rdmaRead(mon_addr+15, 1)[0])
        
        # data path = 64 bit, clock = 156.25 MHz
        total_time = float(total_cycles) * (1/clock_freq)
        if (total_time):
            rate = (total_data/total_time)   #  total data is in bytes already   jac
        else:
            rate = 0

        print "Clock Freq = %d Hz"               % clock_freq
        print "Data Total =                  %e" % total_data
        print "Data Time  =                  %e" % total_time
        print "Data Rate  =                  %e" % rate

    def set_asic_clock_freq(self, base_address, clock_sel):
        ''' Set the asic clock frequency; 0 = 100 MHz; 1 = divided clock '''
        address = base_address + 11
        reg_val = self.rdmaRead(address, 1)[0]

        if clock_sel == 1:
            reg_val |= 0x1
        else:
            reg_val &= 0x0
        
        self.rdmaWrite(address,reg_val)

    def setup_ll_frm_gen(self, base_address, length, data_type, num_ll_frames, hdr_trl_mode):
        ''' Setup the data Generator and resets '''
        
        # Frame Generator - n.b. top nibble/2 - move to data gen setup
        reg_length = length - 2

        self.rdmaWrite(base_address+1,reg_length)
        
        # Data Generator Number of Frames
        self.rdmaWrite(base_address+2, num_ll_frames)
        control_reg = data_type & 0x00000003
        control_reg = control_reg << 4

        # Turn header/trailer mode on if required
        if hdr_trl_mode == 1:
            control_reg = control_reg | 0x00000001
        else:
            control_reg = control_reg & 0xFFFFFFFE 
        # Data Generator Data Type
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
    
        # Data Generator Data Init 0
        self.rdmaWrite(base_address+5,data_0)
        # Data Generator Data Init 1
        self.rdmaWrite(base_address+6,data_1)
        # Data Generator soft reset
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)
        
    def setup_10g_udp_net_block(self, base_addr, net):
        ''' Setup MAC address for source & destination
            src and dest mac, ip and ports are only used if Farm mode LUT is disabled '''
 
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
        
        # Setup IP address for source & destination
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
        ''' Robs udp packet header for 10g '''
        self.rdmaWrite(base_addr + 11, packet_hdr)
 
    def setup_10g_index_cycle(self, base_addr, index_cycle):       
        ''' Override word in header containing index for 10g port lut '''
        index_cycle &= 0x0000000f
        reg = self.rdmaRead(base_addr+10, 1)[0] 
        reg &= ~0x0000000f
        reg = reg | index_cycle
        self.rdmaWrite(base_addr+10, reg) 

    def setup_10g_rx_filter(self, base_addr):
        ''' Set 10g rx filter to accept any udp packet '''     
        reg = self.rdmaRead(base_addr+11, 1)[0]
        reg &= 0xffff00ff
        reg |= 0x0000f300
        self.rdmaWrite(base_addr+11, reg) 

    def setup_10g_udp_block(self, base_addr, udp_pkt_len, udp_frm_sze, eth_ifg):
        ''' Setup 10G UDP block (?) '''
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
        
        # Set udp checksum = zero
        ctrl_reg_val = ctrl_reg_val | 0x00000010

        # Shift udp header length up to the top two bytes
        udp_hdr_len  = (udp_hdr_len << 16)
        
        # Set 8 x 8 Byte Packets
        data0 = ((udp_pkt_len/8)-2)
        # TB UDP Block Packet Size
        self.rdmaWrite(base_addr + 0x0000000C, data0)
        
        # Set IP header length + 64 Bytes
        data1 = 0xDB000000 + ip_hdr_len      
        self.rdmaWrite(base_addr + 0x00000004, data1)    
        
        # Set udp length +64 Bytes
        data2 = 0x0000D1F0 + udp_hdr_len
        self.rdmaWrite(base_addr + 0x00000009, data2)
        
        # Enable & set IFG
        # UDP Block IFG
        self.rdmaWrite(base_addr + 0x0000000F, ctrl_reg_val)
        self.rdmaWrite(base_addr + 0x0000000D, eth_ifg)

    def x10g_set_farm_mode(self, base_addr, mode):
        ''' Enable or Disable 10G Farm Mode  '''

        ctrl_reg = self.rdmaRead(base_addr+15, 1)[0]
        
        if mode == 1:
            ctrl_reg = ctrl_reg | 0x00000020
        else:
            ctrl_reg = ctrl_reg & ~0x00000020
            
        self.rdmaWrite(base_addr+15, ctrl_reg)  
        ctrl_reg = self.rdmaRead(base_addr+15, 1)[0]

    #TODO: Not used?
    def swap_endian(self, data):  
        swapped = ((data << 24) & 0xff000000) | ((data << 8) & 0x00ff0000) | ((data >>24) & 0x000000ff) | ((data >> 8) & 0x0000ff00)
        return swapped

    def dump_regs_hex(self, base_addr, nr_regs):
        ''' Hex dump of registers '''
        
        print "rdma base addr = $%08X" % base_addr 
        for i in range(0, nr_regs/2):
            print "reg %2d = $%08X     %2d = $%08X"   % ((i*2),   self.rdmaRead(base_addr+(i*2), 1)[0], (i*2+1), self.rdmaRead(base_addr+(i*2+1), 1)[0])

    def dump_regs_hex_coe(self, base_addr, nr_regs):
        ''' Hex dump of registers in single column ; for pasting bram contents into .coe '''
        
        print "rdma base addr = $%08X" % base_addr 
        for i in range(0, nr_regs):
            print "%08X," %(self.rdmaRead(base_addr+(i), 1)[0])

    def setup_ppc_bram(self, base_addr, length):
        ''' Setup the bram to provide ppc with run params. Used by PPC when running in Single Shot mode. Replaced by mailbox comms for continuous mode. '''
        self.rdmaWrite(base_addr+8,  0)         # Handshaking
        self.rdmaWrite(base_addr+10, 0)         # Handshaking
        self.rdmaWrite(base_addr+9,  0)         # Port index
        self.rdmaWrite(base_addr+16, length)    # For dma tx length in bytes

    def override_header_ll_frm_gen(self, base_address, enable_override, index_nr):
        ''' Override the index number sent in the ll header (for steeting the port nr in 10g tx) '''
        self.rdmaWrite(base_address+7, index_nr)   # set index number 
        # Override default behaviour         
        format_reg = self.rdmaRead(base_address+4, 1)[0] 
        if enable_override == 1:
            format_reg = format_reg | 0x00000100
        else:
            format_reg = format_reg & 0xFFFFFEFF 
        self.rdmaWrite(base_address+4, format_reg) 

    def config_top_level(self):
        ''' Configure top level of design '''
      
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

    def config_asic_clock_source(self):
        ''' Configure clock sources '''

        # Resets to hold dcm in reset while clock is switched
        self.register_set_bit(self.fem_ctrl_0+11, 16)  # Asic clock dcm
        self.register_set_bit(self.fem_ctrl_0+11, 14)  # Xfel clock dcm
        self.register_set_bit(self.fem_ctrl_0+11, 17)  # Petra clock dcm 
        self.register_set_bit(self.fem_ctrl_0+11, 15)  # Diamond clock dcm 

        self.register_set_bit(self.fem_ctrl_0+11, 18)  # BOT SP3 IO DCM
        self.register_set_bit(self.fem_ctrl_0+11, 19)  # TOP SP3 IO DCM

        #print "reset all dcms" 
    
        # asic clock source
        if self.femAsicClockSource == 0:
            self.register_clear_bit(self.fem_ctrl_0+11, 1)    # fem osc  
        elif self.femAsicClockSource == 1:
            self.register_set_bit(self.fem_ctrl_0+11, 2)    # xfel clock
            self.register_set_bit(self.fem_ctrl_0+11, 1)  
        elif self.femAsicClockSource == 2:
            self.register_clear_bit(self.fem_ctrl_0+11, 2)  # petra clock   
            self.register_set_bit(self.fem_ctrl_0+11, 1)  
            self.register_clear_bit(self.fem_ctrl_0+11, 3)  # extra select between petra and diamond
        elif self.femAsicClockSource == 3:
            self.register_clear_bit(self.fem_ctrl_0+11, 2)  # diamond clock   
            self.register_set_bit(self.fem_ctrl_0+11, 1)   
            self.register_set_bit(self.fem_ctrl_0+11, 3)  # extra select between petra and diamond
        else:
            raise FemClientError("WARNING Illegal Asic Clock Source selected. Defaulting to FEM Osc")
            self.register_clear_bit(self.fem_ctrl_0+11, 1)
 
        # MUST release petra and diamond DCMs BEFORE releasing asic DCM!
        self.register_clear_bit(self.fem_ctrl_0+11, 15)  # Releases reset on Diamond dcm
        self.register_clear_bit(self.fem_ctrl_0+11, 17)  # Releases reset on petra dcm
        self.register_clear_bit(self.fem_ctrl_0+11, 14)  # Releases reset on xfel dcm
        self.register_clear_bit(self.fem_ctrl_0+11, 16)  # Releases reset on asic dcm

        # Release SP3 IO DCM last of all
        self.register_clear_bit(self.fem_ctrl_0+11, 18)  # BOT SP3 IO DCM    
        self.register_clear_bit(self.fem_ctrl_0+11, 19)  # TOP SP3 IO DCM

        #print "released all dcms"

    def config_asic_clock_source_from_osc(self):
        ''' Configure Asic clock source from FEM Osc clock'''

        if self.femDebugLevel >= 1:
            print "Forcing ASIC clock source from FEM Osc" 

        # Resets to hold dcm in reset while clock is switched
        self.register_set_bit(self.fem_ctrl_0+11, 16)  # Asic clock dcm
        self.register_set_bit(self.fem_ctrl_0+11, 18)  # BOT SP3 IO DCM
        self.register_set_bit(self.fem_ctrl_0+11, 19)  # TOP SP3 IO DCM

        self.register_clear_bit(self.fem_ctrl_0+11, 1)    # fem osc  

        self.register_clear_bit(self.fem_ctrl_0+11, 16)  # Releases reset on asic dcm
        self.register_clear_bit(self.fem_ctrl_0+11, 18)  # BOT SP3 IO DCM    
        self.register_clear_bit(self.fem_ctrl_0+11, 19)  # TOP SP3 IO DCM
        
    def config_trig_strobe(self):
        ''' Configure external trigger strobes '''

        self.set_ext_trig_strobe_delay(self.ext_trig_strobe_delay)    
        self.set_ext_trig_strobe_inhibit(self.ext_trig_strobe_inhibit)    
        self.set_ext_trig_strobe_max(self.numberTrains)   # max nr of strobes allowed to trigger train readout (i.e. terminal train count)
        self.set_ext_trig_strobe_polarity(self.ext_trig_strobe_polarity) 
               
        # Trigger strobe for Petra test is derived from petra clock
        if self.femStartTrainSource == 3:
            self.enable_petra_trig_strobe()  
        else: # using C&C RJ45 input for Xfel , LCLS or Diamond
            self.disable_petra_trig_strobe()  

        if self.femStartTrainSource == 3:
            # Petra shutter
            self.set_petra_shutter_polarity(self.petra_shutter_polarity) 
            self.use_petra_shutter(self.femIgnorePetraShutter) 
      
    def config_10g_link(self):
        ''' Configure 10 Gig Link '''
               
        if self.tenGig0['femEnable']:
            if self.femDebugLevel > 0:
                self.pp.pprint(self.tenGig0)

            x10g_base = self.udp_10g_0
            data_gen_base = self.data_gen_0
            ppc_bram_base = self.bram_ppc1
           
            udp_pkt_len = self.tenGigUdpPacketLen
            udp_frm_sze = self.tenGig0['frame_len']

            eth_ifg = self.tenGigInterframeGap
            enable_udp_packet_hdr = 4  # enabled for python = 4  
            
            # Legacy non farm mode (farm mode = 1)
            self.setup_10g_udp_block(x10g_base, udp_pkt_len, udp_frm_sze, eth_ifg)
            self.setup_10g_udp_net_block(x10g_base, self.tenGig0)    
            self.setup_10g_packet_header(x10g_base, enable_udp_packet_hdr)

            self.setup_10g_rx_filter(x10g_base)         # Accepts any udp packets
            self.setup_10g_index_cycle(x10g_base, 0)    # Use 1st word in gen header for 10g index to port lut   
                                 
            self.x10g_set_farm_mode(x10g_base, 0)

            if self.femDebugLevel > 3:                
                print "Dump of Farm Mode LUT for xaui for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(x10g_base+0x10000, 16) 
                self.dump_regs_hex(x10g_base+0x100f0, 16)                               
                self.dump_regs_hex(x10g_base+0x10100, 16)
                self.dump_regs_hex(x10g_base+0x101f0, 16)  
                self.dump_regs_hex(x10g_base+0x10200, 16)
                self.dump_regs_hex(x10g_base+0x103f0, 16)
                    
            if self.femDebugLevel > 1:
                print "Dump of regs for xaui for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(x10g_base, 16)
                print "Dump of regs for Data Gen for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(data_gen_base, 16)
        
            if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_PPC_DATA_DIRECT):
                # Data with PPC ll header
                self.setup_ppc_bram(ppc_bram_base, self.tenGig0['frame_len']) 
                self.setup_10g_index_cycle(x10g_base, 3) # Use 4th word in ppc header for 10g index to port lut 
            else:
                # Data source is data generator               
                self.setup_10g_index_cycle(x10g_base, 0) # Use 1st word in gen header for 10g index to port lut   

    def reset_ppc(self, ppc_nr):
        ''' Reset ppc. Should not be called if PPC is in continuous mode '''

        #-------------------------------------------------
        # Resetting the PPC start the DMA test
        # need to get the timing right or add handshaking
                
        # Resets dma engines
        if ppc_nr == 1:
            self.toggle_bits(self.fem_ctrl_0+9, 0)
            print "Resetting PPC Nr %d.." %ppc_nr
        elif ppc_nr == 2:
            self.toggle_bits(self.fem_ctrl_0+9, 1)
            print "Resetting PPC Nr %d.." %ppc_nr
        else:
            print "WARNING No PPC Reset . Unrecognised PPC Nr  %d.." %ppc_nr
            return
        
        theDelay = self.femPpcResetDelay

        print "Waiting %s seconds.." % theDelay,
        sys.stdout.flush()
        time.sleep(theDelay)
        print "\tDone!"

    def config_data_gen(self):
        ''' Configure data generator '''                        
        data_gen_base = self.data_gen_0
                
        # Final param to enable data gen headers for farm mode
        self.setup_ll_frm_gen(data_gen_base, self.tenGig0['frame_len']/8, self.tenGig0['data_format'], self.tenGig0['num_frames']-1, 1)
        
        self.override_header_ll_frm_gen(data_gen_base, 0, 0)  # Default is not to override index nr in header
                     
    def config_asic_modules(self):
        ''' Configure asic modules '''

#########################################################        
## ASIC Parameters Setup
#########################################################        

        print "Prepare and Load ASIC Parameters"
        
        # Phase delay of sync of slow clock wrt asic reset
        self.rdmaWrite(self.fem_ctrl_0+13, self.femAsicSetupClockPhase)

        # duration of slowed down asic readout clock
        # duration (in slowed down asic clock cycles) for slow readout clock
        # each image takes ~ 480x22=1056 clocks to read out, plus allowance for setup time

        # duration (in slowed down asic clock cycles) for slow readout clock ; allow for offset extra clocks between readout strobe and data arrival and a few extra!
        #asic_slow_readout_duration = self.numberImages * self.nr_clocks_to_readout_image + self.asicRx2tileStart + 200
        #  but if using 100 mhz clock to drive bufgmux clock switch needs to be correspondingly more clock periods
        #asic_slow_readout_duration = self.asic_readout_clock_div * self.numberImages * self.nr_clocks_to_readout_image + self.asicRx2tileStart + 200

        asic_slow_readout_duration = 3000000    # Just make large value for a test
        self.rdmaWrite(self.fem_ctrl_0+12, asic_slow_readout_duration)  
 
        self.rdmaWrite(self.fem_ctrl_0+5, 0)    # Enable asic Tristate output buffers

        # Following is setting up for Asic data taking  
        # Reads new xml file with 128 asics

        # following to speed up asic loading by ignoring modules which are not present.
        module_mask  = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] 

        if self.femAsicSetupLoadMode == 1:  # Daisy chain loading of asic setup params            
            # if any asic in a module is enabled then load the whole module
            
            # femAsicEnableMask follows Christian's asic numbering scheme:          
            #   15 216 1    13 414 3    11 612 5     9 810 7   <= MOD nrs
            #[0x00000000, 0x0000FF00, 0x0000FFFF, 0x00000000]
            
            if self.femAsicEnableMask[0] & 0x000000ff != 0:
                module_mask[1-1] = 1
            if self.femAsicEnableMask[0] & 0x0000ff00 != 0:
                module_mask[16-1] = 1
            if self.femAsicEnableMask[0] & 0x00ff0000 != 0:
                module_mask[2-1] = 1
            if self.femAsicEnableMask[0] & 0xff000000 != 0:
                module_mask[15-1] = 1
            if self.femAsicEnableMask[1] & 0x000000ff != 0:
                module_mask[3-1] = 1
            if self.femAsicEnableMask[1] & 0x0000ff00 != 0:
                module_mask[14-1] = 1
            if self.femAsicEnableMask[1] & 0x00ff0000 != 0:
                module_mask[4-1] = 1
            if self.femAsicEnableMask[1] & 0xff000000 != 0:
                module_mask[13-1] = 1
            if self.femAsicEnableMask[2] & 0x000000ff != 0:
                module_mask[5-1] = 1
            if self.femAsicEnableMask[2] & 0x0000ff00 != 0:
                module_mask[12-1] = 1
            if self.femAsicEnableMask[2] & 0x00ff0000 != 0:
                module_mask[6-1] = 1
            if self.femAsicEnableMask[2] & 0xff000000 != 0:
                module_mask[11-1] = 1
            if self.femAsicEnableMask[3] & 0x000000ff != 0:
                module_mask[7-1] = 1
            if self.femAsicEnableMask[3] & 0x0000ff00 != 0:
                module_mask[10-1] = 1
            if self.femAsicEnableMask[3] & 0x00ff0000 != 0:
                module_mask[8-1] = 1
            if self.femAsicEnableMask[3] & 0xff000000 != 0:
                module_mask[9-1] = 1

        if self.femDebugLevel > 1:
            print "Loading Asic Setup Params in Modules : [%s] ..." %', '.join(map(str, module_mask)) 

#        # extract the asic params from slow xml file (once only)
        t1 = datetime.now()
        asic_setup_params = self.extract_asic_setup_params_from_xml()
        t2 = datetime.now()
        
        if self.femAsicSetupLoadMode == 1:  # Daisy chain loading of asic setup params            
            if self.femDebugLevel >= 0:
                print "INFO: Daisy chain loading of asic setup params .. takes a few seconds"
            
            for modNr in range(16): 
                if module_mask[modNr] == 1:
                    #print "Loading Asic Setup Params in Module Nr : %d " %(modNr+1) 
                    self.enable_sp3io_module(modNr) # selects which of 16 sensor modules to load
                    
                    self.config_asic_slow_xml(modNr, asic_setup_params) # Loads fem slow bram from xml file
                    
                    # load the slow params from bram into asics, put call here so settings are stable by time of first trigger
                    # ensure an asic reset is sent first so that RSYNC is sent to asic slow control block
                    self.register_set_bit(self.fem_ctrl_0+3, 8) # Configure asic sequencer to send only an asic reset  and slow strobe 
                    self.toggle_bits(self.fem_ctrl_0+0, 1)      # Start asic sequencer  
                    #self.toggle_bits(self.fem_ctrl_0+7, 0)      # alternatively just send start slow strobe (Nb this doesn't send asic reset)

            self.enable_sp3io_module(16) # make sure all modules are left enabled again (for resetting)


        else:   # parallel load

            if self.femDebugLevel >= 0:
                print "INFO: Parallel loading of asic setup params "
            
            self.enable_sp3io_module(16) # enables all 16 modules for loading
            
            self.config_asic_slow_xml(0, asic_setup_params) # Loads fem slow bram from xml file
            self.register_set_bit(self.fem_ctrl_0+3, 8) # Configure asic sequencer to send only an asic reset and slow strobe 
            self.toggle_bits(self.fem_ctrl_0+0, 1)      # Start asic sequencer  

        t3 = datetime.now()

# Switching to selected ext clock for sending Fast Commands and Readout

        if self.femDebugLevel >= 0:
            print "INFO: Switching to Selected Asic Clock source for sending Fast Commands and Readout "
        self.config_asic_clock_source()  # Clock sources
        #time.sleep(2)

        # option to downscale Asic clock for Version 1 ASIC (no longer used)                
        #self.set_asic_clock_freq(self.fem_ctrl_0, self.femAsicLocalClock)    # 0 = 100 Mhz, 1 = div clock 10 MHz

 

#########################################################        
## Asic Command Sequence Setup
#########################################################        

        print "Prepare ASIC Command Sequence"

        self.toggle_bits(self.fem_ctrl_0+11, 23)    # main reset ccc 

        if self.cccSystemMode != 0:   # if self.use_ccc_vetos == 1:

            if self.cccEmulationMode == True:

                self.register_set_bit(self.fem_ctrl_0+10, 16)  # mux select inputs from generator
                
                self.toggle_bits(self.fem_ctrl_0+11, 24)    # local reset asic_ccc_cmd_gen
                
                self.config_asic_ccc_cmd_gen()  # set up self test for emulating commands and vetos coming from xfel C&C system
                
                self.register_set_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '0' to ccc nvetos for triggers

            else:
                
                self.register_clear_bit(self.fem_ctrl_0+10, 16)  # mux select inputs from C&C system 
                
                self.register_clear_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '1' to use enabled pattern bram bits for triggers

                    
            self.toggle_bits(self.fem_ctrl_0+11, 22)    # local reset ccc local link
        
            self.config_asic_ccc_veto()
        
            self.config_asic_ccc_fast_xml() # Loads CCC fem fast bram from xml file
        else:
            if self.femDebugLevel > 1:
                print "Start OLD Fast Wrapper config_asic_fast_xml "
            self.config_asic_fast_xml() # Loads fem fast bram from xml file
            
        t4 = datetime.now()

        if self.femDebugLevel > 1:
            print "Start config_asic_datarx "
        self.config_asic_datarx()   # Set up fem to receive asic data
        t5 = datetime.now()

        #  asicrx gain selection
        if self.femAsicGainOverride:
            self.enable_femAsicGainOverride()    # Using fast cmd file commands 
        else:
            self.disable_femAsicGainOverride()   # Using S/W register

        dt12 = t2-t1
        dt23 = t3-t2
        dt34 = t4-t3
        dt45 = t5-t4
        if self.femDebugLevel >= 5:
            print "config_asic_slow_xml Timers: dt12 = %d ; dt23 = %d ; dt34 = %d ; dt45 = %d  secs" %(dt12.seconds, dt23.seconds, dt34.seconds, dt45.seconds) 
            print "config_asic_slow_xml Timers: dt12 = %d ; dt23 = %d ; dt34 = %d ; dt45 = %d  microsecs" %(dt12.microseconds, dt23.microseconds, dt34.microseconds, dt45.microseconds) 

        return


# extract all the asic params from the .xml file (just the once)
    def extract_asic_setup_params_from_xml(self):
        ''' Get Asic Setup Parameters from xml '''

        femAsicSetupParams_xmlfile = self.femAsicSetupParams

        if self.femAsicSetupLoadMode == 0:
            preambleLen = 6 # legacy 
        else:
            preambleLen = 0
        
        try:
            #TODO: Temporary hack, filename passed from API (not XML string)
            LpdAsicSetupParamsParams = LpdAsicSetupParams(femAsicSetupParams_xmlfile,
                                                          self.femAsicPixelFeedbackOverride, self.femAsicPixelSelfTestOverride,
                                                          preambleBit=preambleLen, loadMode=self.femAsicSetupLoadMode, fromFile=True) #False)
            encodedXml = LpdAsicSetupParamsParams.encode()
            
        except LpdAsicSetupParamsError as e:
            raise FemClientError(str(e))

        return encodedXml

# get the asic params for a sensor module (corresponds to bram contents)
    def config_asic_slow_xml(self, modNr, asic_setup_params):
        ''' Configure Asic Setup Parameters '''

        asic_setup_params_module = [0] * self.nr_asics_per_sensor
           
        if self.femAsicSetupLoadMode:   # 1=Serial
            adjust = modNr*8  # Increase by 8 to view next tile's ASICs (e.g. 8=Tile1's, 16=T2, 24=T3, etc)
            #TODO: Scale to use 128 ASICs when firmware is ready!
            for asic_nr in range(0 +adjust, self.nr_asics_per_sensor+adjust):
                asic_setup_params_module[asic_nr-adjust] = asic_setup_params[asic_nr]
        else:
            # 0=Parallel
            asic_setup_params_module[0] = asic_setup_params[0]
                
        no_of_bits = 3911   # includes 6 dummy bits needed at start of stream

        # Load in BRAM
        self.fem_slow_ctrl_setup(self.slow_ctr_0, self.slow_ctr_1, asic_setup_params_module, no_of_bits, self.femAsicSetupLoadMode)

        return


    def config_asic_fast_xml(self):
        ''' Configure Asic Command Sequence from xml '''

        #TODO: Temporary hack, filename passed from API (not XML string)
        fileCmdSeq = LpdAsicCommandSequence(self.femAsicCmdSequence, fromFile=True) #False)
        encodedSequence  = fileCmdSeq.encode()
        
        nr_words = fileCmdSeq.getTotalNumberWords()
        nr_nops  = fileCmdSeq.getTotalNumberNops()
                        
        if self.femDebugLevel > 1:
            print "fast cmds nr_words = %d, nr_nops =%d: " %(nr_words, nr_nops)

        # Setup the fast command block
        self.fem_fast_bram_setup(self.fast_cmd_1, encodedSequence, nr_words)
          
        if ((self.get_v5_firmware_vers()&0xffff) >= 0x0217):
            # for new CCC design must ensure the last word in bram is single command eg single NOP (not with nop loop)
            # in fem_fast_bram_setup() append a NOP cmd word to end in case the xml file has a nop loop as last entry
            # need to add 1 to no of words correspondingly            
            nr_words = nr_words + 1

        # Fill BRAM with RESET section
        self.fem_fast_cmd_setup_new(self.fast_cmd_0+6, 0, nr_words+nr_nops)
            

    def config_asic_ccc_fast_xml(self):
        ''' Configure NEW CCC with Vetos Asic Command Sequence from xml '''

# New CCC interface
# Uses 2 fast command .xml files   to program  Fast Cmd Tx module BRAM with
#   1. Start sequence ; to prepare asics for next train
#   2. Stop sequence  ; to readout asics

# read xml files to get nr of words (including nops) to load in each section of BRAM
# set control registers correspondingly
# load the BRAM sections

# christian's new mechanism with  <trigger_section>  in xml file
              
# first pass with cccEnabled=True 
# as still need to find out where trigger sequence starts even if not using vetos so that start delay can be set

        cccEna = True 
        if self.femDebugLevel > 1:
            print "--------------------- Clock and control is set to be ", cccEna, "---------------------"
        fileCmdSeqComplete = LpdAsicCommandSequence(self.femAsicCmdSequence, fromFile=True, cccEnabled=cccEna)
        encodedSequenceComplete  = fileCmdSeqComplete.encode()
        nr_wordsComplete = fileCmdSeqComplete.getTotalNumberWords()
        nr_nopsComplete  = fileCmdSeqComplete.getTotalNumberNops()
        if self.femDebugLevel > 2:
            print "nr_wordsComplete = %d, nr_nopsComplete =%d: " % (nr_wordsComplete, nr_nopsComplete)
        
        # Ask where trigger section begins 
        (initial_nops, initial_words) = (fileCmdSeqComplete.getTriggerLocation())
        if self.femDebugLevel > 2:
            print "initial_words = %d,initial_words =%d: " % (initial_words, initial_nops)
                  
        encodedSequenceStart = encodedSequenceComplete[:initial_words]
        encodedSequenceStop = encodedSequenceComplete[initial_words:]


# repeat with cccEnabled=False  only if not using ccc vetos 
        if self.cccSystemMode != 2: 

            cccEna = False          
            if self.femDebugLevel > 1:
                print "--------------------- Clock and control is set to be ", cccEna, "---------------------"
            fileCmdSeqComplete = LpdAsicCommandSequence(self.femAsicCmdSequence, fromFile=True, cccEnabled=cccEna)
            encodedSequenceComplete  = fileCmdSeqComplete.encode()
            nr_wordsComplete = fileCmdSeqComplete.getTotalNumberWords()
            nr_nopsComplete  = fileCmdSeqComplete.getTotalNumberNops()
            if self.femDebugLevel > 2:
                print "nr_wordsComplete = %d, nr_nopsComplete =%d: " % (nr_wordsComplete, nr_nopsComplete)
                      
            encodedSequenceStart = encodedSequenceComplete
                      

        if self.cccSystemMode == 2: # Read XML file but would clock and control enabled, trigger section will be omitted
            nr_wordsStart = initial_words
            nr_nopsStart = initial_nops
            nr_wordsStop = nr_wordsComplete-initial_words
            nr_nopsStop = nr_nopsComplete-initial_nops
        else:     # Read entire XML file, with clock and control disabled      
            nr_wordsStart = nr_wordsComplete
            nr_nopsStart = nr_nopsComplete
            nr_wordsStop = 2   # if 0 fast statemachine malfunctions ; so send couple of empty commands
            nr_nopsStop = 0   


        # place stop section immediately after start for most efficient use of bram
        start_offset = 0
        stop_offset = nr_wordsStart
        # lengths includes cmd words + nops encoded in loops
        start_length = nr_wordsStart + nr_nopsStart
        stop_length = nr_wordsStop + nr_nopsStop
        if self.femDebugLevel >= 3:
            print "nr_wordsStart = %d, nr_nopsStart =%d: " % (nr_wordsStart, nr_nopsStart)
            print "nr_wordsStop = %d, nr_nopsStop =%d: " % (nr_wordsStop, nr_nopsStop)
            print "start_length = %d, stop_length =%d: " % (start_length, stop_length)
        

# CCC delays after xml
# needs nr cmd words from parsing xml

#  VETO_START_DELAY = START_NWORDS* WORD_LENGTH+ START_DELAY- 2       (3.1)

        ccc_start_nwords = initial_words + initial_nops

# we know the start veto offset in self test mode as it is the
# delay from ccc cmd gen start cmd to beginning of veto pulses
# but needs measuring in the real beam
# extra fixed term for internal logic delays
        if self.cccEmulationMode == True:
            self.cccVetoStartDelay = self.CCC_CMD_GEN_XRAY_DELAY - 3
        
        self.rdmaWrite(self.ccc_delay_reg + 4, self.cccVetoStartDelay)            
        if self.femDebugLevel >= 3:
            print "ccc_veto_start_delay =%d  [$%08x]: " % (self.cccVetoStartDelay, self.cccVetoStartDelay)

# start delay to send fast cmds is then obtained from measured start veto and known nr of fast setup asic xml cmds
# extra fixed term for internal logic delays
        ccc_start_delay = self.cccVetoStartDelay - (ccc_start_nwords * self.NR_CLOCKS_PER_FAST_CMD) + 1
        if ccc_start_delay < 0 :
            print "*** ERROR: ILLEGAL C&C Start Delay  ccc_start_delay =%d: " %(ccc_start_delay)
            print "Setting  ccc_start_delay to  0 " 
            ccc_start_delay = 0
        
        self.rdmaWrite(self.ccc_delay_reg + 1, ccc_start_delay)   # start delay   
        if self.femDebugLevel >= 3:
            print "ccc_start_delay =%d  [$%08x]: " % (ccc_start_delay, ccc_start_delay)

# TESTING veto logic
  # add a fixed delay to force a stop after some specificed nr of trigger/vetos
        #nr_bunch_cmds_before_stop = self.NR_BUNCHES_IN_TRAIN 
        #self.cccStopDelay = self.cccVetoStartDelay + self.NR_CLOCKS_PER_FAST_CMD * nr_bunch_cmds_before_stop 
          
        self.rdmaWrite(self.ccc_delay_reg + 2, self.cccStopDelay)   # stop delay now from api                
        if self.femDebugLevel >= 3:
            print "ccc_stop_delay =%d: " %(self.cccStopDelay)
       
     
        # clear the bram to ensure no leftover commands from earlier runs  
        fast_bram_size = self.FAST_BRAM_SIZE_BYTES;   # size in 32b words
        self.zero_regs(self.fast_cmd_1, fast_bram_size)  

        # Load the command BRAM with Start and Stop sequences
        
        # Nb when not using ccc vetos the start section is loaded with complete command file
        start_addr = self.fast_cmd_1 + start_offset
        self.fem_fast_bram_setup(start_addr, encodedSequenceStart, nr_wordsStart)

        # stop section will be empty when using ccc vetos
        stop_addr = self.fast_cmd_1 + stop_offset
        self.fem_fast_bram_setup(stop_addr, encodedSequenceStop, nr_wordsStop)

        # for new CCC design must ensure the last word in bram is single command eg single NOP (not with nop loop)
        # in fem_fast_bram_setup() append a NOP cmd word to end in case the xml file has a nop loop as last entry
        # need to add 1 to no of words correspondingly            
        #nr_wordsStart = nr_wordsStart + 1 
        nr_wordsStop = nr_wordsStop + 1


#** Check offsets vs  extra nop added in BRAM  for start and stop

        # set up registers for START and STOP sections 
        # do this after loading the BRAM (because of extra nop on end)
        self.fem_fast_cmd_setup_new(self.fast_cmd_0+2, start_offset, start_length)
        self.fem_fast_cmd_setup_new(self.fast_cmd_0+4, stop_offset, stop_length)


    def config_asic_ccc_cmd_gen(self):
        ''' Configure CCC Command Generator ; XFEL C&C emulator '''

        if self.femDebugLevel >= 0:
            print "Set up NEW CCC XFEL Command Generator"

# 1. COMMANDS

# set up bram with XFEL C&C command words
#-- Start command '1100' + Train ID (32 bits) + Bunch Pattern Index (8 bits) + Checksum (8 bits)    
#-- lsb output first    
#-- train id = 7 
#-- bunch pattern index = 1
#-- checksum = 3
#-- packed into words using lowest 22 bits of each. 
#-- State machine outputs new data every 22 bits (one veto decision every bx) 

# start, stop and reset commands are at fixed addresses (in vhdl state machine) 

# start command 
        if self.TRAIN_ID_LENGTH == 64:
            # 64 bit train id = 0x123456780000000f
            self.rdmaWrite(self.ccc_cmd_gen_bram+0, 0x003048d1)   
            self.rdmaWrite(self.ccc_cmd_gen_bram+1, 0x00167800)   
            self.rdmaWrite(self.ccc_cmd_gen_bram+2, 0x00000003)   
            self.rdmaWrite(self.ccc_cmd_gen_bram+3, 0x00301030) 
        else:
            self.rdmaWrite(self.ccc_cmd_gen_bram+0, 0x00300000)   
            self.rdmaWrite(self.ccc_cmd_gen_bram+1, 0x00000701)   
            self.rdmaWrite(self.ccc_cmd_gen_bram+2, 0x000c0000)   
            self.rdmaWrite(self.ccc_cmd_gen_bram+3, 0x00000000)   
         
        
#-- Stop command '1010' only        
        self.rdmaWrite(self.ccc_cmd_gen_bram+4, 0x00280000)   
        #self.rdmaWrite(self.ccc_cmd_gen_bram+4, 0x00000000)  # test without stops 

#-- RESET command '1001' only        
        self.rdmaWrite(self.ccc_cmd_gen_bram+5, 0x00240000)   

#-- Veto/Nveto commands    
#-- Veto = '110' + BunchId (12 bits) + '0000'       
#-- NoVeto = '101' + BunchId (12 bits) + '0000'
#-- Golden = '111' + BunchId (12 bits) + '0000'    
#-- using lowest 22 bits of each. 
#-- State machine outputs new data every 22 bits (one veto decision every bx) 

# Example sequence  NVeto, NVeto, Veto, NVeto, Golden

        self.rdmaWrite(self.ccc_cmd_gen_bram+6, 0x00280080) # -- no veto  bx 1  
        self.rdmaWrite(self.ccc_cmd_gen_bram+7, 0x00280100) # -- no veto  bx 2
        self.rdmaWrite(self.ccc_cmd_gen_bram+8, 0x00300180) # -- veto  bx 3 
        self.rdmaWrite(self.ccc_cmd_gen_bram+9, 0x00280200) # -- no veto  bx 4  
        self.rdmaWrite(self.ccc_cmd_gen_bram+10, 0x00380280) # -- golden  bx 5   ;  total of 4 triggers  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+11, 0x00380300) #  -- golden  bx 6  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+12, 0x00300380) # -- veto  bx 7  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+13, 0x00280400) #  -- no veto  bx 8
#        self.rdmaWrite(self.ccc_cmd_gen_bram+14, 0x00280480) #  -- no veto  bx 9 
#        self.rdmaWrite(self.ccc_cmd_gen_bram+15, 0x00280500) #  -- no veto  bx 10     ;  total of 8 triggers  


##### Must also MAKE sure the Pattern BRAM contents in config_asic_ccc_veto() enable these triggers   ############


# veto command locations are set by registers for RESET start and offset

        self.rdmaWrite(self.ccc_cmd_gen_reg + 6, 6) # start corresponding to bram filling above            
        self.rdmaWrite(self.ccc_cmd_gen_reg + 7, 10)  # nr of veto/nveto cmds above            

# 2. TIMING
       
# set the delay between xfel start and arrival of pulses/vetos       

        self.rdmaWrite(self.ccc_cmd_gen_reg + 2, self.CCC_CMD_GEN_XRAY_DELAY)   # reuses redundant start offset register          

        
    def config_asic_ccc_veto(self):
        ''' Configure NEW CCC Veto patterns '''

# Patterns will eventually be read from xml file.

        if self.femDebugLevel >= 0:
            print "Set up NEW CCC Veto pattern bram config"
        # Up to 10 possible patterns can be stored in the BRAM
        # using default offsets set by f/w
                
        # Load the Veto Pattern BRAM with sequences
        # Just pattern id = 1 to start with
        pattern_offset = 0
        start_addr = self.ccc_pattern_bram + pattern_offset 

        # zero the bram so default is to allow all C&C triggers
        self.zero_regs(start_addr, self.CCC_PATTERN_VETO_BRAM_SIZE_BYTES)  

# leave the following test options in for now

        cccVetoPatternSource = "fromFile"   # "fromString" 
        
        if cccVetoPatternSource == "fromFile" or cccVetoPatternSource == "fromString":

            if cccVetoPatternSource == "fromFile":
                if self.femDebugLevel >= 2:
                    print "cccVetoPatternSource is from File: "
                # from file
                #self.cccVetoPatternFile = "Config/VetoPatterns/veto_pattern_test1.xml"
                stringCmdSeq = LpdAsicBunchPattern(self.cccVetoPatternFile, fromFile=True) #False)
            
            else:          
                if self.femDebugLevel >= 2:
                    print "cccVetoPatternSource is from TEST String: "
                # from test string
                # Command sequence definition to encode
                stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_bunch_pattern name="testCCC_xml">
                                    <veto   value="0xFFFFFFFF"/>
                                    <veto pattern="0" word="0" value="0x00000000"/>
                                    <veto pattern="0" word="2" value="0x00000000"/>
                                    <veto pattern="1"  value="0xAAAAAAAA"/>
                                </lpd_bunch_pattern>
                '''
                stringCmdSeq = LpdAsicBunchPattern(stringCmdXml)

            
            vetoPatterns = stringCmdSeq.encode()
            
            for i in range (0,self.NR_WORDS_PER_CCC_VETO_PATTERN * self.NR_CCC_VETO_PATTERNS): 
                self.rdmaWrite(start_addr+i, vetoPatterns[i])   

        else: # test with hardcoded patterns 
            if self.femDebugLevel >= 2:
                print "cccVetoPatternSource is from TEST hard coded: "
                
            # pattern 0 : all NoVeto (trigger every bunch)
            # pattern 1 : all Veto  (no triggers in train)
            # pattern 2 : to be defined
            # pattern 3 ; to be defined
            # pattern 9 ; Tests
            
            
            self.rdmaWrite(start_addr+0, 0x00000000)   # 1st word has triggers ; bit 0 corresponds to 1st bunch
            self.rdmaWrite(start_addr+1, 0xffffffff)   # 
            self.rdmaWrite(start_addr+2, 0xffffffff)   # 
            self.rdmaWrite(start_addr+3, 0xffffffff)   # 
            for i in range (4,self.NR_WORDS_PER_CCC_VETO_PATTERN):         
                self.rdmaWrite(start_addr+i, 0xffffffff)   # subsequent words are all vetos
 
        

    def config_asic_datarx(self):
        ''' Configure Asic data rx module '''
        
        # Convert femAsicEnableMask from user format into fem's format
        self.femAsicEnableMaskRemap = self.femAsicEnableCalculate(self.femAsicEnableMask)
        
        # Convert femAsicGain from user format into fem's format
        self.femAsicGainRemap = self.FEM_ASIC_GAIN_LOOKUP[self.femAsicGain]

        no_asic_cols = self.numberImages - 1
        no_asic_cols_per_frm = self.numberImages - 1  # all images will be in one LL frame
             
        # Setup the ASIC RX IP block
        self.fem_asic_rx_setup(self.asic_srx_0, self.femAsicEnableMaskRemap, no_asic_cols, no_asic_cols_per_frm)

        # NEW ; use info on nr triggers coming with readout strobe from CCC to determine how many images to process
        # this overrides asicrx register settings for ncols  etc
        if self.cccProvideNumberImages == True:
            if self.cccSystemMode == 2:
                self.register_set_bit(self.asic_srx_0+0, 12)
            else:
                print "WARNING: Not using CCC Vetos, so will readout Nr of Images set in config file"
                self.register_clear_bit(self.asic_srx_0+0, 12)
            

        # NEW ; if NOT using CCC to provide TrainID for header then insert dummy incrementing TrainID  
        if self.cccSystemMode != 2: #  if self.use_ccc_vetos == 0:
            self.toggle_bits(self.asic_srx_0+0, 17)  # reset dummy train id
            self.register_set_bit(self.asic_srx_0+0, 16)  # enable dummy train id 
        else:
            self.register_clear_bit(self.asic_srx_0+0, 16)  # disable dummy train id 

        # NEW ; insert FEM module ID into header         
        moduleId = self.femModuleId[9-1]     
        #print "FEM moduleId = %d" %moduleId
        self.rdmaWrite(self.asic_srx_0+9, moduleId)    

        # Data source - self test
        if self.femAsicDataType == self.ASIC_DATA_TYPE_RX_COUNTING:            
            self.asicrx_self_test_counting_data_enable()
        else:
            self.asicrx_self_test_counting_data_disable()

        # Asic rx gain override
        self.asicrx_override_gain(self.femAsicGainRemap)

        # Asic rx invert adc data
        if self.femInvertAdcData:
            self.asicrx_invert_data_enable()
        else:
            self.asicrx_invert_data_disable()

        # Compensate for Double Data Rate timing shifts with slowed asic readout 
        # and optional DCM in SP3IO

        if (self.sp3_io_bot_firmware_modules & 0x00000001) == 0:    # assumes f/w is same in top sp3    

            if self.femDebugLevel >= 1:
                print "Not using DCM for Clock in SP3 IO"
            
            if self.femAsicSlowedClock:
                self.register_set_bit(self.fem_ctrl_0+8, 1)    # enable Swap DDR pair of asicrx  
                self.register_clear_bit(self.fem_ctrl_0+8, 0)    # disable timing shift of odd asic rx
            else:
                self.register_set_bit(self.fem_ctrl_0+8, 0)    # disable Swap DDR pair of asicrx  
                self.register_clear_bit(self.fem_ctrl_0+8, 1)    # enable timing shift of odd asic rx

# assign local variable here rather than using self.asicRx2tileStart as latter's state is kept between Gui configures
            asicRx2tileStart_i =  self.asicRx2tileStart;  # adjustment for SP3 IO DCM
              
        else: # with DCM in SP3 IO

            if self.femDebugLevel >= 1:
                print "Using DCM for Clock in SP3 IO"
            
            self.register_set_bit(self.fem_ctrl_0+8, 1)    # enable Swap DDR pair of asicrx  
            
            self.register_clear_bit(self.fem_ctrl_0+8, 0)    # disable timing shift of odd asic rx
                
# assign local variable here rather than using self.asicRx2tileStart as latter's state is kept between Gui configures
            asicRx2tileStart_i =  self.asicRx2tileStart - 1;  # adjustment for SP3 IO DCM
        
        if ( (self.rdmaRead(self.fem_ctrl_0+18, 1)[0] & 0x00000080 != 0 ) or (self.get_v5_firmware_vers()&0xffff) == 0x024c ):  # with CCC 
            asicRx2tileStart_i -= 1


        # Delay individual sensors
        self.set_delay_sensors(self.femDelaySensors)     
        
        if self.femAsicDataType == self.ASIC_DATA_TYPE_PSEUDO_RANDOM:
            asic_rx_start_delay = self.asicRxPseudoRandomStart
        else:
            if self.femAsicModuleType == self.ASIC_MODULE_TYPE_SINGLE_ASIC:
                asic_rx_start_delay = self.asicRxSingleStart
            else:
                if self.femAsicSlowedClock:
                    #TODO: Still testing?
                    # Testing timing difference with slowed down readout
                    asic_rx_start_delay = asicRx2tileStart_i - 2
                else:
                    asic_rx_start_delay = asicRx2tileStart_i

            if self.femAsicVersion == 2:        # Enable this for asic v2 timing (v2 has no header)
                asic_rx_start_delay = asic_rx_start_delay - self.asicRxHeaderBits
            elif self.femAsicSlowedClock:       # Following offsets skip 1st row of pixels
# nb gain selection algorithm can't work with slowed readout as samples from same pixel are no longer contiguous
                if self.femAsicGainRemap == 8:
                    asic_rx_start_delay = asic_rx_start_delay + self.asicRxOffsetSlowReadout_x100
                elif self.femAsicGainRemap == 9:
                    asic_rx_start_delay = asic_rx_start_delay + self.asicRxOffsetSlowReadout_x10
                elif self.femAsicGainRemap == 11:
                    asic_rx_start_delay = asic_rx_start_delay + self.asicRxOffsetSlowReadout_x1

# !!!!!! TESTING ONLY
        # adjust capture point start to Nth image
        #asic_rx_start_delay = asic_rx_start_delay + 0 * self.nr_clocks_to_readout_image

        if self.femDebugLevel > 1:
            print "asic_rx_start_delay = %s " % asic_rx_start_delay
        
        if self.femAsicRxCmdWordStart:
            self.rdmaWrite(self.fem_ctrl_0+14, asic_rx_start_delay) # NEW using strobe from fast command file         
        else:
            self.rdmaWrite(self.fem_ctrl_0+4, asic_rx_start_delay)  # OLD using fixed offsets          

    def bitShifting(self, arg1, direction):
        ''' Bit shift "arg1" by "direction" bits (positive = left shifting, negative = right shifting) '''
        if direction > 0:
            newValue = arg1 << direction
        else:
            newValue = arg1 >> (direction* -1)
        return newValue

    def femAsicEnableCalculate(self, userMask):
        '''  Convert user's femAsicEnableMask selection into fem's own format
            e.g.
                user format: [0] = ASIC1-ASIC32, [1] = 33-64, etc (where 0x1=ASIC1,  0x2=ASIC2, etc)
                fem format:  [0] = ASIC1-4, 17-20, 33-37, etc; [1] = ASIC5-8, 21-24, ..
        '''
        femMask = [0x0, 0x0, 0x0, 0x0]

        bitMask = 0x0000000F
        direction = 28
        maskIndex = 0
        
        for index in range(8):
            maskedValue     = userMask[0] & bitMask
            shifted         = self.bitShifting( maskedValue, direction)
            femMask[maskIndex] = (femMask[maskIndex] | shifted)
            # Update counters
            if index % 7 == 3:
                direction -= 8
            else:
                direction -= 4
            if maskIndex == 3:
                maskIndex = 0
            else:
                maskIndex += 1
            bitMask = bitMask << 4
            
        bitMask = 0x0000000F
        direction = 20
        maskIndex = 0
        
        for index in range(8):
            maskedValue     = userMask[1] & bitMask
            shifted         = self.bitShifting( maskedValue, direction)
            femMask[maskIndex] = (femMask[maskIndex] | shifted)
            # Update counters
            if index % 7 == 3:
                direction -= 8
            else:
                direction -= 4
            if maskIndex == 3:
                maskIndex = 0
            else:
                maskIndex += 1
            bitMask = bitMask << 4
    
        bitMask = 0x0000000F
        direction = 12
        maskIndex = 0
        
        for index in range(8):
            maskedValue     = userMask[2] & bitMask
            shifted         = self.bitShifting( maskedValue, direction)
            femMask[maskIndex] = (femMask[maskIndex] | shifted)
            # Update counters
            if index % 7 == 3:
                direction -= 8
            else:
                direction -= 4
            if maskIndex == 3:
                maskIndex = 0
            else:
                maskIndex += 1
            bitMask = bitMask << 4
    
        bitMask = 0x0000000F
        direction = 4
        maskIndex = 0
        
        for index in range(8):
            maskedValue     = userMask[3] & bitMask
            shifted         = self.bitShifting( maskedValue, direction)
            femMask[maskIndex] = (femMask[maskIndex] | shifted)
            # Update counters
            if index % 7 == 3:
                direction -= 8
            else:
                direction -= 4
            if maskIndex == 3:
                maskIndex = 0
            else:
                maskIndex += 1
            bitMask = bitMask << 4

        if self.femDebugLevel > 2:
            print "userMask => femMask"
            print "==================="
            for idx in range(4):
                print  "%8X    %8X" % (userMask[idx], femMask[idx])
        return femMask

    def send_trigger(self):
        ''' Send triggers '''

        #--------------------------------------------------------------------
        # Send triggers to data generators
        #--------------------------------------------------------------------

        if self.femDataSource == self.RUN_TYPE_LL_DATA_GEN:            
            print "Trigger Data Gen"
            self.toggle_bits(self.fem_ctrl_0+0, 0)                          # Trigger to local link frame gen 
        elif (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_ASIC_DATA_DIRECT):             
            if self.femAsicDataType == self.ASIC_DATA_TYPE_PSEUDO_RANDOM:   # Needs asicrx strobe 
                print "Trigger ASIC_DATA_TYPE_PSEUDO_RANDOM"
                self.register_clear_bit(self.fem_ctrl_0+3, 8)               # Configure asic sequencer to send all strobes              
                self.toggle_bits(self.fem_ctrl_0+0, 1)                      # Start asic seq  = reset, slow, fast & asicrx  
            else:
                if self.cccSystemMode != 0:  

                    if self.cccEmulationMode == True:
                        if self.femDebugLevel > 2:
                            print "Sending CCC Start and Vetos using C&C System EMULATION  CCC Cmd Gen"
                        self.toggle_bits(self.fem_ctrl_0+10, 10)  # ccc start bypass  , vetos follow after programmed delay
                        #self.toggle_bits(self.fem_ctrl_0+10, 11)  # ccc stop bypass
                    else:
                        if self.femDebugLevel > 2:
                            print "Sending CCC Start and Stop in RX BYPASS"
                        self.toggle_bits(self.fem_ctrl_0+10, 8)  # ccc start Rx bypass
                        self.toggle_bits(self.fem_ctrl_0+10, 9)  # ccc stop Rx bypass
                else:
                    self.toggle_bits(self.fem_ctrl_0+7, 1)  # Asic seq without slow or asicrx strobe (slow params are loaded once only during configutation) 
        else:
            print "Warning undefined Trigger Asic"
                    
    def dump_registers(self):
        ''' Dump registers '''
        
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
        self.dump_regs_hex(self.fast_cmd_1, 32)
        #self.dump_regs_hex(self.fast_cmd_1+(self.FAST_BRAM_SIZE_BYTES*4)-16, 30) # deliberately looking beyond end of physical BRAM

        print "Dump of FEM Registers : ASIC SLOW CTRL"
        self.dump_regs_hex(self.slow_ctr_0, 18)

        print "Dump of FEM Registers : ASIC SLOW BRAM"
        self.dump_regs_hex(self.slow_ctr_1, 1024)   # 1024

        print "Dump of Ext Trigger Strobe Registers : TRIG STROBE"
        self.dump_regs_hex(self.trig_strobe, 20)

        print "Dump of FEM Registers : BOT SP3 CTRL"
        try:
            self.dump_regs_hex(self.bot_sp3_ctrl, 20)
        except FemClientError:
            print "WARNING: BOT SP3 dump_regs_hex failed"

        print "Dump of FEM Registers : TOP SP3 CTRL"
        try:
            self.dump_regs_hex(self.top_sp3_ctrl, 20)
        except FemClientError:
            print "WARNING: TOP SP3 dump_regs_hex failed"

        print "Dump of FEM Registers : CFG SP3 CTRL"
        try:
            self.dump_regs_hex(self.cfg_sp3_ctrl, 18)
        except FemClientError:
            print "WARNING: CFG SP3 dump_regs_hex failed"

    def fem_slow_ctrl_setup(self, base_addr_0, base_addr_1, dataTuple, no_of_bits, load_mode):
        ''' Slow control set up function '''

        #return
        t1 = datetime.now()

        # Asic Setup Parameters load mode (0 = parallel, 1 = daisy chain)
        # fixed jac ; bit 1 is load mode select  ; bit 0 is a s/w trigger to start loading 
        if load_mode == 1:
            self.register_set_bit(base_addr_0+0, 1)
        else:
            self.register_clear_bit(base_addr_0+0, 1)  
        
        if load_mode == 0:  # parallel load same in all 8 asics (and same in all sensor modules)     
            #print "Slow Ctrl RAM"
            self.rdmaWrite(base_addr_1, dataTuple[0])

            # clear bram after data
            data_len = len(dataTuple[0])
            rem_len = 20 # just clear a few locations beyond last valid data
            self.zero_regs(self.slow_ctr_1+data_len, rem_len)
            #print 'slow dataTuple len = %d : rem_len = %d' %(data_len, rem_len)

        else:
            # TESTING daisy chain loading
            # only 1 xml file is implemented so far so just same slow params in all asic blocks
            
            # slow bit block for 1st asic needs 6 dummy bits at the start
            # these need to be removed from any subsequent asic blocks 
            
            # New implementation in python script:
            # Translate 32bit values from .xml parsing  into "bit" lists of 0's and 1's
            # Manipulate these lists using list functions. Eg concatenate lists with list.extend, remove bits
            # Then convert back to 32bit words for loading in bram
            # Much easier using python lists than trying to make it like c style bit fields !
            
            # note that Asic8 data is filled first in BRAM as this needs to get shifted to last asic in chain
            
            asic_params = [0] * self.nr_asics_per_sensor
            
            for asic_nr in range(0, self.nr_asics_per_sensor): 
                asic_params[asic_nr] = list() 
            
                #asic_1 = list()
                # convert to list of bits for manipulation
                asic_params[asic_nr] = self.convert_to_bitlist(dataTuple[asic_nr])
            
                # remove unused bits in last word         
                del asic_params[asic_nr][-(32-1):]    # assumes no preamble 6 bits
            
                #print str(asic_1)[1:-1]
                #for i in range(0,len(asic_1)):          
                #  print 'i = %d ; asic_1[i] = %d ' %(i, asic_1[i])  
            
            t2 = datetime.now()

            # prepend initial 6 preamble dummy bits to 1st asic block only 
            # as xml file is readin without preamble data now
            asic_daisy_chain = list(asic_params[0]) 
            for i in range(6):
                asic_daisy_chain.insert(0,0)

            # add remaining asic blocks in chain
            for asic_nr in range(1, self.nr_asics_per_sensor):
                asic_daisy_chain.extend(asic_params[asic_nr])
            
            # back to format that can be loaded in bram          
            packedbits = self.convert_to_packedbits(asic_daisy_chain)
            #print 'packedbits len = %d ' %len(packedbits)
            
            #for i in range(0,len(packedbits)):          
            #  print 'i = %d ; packedbits = %08x ' %(i, packedbits[i])  

            t3 = datetime.now()               
            #self.zero_regs(base_addr_1, len(packedbits))  

            t4 = datetime.now()
            self.rdmaWrite(base_addr_1, packedbits)
            
            # clear bram after data
            #data_len = len(packedbits)
            #rem_len = 20 # just clear a few locations beyond last valid data
            #self.zero_regs(self.slow_ctr_1+data_len, rem_len)  
        
            # load control registers
            t5 = datetime.now()

            dt12 = t2-t1
            dt23 = t3-t2
            dt34 = t4-t3
            dt45 = t5-t4
            #print "fem_slow_ctrl_setup Timers: dt12 = %d ; dt23 = %d ; dt34 = %d ; dt45 = %d  secs" %(dt12.seconds, dt23.seconds, dt34.seconds, dt45.seconds) 
            #print "fem_slow_ctrl_setup Timers: dt12 = %d ; dt23 = %d ; dt34 = %d ; dt45 = %d  microsecs" %(dt12.microseconds, dt23.microseconds, dt34.microseconds, dt45.microseconds) 
        
        # set number of bits register
        max_no_of_bits = 32*1024
        if no_of_bits > max_no_of_bits:
            no_of_bits = max_no_of_bits

        if load_mode == 1:   
            # daisy chain multiple asics; only 1st asic block needs the 6 dummy bits   
            no_of_bits = no_of_bits + (self.nr_asics_per_sensor-1) * (no_of_bits - 6) 

        no_of_bits    = no_of_bits + 1    # keep fix added  jac
        control_reg_1 = base_addr_0 + 1
        
        self.rdmaWrite(control_reg_1, no_of_bits)


    
    
    def convert_to_bitlist(self, dataTuple):
        ''' Convert tuple of slow bit patterns to list '''
    
        bitList = list()

        for i in range(0,len(dataTuple)):          
            #print 'i = %d ; dataTuple = %08x ' %(i, dataTuple[i])  
            for j in range(0,32):
                if (dataTuple[i] & 1<<j):
                    bitList.append(1)
                else:
                    bitList.append(0)
        return bitList        

    def convert_to_packedbits(self, bitList):
        ''' Convert list back to slow bit patterns for loading to bram '''

        packedbits = list()
        
        #print ' len bitList = %d ' %(len(bitList))
        for i in range(0,len(bitList)): 
            if i%32 == 0:
                packedbits.append(0)
            packedbits[i/32] |= bitList[i] << (i%32) 
            #print 'i = %d ; bitList[i] = %d ; packedbits[i/32] = %08x ' %(i, bitList[i], packedbits[i/32])  
            
        return packedbits  

    def fem_fast_bram_setup(self, base_addr_1, fast_cmd_data, nr_words):
        ''' Fast cmd set up function '''
        
        if ((self.get_v5_firmware_vers()&0xffff) >= 0x0215):
            self.FAST_BRAM_SIZE_BYTES = 2048
        else:
            self.FAST_BRAM_SIZE_BYTES = 1024
        #print "Fast BRAM size = %d bytes" %self.FAST_BRAM_SIZE_BYTES
        
        # Check length is not greater than FPGA Block RAM
        
        block_length = nr_words
        if block_length > self.FAST_BRAM_SIZE_BYTES:
            raise FemClientError("**WARNING** fem_fast_bram_setup : block_length = %d  nr commands exceeds max memory size. Please correct command sequence XML file" % block_length)
            #block_length =  self.FAST_BRAM_SIZE_BYTES
        
        # Build tuple of a list of data
        dataTuple = tuple([fast_cmd_data[i] for i in range(block_length)])
        
        if ((self.get_v5_firmware_vers()&0xffff) >= 0x0217):
            # for new CCC design must ensure the last word in bram is single command eg single NOP (not with nop loop)
            # so just append a NOP cmd word to end in case the xml file has a nop loop as last entry
            extra_cmd = (0x00000000,) 
            dataTuple = dataTuple + extra_cmd
            
        # Load command sequence pattern memory
        self.rdmaWrite(base_addr_1, dataTuple)    # Assumes using later PPC GbE server code which can handle large dataTuples

    def fem_fast_cmd_setup_new(self, section_addr, offset, nr_words):
        ''' Asic Command Sequence set up function '''
    
        # load control registers
        # reset mode  for old behaviour outputting bram , without vetos

        if self.femDebugLevel > 2:
            print "fem_fast_cmd_setup_new : section_addr = $%08x , offset = %d, nr_words =%d: " % (section_addr, offset, nr_words)
    
        self.rdmaWrite(section_addr,   offset)      # offset
        self.rdmaWrite(section_addr+1, nr_words)    # nwords (including nops)

    def fem_asic_rx_setup(self, base_addr, mask_array, no_asic_cols, no_cols_frm):
        ''' Setup the XFEL FEM ASIC RX IP Block '''
         
        # Setup IP Address register locations
        mask_reg0 = (0x00000004 | base_addr)
        mask_reg1 = (0x00000005 | base_addr)
        mask_reg2 = (0x00000006 | base_addr)
        mask_reg3 = (0x00000007 | base_addr)
         
        no_clk_cyc_dly_reg        = (0x00000002 | base_addr)
        no_asic_cols_cols_frm_reg = (0x00000003 | base_addr)
         
        # Setup data values
        no_asic_cols          = (no_asic_cols & 0x0000001FF)
        no_cols_frm           = (no_cols_frm & 0x0000001FF)
        no_cols_frm_shft      = (no_cols_frm << 16)
        no_asic_cols_cols_frm = (no_cols_frm_shft | no_asic_cols)

        if self.numberImages == 1:  # FIX for special case if only capturing ONE image
            no_asic_cols_cols_frm = 0x00010000

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
                  
        # Setup Asic rx clk cycle delay
        self.rdmaWrite(no_clk_cyc_dly_reg, no_clk_cyc_dly)
        
        # Setup num asic cols & num cols per frame
        self.rdmaWrite(no_asic_cols_cols_frm_reg,no_asic_cols_cols_frm)
   
        # Setup mask registers
        self.rdmaWrite(mask_reg0,mask_array[0])        # asic rx 0
        self.rdmaWrite(mask_reg1,mask_array[1])        # asic rx 1
        self.rdmaWrite(mask_reg2,mask_array[2])        # asic rx 2
        self.rdmaWrite(mask_reg3,mask_array[3])        # asic rx 3
        
    def asicrx_self_test_counting_data_enable(self):
        ''' Enable internal counting data '''
        reg_addr = self.asic_srx_0+1
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | 0x00000001
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_self_test_counting_data_disable(self):
        ''' Disable internal counting data '''
        reg_addr = self.asic_srx_0+1
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value & ~0x00000001
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_invert_data_enable(self):
        ''' Invert data by subtracting value from 0xFFF '''
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value | 0x00000100
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_invert_data_disable(self):
        ''' Do not invert data '''
        reg_addr = self.asic_srx_0+0
        prev_value = self.rdmaRead(reg_addr, 1)[0] 
        new_value = prev_value & ~0x00000100
        self.rdmaWrite(reg_addr, new_value)

    def asicrx_override_gain(self, femAsicGainRemap):
        # added override to gain selection 
        # 
        #  bits
        #  0000  normal gain selection     0
        #  1000  force select x100         8
        #  1001  force select x10          9
        #  1011  force select x1          11
        #  1111  force error condition ?  15
        gain_select = self.femAsicGainRemap
        reg_addr    = self.asic_srx_0+0
        prev_value  = self.rdmaRead(reg_addr, 1)[0] 
        new_value   = prev_value | (gain_select & 0x0000000f)
        self.rdmaWrite(reg_addr, new_value)

    def soft_reset_ll_frm_gen(self, base_address):
        ''' Reset the frame number in the header '''
        # Data Generator soft reset
        self.rdmaWrite(base_address+0,0x00000000)    
        self.rdmaWrite(base_address+0,0x00000001)
        self.rdmaWrite(base_address+0,0x00000000)        

    def start_10g_link(self):
        ''' Start a 10g link '''

        if self.femDebugLevel > 5:
            print "Start 10G link nr", self.tenGig0['link_nr']

        data_gen_base = self.data_gen_0
      
        time.sleep(self.tenGig0['delay'])   # Wait before trigger

        if self.femDataSource == self.RUN_TYPE_LL_DATA_GEN: # ll data gen
          
            # Check last cycle has completed                
            gen_busy  = self.status_ll_frm_gen(data_gen_base) 
            i = 0

            while gen_busy == 1:
                i=i+1
                print "Waiting to Trigger Next Cycle : 10G link nr %2d is BUSY ; waiting %d secs" % (self.tenGig0['link_nr'], i),
                sys.stdout.flush() 
                time.sleep(1)                    
                gen_busy = self.status_ll_frm_gen(data_gen_base) 

        if self.tenGig0['data_gen'] == 1:
            # Give a soft reset to reset the frame nr in the headers (resets the the ip port nr)
            # don't do this any earlier or won't trigger
            self.soft_reset_ll_frm_gen(data_gen_base)  
            print "Trigger LL Data Gen"
            self.toggle_bits(self.fem_ctrl_0+0, 0)   
 
    def start_dma_tx(self, base_addr, index):
        ''' Start dma tx '''
        self.rdmaWrite(base_addr+9, index) 
        self.rdmaWrite(base_addr+8, 0x1234) 
    
    def final_dma_tx(self, base_addr):
        ''' Flag last dma tx '''
        self.rdmaWrite(base_addr+10, 0x5678) 

    #TODO: No longer used?
    def prev_dma_tx(self, base_addr):
        '''  '''  
        busy = 1
        reg = self.rdmaRead(base_addr+8, 1) [1]
        reg &= 0x0000ffff
        if reg == 0:
            busy = 0
        return busy
 
    def ppc_readout_ready_status(self, base_addr):
        ''' Check whether PPC reset completed '''  
        ready = 0
        
        reg = self.rdmaRead(base_addr+12, 1) [0]
        reg &= 0xffffffff
       
        if reg == 0xFACEFACE:
            ready = 1
        return ready

    def zero_regs(self, base_addr, nr_regs):
        ''' Zero regs eg bram '''
        
        #for i in range(0, nr_regs):
        #    self.rdmaWrite(base_addr+i, 0)

# Use block rdma write which should be much faster
        zero_lst = []
        for i in range(nr_regs):
            zero_lst.append(0)
        self.rdmaWrite(base_addr, zero_lst) 

    def fill_regs(self, base_addr, nr_regs, value):
        ''' Fill regs with fixed value eg bram '''
        
# Use block rdma write which should be much faster
        reg_lst = []
        for i in range(nr_regs):
            reg_lst.append(value)
        self.rdmaWrite(base_addr, reg_lst) 

    def register_set_bit(self, reg_addr, bit_nr):
        ''' Set bit in register '''
        prev_value = self.rdmaRead(reg_addr, 1)[0]  
        on = prev_value | (1 << bit_nr)
        self.rdmaWrite(reg_addr, on)
 
    def register_clear_bit(self, reg_addr, bit_nr):
        ''' Set bit in register '''
        prev_value = self.rdmaRead(reg_addr, 1)[0]  
        off = prev_value & ~(1 << bit_nr)
        self.rdmaWrite(reg_addr, off)

    def status_ll_frm_gen(self, base_address):
        ''' Return busy status of data gen '''
        busy = self.rdmaRead(base_address+17, 1)[0]  
        return busy        

    # new functions for LCLS and Petra beam tests

    def enable_ext_trig_strobe(self):
        ''' Enables acceptance of external trigger strobes '''
        self.register_set_bit(self.fem_ctrl_0+11, 8)  

    def disable_ext_trig_strobe(self):
        ''' Disables acceptance external trigger strobes '''
        self.register_clear_bit(self.fem_ctrl_0+11, 8)  

    def set_ext_trig_strobe_delay(self, value):
        ''' Sets the delay of ext trigger strobe (in nr asic clock periods e.g. 10 nsec for xfel) '''
        self.rdmaWrite(self.trig_strobe+2, value)  

    def get_ext_trig_strobe_delay(self):
        ''' Returns the delay of ext trigger strobe (in nr asic clock periods e.g. 10 nsec for xfel) '''
        return self.rdmaRead(self.trig_strobe+2, 1)[0]  

    def set_ext_trig_strobe_inhibit(self, value):
        ''' Gets the length of inhibit preventing further readout after an ext trigger strobe (in nr asic clock periods e.g. 10 nsec for xfel) '''
        self.rdmaWrite(self.trig_strobe+3, value)  

    def get_ext_trig_strobe_inhibit(self):
        ''' Gets the length of inhibit preventing further readout after an ext trigger strobe (in nr asic clock periods e.g. 10 nsec for xfel) '''
        return self.rdmaRead(self.trig_strobe+3, 1)[0]  

    def get_ext_trig_strobe_count(self):
        ''' Gets the count nr of ext trigger strobes received (incl those inhibited) [READONLY] '''
        return self.rdmaRead(self.trig_strobe+17, 1)[0]

    def get_ext_trig_strobe_accepted_count(self):
        ''' Gets the count nr of ext trigger strobes accepted i.e. not inibited [READONLY] '''
        return self.rdmaRead(self.trig_strobe+18, 1)[0]

    def get_v5_firmware_vers(self):
        ''' Gets the firmware version loaded in main V5 FPGA [READONLY]   '''
        return self.rdmaRead(self.fem_ctrl_0+17, 1)[0]

    def get_bot_sp3_firmware_vers(self):
        ''' Gets the firmware version loaded in BOT SP3 FPGA [READONLY]   '''
        value = -1
        try:
            value = self.rdmaRead(self.bot_sp3_ctrl+17, 1)[0]
        except FemClientError:
            print "WARNING: BOT SP3 Firmware version read failed"
        return value

    def get_top_sp3_firmware_vers(self):
        ''' Gets the firmware version loaded in TOP SP3 FPGA [READONLY]   '''
        value = -1
        try:
            value = self.rdmaRead(self.top_sp3_ctrl+17, 1)[0]
        except FemClientError:
            print "WARNING: TOP SP3 Firmware version read failed"
        return value

    def get_cfg_sp3_firmware_vers(self):
        ''' Gets the firmware version loaded in CFG SP3 FPGA [READONLY]   '''
        value = -1
        try:
            value = self.rdmaRead(self.cfg_sp3_ctrl+17, 1)[0]
        except FemClientError:
            print "WARNING: CFG SP3 Firmware version read failed"
        return value

    def set_ext_trig_strobe_max(self, value):
        ''' Sets the nr of ext strobes to trigger readout '''
        self.rdmaWrite(self.trig_strobe+4, value)

    def get_ext_trig_strobe_max(self):
        ''' Returns the nr of ext strobes to trigger readout '''
        return self.rdmaRead(self.trig_strobe+4, 1)[0]

    def set_ext_trig_strobe_polarity(self, value):
        ''' Selects ext trigger strobe polarity '''
        if value == 0:
            self.register_set_bit(self.fem_ctrl_0+11, 9)
        else:
            self.register_clear_bit(self.fem_ctrl_0+11, 9)

    def set_delay_sensors(self, value):
        ''' Delays timing of 16 sensors; bit = 1 adds 1 clock delay; lsb = sensor tile 1;  '''
        self.rdmaWrite(self.fem_ctrl_0+15, value)
 
    def get_delay_sensors(self):
        ''' Returns delays timing of 16 sensors ; bit = 1 adds 1 clock delay ; lsb = sensor tile 1;'''
        return self.rdmaRead(self.fem_ctrl_0+15, 1)[0]

    def enable_femAsicGainOverride(self):
        ''' Enables gain selection using fast commands '''
        self.register_set_bit(self.fem_ctrl_0+11, 20)

    def disable_femAsicGainOverride(self):
        ''' Disables gain selection using fast commands '''
        self.register_clear_bit(self.fem_ctrl_0+11, 20)  

    def enable_petra_trig_strobe(self):
        ''' Enables trigger strobes for PetraIII (derived from Petra clock) '''
        self.register_set_bit(self.fem_ctrl_0+11, 12 )

    def disable_petra_trig_strobe(self):
        ''' Disables trigger strobes for PetraIII '''
        self.register_clear_bit(self.fem_ctrl_0+11, 12)  

    def set_petra_shutter_polarity(self, value):
        ''' Selects ext trigger strobe polarity '''
        if value == 0:
            self.register_set_bit(self.fem_ctrl_0+11, 10)
        else:
            self.register_clear_bit(self.fem_ctrl_0+11, 10)

    def use_petra_shutter(self, value):
        ''' Option to ignore the shutter for PetraIII '''
        if value == 0:
            self.register_clear_bit(self.fem_ctrl_0+11, 11)
        else:
            self.register_set_bit(self.fem_ctrl_0+11, 11)   # ignore shutter

    def is_petra_shutter_ignored(self):
        ''' Is the shutter for PetraIII ignored '''
        return ((self.rdmaRead(self.fem_ctrl_0+11, 1)[0] & 0x800) != 0)

    def config_sp3io_top(self):   
        ''' Configure SP3 IO TOP '''

        self.rdmaWrite(self.top_sp3_ctrl+0, 0xff)  # enable ctrl_reg_en and reset signals on all 8 sensor tiles

    def config_sp3io_bot(self):   
        ''' Configure SP3 IO BOT '''

        self.rdmaWrite(self.bot_sp3_ctrl+0, 0xff)  # enable ctrl_reg_en and reset signals on all 8 sensor tiles 

    def enable_sp3io_module(self, modNr):   
        ''' Select module on SP3 IO TOP or BOT. modNr = 16 to enable all 16 modules '''

#-------------------------------
#    FPGA    | Sensor Module   |
#    mod<N>  |    Top  | Bot   |
#-------------------------------
#    <0>     |    1    |  5    |
#    <1>     |    2    |  6    |
#    <2>     |    3    |  7    |
#    <3>     |    4    |  8    |
#    <4>     |    16   |  12   |
#    <5>     |    15   |  11   |
#    <6>     |    14   |  10   |
#    <7>     |    13   |  9    |
#-------------------------------

# as IO signals are always sent to BOTH top and bot simultaneously must take care to disable the unwanted fpga

        modNr += 1            # to match physical numbering

        # map module number to numbering within fpgas 
        # Nb module nr running from 1 to 16    
        fpga_index = [99,0,1,2,3,0,1,2,3,7,6,5,4,7,6,5,4,99]   # from table above
        val = 1 << fpga_index[modNr]
 
        if ((modNr >= 1 and modNr <= 4) or (modNr >= 13 and modNr <= 16)):    # top
            self.rdmaWrite(self.top_sp3_ctrl+0, val)  # enable ctrl_reg_en and reset signals
            self.rdmaWrite(self.bot_sp3_ctrl+0, 0x0)  # ensure bot is disabled when enabling top modules
        elif (modNr >= 5 and modNr <= 12):    # bot
            self.rdmaWrite(self.bot_sp3_ctrl+0, val)  # enable ctrl_reg_en and reset signals
            self.rdmaWrite(self.top_sp3_ctrl+0, 0x0)  # ensure top is disabled when enabling bot modules
        else: # parallel load
            self.rdmaWrite(self.top_sp3_ctrl+0, 0xff)  # enable ctrl_reg_en and reset signals on all 8 sensor tiles
            self.rdmaWrite(self.bot_sp3_ctrl+0, 0xff)  # enable ctrl_reg_en and reset signals on all 8 sensor tiles 

        #print "enable_sp3io hw modnr = %d , fpga index = %d , val = $%08x" %(modNr, fpga_index[modNr], val)
        return

    def get_asic_clock_status(self):   
        ''' Get status of clock being sent to ASICs (DCM Lock) '''

        if ((self.get_v5_firmware_vers()&0xffff) >= 0x0216):            
            status = self.rdmaRead(self.fem_ctrl_0+24, 1)[0]
            return (status & 0x1)
        else:   # earlier versions of f/w without clock status info
            return 1

    def get_petra_shutter_status(self):   
        ''' Get status of petra shutter (after any inversion) '''

        if ((self.get_v5_firmware_vers()&0xffff) >= 0x0216):            
            status = self.rdmaRead(self.fem_ctrl_0+24, 1)[0]
            return (status & 0x100)
        else:   # earlier versions of f/w without clock status info
            return 1
        

    '''
        --------------------------------------------------------
        Rationalised various bits of jac's code into standalone functions
        --------------------------------------------------------
    '''

    def send_long_asic_reset(self):
        ''' Send Long Reset to ASIC pin '''
        self.register_set_bit(self.fem_ctrl_0+10, 0)  
        #time.sleep(self.femPpcResetDelay)  # register access is long enough delay!
        self.register_clear_bit(self.fem_ctrl_0+10, 0)  
    
    def resetFwModulesToggleTristateIO(self):
        ''' Reset firmware modules, disable and re-enable tri-state asic i/o '''
        # Reset f/w modules (resets asicrx counters, but also disables tristate outputs to asic fast and slow lines)
        self.toggle_bits(self.fem_ctrl_0+9, 8)  # async reset to v5 top level
        # Re-enable v5 tristate i/o to asic 
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

        print "=======================================================================" 
  
        self.pp = pprint.PrettyPrinter(indent=4)

        print "     V5 FPGA Firmware vers = %08x" % self.get_v5_firmware_vers()
        print "BOT SP3 FPGA Firmware vers = %08x" % self.get_bot_sp3_firmware_vers()
        print "TOP SP3 FPGA Firmware vers = %08x" % self.get_top_sp3_firmware_vers()
        print "CFG SP3 FPGA Firmware vers = %08x" % self.get_cfg_sp3_firmware_vers()
        print "=======================================================================" 

        if self.get_top_sp3_firmware_vers() != self.get_bot_sp3_firmware_vers() :
            print "*** WARNING:  Firmware Versions in SP3 IO TOP and BOTTOM are Different" 

        femAsicClockSourceNames = { 0 : "On board 100MHz Osc",
                                    1 : "XFEL C&C",
                                    2 : "Petra-III",
                                    3 : "Diamond B16"
                                    }
        
        femStartTrainSourceNames = { 0 : "XFEL C&C",
                                    1 : "Software",
                                    2 : "LCLS",
                                    3 : "Petra-III",
                                    4 : "Diamond B16"
                                    }
        
        femAsicDataTypeNames = { 0 : "Asic Data",
                                 1 : "Counting Data",
                                 2 : "PseudoRandom Asic Data"
                                  }
                                  
        femAsicModuleTypeNames = { 0 : "Supermodule",
                                   1 : "Single ASIC",
                                   2 : "2-Tile System",
                                   3 : "stand-alone"
                                  }
                                  
        cccSystemModeNames = { 0 : "Not using XFEL C&C system",
                              1 : "XFEL C&C for Start command but not using veto system",
                              2 : "Full XFEL C&C with veto system"
                                  }
        
        print "femAsicClockSource  = %s" % femAsicClockSourceNames[self. femAsicClockSource]
        print "femStartTrainSource = %s" % femStartTrainSourceNames[self.femStartTrainSource]
        print "femAsicModuleType   = %s" % femAsicModuleTypeNames[self.femAsicModuleType]
        print "femAsicDataType     = %s" % femAsicDataTypeNames[self.femAsicDataType]
        print "cccSystemMode       = %s" % cccSystemModeNames[self.cccSystemMode]

 
        self.zero_regs(self.bram_ppc1, 20)  # Clear ppc ready
  
        self.init_ppc_bram(self.bram_ppc1, 0xBEEFFACE)

        if 1:
            self.resetFwModulesToggleTristateIO()

        # Use FEM 100 Mhz Osc as Asic clock source during first stages of configuration
        # As need 100 Mhz clock source for rdma access for SP3 IO channel selection during loading of Slow Setup Paramaters  
        # Don't change to selected asic clock until the Fast Asic Command words are sent and readout starts       
        self.config_asic_clock_source_from_osc()

        #TODO: Is Comment Still Relevant?
        # send Reset to ASIC pin . Shouldn't be necessary? as short reset pulse is sent before trigger sequence.
        self.send_long_asic_reset()
        
        self.clear_ll_monitor(self.llink_mon_asicrx)
        self.clear_ll_monitor(self.llink_mon_0)

        # configure data paths between top level modules
        self.config_top_level()         
        
        # Setup the 10g link params
        self.config_10g_link()         

        # Pass readout data length to ppc bram before restarting ppc
        self.setup_ppc_bram(self.bram_ppc1, self.numberImages * self.lpd_image_size) 

        if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_PPC_DATA_DIRECT):  # runs with ppc
            if self.femPpcMode == 0:  # single shot readout mode, test only
                #print "skipping ppc reset"
                self.reset_ppc(1)  # Reset ppc nr 1                                       
            elif self.femPpcMode == 1:  # continuous Train readout mode with new PPC1 code
                print "Configure PPC1 Readout for CMD_ACQ_CONFIG."

                # compute the DMA buffer sizes based on the numberImages in the Train(s)
                # whole nr of Trains must fit in the BD ring buffers 
        
                maxNrImagesPerBD = 127  # limit the nr of images in a BD (physical limit is 127)
                nrTrainsInMemory = 4   # allow for N Trains worth in BDs

                nrBufsPerTrain = (self.numberImages / maxNrImagesPerBD) + 1
                if ((self.numberImages % maxNrImagesPerBD) == 0):
                    nrBufsPerTrain -= 1
                BufCount = nrBufsPerTrain * nrTrainsInMemory   # ensure whole nr of Trains in BD ring
                #BufCount = 10   

                BufSize = (maxNrImagesPerBD * self.lpd_image_size)    
                NumAcqs = self.numberTrains * nrBufsPerTrain    # number of BDs to process
                Coalesce = self.numberImages    # for LPD use this param instead to pass the nr of images to set up Tx descriptors
                ##AcqMode = FemTransaction.ACQ_MODE_TX_ONLY
                AcqMode = FemTransaction.ACQ_MODE_NORMAL
                if (AcqMode == FemTransaction.ACQ_MODE_TX_ONLY):
                    print "*** WARNING TESTING  FemTransaction.ACQ_MODE_TX_ONLY " 
                self.acquireSend(FemTransaction.CMD_ACQ_CONFIG, AcqMode, BufSize, BufCount, NumAcqs, Coalesce)

                print "CMD_ACQ_CONFIG. Total Nr BDs = %d ; Nr BD per Train = %d " % (BufCount, nrBufsPerTrain)
                print "CMD_ACQ_CONFIG. Nr BDs to Process this Run = %d ; Length of BD = $%08x bytes" % ( NumAcqs, BufSize)

        #print "TEST Reset of PPC2"        
        #self.reset_ppc(2) # Reset ppc nr 2  ############   TEST , careful as it kills the gbe!     

        #TODO: Still needed for local link generator or redundant?
        # Setup data gen - not necessary for actual data but leave alone, "just in case"
        self.config_data_gen()

        if self.femDebugLevel >= 0:        
            print ""           
            print "Configuring ASICs..."

        if self.femDebugLevel > 1:
            print "INFO start config_trig_strobe  "
        self.config_trig_strobe()   # External trigger strobes

        if self.femDebugLevel > 1:
            print "INFO start config_sp3io_top  "
        try:
            self.config_sp3io_top()   
        except FemClientError:
            print "WARNING: config_sp3io_top failed"
        
        if self.femDebugLevel > 1:
            print "INFO start config_sp3io_bot  "
        try:
            self.config_sp3io_bot()   
        except FemClientError:
            print "WARNING: config_sp3io_bot failed"

        # find out if DCM is present in SP3 IO (info is used to adjust asicrx timing)
        try:
            self.sp3_io_bot_firmware_modules = self.rdmaRead(self.bot_sp3_ctrl+18, 1)[0]
        except FemClientError:
            print "WARNING: BOT SP3 IO firmware modules register read failed"

        # Setup asic blocks
        if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_ASIC_DATA_DIRECT):  # data from asic
            if self.femDebugLevel > 1:
                print "INFO config_asic_modules  "
            self.config_asic_modules()

    def run(self):
        '''
            Execute run
        '''
        try:
          
            #return 1       # TEST 


            print ""           
            print "Starting Run ..."

            # check that a valid clock is being sent to the ASICs
            valid_clock = self.get_asic_clock_status()
            if valid_clock == 0:
                print "*** ERROR: There is NO VALID CLOCK to the ASIC" 
                #print "*** RUN was ABORTED."
                #print "*** Please verify the ASIC clock source." 
                #return 99

            if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource ==  self.RUN_TYPE_PPC_DATA_DIRECT):  # runs with ppc
                if self.femPpcMode == 0:  # single shot readout mode, test only
                    print "Running with PPC1 Readout. SINGLE TRAIN mode ..."
                    if (self.femPpcResetDelay == 0):
                        while self.ppc_readout_ready_status(self.bram_ppc1) == 0:
                            print "Waiting for PPC readout to be ready...",
                            sys.stdout.flush()
                    #return 1   # TEST    
                elif self.femPpcMode == 1:  # continuous Train readout mode with new PPC1 code
                    print "Running with PPC1 Readout CMD_ACQ_START. MULTIPLE TRAIN mode ......"
                    self.acquireSend(FemTransaction.CMD_ACQ_START)
                    #return 1   # TEST   
  
            else:
                if self.femDebugLevel > 1:
                    print "Running in PPC1 BYPASS mode..."
    
            print "=========================================================" 
            print "Starting Sequence of %d Trains , with each Train reading out %d images" % (self.numberTrains, self.numberImages)

            #print "Dump of FEM Registers : TOP LEVEL CTRL"
            #self.dump_regs_hex(self.fem_ctrl_0, 18)

            if self.STOP_RUN_ON_ESC_KEY == True:
                print ""           
                print "Hit the ESC KEY to Stop Run..." 
                print ""           
    
            if self.femStartTrainSource == 1:  # If S/W send triggers manually         
                self.enable_ext_trig_strobe()   # Enable and disable to reset trigger strobe counters!
                self.disable_ext_trig_strobe()
                
                for i in range (1, self.numberTrains+1):

                    if self.STOP_RUN_ON_ESC_KEY == True:           

                        try:
                            tty.setcbreak(sys.stdin.fileno())    

                            print "Train nr %d" % i
                            self.send_trigger() 
                            time.sleep(0.5)             # Need to check if images are all readout before sending next train
                          
                            if isData():
                                c = sys.stdin.read(1)
                                if c == '\x1b':         # x1b is the ESC KEY
                                    print 'Pressed the ESC key ' 
                                    break

                        finally:
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                    else:
                        
                        print "Train nr %d" % i
                        self.send_trigger() 
                        time.sleep(0.5)             # Need to check if images are all readout before sending next train
                       
    
            else:   # Else start run and use external c&c strobes

                print "Run is STARTED. Waiting for %d trigger strobes" % self.numberTrains 

                if self.femStartTrainSource == 3:
                    print "Running in PETRA mode."
                    if self.is_petra_shutter_ignored() == 1:
                        print "INFO: Petra Shutter status will be Ignored"
                    else:
                        petra_shutter_open = self.get_petra_shutter_status()
                        if petra_shutter_open == 0:
                            print "*** WARNING: Petra Shutter is Closed; Status = %d" %petra_shutter_open
                            print "*** Triggers will not be accepted whilst Shutter is Closed."
                            print "*** Please either open shutter..."
                            print "*** ... or abort this run and invert shutter polarity or ignore shutter"
                       
                nr_ext_trig_strobes = 0
                nr_ext_trig_strobes_accepted = 0

                self.enable_ext_trig_strobe()

                if self.STOP_RUN_ON_ESC_KEY == True:           

                    try:
                        tty.setcbreak(sys.stdin.fileno())
                                                
                        while nr_ext_trig_strobes_accepted < self.numberTrains:
                        
                            if isData():
                                c = sys.stdin.read(1)
                                if c == '\x1b':         # x1b is the ESC KEY
                                    print 'Pressed the ESC key ' 
                                    break
                        
                            nr_ext_trig_strobes_accepted = self.get_ext_trig_strobe_accepted_count()
                        
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                else:
                    
                    while nr_ext_trig_strobes_accepted < self.numberTrains:
                    
                        nr_ext_trig_strobes_accepted = self.get_ext_trig_strobe_accepted_count()
                    
                self.disable_ext_trig_strobe()
                print "Run is STOPPED" 
                #print "nr_ext_trig_strobes_accepted = %d" % nr_ext_trig_strobes_accepted 
                    
    
            print "======== Train Cycle Completed ===========" 
            print ""           
            #time.sleep(2)   # just to see output before dumping registers

            # Switch back to FEM Osc clock as Asic clock source for run end       
            self.config_asic_clock_source_from_osc()
    
            if self.femDebugLevel > 1:
                print "     V5 FPGA Firmware vers = %08x" % self.get_v5_firmware_vers()
                print "BOT SP3 FPGA Firmware vers = %08x" % self.get_bot_sp3_firmware_vers()
                print "TOP SP3 FPGA Firmware vers = %08x" % self.get_top_sp3_firmware_vers()
                print "CFG SP3 FPGA Firmware vers = %08x" % self.get_cfg_sp3_firmware_vers()

            if self.get_top_sp3_firmware_vers() != self.get_bot_sp3_firmware_vers() :
                print "*** WARNING:  Firmware Versions in SP3 IO TOP and BOTTOM are Different" 
            
            
            if self.femDebugLevel >= 0:
                print ""
                print "Dump of FEM Registers : TOP LEVEL CTRL"
                self.dump_regs_hex(self.fem_ctrl_0, 30)

            if self.femDebugLevel > 0:
                print "Dump of FEM Registers : BOT SP3 CTRL"
                try:
                    self.dump_regs_hex(self.bot_sp3_ctrl, 20)
                except FemClientError:
                    print "WARNING: BOT SP3 dump_regs_hex failed"

                print "Dump of FEM Registers : TOP SP3 CTRL"
                try:
                    self.dump_regs_hex(self.top_sp3_ctrl, 20)
                except FemClientError:
                    print "WARNING: TOP SP3 dump_regs_hex failed"

            if self.femDebugLevel >= 1:

                print "Dump of FEM Registers : TRIGGER STROBE"
                self.dump_regs_hex(self.trig_strobe, 20)
                
                print "Dump of FEM Registers : ASIC DATA RX"
                self.dump_regs_hex(self.asic_srx_0, 16)

#              print "Dump of FEM Registers : ASIC SLOW CTRL"
#              self.dump_regs_hex(self.slow_ctr_0, 18)

#              print "Dump of FEM Registers : ASIC SLOW BRAM"
#              self.dump_regs_hex(self.slow_ctr_1, 1024)   # 1024

                print "Dump of FEM Registers : ASIC FAST CTRL"
                self.dump_regs_hex(self.fast_cmd_0, 16)
                
                print "Dump of FEM Registers : ASIC FAST BRAM"
                self.dump_regs_hex(self.fast_cmd_1, 128)          
                
                #print "Dump of FEM Registers : ASIC FAST BRAM COE"
                #self.dump_regs_hex_coe(self.fast_cmd_1, 1024)
                
                if ((self.get_v5_firmware_vers()&0xffff) >= 0x0220):
                    print "Dump of FEM Registers : CCC DELAY REG"
                    self.dump_regs_hex(self.ccc_delay_reg, 6) 
                    print "Dump of FEM Registers : CCC PATTERN ID REG"
                    self.dump_regs_hex(self.ccc_pattern_id, 16)                  
                    print "Dump of FEM Registers : CCC PATTERN BRAM"
                    self.dump_regs_hex(self.ccc_pattern_bram, 0x80)
                
                if ((self.get_v5_firmware_vers()&0xffff) >= 0x022d):
                    print "Dump of FEM Registers : CCC CMD GEN REG"
                    self.dump_regs_hex(self.ccc_cmd_gen_reg, 16) 
                    print "Dump of FEM Registers : CCC CMD GEN BRAM"
                    self.dump_regs_hex(self.ccc_cmd_gen_bram, 24) 
    
            if self.femDebugLevel > 0:
                print "Register Settings"
                self.dump_registers()
            else:
                time.sleep(2)   # if no dump add wait to allow 10g transfers to complete
                #print "Dump of FEM Registers : TOP LEVEL CTRL"
                #self.dump_regs_hex(self.fem_ctrl_0, 18)
                #print "Dump of FEM Registers : PPC1 BRAM"
                #self.dump_regs_hex(self.bram_ppc1, 20)

            if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource ==  self.RUN_TYPE_PPC_DATA_DIRECT):  # runs with ppc
                if self.femPpcMode == 1:  # continuous Train readout mode with new PPC1 code
                    #time.sleep(3)  
                    print "Stopping PPC1 Readout CMD_ACQ_STOP. "
                    self.acquireSend(FemTransaction.CMD_ACQ_STOP)
    

            print ""
            print "Summary of Data Readout..."
    
            # 10g ll monitor
            print ""
            print "10G LLink Monitor: 64b "
            self.read_ll_monitor(self.llink_mon_0, 156.25e6)

            print ""    
            print "Asic Rx LLink Monitor: 32b "
            self.read_ll_monitor(self.llink_mon_asicrx, 220.0e6)    # 220.0e6 
    
            print "======== Run Completed ==========="
            print ""           
        
        except FemClientError as e:
            raise e
        except Exception as e:
            raise FemClientError(str(e))

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

    def tenGigInterframeGapGet(self):
        '''
            Get the 10 Gig Ethernet Inter-frame gap timer [clock cycles]
        '''
        return self.tenGigInterframeGap

    def tenGigInterframeGapSet(self, aValue):
        '''
            Set the 10 Gig Ethernet Inter-frame gap timer in clock cycles
        '''
        self.tenGigInterframeGap = aValue

    def tenGigUdpPacketLenGet(self):
        '''
            Get the 10 Gig Ethernet UDP packet payload length
        '''
        return self.tenGigUdpPacketLen

    def tenGigUdpPacketLenSet(self, aValue):
        '''
            Set the 10 Gig Ethernet UDP packet payload length
        '''
        self.tenGigUdpPacketLen = aValue

    def femEnableTenGigGet(self):
        '''
            Get the 10 GigE UDP interface image data transmission status
        '''
        return self.tenGig0['femEnable']

    def femEnableTenGigSet(self, aValue):
        '''
            Set the 10 GigE UDP interface image data transmission status
        '''
        self.tenGig0['femEnable'] = aValue

    def femDataSourceGet(self):
        '''
            Get the 10 Gig Ethernet Data Source
        '''
        return self.femDataSource

    def femDataSourceSet(self, aValue):
        '''
            Set the 10 Gig Ethernet Data Source
        '''
        self.femDataSource = aValue

    def femAsicModuleTypeGet(self):
        '''
            Get the Asic Module type
        '''
        return self.femAsicModuleType

    def femAsicModuleTypeSet(self, aValue):
        '''
            Set the Asic Module Type
        '''
        self.femAsicModuleType = aValue

    def femAsicEnableMaskGet(self):
        '''
            Get the Asic Receive Enable Mask
        '''
        return self.femAsicEnableMask

    def femAsicEnableMaskSet(self, aValue):
        '''
            Set the Asic Receive Enable Mask
        '''
        self.femAsicEnableMask = aValue
                
    def numberImagesGet(self):
        '''
            Get the number of images per train
        '''
        return self.numberImages

    def numberImagesSet(self, aValue):
        '''
            Set the number of images per train
        '''
        self.numberImages = aValue

    def femAsicGainGet(self):
        '''
            Get the ASIC Gain Selection Algorithm
        '''
        return self.femAsicGain

    def femAsicGainSet(self, aValue):
        '''
            Set the ASIC Gain Selection Algorithm
        '''
        self.femAsicGain = aValue

    def femAsicSetupParamsGet(self):
        '''
            Get the Lpd ASIC control parameter definition in XML
        '''
        return self.femAsicSetupParams

    def femAsicSetupParamsSet(self, aValue):
        '''
            Set the Lpd ASIC control parameter definition in XML
        '''
        self.femAsicSetupParams = aValue

    def femAsicCmdSequenceGet(self):
        '''
            Get the Lpd ASIC Command Sequence
        '''
        return self.femAsicCmdSequence

    def femAsicCmdSequenceSet(self, aValue):
        '''
            Set the Lpd ASIC Command Sequence
        '''
        self.femAsicCmdSequence = aValue

    def femAsicPixelFeedbackOverrideGet(self):
        '''
            Get the ASIC pixel feedback override
        '''
        return self.femAsicPixelFeedbackOverride
                    
    def femAsicPixelFeedbackOverrideSet(self, aValue):
        '''
            Set the ASIC pixel feedback override
        '''
        self.femAsicPixelFeedbackOverride = aValue
            
    def femAsicPixelSelfTestOverrideGet(self):
        '''
            Get the ASIC pixel self-test override
        '''
        return self.femAsicPixelSelfTestOverride
                    
    def femAsicPixelSelfTestOverrideSet(self, aValue):
        '''
            Set the ASIC pixel self-test override
        '''
        self.femAsicPixelSelfTestOverride = aValue

    def femReadoutOperatingModeGet(self):
        '''
            Get the Fem Readout Operating Mode
        '''
        return self.femReadoutOperatingMode

    def femReadoutOperatingModeSet(self, aValue):
        '''
            Set the Fem Readout Operating Mode
        '''
        self.femReadoutOperatingMode = aValue

    def femAsicDataTypeGet(self):
        '''
            Get the Asic Data Type
        '''
        return self.femAsicDataType

    def femAsicDataTypeSet(self, aValue):
        '''
            Set the Asic Data Type
        '''
        self.femAsicDataType = aValue

    def femAsicLocalClockGet(self):
        '''
            Get the ASIC Clock Scale
        '''
        return self.femAsicLocalClock

    def femAsicLocalClockSet(self, aValue):
        '''
            Set the ASIC Clock Scale
        '''
        self.femAsicLocalClock = aValue

    def femAsicSetupLoadModeGet(self):
        '''
            Get the ASIC Control Load Mode
        '''
        return self.femAsicSetupLoadMode

    def femAsicSetupLoadModeSet(self, aValue):
        '''
            Set the ASIC Control Load Mode
        '''
        self.femAsicSetupLoadMode = aValue

    def femInvertAdcDataGet(self):
        '''
            Get the ASIC ADC Data Inversion
        '''
        return self.femInvertAdcData

    def femInvertAdcDataSet(self, aValue):
        '''
            Set the ASIC ADC Data Inversion
        '''
        self.femInvertAdcData = aValue

    def femAsicRxCmdWordStartGet(self):
        '''
            Get the ASIC readout started by Command Word from file
        '''
        return self.femAsicRxCmdWordStart

    def femAsicRxCmdWordStartSet(self, aValue):
        '''
            Set the ASIC readout started by Command Word from file
        '''
        self.femAsicRxCmdWordStart = aValue

    def femAsicSetupClockPhaseGet(self):
        '''
            Get the ASIC Setup Params clock additional phase adjustment
        '''
        return self.femAsicSetupClockPhase

    def femAsicSetupClockPhaseSet(self, aValue):
        ''' 
            Set the ASIC Setup Params clock additional phase adjustment
        '''
        self.femAsicSetupClockPhase = aValue

    def femAsicVersionGet(self):
        '''
            Get the Asic Tile Version
        '''
        return self.femAsicVersion

    def femAsicVersionSet(self, aValue):
        '''
            Set the Asic Tile Version
        '''
        self.femAsicVersion = aValue

    def femAsicClockSourceGet(self):
        '''
            Get the Asic Clock Source
        '''
        return self.femAsicClockSource

    def femAsicClockSourceSet(self, aValue):
        '''
            Set the Asic Clock Source
        '''
        self.femAsicClockSource = aValue

    def femStartTrainSourceGet(self):
        '''
            Get the Fem Beam Trigger Source
        '''
        return self.femStartTrainSource

    def femStartTrainSourceSet(self, aValue):
        '''
            Set the Fem Beam Trigger Source
        '''
        self.femStartTrainSource = aValue

    def femStartTrainDelayGet(self):
        '''
            Get the Train Start Delay
        '''
        return self.ext_trig_strobe_delay

    def femStartTrainDelaySet(self, aValue):
        '''
            Set the Train Start Delay
        '''
        self.ext_trig_strobe_delay = aValue

    def femStartTrainInhibitGet(self):
        '''
            Get the Train Start Inhibit
        '''
        return self.ext_trig_strobe_inhibit

    def femStartTrainInhibitSet(self, aValue):
        '''
            Set the Train Start Inhibit
        '''
        self.ext_trig_strobe_inhibit = aValue

    def femAsicGainOverrideGet(self):
        '''
            Get the Fem Gain Selection Mode
        '''
        return self.femAsicGainOverride

    def femAsicGainOverrideSet(self, aValue):
        '''
            Set the Fem Gain Selection Mode
        '''
        self.femAsicGainOverride = aValue

    def femPpcModeGet(self):
        '''
            Get the Fem PPC Mode
        '''
        return self.femPpcMode

    def femPpcModeSet(self, aValue):
        '''
            Set the Fem PPC Mode
        '''
        self.femPpcMode = aValue

    def numberTrainsGet(self):
        '''
            Get the Number of Trains
        '''
        return self.numberTrains

    def numberTrainsSet(self, aValue):
        '''
            Set the Number of Trains
        '''
        self.numberTrains = aValue

    def tenGigFarmModeGet(self):
        '''
            Get the 10 Gig Ethernet Farm Mode
        '''
        return self.tenGigFarmMode

    def tenGigFarmModeSet(self, aValue):
        '''
            Set the 10 Gig Ethernet Farm Mode
        '''
        self.tenGigFarmMode = aValue

    def femDebugLevelGet(self):
        '''
            Get the Fem Debug Level
        '''
        return self.femDebugLevel

    def femDebugLevelSet(self, aValue):
        '''
            Set the Fem Debug Level
        '''
        self.femDebugLevel = aValue

    def tenGig0DataGeneratorGet(self):
        '''
            Get the 10 Gig Ethernet 0 Data Generator
        '''
        return self.tenGig0['data_gen']

    def tenGig0DataGeneratorSet(self, aValue):
        '''
            Set the 10 Gig Data Ethernet 0 Generator
        '''
        self.tenGig0['data_gen'] = aValue

    def tenGig0DataFormatGet(self):
        '''
            Get the 10 Gig Ethernet 0 Data Format Type
        '''
        return self.tenGig0['data_format']

    def tenGig0DataFormatSet(self, aValue):
        '''
            Set the 10 Gig Ethernet 0 Data Format Type
        '''
        self.tenGig0['data_format'] = aValue

    def tenGig0FrameLengthGet(self):
        '''
            Get the 10 Gig Ethernet 0 Frame Length
        '''
        return self.tenGig0['frame_len']

    def tenGig0FrameLengthSet(self, aValue):
        '''
            Set the 10 Gig Ethernet 0 Frame Length
        '''
        self.tenGig0['frame_len'] = aValue

    def tenGig0NumberOfFramesGet(self):
        '''
            Get the 10 Gig Ethernet 0 Number of Frames in each cycle
        '''
        return self.tenGig0['num_frames']

    def tenGig0NumberOfFramesSet(self, aValue):
        '''
            Set the 10 Gig Ethernet 0 Number of Frames in each cycle
        '''
        self.tenGig0['num_frames'] = aValue

    def femV5FirmwareVersionGet(self):
        '''
            Get the Fem V5 Firmware Version
        '''
        return self.get_v5_firmware_vers()

    def femBotSp3FirmwareVersionGet(self):
        '''
            Get the Fem Bottom Sp3 Firmware Version
        '''
        return self.get_bot_sp3_firmware_vers()

    def femTopSp3FirmwareVersionGet(self):
        '''
            Get the Fem Top Sp3 Firmware Version
        '''
        return self.get_top_sp3_firmware_vers()

    def femCfgSp3FirmwareVersionGet(self):
        '''
            Get Fem Cfg Sp3 Firmware Version
        '''
        return self.get_cfg_sp3_firmware_vers()
        
    def femStartTrainPolarityGet(self):
        '''
            Get the Beam trigger polarity
        '''
        return self.ext_trig_strobe_polarity

    def femStartTrainPolaritySet(self, aValue):
        '''
            Set the Beam trigger polarity
        '''
        self.ext_trig_strobe_polarity = aValue

    def femVetoPolarityGet(self):
        '''
            Get the Beam veto polarity
        '''
        return self.petra_shutter_polarity

    def femVetoPolaritySet(self, aValue):
        '''
            Set the Beam veto polarity
        '''
        self.petra_shutter_polarity = aValue

    def setbit(self, addr, bit):
        """ set bit in register """     

        reg = self.rdmaRead(addr, 1)[0]
        reg |= (1 << bit)
        self.rdmaWrite(addr, reg) 
        
        return reg   

    def clrbit(self, addr, bit):
        """ set bit in register """     

        reg = self.rdmaRead(addr, 1)[0]
        reg &= ~(1 << bit)
        self.rdmaWrite(addr, reg) 
        
        return reg  

    def femModuleIdGet(self):
        '''
            Get the fem module ID
        '''
        return self.femModuleId

    def femModuleIdSet(self, aValue):
        '''
            Set the fem module ID
        '''
        self.femModuleId = aValue

    def cccSystemModeGet(self):
        ''' 
            Get the C&C System Mode
        '''
        return self.cccSystemMode

    def cccSystemModeSet(self, aValue):
        ''' 
            Set the C&C System Mode
        '''
        self.cccSystemMode = aValue
    
    def cccEmulationModeGet(self):
        '''
            Get the C&C Emulation Mode Status
        '''
        return self.cccEmulationMode
    
    def cccEmulationModeSet(self, aValue):
        '''
            Set the C&C Emulation Mode Status
        '''
        self.cccEmulationMode = aValue
    
    def cccProvideNumberImagesGet(self):
        '''
            Get the C&C Override Number of Images Status
        '''
        return self.cccProvideNumberImages
    
    def cccProvideNumberImagesSet(self, aValue):
        '''
            Set the C&C Override Number of Images Status
        '''
        self.cccProvideNumberImages = aValue
        
    def cccVetoStartDelayGet(self):
        ''' 
            Get the C&C Veto Start Delay
        '''
        return self.cccVetoStartDelay
    
    def cccVetoStartDelaySet(self, aValue):
        ''' 
            Set the C&C Veto Start Delay
        '''
        self.cccVetoStartDelay = aValue
        
    def cccStopDelayGet(self):
        ''' 
            Get the C&C Stop Delay
        '''
        return self.cccStopDelay
    
    def cccStopDelaySet(self, aValue):
        ''' 
            Set the C&C Stop Delay
        '''
        self.cccStopDelay = aValue
        
    def cccResetDelayGet(self):
        ''' 
            Get the C&C Reset Delay
        '''
        return self.cccResetDelay
    
    def cccResetDelaySet(self, aValue):
        ''' 
            Set the C&C Reset Delay 
        '''
        self.cccResetDelay = aValue
        
    def cccVetoPatternFileGet(self):
        ''' 
            Get the C&C veto pattern xml file
        '''
        return self.cccVetoPatternFile
    
    def cccVetoPatternFileSet(self, aValue):
        ''' 
            Set the C&C veto pattern xml file 
        '''
        self.cccVetoPatternFile = aValue
