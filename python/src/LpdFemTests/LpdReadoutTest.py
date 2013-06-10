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
    xmlConfiguration = 2   # 0 = test, 1=short exposure, 2= long exposure, 3= pseudorandom, 4 = all 3 gain readout short exposure, 5 = all 3 gain readout long exposure
	# (also for pseudo random  select that in asic data type and disable fast strobe for asicrx start)

    if AsicVersion == 1:
        femAsicSlowedClockFlag = True	# must ensure fast cmd file corresponds with readout clock selection
        if xmlConfiguration == 1:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/AutoResets_ShortExposures_AsicControl_jacv1.xml'
        elif xmlConfiguration == 2:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/ManualReset_longExposure_AsicControl_jacv1.xml' 
        elif xmlConfiguration == 3:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/asic_pseudo_random_asicv1.xml' 
        else:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_SingleFrameTestPulse.xml'
            FastCmdXmlString = 'ConfigFiles/CmdsSingleFrameTestPulse.xml'
    elif AsicVersion == 2:
        femAsicSlowedClockFlag = False	# must ensure fast cmd file corresponds with readout clock selection
        if xmlConfiguration == 1:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/AutoResets_ShortExposures_asicv2_jacv1.xml' # 'ConfigFiles/short_exposure_500_images_A.xml'  #  'ConfigFiles/AutoResets_ShortExposures_asicv2_B.xml'
        elif xmlConfiguration == 2:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/ManualReset_longExposure_asicv2_jacv1.xml' 
        elif xmlConfiguration == 3:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/asic_pseudo_random_asicv2.xml' 
        elif xmlConfiguration == 4:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/short_exposure_all_3gains_asicv2_B.xml' 
        elif xmlConfiguration == 5:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_lowpower.xml'
            FastCmdXmlString     = 'ConfigFiles/long_exposure_all_3gains_asicv2_C.xml' 
        else:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_SingleFrameTestPulse.xml'
            FastCmdXmlString = 'ConfigFiles/CmdsSingleFrameTestPulse.xml'

	print SlowControlXmlString
	print FastCmdXmlString

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
    param = 'femAsicEnableMask'
    rc = theDevice.paramSet(param, 9999)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'femAsicPixelSelfTestOverride'
    rc = theDevice.paramSet(param, 0)   # per-pixel override of self-test enable: 1 = enabled
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'femAsicPixelFeedbackOverride'
    rc = theDevice.paramSet(param, 0)   # per-pixel override of feedback selection: 0 = high(10p), 1= low(50p)'
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    
    param = 'femPpcResetDelay'
    rc = theDevice.paramSet(param, 0)   # Delay after resetting ppc
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicDataType'
    rc = theDevice.paramSet(param, 0)   # 0=Normal Data, 1=Counting data, 2=Pseudo random
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicModuleType'
    rc = theDevice.paramSet(param, 0)   # 0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone'
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femDataSource'
    rc = theDevice.paramSet(param, 1)   # 0=ASIC (via PPC), 1=ASIC (from Rxblock), 2=frame generator, 3=PPC (preprogrammed)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicColumns'
    rc = theDevice.paramSet(param, 4)   # Time-slices per trigger (images per train) - combine with ASIC command XML tag
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicLocalClock'
    rc = theDevice.paramSet(param, 0)   # ASIC clock scaling 0=100 MHz, 1=scaled down clock (10 MHz)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicSlowedClock'
    rc = theDevice.paramSet(param, femAsicSlowedClockFlag)           # True for V1 asic, False for V2 asic
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicSlowLoadMode'
    rc = theDevice.paramSet(param, 0)   # ASIC control load mode 0=parallel, 1=serial
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicRxInvertData'
    rc = theDevice.paramSet(param, False)   # Invert ADC ASIC Data
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicRxFastStrobe'
    rc = theDevice.paramSet(param, True)    # Start ASIC capture using strobe derived from ASIC Command file
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicVersion'
    rc = theDevice.paramSet(param, AsicVersion) # 1 or 2
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    #TODO: not used?
#    rc = theDevice.paramSet('femPpcMode', 0) # 0=single train shot with PPC reset, 1=Continuous readout
#    if rc != LpdDevice.ERROR_OK:
#        print "femPpcMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    param = 'tenGig0DataGenerator'
    rc = theDevice.paramSet(param, 1)   # Data generator 1=DataGen 2=PPC DDR2
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'tenGig0DataFormat'
    rc = theDevice.paramSet(param, 0)   # Data format type, 0=counting data (doesn't affect "normal" data")
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'tenGig0NumberOfFrames'
    rc = theDevice.paramSet(param, 1)   # Number of frames to send in each cycle
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    ######################################################
    # "Expert" variables
    ######################################################

    param = 'tenGigInterframeGap'
    rc = theDevice.paramSet(param, 0)   # 10GigE inter-frame gap timer (clock cycles)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'tenGigUdpPacketLen'
    rc = theDevice.paramSet(param, 8000)    # 10GigE UDP packet payload length'
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicGainOverride'
    rc = theDevice.paramSet(param, 8)   # (Default value is 0)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femFastCtrlDynamic'
    rc = theDevice.paramSet(param, True)    # Enables Fast Control with Dynamic Vetoes
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femEnableTenGig'
    rc = theDevice.paramSet(param, True)    # Enables transmission of image data via 10GigE UDP interface
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicRxDelayOddChannels'
    rc = theDevice.paramSet(param, True)    # Delay odd ASIC data channels by one clock to fix alignment
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicSlowClockPhase'
    rc = theDevice.paramSet(param, 0)   # additional phase adjustment of slow clock rsync wrt ASIC reset
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femNumTestCycles'
    rc = theDevice.paramSet(param, 2)   # number of test cycles if LL Data Generator / PPC Data Direct selected
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'tenGigFarmMode'
    rc = theDevice.paramSet(param, 1)   # 1=disabled, 2=fixed IP,multi port, 3=farm mode with nic lists
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

#    rc = theDevice.paramSet('femI2cBus', 0x300)
#    if rc != LpdDevice.ERROR_OK:
#        print "femI2cBus set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    param = 'femDebugLevel'
    rc = theDevice.paramSet(param, 0)   # Set the debug level
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'tenGig0FrameLength'
    rc = theDevice.paramSet(param, 0x10000) # Frame length in bytes
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femExternalTriggerStrobeDelay'
    triggerDelay = (2+88)
    rc = theDevice.paramSet(param, triggerDelay)    # Fem external trigger strobe delay (in ASIC clock periods)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femDelaySensors'
    rc = theDevice.paramSet(param, 0xffef)  # delay timing of 16 sensors; bit = 1 adds 1 clock delay; sensor mod 1 is LSB
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femAsicClockSource'
    rc = theDevice.paramSet(param, 0)   #  0=Fem local oscillator, 1=Clock sync with xray
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femBeamClockSource'
    rc = theDevice.paramSet(param, 0)   #  Xray sync clock source 0=XFEL, 1=PETRA
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femBeamTriggerSource'
    rc = theDevice.paramSet(param, 1)   #  0=XFEL Clock & Ctrl system, 1=Software
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femGainFromFastCmd'
    rc = theDevice.paramSet(param, 0)   #0=asicrx gain select fixed by register, 1=asicrx gain select taken from fast cmd file commands on the fly
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femBeamTriggerPetra'
    rc = theDevice.paramSet(param, 1)   # 0=XFEL reset line as for LCLS, 1=special trigger for Petra
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    param = 'femExternalTriggerStrobeInhibit'
    rc = theDevice.paramSet(param, 0)   # Inhibit in ASIC clock cycles 
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())

    ######################################################
    # Read back all the configured values
    ######################################################
    
    param = 'tenGig0SourceMac'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0SourceIp'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0SourcePort'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0DestMac'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0DestIp'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0DestPort'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0DataFormat'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0DataGenerator'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'tenGig0NumberOfFrames'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)
    
    param = 'femAsicColumns'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)

    param = 'femAsicDataType'
    (rc, value) = theDevice.paramGet(param)
    if rc != LpdDevice.ERROR_OK:
        print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
    else:
        print "{0:<30} = {1:<10}".format(param, value)
    
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

    (rc, value) = theDevice.paramGet('femAsicPixelSelfTestOverride')
    if rc != LpdDevice.ERROR_OK:
        print rc, theDevice.errorStringGet(), LpdDevice.ERROR_OK, "\n"
        print "femAsicPixelSelfTestOverride get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femAsicPixelSelfTestOverride\t= %d" % value
    
    (rc, value) = theDevice.paramGet('femAsicPixelFeedbackOverride')
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

        (rc, value) = theDevice.paramGet('femBeamTriggerPetra')
        if rc != LpdDevice.ERROR_OK:
            print "femBeamTriggerPetra get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femBeamTriggerPetra\t= %d." % value

        (rc, value) = theDevice.paramGet('femExternalTriggerStrobeInhibit')
        if rc != LpdDevice.ERROR_OK:
            print "femExternalTriggerStrobeInhibit get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femExternalTriggerStrobeInhibit\t= %d." % value

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

