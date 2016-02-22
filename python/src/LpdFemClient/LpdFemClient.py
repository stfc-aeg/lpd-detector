'''
LpdFemClient - XFEL LPD class sitting between the API and the FemClient
         
Created 16 October 2012

@Author: ckd    -    TRUNK VERSION

LINUX
'''

##################################################################
#
# vers 0x10000004  25/09/15  John Coughlan
#
# Starting from Christian's merge of vers 0x10000003 with the trunk. Trunk rev 1550
#
# Renamed new Karabo params for Pipeline emulation support (to match Christian's conventions). Specfied min,max,def values.
# Added corresponding get and set functions for device parameters.
#
# vers 0x10000003  22/09/15  John Coughlan
#
# Fixes to some print out statements.
# Uses train id init values in checker.
#
# vers 0x10000002  21/09/15  John Coughlan
#
# Added Train ID init lsw and msw
#
# Params for Karabo release.
#
# vers 0x10000001  18/09/15  John Coughlan
#
# This version released for f/w 01000298  which implements Pipeline Emulation and requires PPC1 in Data path.
# Only works WITH PPC1   ie  <femDataSource> = 0 ASIC [via PPC],
#
# Is backward compatible with f/w 0100026f  (C&C XFEL May 2015 format but no pipeline emulation so just counters in Image Desc)
# Only works without PPC1   ie  <femDataSource> = 1 ASIC [from Rxblock],
#
# Added readonly code version param  LpdClientVersion
# 
# Made fixes for 64b field swapping in header and trailer.
# 
#
#
##################################################################


# to get OS info
import platform

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

# python debugger test
#import pdb


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
    lpd_checker         = 0x08000000    # 16
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
    fem_ctrl_top2       = 0x0f800000    # 31 - more top level fem ctrl
 
# Spartan 3 devices 
# needs new gbe embedded software with rs232 mux control
    bot_sp3_ctrl        = 0x10000000    #  0
    top_sp3_ctrl        = 0x20000000    #  0
    cfg_sp3_ctrl        = 0x30000000    #  0

   
    # BRAM memory shared by ppc1 and ppc2 
    # filled by ppc1 with status information
    # can be readout from ppc2 by python using raw memory mapped access (not rdma access)
    ppc_shared_bram_base  = 0x8a000000
   
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

        self.LPD_NUM_PIXELS_PER_ASIC = 512  

        ########### Constants ###########
        self.nr_clocks_to_readout_image     = (self.LPD_NUM_PIXELS_PER_ASIC * 3 * 12)    # * asic_clock_downscale_factor # 512 pixels with 3 gain values each. this is time for asic data streams to enter asicrx (output takes longer)
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
        self.integrationCycles                      = 1         # Number of integration cycles per image
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
        self.femPpcMode                 = 1     # 0 = Single Train Shot with PPC reset (select for legacy f/w without PPC), 1 = Continuous readout (not working yet)

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
        
        self.cccEmulationMode = True;  #  = True to emulate c&c commands (for testing if no c&c system connected)

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
        
        self.CCC_CMD_GEN_XRAY_DELAY = 700   # 1024  # nr of clocks between emulated xfel c&c start and arrival of xrays

        self.TRAIN_ID_LENGTH = 64   # nr bits

        self.femModuleId = [0] * 16; # module ID for header

        self.NR_CLOCKS_PER_FAST_CMD = 22
        
        self.CCC_PATTERN_VETO_BRAM_SIZE_BYTES = 1024

        self.NR_CCC_VETO_PATTERNS = 10
        self.NR_WORDS_PER_CCC_VETO_PATTERN = 96  # size of pattern in bram words

        self.CCC_EMULATOR_BRAM_SIZE_BYTES = 1024

        self.LPD_PIPELINE_LENGTH = 512  
       
#----       
        self.sp3_io_bot_firmware_modules = 0
        
        if os.name == 'nt':
            self.STOP_RUN_ON_ESC_KEY = False    # not supported by windows
        else:
            self.STOP_RUN_ON_ESC_KEY = False    # Set False if running with Gui ; 
            
          
# since f/w 026f            
               
        self.cccSimpleEmulation = True #    =True  use simple ccc sm to generate start cmd and nveto tied '1' with pattern mask for triggers

        gap_1_sec = 100000000    # asic clock periods
        gap_1_msec = 100000    # asic clock periods
        
        #First Level of printout on PPC1 terminal ; Default = 1        
        self.ppcDebugLevel = 1
        
        #Second Level of printout on PPC1 terminal for pipeline emulation  and reordering ; Default = 1
        self.ppcDebugLevel2 = 1   

        self.wait_for_ppc_run_stop = 0   # additional wait for debugging on ppc terminal  ; in secs
        
        self.asicrx_llink_clock_rate = 200.0e6  # 250.0e6  # 200.0e6
        self.ppc_clock_period = 4 # 3.33  # 4   # processor clock period nsec
        
        # Special test which disables output of Readout data
        self.ppc1_disable_tx_dma = False   # default FalseSTOP_RUN_ON_ESC_KEY

        # Change defaults used by Pipeline Emulation; Default = TRUE
        self.ppc1_override_pipeline_defaults = True 
               
        # Max Length of Pulse Train; Default = 3072
        self.NR_BUNCHES_IN_TRAIN_OVERRIDE = 1536  # 36  # 1500         
        
        # Pipeline Length; Default = 512
        self.LPD_PIPELINE_LENGTH_OVERRIDE = self.LPD_PIPELINE_LENGTH      # 12  # override for special tests of emulation only 

        # Sets depth of DDR2 Buffer storage . Default = 10
        self.NUM_TRAINS_TO_STORE_IN_BD_RING = 10   # PPC will assume 512 images per Train

#####################################################
# Begin New Params for Karabo API
        
        #1  # Only used if running with cccEmulationMode = True. Enables fixed rate Train triggers.  
        # Default = False
        self.cccEmulatorFixedRateStarts = False  
        
        #2  # Only used if running with cccEmulationMode = True. Interval (in 100 mhz clock periods) between fixed rate triggers. 
        # Min = 0 ; Max = 0xffffffff ; Default = 10000000 (100 msec)
        self.cccEmulatorIntervalBetweenFixedRateStarts = 100 * gap_1_msec  
        
        #3  # Only used if running with cccEmulationMode = True. Number of fixed rate triggers to send this run.  
        # Min = 1 ; Max = 0xffffffff ; Default = 1
        self.cccEmulatorNumFixedRateStarts =  1   #       10 * 60 * 90 * 1    #  hz x sec x min x hour
                                
        #4  # Only used if femAsicDataType set to counting data from AsicRx. 
        # Min = 0 ; Max = 1 ; Default = 0
        self.femAsicTestDataPatternType  = 0   # 0 = if test data counter increments every Pixel ; 1 = only increments every Image
        
        #5  # Emulate the LPD Asic Pipeline to compute the Pulse Nr and Cell Id for the Image Descriptors ;
        # Default = True
        self.femPpcEmulatePipeline = True    # (Must be False if cccSystemMode != 2 ; as PPC will fail without valid C&C veto information) 

        #6  # After Pipeline Emulation reorder Images in readout in Pulse Number order ;
        # Default = True
        # Re-ordering will only work if ppc1_emulate_pipeline = True
        self.femPpcImageReordering = True    
                         
        #7  # LpdClient Software Version  ; Read Only  
        # Default to following value     
        self.femLpdClientVersion = 0x10000004

        #8  # init value for train id (used if not running with C&C and also by Data Checker)  lower 32b value 
        # Min = 0 ; Max = 0xffffffff ; Default = 1 
        self.femTrainIdInitLsw = 1
        
        #9  # init value for train id (used if not running with C&C and also by Data Checker)  upper 32b value 
        # Min = 0 ; Max = 0xffffffff ; Default = 0  
        self.femTrainIdInitMsw = 0

# End New Params for Karabo API
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
        
    ## Rob Halsall 08-04-2011
    #def read_ll_monitor(self, base, clock_freq):
        #''' readout a local link monitor block '''
        
        #mon_addr = base + 16

        #print "frm_last_length (bytes):      %s" % hex( self.rdmaRead(mon_addr+0, 1)[0])
        #print "frm_max_length (bytes):       %s" % hex( self.rdmaRead(mon_addr+1, 1)[0])
        #print "frm_min_length (bytes):       %s" % hex( self.rdmaRead(mon_addr+2, 1)[0])
        #total_frames = self.rdmaRead(mon_addr+3, 1)[0]
        #print "frm_count:                    %d [%s]" % (total_frames, hex(total_frames))
        #print "frm_last_cycles:              %s" % hex( self.rdmaRead(mon_addr+4, 1)[0])
        #print "frm_max_cycles:               %s" % hex( self.rdmaRead(mon_addr+5, 1)[0])
        #print "frm_min_cycles:               %s" % hex( self.rdmaRead(mon_addr+6, 1)[0]) 
        #total_data = self.rdmaRead(mon_addr+7, 1)[0]
        #print "frm_data_total (bytes):       %d [%s]" % (total_data, hex(total_data))         
        #total_cycles = self.rdmaRead(mon_addr+8, 1)[0]
        #print "frm_cycle_total:              %d" % total_cycles
        #print "frm_trig_count:               %s" % hex( self.rdmaRead(mon_addr+9, 1)[0])
        #print "frm_in_progress:              %s" % hex( self.rdmaRead(mon_addr+15, 1)[0])
        
        ## data path = 64 bit, clock = 156.25 MHz
        #total_time = float(total_cycles) * (1/clock_freq)
        #if (total_time):
            #rate = (total_data/total_time)   #  total data is in bytes already   jac
        #else:
            #rate = 0

        #print "Clock Freq = %d Hz"               % clock_freq
        #print "Data Total =                  %e" % total_data
        #print "Data Time  =                  %e" % total_time
        #print "Data Rate  =                  %e" % rate

    # Rob Halsall 08-04-2011
    # John Coughlan 64b counters 2015
    def read_ll_monitor(self, base, clock_freq):
        ''' readout a local link monitor block '''
        
        mon_addr = base + 16
        
        number_frames = self.rdmaRead(mon_addr+3, 1)[0]
        number_eofs = self.rdmaRead(mon_addr+15, 1)[0]       
        frm_max_cycles = self.rdmaRead(mon_addr+5, 1)[0]
        frm_min_cycles = self.rdmaRead(mon_addr+6, 1)[0] 
        gap_min_cycles = self.rdmaRead(mon_addr+14, 1)[0] 

        print "NEW local link monitor (64 bit counters):      "
        print "frm_last_length (bytes):      %s" % hex( self.rdmaRead(mon_addr+0, 1)[0])
        print "frm_max_length (bytes):       %s" % hex( self.rdmaRead(mon_addr+1, 1)[0])
        print "frm_min_length (bytes):       %s" % hex( self.rdmaRead(mon_addr+2, 1)[0])
        print "frm_number:               %d    %s" %(number_frames, hex(number_frames))
        print "frm_last_cycles:              %s" % hex( self.rdmaRead(mon_addr+4, 1)[0])
        print "frm_max_cycles:               %s" % hex( frm_max_cycles )
        print "frm_min_cycles:               %s" % hex( frm_min_cycles ) 
        total_data_lower = self.rdmaRead(mon_addr+7, 1)[0]
        total_data_upper = self.rdmaRead(mon_addr+12, 1)[0]
        print "frm_data_total lower (bytes):       %d %s" % (total_data_lower, hex(total_data_lower))         
        print "frm_data_total upper (bytes):       %d %s" % (total_data_upper, hex(total_data_upper))         
        total_cycles_lower = self.rdmaRead(mon_addr+8, 1)[0]
        total_cycles_upper = self.rdmaRead(mon_addr+13, 1)[0]
        print "frm_cycle_total lower:      %s" % hex( total_cycles_lower)
        print "frm_cycle_total upper:      %s" % hex( total_cycles_upper)
        print "frm_trig_count:               %s" % hex( self.rdmaRead(mon_addr+9, 1)[0])
        print "eof counter:              %s" % hex( self.rdmaRead(mon_addr+15, 1)[0])
        
        total_cycles_frm_in_progress_lower = self.rdmaRead(mon_addr+10, 1)[0]
        total_cycles_frm_in_progress_upper = self.rdmaRead(mon_addr+11, 1)[0]
        print "total_cycles_frm_in_progress lower:   %s" % hex(total_cycles_frm_in_progress_lower)
        print "total_cycles_frm_in_progress upper:   %s" % hex(total_cycles_frm_in_progress_upper)
        print "gap_min_cycles:               %s" % hex( gap_min_cycles ) 


        frm_max_time = float(frm_max_cycles) * (1/clock_freq)
        print "frm_max_time (sec) =                  %e" % frm_max_time
        frm_min_time = float(frm_min_cycles) * (1/clock_freq)
        print "frm_min_time (sec) =                  %e" % frm_min_time
        gap_min_time = float(gap_min_cycles) * (1/clock_freq)
        print "gap_min_time (sec) =                  %e" % gap_min_time
        
        # data path = 64 bit, clock = 156.25 MHz
        total_time = float(total_cycles_lower) * (1/clock_freq)
                
        if (total_time):
            rate = (total_data_lower/total_time)   #  total data is in bytes already   jac
        else:
            rate = 0

        frame_time = float(total_cycles_frm_in_progress_lower) * (1/clock_freq)
        if (frame_time):
            rate_in_frames = (total_data_lower/frame_time)   #  total data is in bytes already   jac
        else:
            rate_in_frames = 0

# 64 bit counters

        total_data_64b = total_data_upper * 0x100000000 + total_data_lower
        #print "total_data_64b = %s "               % hex(total_data_64b)

        total_cycles_64b = total_cycles_upper * 0x100000000 + total_cycles_lower
        #print "total_cycles_64b = %s "   % hex(total_cycles_64b)

        total_cycles_frm_in_progress_64b = total_cycles_frm_in_progress_upper * 0x100000000 + total_cycles_frm_in_progress_lower
        #print "total_cycles_frm_in_progress_64b = %s "   % hex(total_cycles_frm_in_progress_64b)

        total_time_64b = (float(total_cycles_upper * 0x100000000) + float(total_cycles_lower)) * (1/clock_freq)
        if (total_time_64b):
            rate_64b = (total_data_64b/total_time_64b)   
        else:
            rate_64b = 0

        frame_time_64b = (float(total_cycles_frm_in_progress_upper * 0x100000000) + float(total_cycles_frm_in_progress_lower)) * (1/clock_freq)
        if (frame_time_64b):
            rate_in_frames_64b = (total_data_64b/frame_time_64b)   
        else:
            rate_in_frames_64b = 0

        print "------------------"              
        print "Clock Freq = %d Hz"               % clock_freq
        print "Data Total (Bytes) =                  %e" % total_data_64b
        print "Data Time (sec) =                  %e" % total_time_64b
        print "Data Rate during Frames (Bytes/sec) =                  %e" %rate_in_frames_64b 
        print "Data Rate during Run (Bytes/sec) =                  %e" %rate_64b


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
            print "--"
            print "Switching ASIC clock source to FEM Osc" 

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
            # Petra shutter
            self.set_petra_shutter_polarity(self.petra_shutter_polarity) 
            self.use_petra_shutter(self.femIgnorePetraShutter) 
        else: # using C&C RJ45 input for Xfel , LCLS or Diamond  ;    shutter signal becomes vetos
            self.disable_petra_trig_strobe()  
            # Petra shutter = c&c veto input
            self.set_petra_shutter_polarity(self.petra_shutter_polarity) # want to use polarity for vetos
            self.use_petra_shutter(0)     # force to use vetos
      
    def config_10g_link(self):
        ''' Configure 10 Gig Link '''

        if self.tenGig0['femEnable']:
            if self.femDebugLevel >= 5:
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

            if self.femDebugLevel >= 5:
                print "Dump of Farm Mode LUT for xaui for Link %d" % self.tenGig0['link_nr']
                self.dump_regs_hex(x10g_base+0x10000, 16) 
                self.dump_regs_hex(x10g_base+0x100f0, 16)                               
                self.dump_regs_hex(x10g_base+0x10100, 16)
                self.dump_regs_hex(x10g_base+0x101f0, 16)  
                self.dump_regs_hex(x10g_base+0x10200, 16)
                self.dump_regs_hex(x10g_base+0x103f0, 16)
                    
            if self.femDebugLevel >= 5:
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

        if self.femDebugLevel >= 2:
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

                if self.cccSimpleEmulation == True: # use simple ccc sm to generate start cmd and nveto tied '1' with pattern mask for triggers
                    self.register_set_bit(self.fem_ctrl_0+10, 18)
                    self.register_clear_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '1' to use enabled pattern bram bits for triggers
                else:                  
                    self.register_clear_bit(self.fem_ctrl_0+10, 18)
                    self.register_set_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '0' to ccc nvetos for triggers

                self.register_set_bit(self.fem_ctrl_0+10, 16)  # mux select inputs from generator

                self.register_clear_bit(self.fem_ctrl_0+10, 17)  # reenable trigger strobes if NOT using real ccc commands
                
                self.toggle_bits(self.fem_ctrl_0+11, 24)    # local reset asic_ccc_cmd_gen
                
                self.config_asic_ccc_cmd_gen()  # set up self test for emulating commands and vetos coming from xfel C&C system
                

            else:
                
                self.register_clear_bit(self.fem_ctrl_0+10, 16)  # mux select inputs from C&C system 

                self.register_set_bit(self.fem_ctrl_0+10, 17)  # inhibit trigger strobes if using real ccc commands
                
                if self.cccSystemMode == 1: # no vetos from c&c
                
                    #self.register_clear_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '1' to use enabled pattern bram bits for triggers
                    self.register_set_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '0' 
                else:   # with vetos from c&c
                
                    self.register_set_bit(self.fem_ctrl_0+10, 14)  # bypass nveto = '0' to ccc nvetos for triggers
                    

                    
            self.toggle_bits(self.fem_ctrl_0+11, 22)    # local reset ccc local link
        
            self.config_asic_ccc_veto()
        
            self.config_asic_ccc_fast_xml() # Loads CCC fem fast bram from xml file
        else:
            if self.femDebugLevel >= 2:
                print "Start OLD Fast Wrapper config_asic_fast_xml "
            self.config_asic_fast_xml() # Loads fem fast bram from xml file
            
            self.register_clear_bit(self.fem_ctrl_0+10, 17)  # reenable trigger strobes if NOT using real ccc commands

            
        t4 = datetime.now()

        if self.femDebugLevel >= 0:
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
                        
        if self.femDebugLevel >= 2:
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
        if self.femDebugLevel >= 3:
            print "--------------------- Clock and control is set to be ", cccEna, "---------------------"
        fileCmdSeqComplete = LpdAsicCommandSequence(self.femAsicCmdSequence, fromFile=True, cccEnabled=cccEna)
        encodedSequenceComplete  = fileCmdSeqComplete.encode()
        nr_wordsComplete = fileCmdSeqComplete.getTotalNumberWords()
        nr_nopsComplete  = fileCmdSeqComplete.getTotalNumberNops()
        if self.femDebugLevel >= 3:
            print "nr_wordsComplete = %d, nr_nopsComplete =%d: " % (nr_wordsComplete, nr_nopsComplete)
        
        # Ask where trigger section begins 
        (initial_nops, initial_words) = (fileCmdSeqComplete.getTriggerLocation())
        if self.femDebugLevel >= 3:
            print "initial_words = %d,initial_words =%d: " % (initial_words, initial_nops)
                  
        encodedSequenceStart = encodedSequenceComplete[:initial_words]
        encodedSequenceStop = encodedSequenceComplete[initial_words:]


# repeat with cccEnabled=False  only if not using ccc vetos 
        if self.cccSystemMode != 2: 

            cccEna = False          
            if self.femDebugLevel >= 3:
                print "--------------------- Clock and control is set to be ", cccEna, "---------------------"
            fileCmdSeqComplete = LpdAsicCommandSequence(self.femAsicCmdSequence, fromFile=True, cccEnabled=cccEna)
            encodedSequenceComplete  = fileCmdSeqComplete.encode()
            nr_wordsComplete = fileCmdSeqComplete.getTotalNumberWords()
            nr_nopsComplete  = fileCmdSeqComplete.getTotalNumberNops()
            if self.femDebugLevel >= 3:
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
# changed to (ccc_start_nwords-1) so that 1st trigger flag set goes out in xray pulse immediately after trigger pointer start
        ccc_start_delay = self.cccVetoStartDelay - ((ccc_start_nwords-1) * self.NR_CLOCKS_PER_FAST_CMD) + 1
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
        
        # Nb If NOT using ccc vetos the start section is loaded with COMPLETE command file  <== ***
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

        # clear previous values
        
        self.zero_regs(self.ccc_cmd_gen_bram+0, self.CCC_EMULATOR_BRAM_SIZE_BYTES) 
        
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
            self.rdmaWrite(self.ccc_cmd_gen_bram+3, 0x00301030)     # 0x00301030 => bunch pattern index = 01
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
        self.rdmaWrite(self.ccc_cmd_gen_bram+8, 0x00280100) # -- no veto  bx 2
#        self.rdmaWrite(self.ccc_cmd_gen_bram+8, 0x00300180) # -- veto  bx 3 
        self.rdmaWrite(self.ccc_cmd_gen_bram+9, 0x00280200) # -- no veto  bx 4  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+10, 0x00380280) # -- golden  bx 5   ;  total of 4 triggers  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+11, 0x00380300) #  -- golden  bx 6  
##        self.rdmaWrite(self.ccc_cmd_gen_bram+12, 0x00380300) #  -- golden  bx 6  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+12, 0x00300380) # -- veto  bx 7  
#        self.rdmaWrite(self.ccc_cmd_gen_bram+13, 0x00280400) #  -- no veto  bx 8    ; total 6 triggers
#        self.rdmaWrite(self.ccc_cmd_gen_bram+14, 0x002DDD80) #  -- no veto  bx ID = $BBB  for cable test 
#        self.rdmaWrite(self.ccc_cmd_gen_bram+15, 0x00280500) #  -- no veto  bx 10     ;  total of 8 triggers  
        
#        for i in range (16, 400):  # with increased size bram 
#          self.rdmaWrite(self.ccc_cmd_gen_bram+i, 0x00280080) # -- no veto  bx 1  


##### Must also MAKE sure the Pattern BRAM contents in config_asic_ccc_veto() enable these triggers   ############


# veto command locations are set by registers for RESET start and offset

        self.rdmaWrite(self.ccc_cmd_gen_reg + 6, 6) # start corresponding to bram filling above            
        self.rdmaWrite(self.ccc_cmd_gen_reg + 7, 400)  # nr of veto/nveto cmds above    ;  increase to read more veto command words           

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
                print "Veto Mask Pattern File Nane = %s " %self.cccVetoPatternFile
            
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
            
            
            if self.cccSimpleEmulation == True:
                self.rdmaWrite(start_addr+0, 0x0fffffff)   # any unmasked bits will give trigger
            else:
                self.rdmaWrite(start_addr+0, 0x00000000)   # 1st word has triggers ; bit 0 corresponds to 1st bunch
            self.rdmaWrite(start_addr+1, 0xffffffff)   # 
            self.rdmaWrite(start_addr+2, 0xffffffff)   # 
            self.rdmaWrite(start_addr+3, 0xffffffff)   # 
            for i in range (4,self.NR_WORDS_PER_CCC_VETO_PATTERN):         
                self.rdmaWrite(start_addr+i, 0xffffffff)   # subsequent words are all vetos

    def config_asic_datarx(self):
        ''' Configure Asic data rx module '''
        if os.name == 'nt':
            self.femAsicEnableMask = [0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff]
        
        # Convert femAsicEnableMask from user format into fem's format
        self.femAsicEnableMaskRemap = self.femAsicEnableCalculate(self.femAsicEnableMask)
        
        # Convert femAsicGain from user format into fem's format
        self.femAsicGainRemap = self.FEM_ASIC_GAIN_LOOKUP[self.femAsicGain]

        no_asic_cols = self.numberImages - 1
        no_asic_cols_per_frm = self.numberImages - 1  # all images will be in one LL frame
             
        if no_asic_cols < 0:
            no_asic_cols = 0

        if no_asic_cols_per_frm < 0:
            no_asic_cols_per_frm = 0

        # Setup the ASIC RX IP block
        self.fem_asic_rx_setup(self.asic_srx_0, self.femAsicEnableMaskRemap, no_asic_cols, no_asic_cols_per_frm)

        # NEW ; use info on nr triggers coming with readout strobe from CCC to determine how many images to process
        # this overrides asicrx register settings for ncols  etc          
        if self.cccSystemMode != 2:  
            print "INFO: Number of Images to readout from value in config xml file"
            self.register_clear_bit(self.asic_srx_0+0, 12)
        else:
            if self.cccProvideNumberImages == False:
                print "**WARNING: In CC Mode with Vetos ; OVERRIDING number of Images to readout from value in config xml file"
                self.register_clear_bit(self.asic_srx_0+0, 12)
            else:
                print "INFO: In CC Mode with Vetos ; Num Images readout according to CCC Veto input"
                self.register_set_bit(self.asic_srx_0+0, 12)


        # NEW ; if NOT using CCC to provide TrainID for header then insert dummy incrementing TrainID  
        if self.cccSystemMode == 1 or self.cccSystemMode == 2: 
            self.register_clear_bit(self.asic_srx_0+0, 16)  # disable dummy train id 
        else:
            self.rdmaWrite(self.asic_srx_0+8, self.femTrainIdInitLsw)   # set initial value for dummy train id lower word (minus 1)
            self.rdmaWrite(self.asic_srx_0+10, self.femTrainIdInitMsw)   # set initial value for dummy train id upper word 
            self.toggle_bits(self.asic_srx_0+0, 17)  # reset dummy train id
            self.register_set_bit(self.asic_srx_0+0, 16)  # enable dummy train id 

        # NEW ; insert FEM module ID into header         
        moduleId = self.femModuleId[9-1]     
        #print "FEM moduleId = %d" %moduleId
        self.rdmaWrite(self.asic_srx_0+9, moduleId)    

        # Data source - self test
        if self.femAsicDataType == self.ASIC_DATA_TYPE_RX_COUNTING:            
            self.asicrx_self_test_counting_data_enable()
            if self.femAsicTestDataPatternType:            
                self.register_set_bit(self.asic_srx_0+1, 4)  # counting data changes every Image
            else:            
                self.register_clear_bit(self.asic_srx_0+1, 4)  # counting data changes every Pixel
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


# assign local variable here rather than using self.asicRx2tileStart as latter's state is kept between Gui configures
        asicRx2tileStart_i =  self.asicRx2tileStart  # adjustment for SP3 IO DCM
          
        # new timing needed for PPC readout with asicrx generating 2 Llink frames per Train
        # need to bring start strobe to asicrx earlier
        if self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC:   # asic data via ppc 
            if (self.get_v5_firmware_vers() & 0xffff) >= 0x027e :
                asicRx2tileStart_i -= 400;
            else:
                asicRx2tileStart_i =  self.asicRx2tileStart
          
        if (self.sp3_io_bot_firmware_modules & 0x00000001) == 0:    # assumes f/w is same in top sp3    

            if self.femDebugLevel >= 1:
                print "Not using DCM for Clock in SP3 IO"
            
            if self.femAsicSlowedClock:
                self.register_set_bit(self.fem_ctrl_0+8, 1)    # enable Swap DDR pair of asicrx  
                self.register_clear_bit(self.fem_ctrl_0+8, 0)    # disable timing shift of odd asic rx
            else:
                self.register_set_bit(self.fem_ctrl_0+8, 0)    # disable Swap DDR pair of asicrx  
                self.register_clear_bit(self.fem_ctrl_0+8, 1)    # enable timing shift of odd asic rx

        else: # with DCM in SP3 IO

            if self.femDebugLevel >= 1:
                print "Using DCM for Clock in SP3 IO"
            
            self.register_set_bit(self.fem_ctrl_0+8, 1)    # enable Swap DDR pair of asicrx  
            
            self.register_clear_bit(self.fem_ctrl_0+8, 0)    # disable timing shift of odd asic rx
                
# assign local variable here rather than using self.asicRx2tileStart as latter's state is kept between Gui configures
            asicRx2tileStart_i -=  1  # adjustment for SP3 IO DCM
        
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

        if self.femDebugLevel >= 2:
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

        if self.femDebugLevel >= 3:
            print "userMask => femMask"
            #print "==================="
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
                        if self.femDebugLevel >= 3:
                            print "Sending CCC Start and Vetos using C&C System EMULATION  CCC Cmd Gen"

                        self.register_set_bit(self.fem_ctrl_0+10, 16)  # mux select inputs from generator

                        self.toggle_bits(self.fem_ctrl_0+10, 10)  # ccc start   , vetos follow after programmed delay
                        #self.toggle_bits(self.fem_ctrl_0+10, 11)  # ccc stop ; just for test as not actually used to start readout
                        #self.toggle_bits(self.fem_ctrl_0+10, 12)  # ccc reset ; just for test as not actually used to reset
                    else:
                        if self.femDebugLevel >= 3:
                            print "Sending CCC Start and Stop in RX BYPASS"
                        self.toggle_bits(self.fem_ctrl_0+10, 8)  # ccc start Rx bypass
                        self.toggle_bits(self.fem_ctrl_0+10, 9)  # ccc stop Rx bypass
                else:
                    print "Trigger Fast Seq"
                    self.toggle_bits(self.fem_ctrl_0+7, 1)  # Asic seq without slow or asicrx strobe (slow params are loaded once only during configutation) 
        else:
            print "Warning undefined Trigger Asic"
                    
    def dump_registers(self):
        ''' Dump registers '''
        
        #print "Dump of FEM Registers : TOP LEVEL CTRL"
        #self.dump_regs_hex(self.fem_ctrl_0, 18)

        #print "Dump of FEM Registers : PPC1 BRAM"
        #self.dump_regs_hex(self.bram_ppc1, 20)
        
        print "Dump of FEM Registers : XAUI link 1"
        self.dump_regs_hex(self.udp_10g_0, 16)

        print "Dump of FEM Registers : DATA GEN on link 1"
        self.dump_regs_hex(self.data_gen_0, 8)

        #print "Dump of FEM Registers : ASIC RX"
        #self.dump_regs_hex(self.asic_srx_0, 16)

        print "Dump of FEM Registers : ASIC FAST CTRL"
        self.dump_regs_hex(self.fast_cmd_0, 12)

        print "Dump of FEM Registers : ASIC FAST BRAM"
        self.dump_regs_hex(self.fast_cmd_1, 16)
        #self.dump_regs_hex(self.fast_cmd_1+(self.FAST_BRAM_SIZE_BYTES*4)-16, 30) # deliberately looking beyond end of physical BRAM

        print "Dump of FEM Registers : ASIC SLOW CTRL"
        self.dump_regs_hex(self.slow_ctr_0, 12)

        print "Dump of FEM Registers : ASIC SLOW BRAM"
        self.dump_regs_hex(self.slow_ctr_1+16, 8)   # 1024

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
            self.dump_regs_hex(self.cfg_sp3_ctrl, 8)
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

        if self.femDebugLevel >= 3:
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

        if self.numberImages == 0:  # FIX for special case if only capturing NO images
            no_asic_cols_cols_frm = 0x00000000
        if self.numberImages == 1:  # FIX for special case if only capturing just ONE image
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
        no_clk_cyc_dly = (self.LPD_NUM_PIXELS_PER_ASIC * 36 * (no_cols_frm + 1)) - 36       # as no_cols starts from '0'

                  
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

        if self.femDebugLevel >= 5:
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


    def checkEventLength(self, numImages, numTrains, llmonEventLength, llmonTotalData, dataFormat, numRxFramesperTrain):
        ''' 
            Calculate the expected event length in bytes
        '''
        # To check Llink data lengths coming from ASIC Rx (against corresponding LLMon)
        # *** NB This function only works if numImages per Train is FIXED
        
        # For readout with LPD Data Formatting ; 
        # lpd headers and trailers in the data payload
        # lpd header ; image data ; image descriptors ; lpd detector dependent ; lpd trailer ; 
        # all sizes in BYTES
        
        # All LPD blocks are padded to align on 32 byte boundaries
        # consequence of FIFO input width (256 bits) in Asicrx firmware module
        
        # numRxFramesperTrain = 2 for new AsicRx module
        # Frame 1 with XFEL Header & Det Spec
        # Frame 2 with Dummy Short Header & Image Data & Trailer
        # NB Image Descriptors are added by PPC
        # Frame 2 should always be the "last" Frame 
        
 
        LL_HEADER_SIZE = 32   # Local Link          
        LL_TRAILER_SIZE = 32

        MIN_LPD_BLOCK_SIZE = 32
        
        LPD_TRAILER_SIZE = (1*32); # includes crc
        
        if ((self.get_v5_firmware_vers()&0xffff) >= 0x026e):        
            LPD_HEADER_SIZE = 64 # xfel format may 2015 
        else:       
            LPD_HEADER_SIZE = 32 # xfel format feb 2015

        FRAME2_DUMMY_TRAILER_SIZE = 32   # redundant trailer block sent with Frame 2 (fudge to ensure sop when 0 images in train)

        # Number of Image Descriptors are now Variable :
        # aligned on 32 byte boundaries
        # 1) storageCellNumber (2 bytes)
        # 2) bunchNumber (8 bytes)
        # 3) status (2 bytes)
        # 4) length (4 bytes)
        
        LPD_IMAGE_DESCRIPTOR_SIZE_STORAGE_CELL = 2; 
        LPD_IMAGE_DESCRIPTOR_SIZE_BUNCH_NUMBER = 8; 
        LPD_IMAGE_DESCRIPTOR_SIZE_IMAGE_STATUS = 2; 
        LPD_IMAGE_DESCRIPTOR_SIZE_IMAGE_LENGTH = 4; 
        
        LPD_DETECTOR_SPECIFIC_SIZE = (13*32); # fixed with trigger information from C&C module

        LPD_IMAGE_DESCRIPTOR_SIZE = 8192;  # 0 # 8192

        LPD_IMAGE_SIZE = 0x20000;  # is aligned on 32 bytes
        
        llHeaderLength =  LL_HEADER_SIZE      # local link header is stripped off by 10g block (but counted by ll monitor)
        llTrailerLength = LL_TRAILER_SIZE     # local link trailer is stripped off by 10g block (but counted by ll monitor)
        
        lpdHeaderLength = LPD_HEADER_SIZE
        lpdTrailerLength = LPD_TRAILER_SIZE
        
        lpdImageDataLength = numImages * LPD_IMAGE_SIZE
        
        # blocks are padded to 32 byte alignment
        
        numDescriptorsPerBlockStorageCell = MIN_LPD_BLOCK_SIZE / LPD_IMAGE_DESCRIPTOR_SIZE_STORAGE_CELL
        numDescriptorsPerBlockBunchNumber = MIN_LPD_BLOCK_SIZE / LPD_IMAGE_DESCRIPTOR_SIZE_BUNCH_NUMBER
        numDescriptorsPerBlockImageStatus = MIN_LPD_BLOCK_SIZE / LPD_IMAGE_DESCRIPTOR_SIZE_IMAGE_STATUS
        numDescriptorsPerBlockImageLength = MIN_LPD_BLOCK_SIZE / LPD_IMAGE_DESCRIPTOR_SIZE_IMAGE_LENGTH
        
        if dataFormat == 1:      # fixed 512 image descriptors      
            lenDescriptorsStorageCell = self.LPD_PIPELINE_LENGTH * LPD_IMAGE_DESCRIPTOR_SIZE_STORAGE_CELL
            lenDescriptorsBunchNumber = self.LPD_PIPELINE_LENGTH * LPD_IMAGE_DESCRIPTOR_SIZE_BUNCH_NUMBER
            lenDescriptorsImageStatus = self.LPD_PIPELINE_LENGTH * LPD_IMAGE_DESCRIPTOR_SIZE_IMAGE_STATUS
            lenDescriptorsImageLength = self.LPD_PIPELINE_LENGTH * LPD_IMAGE_DESCRIPTOR_SIZE_IMAGE_LENGTH
        else:                   # variable nr image descriptors
            if numImages == 0:
                lenDescriptorsStorageCell = 0
                lenDescriptorsBunchNumber = 0
                lenDescriptorsImageStatus = 0
                lenDescriptorsImageLength = 0
            else:
                lenDescriptorsStorageCell = ((numImages-1) / numDescriptorsPerBlockStorageCell + 1) * MIN_LPD_BLOCK_SIZE
                lenDescriptorsBunchNumber = ((numImages-1) / numDescriptorsPerBlockBunchNumber + 1) * MIN_LPD_BLOCK_SIZE
                lenDescriptorsImageStatus = ((numImages-1) / numDescriptorsPerBlockImageStatus + 1) * MIN_LPD_BLOCK_SIZE
                lenDescriptorsImageLength = ((numImages-1) / numDescriptorsPerBlockImageLength + 1) * MIN_LPD_BLOCK_SIZE
         
        
        lenDescriptorsTotal = lenDescriptorsStorageCell + lenDescriptorsBunchNumber + lenDescriptorsImageStatus + lenDescriptorsImageLength
        
        lpdDectectorSpecificLength = LPD_DETECTOR_SPECIFIC_SIZE
        
        lpdEventLength = lpdHeaderLength + lpdImageDataLength + lenDescriptorsTotal + lpdDectectorSpecificLength + lpdTrailerLength 
        
        if numRxFramesperTrain == 2: 
            frame1Length = lpdHeaderLength + lpdDectectorSpecificLength + llHeaderLength + llTrailerLength
            frame2Length = FRAME2_DUMMY_TRAILER_SIZE + lpdImageDataLength + lpdTrailerLength + llHeaderLength + llTrailerLength      
            lastFrameLength = frame2Length
            totalExpectedData = (frame1Length + frame2Length) * numTrains
        else:
            lastFrameLength = llHeaderLength + lpdEventLength + llTrailerLength
            totalExpectedData = lastFrameLength * numTrains

        print "  ------------------------------------------------------------------------" 
        if self.femDebugLevel >= 3:
            print "Expected Event Data Length in Bytes for Num Trains = %d and Num Images = %d :" %(numTrains, numImages)
            if dataFormat == 1:      # fixed 512 image descriptors 
                print "Event Format with Fixed 512 Image Descriptors"
            else:
                print "Event Format with Variable number of Image Descriptors"
            print "              Local Link Header = %d \t ($%08x)" %(llHeaderLength, llHeaderLength)
            print "             Local Link Trailer = %d \t ($%08x)" %(llTrailerLength, llTrailerLength)
            print "                     LPD Header = %d \t ($%08x)" %(lpdHeaderLength, lpdHeaderLength)
            print "                     LPD Images = %d \t ($%08x)" %(lpdImageDataLength, lpdImageDataLength)
            print " LPD Descriptors [Storage Cell] = %d \t ($%08x)" %(lenDescriptorsStorageCell, lenDescriptorsStorageCell)
            print " LPD Descriptors [Bunch Number] = %d \t ($%08x)" %(lenDescriptorsBunchNumber, lenDescriptorsBunchNumber)
            print " LPD Descriptors [Image Status] = %d \t ($%08x)" %(lenDescriptorsImageStatus, lenDescriptorsImageStatus)
            print " LPD Descriptors [Image Length] = %d \t ($%08x)" %(lenDescriptorsImageLength, lenDescriptorsImageLength)
            print "          LPD Descriptors Total = %d \t ($%08x)" %(lenDescriptorsTotal, lenDescriptorsTotal)
            print "          LPD Detector Specific = %d \t ($%08x)" %(lpdDectectorSpecificLength, lpdDectectorSpecificLength)
            print "                    LPD Trailer = %d \t ($%08x)" %(lpdTrailerLength, lpdTrailerLength)
            print "  ------------------------------------------------------------------------"
            print "               LPD Event Length = %d \t ($%08x)" %(lpdEventLength, lpdEventLength)
            print " Last Frame Length (incl LLink) = %d \t ($%08x)" %(lastFrameLength, lastFrameLength)
            print "  ------------------------------------------------------------------------"         
            print "        Total Data (incl LLink) = %d \t ($%08x)" %(totalExpectedData, totalExpectedData)
            print "  ------------------------------------------------------------------------"
        
        if lastFrameLength != llmonEventLength:
            print "***ERROR   LPD Last Frame Length Expected = %d ($%08x) but Received %d ($%08x) ; Exp-Rec = %d ($%08x)" %(lastFrameLength, lastFrameLength, llmonEventLength, llmonEventLength, (lastFrameLength - llmonEventLength), (lastFrameLength - llmonEventLength))
        else:
            print " OK        LPD Last Frame Length Expected = %d ($%08x) and Received %d ($%08x)" %(lastFrameLength, lastFrameLength, llmonEventLength, llmonEventLength)
        
        if totalExpectedData != llmonTotalData:
            print "***ERROR          LPD Total Data Expected = %d ($%08x) but Received %d ($%08x) ; Exp-Rec = %d ($%08x)" %(totalExpectedData, totalExpectedData, llmonTotalData, llmonTotalData, (totalExpectedData - llmonTotalData), (totalExpectedData - llmonTotalData))
            print "Note that Total Data checking is not valid if there are varying number of Images per Train OR if any Trains have been inhibited"
        else:
            print " OK               LPD Total Data Expected = %d ($%08x) and Received %d ($%08x)" %(totalExpectedData, totalExpectedData, llmonTotalData, llmonTotalData)
        print "  ------------------------------------------------------------------------" 
  
          
        
        return totalExpectedData

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

        print " Firmware:" 
        print "     V5 FPGA Firmware vers = %08x" % self.get_v5_firmware_vers()
        print "BOT SP3 FPGA Firmware vers = %08x" % self.get_bot_sp3_firmware_vers()
        print "TOP SP3 FPGA Firmware vers = %08x" % self.get_top_sp3_firmware_vers()
        print "CFG SP3 FPGA Firmware vers = %08x" % self.get_cfg_sp3_firmware_vers()
        
        print " Embedded PPC Software:" 
        print "  PPC1 s/w vers = %08x" % self.ppc1_get_sw_vers() 
        print "  PPC2 s/w vers = %08x" % self.ppc2_get_sw_vers()

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
        
        femDataSourceNames = { 0 : "Std ASIC [via PPC1 and DDR2 Memory]",
                            1 : "Std ASIC [Direct from AsicRx]",
                            2 : "Test Frame Generator",
                            3 : "Test PPC DDR2"
                          }

        print "femAsicClockSource  = %s" % femAsicClockSourceNames[self.femAsicClockSource]
        print "femStartTrainSource = %s" % femStartTrainSourceNames[self.femStartTrainSource]
        print "femAsicModuleType   = %s" % femAsicModuleTypeNames[self.femAsicModuleType]
        print "femAsicDataType     = %s" % femAsicDataTypeNames[self.femAsicDataType]
        print "femDataSource       = %s" % femDataSourceNames[self.femDataSource]
        print "cccSystemMode       = %s" % cccSystemModeNames[self.cccSystemMode]

        if self.cccSystemMode != 0 :
            if self.cccEmulationMode == True:
                print "***WARNING: C&C signals are being EMULATED inside the FEM. Set param 'cccEmulationMode'=False to run with a REAL C&C System."
            
        print "================"
        print "OS name is %s" %(os.name)
        print "================"

        if 0:
            test1 = (0x45 << 32) | 0x123
            print " test1 (64 bits) = $%x" %(test1)
          
            test1 = float(self.numberTrains * self.cccEmulatorNumFixedRateStarts * self.cccEmulatorIntervalBetweenFixedRateStarts)/float(100000000)
            print "Waiting %f secs for end of Fixed Rate Trains before Stopping PPC Readout " %(float(test1))
            time.sleep(float(test1))

            return
            
        self.zero_regs(self.bram_ppc1, 20)  # Clear ppc ready
  
        self.init_ppc_bram(self.bram_ppc1, 0xBEEFFACE)

        if 1:
            self.resetFwModulesToggleTristateIO()

        # Use FEM 100 Mhz Osc as Asic clock source during first stages of configuration
        # As need 100 Mhz clock source for rdma access for SP3 IO channel selection during loading of Slow Setup Paramaters  
        # Don't change to selected asic clock until the Fast Asic Command words are sent and readout starts       
        self.config_asic_clock_source_from_osc()

        # NEW reset to CCC IDELAY logic
        if self.femDebugLevel >= 0:        
            print "Sending Reset to CCC IDELAY logic"
        self.toggle_bits(self.fem_ctrl_0+11, 25)                
        
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

                ## compute the DMA buffer sizes based on the numberImages in the Train(s)
                ## whole nr of Trains must fit in the BD ring buffers 
        
                #maxNrImagesPerBD = 127  # limit the nr of images in a BD (physical limit is 127)
                #nrTrainsInMemory = 4   # allow for N Trains worth in BDs

                #nrBufsPerTrain = (self.numberImages / maxNrImagesPerBD) + 1
                #if ((self.numberImages % maxNrImagesPerBD) == 0):
                  #if ((self.get_v5_firmware_vers()&0xffff) >= 0x0270): # for PPC readout with new XFEL Data format May 2015  
                    #dummy = 0  
                    ## even if nr images fits exactly into BDs still need an extra BD to hold overspill from header and trailer
                    ## and if not works if header and trailer size will be less than that of one image 
                  #else:
                    #nrBufsPerTrain -= 1
                #BufCount = nrBufsPerTrain * nrTrainsInMemory   # ensure whole nr of Trains in BD ring
                #BufCount = 10   
                BufCount = self.NUM_TRAINS_TO_STORE_IN_BD_RING    # param is now used to set how many Trains to store at one time

                #set debug printout level by writing directly to the PPC shared BRAM (via PPC2 raw memory map)
                self.ppc_set_debug_printout(self.ppcDebugLevel, self.ppcDebugLevel2)
                
                # enable ppc1 pipleline emulation 
                if self.femPpcEmulatePipeline == True:
                    if self.cccSystemMode != 2:
                        print "WARNING ** CMD_ACQ_CONFIG. self.cccSystemMode != 2 ; so Disabled PPC Pipeline Emulation "
                        self.ppc_disable_pipeline_emulation()
                    else:
                        print "CMD_ACQ_CONFIG. Enabled PPC Pipeline Emulation "
                        self.ppc_enable_pipeline_emulation()
                else:                                 
                    print "CMD_ACQ_CONFIG. Disabled PPC Pipeline Emulation "
                    self.ppc_disable_pipeline_emulation()

                # enable ppc1 reordering of Image readout by pulse nr 
                if self.femPpcImageReordering == True:              
                    if self.cccSystemMode != 2:
                        print "WARNING ** CMD_ACQ_CONFIG. self.cccSystemMode != 2 ; so Disabled PPC Reordering of Images "
                        self.ppc_disable_image_reordering()
                    else:
                        print "CMD_ACQ_CONFIG. Enabled PPC Reordering of Images "
                        self.ppc_enable_image_reordering()
                else:                                 
                    print "CMD_ACQ_CONFIG. Disabled PPC Reordering of Images "
                    self.ppc_disable_image_reordering()
                  
                # enable ppc1 pipleline emulation 
                if self.ppc1_disable_tx_dma == True:               
                    print "CMD_ACQ_CONFIG. DISABLED TX DMA *** TEST ONLY ***"
                    self.ppc_disable_tx_dma()
                else:                                 
                    print "CMD_ACQ_CONFIG. Enabled PPC Tx (& Rx) DMA "
                    self.ppc_enable_tx_dma()

                if self.ppc1_override_pipeline_defaults == True:
                    # for tests override ppc1 defaults
                    pNumPulsesInTrain = self.NR_BUNCHES_IN_TRAIN_OVERRIDE
                    pPipelineLength = self.LPD_PIPELINE_LENGTH_OVERRIDE
                else:
                    pNumPulsesInTrain = self.NR_BUNCHES_IN_TRAIN
                    pPipelineLength = self.LPD_PIPELINE_LENGTH
                  
                self.rawWrite(self.ppc_shared_bram_base + 128*4 + 8, pNumPulsesInTrain)
                self.rawWrite(self.ppc_shared_bram_base + 128*4 + 12, pPipelineLength)

                BufSize = 0    # now redundant  # (maxNrImagesPerBD * self.lpd_image_size)   
                #NumAcqs = 0   # now redundant self.numberTrains * nrBufsPerTrain     # number of BDs to process
                #Coalesce = self.numberImages     # now redundant  # for LPD use this param instead to pass the nr of images to set up Tx descriptors                
                Coalesce = 16    # Pass but is ignored now     # NMax nr of images allowed per BD (up to 127)
                # Nr Trains this run for PPC1 to process and then stop
                if self.cccEmulatorFixedRateStarts == True:
                    NumAcqs = self.numberTrains * self.cccEmulatorNumFixedRateStarts  # fixed rate trains
                else:
                    NumAcqs = self.numberTrains  
                
                print "CMD_ACQ_CONFIG. Total Nr Trains to Store concurrently in Memory = %d  " % (BufCount)
                #print "CMD_ACQ_CONFIG. Nr BDs to Process this Run = %d ; Length of BD = $%08x bytes" % ( NumAcqs, BufSize)
                
                ##AcqMode = FemTransaction.ACQ_MODE_TX_ONLY
                AcqMode = FemTransaction.ACQ_MODE_NORMAL
                if (AcqMode == FemTransaction.ACQ_MODE_TX_ONLY):
                    print "*** WARNING TESTING  FemTransaction.ACQ_MODE_TX_ONLY " 
                self.acquireSend(FemTransaction.CMD_ACQ_CONFIG, AcqMode, BufSize, BufCount, NumAcqs, Coalesce)
                
                # init buffer memory takes a while
                buffer_wait = 1 * BufCount #  10 * BufCount
                print "Waiting %d secs for PPC Buffers to be Initialised... " %(buffer_wait) 
                time.sleep(buffer_wait)

        #print "TEST Reset of PPC2"        
        #self.reset_ppc(2) # Reset ppc nr 2  ############   TEST , careful as it kills the gbe!     

        #TODO: Still needed for local link generator or redundant?
        # Setup data gen - not necessary for actual data but leave alone, "just in case"
        self.config_data_gen()

        if self.femDebugLevel >= 0:        
            print "--"
            print "Configuring ASICs..."

        if self.femDebugLevel >= 2:
            print "INFO start config_trig_strobe  "
        self.config_trig_strobe()   # External trigger strobes

        if self.femDebugLevel >= 2:
            print "INFO start config_sp3io_top  "
        try:
            self.config_sp3io_top()   
        except FemClientError:
            print "WARNING: config_sp3io_top failed"
        
        if self.femDebugLevel >= 2:
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
            if self.femDebugLevel >= 2:
                print "INFO config_asic_modules  "
            self.config_asic_modules()
            
        if self.cccEmulatorFixedRateStarts == True:
            # set up for fixed rate strobes if using ccc cmd gen
            # this will send a fixed nr of trains at fixed interval after if running with s/w triggers
            # assumes param self.numberTrains = 1
            self.rdmaWrite(self.fem_ctrl_top2+1, self.cccEmulatorIntervalBetweenFixedRateStarts)  # nb usig new top level ctrl regs
            self.rdmaWrite(self.fem_ctrl_top2+2, self.cccEmulatorNumFixedRateStarts)
            self.register_set_bit(self.fem_ctrl_0+10, 20)  # enable
            print "INFO Setting up Fixed Rate Triggers to ccc cmd start gen  "
            print "numFixedRateTrigs = %d ; gapBetweenFixedRateTrigs = %d " %(self.cccEmulatorNumFixedRateStarts, self.cccEmulatorIntervalBetweenFixedRateStarts)
        else:
            self.register_clear_bit(self.fem_ctrl_0+10, 20)  # disable
          
        # LPD Frame Checker setup
        # defaults for checking magic words etc are setup in reset values of rdma regs           
        
        # New values after 64b field little endian correction  f/w 0297
        self.rdmaWrite(self.lpd_checker+1, 0xBEEFFACE)  # magic header
        self.rdmaWrite(self.lpd_checker+2, 0x58544446)
        self.rdmaWrite(self.lpd_checker+3, self.femTrainIdInitLsw)  # train id lower init
        self.rdmaWrite(self.lpd_checker+4, self.femTrainIdInitMsw)  # train id upper init
        self.rdmaWrite(self.lpd_checker+5, 0xDEADABCD)  # magic trailer
        self.rdmaWrite(self.lpd_checker+6, 0x58544446)
        
        self.toggle_bits(self.lpd_checker+0, 0)  # reset to load these new reg values to h/w

    def run(self):
        '''
            Execute run
        '''
        try:

            #return 1       # TEST 


            print "--"           
            print "Starting Run ..."

            # check that a valid clock is being sent to the ASICs
            valid_clock = self.get_asic_clock_status()
            if valid_clock == 0:
                print "*** ERROR: There is NO VALID CLOCK to the ASIC" 
                #print "*** RUN was ABORTED."
                #print "*** Please verify the ASIC clock source." 
                #return 99

            # Clear the monitors at run start is needed for running with the LpdFemGui
            self.clear_ll_monitor(self.llink_mon_asicrx)
            self.clear_ll_monitor(self.llink_mon_0)

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
                if self.femDebugLevel >= 2:
                    print "Running in PPC1 BYPASS mode..."

            print "========================================================="
            if self.cccSystemMode != 2:  
                print "Starting Sequence of %d Trains , with each Train reading out %d images" % (self.numberTrains, self.numberImages)
            else:
                if self.cccProvideNumberImages == True:
                    print "Starting Sequence of %d Trains , with each Train reading varying Number of images according to CCC Veto input" % (self.numberTrains)  
                else:              
                    print "Starting Sequence of %d Trains , with each Train reading out %d images" % (self.numberTrains, self.numberImages)

            #print "Dump of FEM Registers : TOP LEVEL CTRL"
            #self.dump_regs_hex(self.fem_ctrl_0, 18)

            if self.STOP_RUN_ON_ESC_KEY == True:
                print "--"           
                print "Hit the ESC KEY to Stop Run..." 
                print "--"           
    
            if self.femStartTrainSource == 1:  # If S/W send triggers manually         
                self.enable_ext_trig_strobe()   # # causes toggle on reset to trigger strobe module
                self.disable_ext_trig_strobe()  # this deasserts reset (not disable) ;  it is NEEDED .
                
                for i in range (1, self.numberTrains+1):

                    if self.STOP_RUN_ON_ESC_KEY == True:           

                        try:
                            tty.setcbreak(sys.stdin.fileno())    

                            print "Train nr %d" % i
                            self.send_trigger() 
                            time.sleep(3)             # Need to check if images are all readout before sending next train
                          
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
                        time.sleep(1)             # Need to check if images are all readout before sending next train
                       
    
            else:   # Else start run and use external c&c strobes

                if self.cccEmulationMode == True:   # ext trigger strobe used to start emulator
                    print "Run is STARTED. Waiting for %d trigger strobes" % self.numberTrains 
                else:
                    print "Run is STARTED. Waiting for %d CCC Start Command Sequences" % self.numberTrains 
                    
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
                       
                nr_trains = 0

                self.enable_ext_trig_strobe()   # causes toggle on reset to trigger strobe module

                if self.STOP_RUN_ON_ESC_KEY == True:           

                    try:
                        tty.setcbreak(sys.stdin.fileno())
                        
                        if self.cccEmulationMode == True:   # ext trigger strobe used to start emulator
                                                
                            while nr_trains < self.numberTrains:
                            
                                if isData():
                                    c = sys.stdin.read(1)
                                    if c == '\x1b':         # x1b is the ESC KEY
                                        print 'Pressed the ESC key ' 
                                        break
                            
                                nr_trains = self.get_ext_trig_strobe_accepted_count()
                                
                        else:   # with real ccc command input uses new counter detecting nr of start commands decoded
                          
                            while nr_trains < self.numberTrains:
                            
                                if isData():
                                    c = sys.stdin.read(1)
                                    if c == '\x1b':         # x1b is the ESC KEY
                                        print 'Pressed the ESC key ' 
                                        break
                            
                                nr_trains = self.rdmaRead(self.fem_ctrl_0+26, 1)[0]

                        
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                else:
                    
                    if self.cccEmulationMode == True:   # ext trigger strobe used to start emulator
                                            
                        while nr_trains < self.numberTrains:

                            nr_trains = self.get_ext_trig_strobe_accepted_count()
                            
                    else:   # with real ccc command input uses new counter detecting nr of start commands decoded

                        while nr_trains < self.numberTrains:

                            nr_trains = self.rdmaRead(self.fem_ctrl_0+26, 1)[0]
                        
                
                self.disable_ext_trig_strobe()
                
                print "Run is STOPPED" 
                print "nr_trains processed = %d" % nr_trains 
                    
    
            if self.femPpcMode == 1:  # continuous Train readout mode with new PPC1 code
                if self.cccEmulatorFixedRateStarts == True:
                    wait_fixed_rate_trains = float(self.numberTrains * self.cccEmulatorNumFixedRateStarts * self.cccEmulatorIntervalBetweenFixedRateStarts)/float(100000000)
                    print "Waiting %f secs for end of Fixed Rate Trains before Stopping PPC Readout " %(float(wait_fixed_rate_trains))
                    time.sleep(float(wait_fixed_rate_trains + self.wait_for_ppc_run_stop))
                else:
                    print "Waiting %f secs at end before Stopping PPC Readout " %(float(self.wait_for_ppc_run_stop))
                    time.sleep(self.wait_for_ppc_run_stop)
                 
            if 0:              
                print "*** TEST NOT Stopping PPC1 Readout . "
            else:
                if (self.femDataSource == self.RUN_TYPE_ASIC_DATA_VIA_PPC) or (self.femDataSource == self.RUN_TYPE_PPC_DATA_DIRECT):  # runs with ppc
                    print "Stopping PPC1 Readout CMD_ACQ_STOP. "
                    self.acquireSend(FemTransaction.CMD_ACQ_STOP)
    

            print "======== Train Cycle Completed ===========" 
            print "--"           
            #time.sleep(2)   # just to see output before dumping registers

            if self.femDebugLevel >= 1:
                print "--"           
                print "=======================================================================" 
        
                self.pp = pprint.PrettyPrinter(indent=4)
        
                print "     V5 FPGA Firmware vers = %08x" % self.get_v5_firmware_vers()
                print "BOT SP3 FPGA Firmware vers = %08x" % self.get_bot_sp3_firmware_vers()
                print "TOP SP3 FPGA Firmware vers = %08x" % self.get_top_sp3_firmware_vers()
                print "CFG SP3 FPGA Firmware vers = %08x" % self.get_cfg_sp3_firmware_vers()
                print "=======================================================================" 

                if self.get_top_sp3_firmware_vers() != self.get_bot_sp3_firmware_vers() :
                    print "*** WARNING:  Firmware Versions in SP3 IO TOP and BOTTOM are Different" 
            
            
            if self.femDebugLevel >= 0:
                print "--"
                print "Dump of FEM Registers : TOP LEVEL CTRL"
                self.dump_regs_hex(self.fem_ctrl_0, 32)

            if self.femDebugLevel >= 1:
                print "Dump of FEM Registers : ASIC DATA RX"
                self.dump_regs_hex(self.asic_srx_0, 32)
                
            if self.femDebugLevel >= 3:
                print "Dump of FEM Registers : XAUI link 1"
                self.dump_regs_hex(self.udp_10g_0, 16)

            if self.femDebugLevel >= 3:
                print "Dump of FEM Registers : BOT SP3 CTRL"
                try:
                    self.dump_regs_hex(self.bot_sp3_ctrl+16, 4)
                except FemClientError:
                    print "WARNING: BOT SP3 dump_regs_hex failed"

                print "Dump of FEM Registers : TOP SP3 CTRL"
                try:
                    self.dump_regs_hex(self.top_sp3_ctrl+16, 4)
                except FemClientError:
                    print "WARNING: TOP SP3 dump_regs_hex failed"

                print "Dump of FEM Registers : CFG SP3 CTRL"
                try:
                    self.dump_regs_hex(self.cfg_sp3_ctrl+16, 4)
                except FemClientError:
                    print "WARNING: CFG SP3 dump_regs_hex failed"

            if self.femDebugLevel >= 2:

#              print "Dump of FEM Registers : ASIC SLOW CTRL"
#              self.dump_regs_hex(self.slow_ctr_0, 18)

#              print "Dump of FEM Registers : ASIC SLOW BRAM"
#              self.dump_regs_hex(self.slow_ctr_1, 1024)   # 1024

                print "Dump of FEM Registers : ASIC FAST CTRL"
                self.dump_regs_hex(self.fast_cmd_0, 12)
                
                print "Dump of FEM Registers : ASIC FAST BRAM"
                self.dump_regs_hex(self.fast_cmd_1, 16)          
                
                print "Dump of FEM Registers : ASIC SLOW CTRL"
                self.dump_regs_hex(self.slow_ctr_0, 12)
        
                print "Dump of FEM Registers : ASIC SLOW BRAM"
                self.dump_regs_hex(self.slow_ctr_1+16, 8)   # 1024

                #print "Dump of FEM Registers : ASIC FAST BRAM COE"
                #self.dump_regs_hex_coe(self.fast_cmd_1, 1024)
                
                if ((self.get_v5_firmware_vers()&0xffff) >= 0x0220):
                    print "Dump of FEM Registers : CCC DELAY REG"
                    self.dump_regs_hex(self.ccc_delay_reg, 6) 
                    print "Dump of FEM Registers : CCC PATTERN ID REG"
                    self.dump_regs_hex(self.ccc_pattern_id, 12)                  
                    print "Dump of FEM Registers : CCC PATTERN BRAM"
                    self.dump_regs_hex(self.ccc_pattern_bram, 16)
                
                if ((self.get_v5_firmware_vers()&0xffff) >= 0x022d):
                    print "Dump of FEM Registers : CCC CMD GEN REG"
                    self.dump_regs_hex(self.ccc_cmd_gen_reg, 12) 
                    print "Dump of FEM Registers : CCC CMD GEN BRAM"
                    self.dump_regs_hex(self.ccc_cmd_gen_bram, 12) 
    
                print "Dump of FEM Registers : TOP LEVEL CTRL GROUP 2"
                self.dump_regs_hex(self.fem_ctrl_top2, 24)

                print "Dump of FEM Registers : TRIGGER STROBE"
                self.dump_regs_hex(self.trig_strobe, 20)
                
                print "Dump of FEM Registers :LPD CHECKER"
                self.dump_regs_hex(self.lpd_checker, 24)


            if self.femDebugLevel >= 5:
                print "Register Settings"
                self.dump_registers()
            else:
                dummy = 0
                #time.sleep(2)   # if no dump add wait to allow 10g transfers to complete
                #print "Dump of FEM Registers : TOP LEVEL CTRL"
                #self.dump_regs_hex(self.fem_ctrl_0, 18)
                #print "Dump of FEM Registers : PPC1 BRAM"
                #self.dump_regs_hex(self.bram_ppc1, 20)


            print "--"
            print "Summary of Data Readout..."
    
            print "--"    
            print "Asic Rx LLink Monitor: 32b "
            self.read_ll_monitor(self.llink_mon_asicrx, self.asicrx_llink_clock_rate)    # 220.0e6   # 200.0e6  # 225.0e6  # 230.0e6
            
            print "--"
            print "10G LLink Monitor: 64b "
            self.read_ll_monitor(self.llink_mon_0, 156.25e6)
            
            # get info from first word from veto filter
            if ((self.get_v5_firmware_vers()&0xffff) >= 0x026a):  # 1 = fixed 512 descriptors, 2 = variable nr descriptors
                cccTrainId = 0L
                cccTrainIdUpper = self.rdmaRead(self.asic_srx_0+16+0, 1)[0]
                cccTrainIdLower = self.rdmaRead(self.asic_srx_0+16+1, 1)[0]
                cccTrainId = (cccTrainIdUpper << 32) + cccTrainIdLower
                cccBunchPatternId = (0xff000000 & self.rdmaRead(self.asic_srx_0+16+2, 1)[0]) >> 24
                cccNumTriggers = (0x001ff000 & self.rdmaRead(self.asic_srx_0+16+2, 1)[0]) >> 12
            
            if self.cccSystemMode != 0:  
                print "  ------------------------------------------------------------------------" 
                print "Info from CCC Veto System for last Train in Run:"
                #print " cccTrainIdUpper = $%08x" %(cccTrainIdUpper)
                #print " cccTrainIdLower = $%08x" %(cccTrainIdLower)
                print " Train ID = $%x" %(cccTrainId)
                print " Bunch Pattern ID = %d" %(cccBunchPatternId)
                if self.cccSystemMode == 2:  
                    print " Number Triggers sent to Asic = %d" %(cccNumTriggers)
                    if self.cccProvideNumberImages == False: 
                        print "*** WARNING: Overiding Number of Images to readout = %d" %(self.numberImages)

            else:
                cccTrainId = 0L
                cccTrainIdUpper = 0
                cccTrainIdLower = 0
                cccTrainId = (cccTrainIdUpper << 32) + cccTrainIdLower
                cccBunchPatternId = 0
                cccNumTriggers = self.numberImages

            
            llmonEventLength = self.rdmaRead(self.llink_mon_asicrx+16+0, 1)[0]

            llmonTotalDataLsw = self.rdmaRead(self.llink_mon_asicrx+16+7, 1)[0]
            llmonTotalDataMsw = self.rdmaRead(self.llink_mon_asicrx+16+12, 1)[0]
            llmonTotalData = (llmonTotalDataMsw << 32) | llmonTotalDataLsw  
                                  
            if ((self.get_v5_firmware_vers()&0xffff) >= 0x0269):  # 1 = fixed 512 descriptors, 2 = variable nr descriptors
                dataFormat = 2  
            else:
                dataFormat = 1
              
            if self.cccSystemMode != 2:  
                numImages = self.numberImages
            else:
                if self.cccProvideNumberImages == True:
                    numImages = cccNumTriggers
                else:
                    numImages = self.numberImages 
              
            if self.femPpcMode == 1:
                numRxFramesperTrain = 2
            else:
                numRxFramesperTrain = 1
              
            if self.cccEmulatorFixedRateStarts == True:
                numTrainsTot = self.numberTrains * self.cccEmulatorNumFixedRateStarts  # fixed rate trains
            else:
                numTrainsTot = self.numberTrains  
            
            self.checkEventLength(numImages, numTrainsTot, llmonEventLength, llmonTotalData, dataFormat, numRxFramesperTrain)
    
    

            if self.femPpcMode == 1:
                # dump shared ppc bram with ppc1 counters status using raw memory mapped access from ppc2
                print "---------------"
                print "Dump of PPC Shared BRAM:"
                if self.femDebugLevel >= 3:
                    self.dump_raw_memory_hex(self.ppc_shared_bram_base, 40)
                    self.dump_raw_memory_hex(self.ppc_shared_bram_base+128*4, 8)
                self.ppc1_status_dump(self.ppc_shared_bram_base)

            # number of triggers
            ccc_start_count = self.rdmaRead(self.fem_ctrl_0+26, 1)[0]
            ccc_start_accepted_count = self.rdmaRead(self.fem_ctrl_0+27, 1)[0]
            print "---------------"
            print "CCC Start Train Commands:"
            print " Num CCC Starts Received = %d" %(ccc_start_count)
            print " Num CCC Starts Accepted = %d" %(ccc_start_accepted_count)

            # LPD Frame Checker results
            # 
            lpd_chk_nr_errors = self.rdmaRead(self.lpd_checker+16+1, 1)[0]
            lpd_chk_nr_hdr_words = self.rdmaRead(self.lpd_checker+16+2, 1)[0]
            lpd_chk_nr_trl_words = self.rdmaRead(self.lpd_checker+16+3, 1)[0]
            print "---------------"
            print "LPD Checker Results:"
            print " Num Errors = %d" %(lpd_chk_nr_errors)
            print " Num Header Words = %d" %(lpd_chk_nr_hdr_words)
            print " Num Trailer Words = %d" %(lpd_chk_nr_trl_words)

            

            # Switch back to FEM Osc clock as Asic clock source for run end       
            print "---------------"
            self.config_asic_clock_source_from_osc()
    
            print "--"           
            print "======== Run Completed ==========="
            print "--"           
        
        
            #print "Stopping PPC1 Readout CMD_ACQ_STOP. "
            #self.acquireSend(FemTransaction.CMD_ACQ_STOP)

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

    def integrationCyclesGet(self):
        '''
            Get the number of integration cycles per image
        '''
        return self.integrationCycles

    def integrationCyclesSet(self, aValue):
        '''
            Set the number of integration cycles per image
        '''
        self.integrationCycles = aValue

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
    
    def cccEmulatorFixedRateStartsGet(self):
        ''' 
        '''
        return self.cccEmulatorFixedRateStarts
    
    def cccEmulatorFixedRateStartsSet(self, aValue):
        ''' 
        '''
        self.cccEmulatorFixedRateStarts = aValue

    def cccEmulatorIntervalBetweenFixedRateStartsGet(self):
        ''' 
        '''
        return self.cccEmulatorIntervalBetweenFixedRateStarts
    
    def cccEmulatorIntervalBetweenFixedRateStartsSet(self, aValue):
        ''' 
        '''
        self.cccEmulatorIntervalBetweenFixedRateStarts = aValue

    def cccEmulatorNumFixedRateStartsGet(self):
        ''' 
        '''
        return self.cccEmulatorNumFixedRateStarts
    
    def cccEmulatorNumFixedRateStartsSet(self, aValue):
        ''' 
        '''
        self.cccEmulatorNumFixedRateStarts = aValue

    def femAsicTestDataPatternTypeGet(self):
        ''' 
        '''
        return self.femAsicTestDataPatternType
    
    def femAsicTestDataPatternTypeSet(self, aValue):
        ''' 
        '''
        self.femAsicTestDataPatternType = aValue

    def femPpcEmulatePipelineGet(self):
        ''' 
        '''
        return self.femPpcEmulatePipeline
    
    def femPpcEmulatePipelineSet(self, aValue):
        ''' 
        '''
        self.femPpcEmulatePipeline = aValue

    def femPpcImageReorderingGet(self):
        ''' 
        '''
        return self.femPpcImageReordering
    
    def femPpcImageReorderingSet(self, aValue):
        ''' 
        '''
        self.femPpcImageReordering = aValue

    def femLpdClientVersionGet(self):
        ''' 
        '''
        return self.femLpdClientVersion
    
    def femLpdClientVersionSet(self, aValue):
        ''' 
        '''
        self.femLpdClientVersion = aValue

    def femTrainIdInitLswGet(self):
        ''' 
        '''
        return self.femTrainIdInitLsw
    
    def femTrainIdInitLswSet(self, aValue):
        ''' 
        '''
        self.femTrainIdInitLsw = aValue

    def femTrainIdInitMswGet(self):
        ''' 
        '''
        return self.femTrainIdInitMsw
    
    def femTrainIdInitMswSet(self, aValue):
        ''' 
        '''
        self.femTrainIdInitMsw = aValue

    def dump_raw_memory_hex(self, base_addr, nr_regs):
        ''' Hex dump of raw memory mapped space (not rdma reg space) '''
        
        print "raw memory addr = $%08X" % base_addr 
        for i in range(0, nr_regs/2):
            print "word %2d = $%08X     %2d = $%08X"   % ((i*2),   self.rawRead(base_addr+(i*2*4), 1)[0], (i*2+1), self.rawRead(base_addr+(i*2*4+4), 1)[0])
            
    def ppc1_status_dump(self, base_addr):
        ''' Formatted dump of ppc1 counters from shared memory accessed by ppc2 raw memory mapped space (not rdma reg space) '''
        
        numTrainsRequested = self.rawRead(base_addr+(6*4), 1)[0]
        totalRecvBot = self.rawRead(base_addr+(9*4), 1)[0]
        numRxFrameTot1 = self.rawRead(base_addr+(13*4), 1)[0]
        numRxFrameTot2 = self.rawRead(base_addr+(14*4), 1)[0]
        totalSent = self.rawRead(base_addr+(10*4), 1)[0]
        numTxBDsExpected = self.rawRead(base_addr+(21*4), 1)[0]
        numTrainsSent = self.rawRead(base_addr+(15*4), 1)[0]
        numRxTrainsToSendPeak = self.rawRead(base_addr+(27*4), 1)[0]
        numTrainsReceived = self.rawRead(base_addr+(16*4), 1)[0]
        maxIterations = self.rawRead(base_addr+(26*4), 1)[0]
        numBotAsicRxPeak = self.rawRead(base_addr+(17*4), 1)[0]
        numTxBDsToSendPeak = self.rawRead(base_addr+(18*4), 1)[0]
                
        numImagesPeak = self.rawRead(base_addr+(19*4), 1)[0]
        numImagesTrough = self.rawRead(base_addr+(20*4), 1)[0]

        totalErrors = self.rawRead(base_addr+(24*4), 1)[0]
        nrErrorsPipelineOverflow = self.rawRead(base_addr+(25*4), 1)[0]
        nrErrorsValidateBufferRx = self.rawRead(base_addr+(58*4), 1)[0]
        nrErrorsValidateBufferTx = self.rawRead(base_addr+(59*4), 1)[0]
        nrErrorsRecycleBufferRx = self.rawRead(base_addr+(60*4), 1)[0]
        nrErrorsRecycleBufferTx = self.rawRead(base_addr+(61*4), 1)[0]
        nrErrorsRingToHWRx = self.rawRead(base_addr+(62*4), 1)[0]
        nrErrorsRingToHWTx = self.rawRead(base_addr+(63*4), 1)[0]        
        nrErrorsPipelineSkipFull = self.rawRead(base_addr+(64*4), 1)[0]

        maxIterationsPipeline = self.rawRead(base_addr+(65*4), 1)[0]
        
        print "PPC1 Ctrl Params  --------------------------"  
        pNumPulsesInTrain = self.rawRead(base_addr+(128*4 + 8), 1)[0]        
        pPipelineLength = self.rawRead(base_addr+(128*4 + 12), 1)[0]
        print "NumPulsesInTrain = %d" %(pNumPulsesInTrain)     
        print "PipelineLength = %d" %(pPipelineLength)


        print "PPC1 Status  --------------------------"         
        print "PPC1 Status from Shared BRAM @ $%08x :" % base_addr         
        print "Num Trains Requested this run = %d" %(numTrainsRequested)        
        print "Total Nr Rx BDs = %d" %(totalRecvBot)       
        print "Total Num Rx Frame 1 = %d" %(numRxFrameTot1)      
        print "Total Num Rx Frame 2 = %d" %(numRxFrameTot2)       
        print "Total Num Trains Received = %d" %(numTrainsReceived)       
        print "Total Nr Tx BDs = %d" %(totalSent)      
        print "Total Nr Tx BDs Expected = %d" %(numTxBDsExpected)             
        print "Total Nr Trains Sent to 10G (may undercount) = %d" %(numTrainsSent)      
        print "Peak Nr Trains in BD Ring = %d  (Max = %d)" %(numRxTrainsToSendPeak, self.NUM_TRAINS_TO_STORE_IN_BD_RING )              
        print "Max Nr Pipeline Skip Iterations = %d" %(maxIterationsPipeline)              
        print "Max Nr Pulse Number Reordering Iterations = %d" %(maxIterations)           
        print "Peak Nr Rx BD Buffers = %d" %(numBotAsicRxPeak)       
        print "Peak Nr Tx BD Buffers = %d" %(numTxBDsToSendPeak)       
        print "Peak Nr Images in any Train = %d" %(numImagesPeak)       
        print "Trough Nr Images in any Train = %d" %(numImagesTrough) 
        
              
        print "PPC1 Errors  --------------------------"          
        print "PipeLine Overflow = %d" %(nrErrorsPipelineOverflow)          
        print "Validate Buffer Rx = %d" %(nrErrorsValidateBufferRx)          
        print "Validate Buffer Tx = %d" %(nrErrorsValidateBufferTx)          
        print "Recycle Buffer Rx = %d" %(nrErrorsRecycleBufferRx)          
        print "Recycle Buffer Tx = %d" %(nrErrorsRecycleBufferTx)          
        print "Committing BDRingToHW Rx = %d" %(nrErrorsRingToHWRx)          
        print "Committing BDRingToHW Tx = %d" %(nrErrorsRingToHWTx)        
        print "Pipeline Skips FULL= %d" %(nrErrorsPipelineSkipFull)
        if totalErrors == 0:         
            print "OK TOTAL PPC1 Errors = %d" %(totalErrors) 
        else:                  
            print "*** TOTAL PPC1 Errors = %d" %(totalErrors)
        
             
        print "--" 
        print "PPC1 Timers for Final Train -----------------" 
        ppc1_timer0 = self.rawRead(base_addr+(28*4), 1)[0]
        
        ppc1_timer = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        for i in range(0, 12):
            ppc1_timer[i] = self.rawRead(base_addr+((28+i)*4), 1)[0] 
            print "Timer %d - 0 = %.3g msec" %( i, float((( (ppc1_timer[i] - ppc1_timer0) * self.ppc_clock_period ) / 1000) ) / 1000 )         
        
        timer_postProcessRxFrame1 = ppc1_timer[2] - ppc1_timer[1]  
        timer_lpd_emulate_asic_pipeline = ppc1_timer[5] - ppc1_timer[3]  
        timer_order_images_by_pulse_nr = ppc1_timer[6] - ppc1_timer[5] 
        timer_lpd_update_image_descriptors = ppc1_timer[11] - ppc1_timer[6] 
        timer_preProcessTxBD = ppc1_timer[4] - ppc1_timer[2]
        timer_process_frame1 = ppc1_timer[4] - ppc1_timer[0]
        
        print "postProcessRxFrame1 = %.3g msec" %( float((( timer_postProcessRxFrame1 * self.ppc_clock_period ) / 1000) ) / 1000 )         
        print "emulate_asic_pipeline = %.3g msec" %( float((( timer_lpd_emulate_asic_pipeline * self.ppc_clock_period ) / 1000) ) / 1000 )         
        print "order_images_by_pulse_nr = %.3g msec" %( float((( timer_order_images_by_pulse_nr * self.ppc_clock_period ) / 1000) ) / 1000 )         
        print "update_image_descriptors = %.3g msec" %( float((( timer_lpd_update_image_descriptors * self.ppc_clock_period ) / 1000) ) / 1000 )         
        print "preProcessTxBD = %.3g msec" %( float((( timer_preProcessTxBD * self.ppc_clock_period ) / 1000) ) / 1000 )         
        print "Total Time for Processing Frame 1 = %.3g msec" %( float((( timer_process_frame1 * self.ppc_clock_period ) / 1000) ) / 1000 )         

        # assumes 200 mhz ppc proc clk                        
        #print "Timer 1 - 0 = %d micro sec" %((timer1 - timer0)/200)                          

        #print "Timer 2 - 0 = %.2g msec" %( float((( (timer2 - timer0) * 5 ) / 1000) ) / 1000 )         
        #print "Timer 3 - 0 = %.2g msec" %( float((( (timer3 - timer0) * 5 ) / 1000) ) / 1000 )         
        #print "Timer 4 - 0 = %.2g msec" %( float((( (timer4 - timer0) * 5 ) / 1000) ) / 1000 )         
        #print "Timer 5 - 0 = %.2g msec" %( float((( (timer5 - timer0) * 5 ) / 1000) ) / 1000 )         
        #print "Timer 6 - 0 = %.2g msec" %( float((( (timer6 - timer0) * 5 ) / 1000) ) / 1000 )         
        
        #print "Timer 3 - 0 = %.2e msec" %( float((( (timer3 - timer0) * 5 ) / 1000) ) / 1000 )         
        #print "Timer 6 - 0 = %.2e msec" %( float((( (timer6 - timer0) * 5 ) / 1000) ) / 1000 )         


    def ppc_set_debug_printout(self, pDebug, pDebug2):
        ''' Set debug prinout level by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4
        #print "pDebug mem addr = $%08X ; value = %d" %(addr, pDebug)
        
        self.rawWrite(addr, pDebug)
        
        addr = self.ppc_shared_bram_base + (128+4)*4
        self.rawWrite(addr, pDebug2)

    def ppc1_get_sw_vers(self):
        ''' Get ppc1 code vers shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 12*4
        return self.rawRead(addr, 1)[0]

    def ppc2_get_sw_vers(self):
        ''' Get ppc1 code vers shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 13*4
        return self.rawRead(addr, 1)[0]

    def ppc_enable_pipeline_emulation(self):
        ''' by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4 + 4
        bit = 4
        #print "pControlParams mem addr = $%08X ; ENABLE Pipeline Emulation" %(addr)
        
        self.setbit_raw_mem(addr, bit)

    def ppc_disable_pipeline_emulation(self):
        ''' by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4 + 4
        bit = 4
        #print "pControlParams mem addr = $%08X ; DISable Pipeline Emulation" %(addr)
        
        self.clrbit_raw_mem(addr, bit)

    def ppc_enable_image_reordering(self):
        ''' by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4 + 4
        bit = 0
        #print "pControlParams mem addr = $%08X ; ENABLE pulse reordering" %(addr)
        
        self.setbit_raw_mem(addr, bit)

    def ppc_disable_image_reordering(self):
        ''' by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4 + 4
        bit = 0
        #print "pControlParams mem addr = $%08X ; DISable pulse reordering" %(addr)
        
        self.clrbit_raw_mem(addr, bit)

    def ppc_disable_tx_dma(self):
        ''' by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4 + 4
        bit = 16
        #print "pControlParams mem addr = $%08X ; DISABLE TX DMA" %(addr)
        
        self.setbit_raw_mem(addr, bit)

    def ppc_enable_tx_dma(self):
        ''' by setting parm in shared memory directly using raw memory mapped space (not rdma reg space) '''
        
        addr = self.ppc_shared_bram_base + 128*4 + 4
        bit = 16
        #print "pControlParams mem addr = $%08X ; ENABLE TX DMA" %(addr)
        
        self.clrbit_raw_mem(addr, bit)

    def setbit_raw_mem(self, addr, bit):
        """ set bit in raw memory """     

        reg = self.rawRead(addr, 1)[0]
        reg |= (1 << bit)
        self.rawWrite(addr, reg) 
        
        return reg   

    def clrbit_raw_mem(self, addr, bit):
        """ set bit in raw memory """     

        reg = self.rawRead(addr, 1)[0]
        reg &= ~(1 << bit)
        self.rawWrite(addr, reg) 
        
        return reg   
    