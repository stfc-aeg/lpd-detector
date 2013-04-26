'''
    LpdReadoutTest.py - Readout a system using the API
                    
'''

from LpdDevice.LpdDevice import LpdDevice
from networkConfiguration import networkConfiguration
import sys


def LpdReadoutTest(femHost=None, femPort=None):
    
    theDevice = LpdDevice()

    # Was either femHost or femPort NOT provided to this class?
    if (femHost == None) or (femPort == None):
        # At least one wasn't supplied from the command line; Use networkConfiguration class
        networkConfig = networkConfiguration()
        femHost = networkConfig.ctrl0SrcIp
        femPort = int(networkConfig.ctrlPrt)

    rc = theDevice.open(femHost, femPort)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return

    # Display "expert" variables?
    bDebug = True

    ################################################################
    
    AsicVersion = 2    # 1 or 2
    xmlConfiguration = 2    # 0 = test, 1=short (normal) exposure, 2= long exposure (slowed down)

    if AsicVersion == 1:
        femAsicSlowedClockFlag = True    # must ensure fast cmd file corresponds with readout clock selection
        
        if xmlConfiguration == 1:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters.xml'
            FastCmdXmlString     = 'ConfigFiles/ManualReset_longExposure_AsicControl.xml'
        elif xmlConfiguration == 2:
            SlowControlXmlString = 'ConfigFiles/preambleDelaySlowControl.xml'
            FastCmdXmlString     = 'ConfigFiles/playingWivLasers.xml' # SupdMod (or 2Tile), slowed down, can use laser pointer

    elif AsicVersion == 2:
        femAsicSlowedClockFlag = False    # must ensure fast cmd file corresponds with readout clock selection
        if xmlConfiguration == 1:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/AutoResets_ShortExposures_asicv2_jacv1.xml'
        elif xmlConfiguration == 2:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/ManualReset_longExposure_asicv2_jacv1.xml' 
        else:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_SingleFrameTestPulse.xml'
            FastCmdXmlString = 'ConfigFiles/CmdsSingleFrameTestPulse.xml'

    print SlowControlXmlString
    print FastCmdXmlString
    
    ################################################################

# The second of the two command sequence configurations provided by Matt:
#        FastCmdXmlString     = 'ConfigFiles/AutoResets_ShortExposures_AsicControl.xml'

    #TODO: Temporary hack, pass filename instead of XML string
    # Read Slow Control (LpdAsicControl) XML file into a string
#    ff = open('ConfigFiles/preambleDelaySlowControl.xml', 'r')
#    SlowControlXmlString = ff.read(-1)
#    ff.close ()
    
    #TODO: Temporary hack, pass filename instead of XML string
    # Read Asic Command Sequence (LpdAsicCommandSequence) XML file into a string
#    ff = open('ConfigFiles/playingWivLasers.xml', 'r')
#    FastCmdXmlString = ff.read(-1)
#    ff.close ()

    rc = theDevice.paramSet('femAsicSlowControlParams', SlowControlXmlString)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowControlParams set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('femAsicFastCmdSequence', FastCmdXmlString)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicFastCmdSequence set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    ######################################################
    # Start configuring variables using API calls
    ######################################################

    param = 'tenGig0SourceMac'
    rc = theDevice.paramSet(param, '62-00-00-00-00-01')
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'tenGig0SourceIp'
    rc = theDevice.paramSet(param, networkConfig.tenGig0SrcIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'tenGig0SourcePort'
    rc = theDevice.paramSet(param, 0)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'tenGig0DestMac'
    rc = theDevice.paramSet(param, networkConfig.tenGig0DstMac)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'tenGig0DestIp'
    rc = theDevice.paramSet(param, networkConfig.tenGig0DstIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'tenGig0DestPort'
    rc = theDevice.paramSet(param, 61649)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
#    rc = theDevice.paramSet('femAsicEnableMask', [0x00FF0000, 0x00000000, 0x00000000, 0x000000FF])    # Enable 2 Tile System's ASICs
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF])    # Enable everything
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFF0000, 0x00000000, 0x0000FF00, 0x00000000])      # Supermodule with three tiles
    rc = theDevice.paramSet('femAsicEnableMask', 9999)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicEnableMask set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('femAsicPixelSelfTestOverride', 0)  # per-pixel override of self-test enable: 1 = enabled
    if rc != LpdDevice.ERROR_OK:
        print "femAsicPixelSelfTestOverride set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('femAsicPixelFeedbackOverride', 0)  # per-pixel override of feedback selection: 0 = high(10p), 1= low(50p)'
    if rc != LpdDevice.ERROR_OK:
        print "femAsicPixelFeedbackOverride set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('femPpcResetDelay', 0)  # Delay after resetting ppc
    if rc != LpdDevice.ERROR_OK:
        print "femPpcResetDelay set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicDataType', 0)    # 0=Normal Data, 1=Counting data, 2=Pseudo random
    if rc != LpdDevice.ERROR_OK:
        print "femAsicDataType set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicModuleType', 0) # 0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone'
    if rc != LpdDevice.ERROR_OK:
        print "femAsicModuleType set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femDataSource', 1) # 0=ASIC (via PPC), 1=ASIC (from Rxblock), 2=frame generator, 3=PPC (preprogrammed)
    if rc != LpdDevice.ERROR_OK:
        print "femDataSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicColumns', 4)    # Time-slices per trigger (images per train) - combine with ASIC command XML tag
    if rc != LpdDevice.ERROR_OK:
        print "femAsicColumns set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicLocalClock', 0) # ASIC clock scaling 0=100 MHz, 1=scaled down clock (10 MHz)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicLocalClock set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicSlowedClock', femAsicSlowedClockFlag)           # True for V1 asic, False for V2 asic
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowedClock set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicSlowLoadMode', 0)   # ASIC control load mode 0=parallel, 1=serial
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowLoadMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicRxInvertData', False)   # Invert ADC ASIC Data
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxInvertData set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicRxFastStrobe', True)    # Start ASIC capture using strobe derived from ASIC Command file
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxFastStrobe set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicVersion', AsicVersion) # 1 or 2
    if rc != LpdDevice.ERROR_OK:
        print "femAsicVersion set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    #TODO: not used?
#    rc = theDevice.paramSet('femPpcMode', 0) # 0=single train shot with PPC reset, 1=Continuous readout
#    if rc != LpdDevice.ERROR_OK:
#        print "femPpcMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0DataGenerator', 1)  # Data generator 1=DataGen 2=PPC DDR2
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DataGenerator set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0DataFormat', 0) # Data format type, 0=counting data (doesn't affect "normal" data")
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DataFormat set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0NumberOfFrames', 1) # Number of frames to send in each cycle
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0NumberOfLength set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    ######################################################
    # "Expert" variables
    ######################################################

    rc = theDevice.paramSet('tenGigInterframeGap', 0)   # 10GigE inter-frame gap timer (clock cycles)
    if rc != LpdDevice.ERROR_OK:
        print "tenGigInterframeGap set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGigUdpPacketLen', 8000) # 10GigE UDP packet payload length'
    if rc != LpdDevice.ERROR_OK:
        print "tenGigUdpPacketLen set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicGainOverride', 8)   # (Default value is 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicGainOverride set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femFastCtrlDynamic', True) # Enables Fast Control with Dynamic Vetoes
    if rc != LpdDevice.ERROR_OK:
        print "femFastCtrlDynamic set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femEnableTenGig', True)    # Enables transmission of image data via 10GigE UDP interface
    if rc != LpdDevice.ERROR_OK:
        print "femEnableTenGig set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicRxDelayOddChannels', True)  # Delay odd ASIC data channels by one clock to fix alignment
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxDelayOddChannels set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicSlowClockPhase', 0) # additional phase adjustment of slow clock rsync wrt ASIC reset
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowClockPhase set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femNumTestCycles', 7)  # number of test cycles if LL Data Generator / PPC Data Direct selected
    if rc != LpdDevice.ERROR_OK:
        print "femNumTestCycles set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGigFarmMode', 1)    # 1=disabled, 2=fixed IP,multi port, 3=farm mode with nic lists
    if rc != LpdDevice.ERROR_OK:
        print "tenGigFarmMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

#    rc = theDevice.paramSet('femI2cBus', 0x300)
#    if rc != LpdDevice.ERROR_OK:
#        print "femI2cBus set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femDebugLevel', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femDebugLevel set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0FrameLength', 0x10000)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0FrameLength set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    triggerDelay = (2+88)
    rc = theDevice.paramSet('femExternalTriggerStrobeDelay', triggerDelay)  # Fem external trigger strobe delay (in ASIC clock periods)
    if rc != LpdDevice.ERROR_OK:
        print "femExternalTriggerStrobeDelay set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femDelaySensors', 0xffef)  # delay timing of 16 sensors; bit = 1 adds 1 clock delay; sensor mod 1 is LSB
    if rc != LpdDevice.ERROR_OK:
        print "femDelaySensors set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicClockSource', 1)    #  0=Fem local oscillator, 1=Clock sync with xray
    if rc != LpdDevice.ERROR_OK:
        print "femAsicClockSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femBeamClockSource', 0)    #  Xray sync clock source 0=XFEL, 1=PETRA
    if rc != LpdDevice.ERROR_OK:
        print "femBeamClockSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femBeamTriggerSource', 1) #  0=XFEL Clock & Ctrl system, 1=Software
    if rc != LpdDevice.ERROR_OK:
        print "femBeamTriggerSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    #0=asicrx gain select fixed by register, 1=asicrx gain select taken from fast cmd file commands on the fly'
    rc = theDevice.paramSet('femGainFromFastCmd', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femGainFromFastCmd set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    
    ######################################################
    # Read back all the configured values
    ######################################################
    
    (rc, value) = theDevice.paramGet('tenGig0SourceMac')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourceMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0SourceMac \t= %s" % value

    (rc, value) = theDevice.paramGet('tenGig0SourceIp')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourceIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0SourceIp \t= %s" % value

    (rc, value) = theDevice.paramGet('tenGig0SourcePort')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourcePort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0SourcePort \t= %s" % value

    (rc, value) = theDevice.paramGet('tenGig0DestMac')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DestMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0DestMac \t\t= %s" % value

    (rc, value) = theDevice.paramGet('tenGig0DestIp')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DestIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0DestIp \t\t= %s" % value

    (rc, value) = theDevice.paramGet('tenGig0DestPort')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DestPort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0DestPort \t= %s" % value

    (rc, value) = theDevice.paramGet('tenGig0DataFormat')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DataFormat get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0DataFormat\t= %d" % value

    (rc, value) = theDevice.paramGet('tenGig0DataGenerator')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DataGenerator get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0DataGenerator\t= %d" % value

    (rc, value) = theDevice.paramGet('tenGig0NumberOfFrames')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0NumberOfFrames get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0NumberOfFrames\t= %d" % value
    
    (rc, value) = theDevice.paramGet('femAsicColumns')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicColumns get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicColumns \t\t= %d" % value

    (rc, value) = theDevice.paramGet('femAsicDataType')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicDataType get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicDataType\t\t= %d" % value
    
#    (rc, value) = theDevice.paramGet('femAsicEnableMask')
#    if rc != LpdDevice.ERROR_OK:
#        print "femAsicEnableMask get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    else:
#        print "femAsicEnableMask \t= [%8X, %8X, %8X, %8X]" %  (value[0], value[1], value[2], value[3])

    (rc, value) = theDevice.paramGet('femAsicFastCmdSequence')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicFastCmdSequence get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#        else:
#            print "femAsicFastCmdSequence:\n", value

    (rc, value) = theDevice.paramGet('femAsicLocalClock')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicLocalClock get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicLocalClock\t= %d" % value

    (rc, value) = theDevice.paramGet('femAsicModuleType')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicModuleType get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicModuleType \t= %d" % value

    (rc, value) = theDevice.paramGet('femAsicRxFastStrobe')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxFastStrobe get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicRxFastStrobe\t= ", value

    (rc, value) = theDevice.paramGet('femAsicRxInvertData')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxInvertData get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicRxInvertData\t= ", value

    (rc, value) = theDevice.paramGet('femAsicSlowControlParams')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowControlParams get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#        else:
#            print "femAsicSlowControlParams:\n", value

    (rc, value) = theDevice.paramGet('femAsicSlowedClock')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowedClock get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicSlowedClock\t= ", value

    (rc, value) = theDevice.paramGet('femAsicSlowLoadMode')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowLoadMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicSlowLoadMode\t= %d" % value

    (rc, value) = theDevice.paramGet('femDataSource')
    if rc != LpdDevice.ERROR_OK:
        print "femDataSource get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femDataSource \t\t= %d" % value
    
#    (rc, value) = theDevice.paramGet('femPpcMode')
#    if rc != LpdDevice.ERROR_OK:
#        print "femPpcMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    else:
#        print "femPpcMode\t\t= %d" % value

    rc = theDevice.paramGet('femAsicPixelSelfTestOverride')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicPixelSelfTestOverride get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicPixelSelfTestOverride\t= %d" % value
    
    rc = theDevice.paramGet('femAsicPixelFeedbackOverride')
    if rc != LpdDevice.ERROR_OK:
        print "femAsicPixelFeedbackOverride get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicPixelFeedbackOverride\t= %d" % value

    (rc, value) = theDevice.paramGet('femPpcResetDelay')
    if rc != LpdDevice.ERROR_OK:
        print "femPpcResetDelay get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femPpcResetDelay\t= %d" % value

    ######################################################
    # Display "Expert" variables' settings
    ######################################################

    if bDebug:
        (rc, value) = theDevice.paramGet('tenGig0FrameLength')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0FrameLength get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0FrameLength\t= %3X" % value

        (rc, value) = theDevice.paramGet('tenGigFarmMode')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigFarmMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigFarmMode\t\t= %d" % value
    
        (rc, value) = theDevice.paramGet('tenGigInterframeGap')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigInterframeGap get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigInterframeGap \t= %d" % value
    
        (rc, value) = theDevice.paramGet('tenGigUdpPacketLen')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigUdpPacketLen get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigUdpPacketLen \t= %d" % value

        (rc, value) = theDevice.paramGet('femAsicGainOverride')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicGainOverride get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicGainOverride \t= %d" % value

        (rc, value) = theDevice.paramGet('femAsicRxDelayOddChannels')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxDelayOddChannels get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicRxDelayOddChannels= ", value
    
        (rc, value) = theDevice.paramGet('femAsicSlowClockPhase')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowClockPhase get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicSlowClockPhase\t= %d" % value
    
        (rc, value) = theDevice.paramGet('femAsicVersion')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicVersion get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicVersion \t\t= %d." % value
    
        (rc, value) = theDevice.paramGet('femDebugLevel')
        if rc != LpdDevice.ERROR_OK:
            print "femDebugLevel get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femDebugLevel\t\t= %i" % value
    
        (rc, value) = theDevice.paramGet('femEnableTenGig')
        if rc != LpdDevice.ERROR_OK:
            print "femEnableTenGig get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femEnableTenGig\t\t= %d" % value

        (rc, value) = theDevice.paramGet('femFastCtrlDynamic')
        if rc != LpdDevice.ERROR_OK:
            print "femFastCtrlDynamic get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femFastCtrlDynamic \t= ", value
    
#        (rc, value) = theDevice.paramGet('femI2cBus')
#        if rc != LpdDevice.ERROR_OK:
#            print "femI2cBus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#        else:
#            print "femI2cBus\t\t= %3X" % value
    
        (rc, value) = theDevice.paramGet('femNumTestCycles')
        if rc != LpdDevice.ERROR_OK:
            print "femNumTestCycles get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femNumTestCycles\t= %d" % value
    
        (rc, value) = theDevice.paramGet('femExternalTriggerStrobeDelay')
        if rc != LpdDevice.ERROR_OK:
            print "femExternalTriggerStrobeDelay get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femExternalTriggerStrobeDelay\t= %d" % value
        
        (rc, value) = theDevice.paramGet('femDelaySensors')
        if rc != LpdDevice.ERROR_OK:
            print "femDelaySensors get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femDelaySensors\t= %d." % value
    
        (rc, value) = theDevice.paramGet('femAsicClockSource')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicClockSource get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicClockSource\t= %d." % value
    
        (rc, value) = theDevice.paramGet('femBeamTriggerSource')
        if rc != LpdDevice.ERROR_OK:
            print "femBeamTriggerSource get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femBeamTriggerSource\t= %d." % value

        (rc, value) = theDevice.paramGet('femGainFromFastCmd')
        if rc != LpdDevice.ERROR_OK:
            print "femGainFromFastCmd get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femGainFromFastCmd\t= %d." % value


    ######################################################
    # Configure the FEM
    ######################################################
    
    rc = theDevice.configure()
    if rc != LpdDevice.ERROR_OK:
        print "configure() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
 
    # Acquire image data
    rc = theDevice.start()
    if rc != LpdDevice.ERROR_OK:
        print "run() failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    # Stop transaction
    rc = theDevice.stop()
    if rc != LpdDevice.ERROR_OK:
        print "stop() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        
    print "Closing Fem connection.. "        
    theDevice.close()


if __name__ == '__main__':
    
    # Check command line for host and port info    
    if len(sys.argv) == 3:
        femHost = sys.argv[1]
        femPort = int(sys.argv[2])
    else:
        # Nothing provided from command line; Use defaults
        femHost = None
        femPort = None        

    LpdReadoutTest(femHost, femPort)

