'''
    LpdReadoutTest.py - Readout a system using the API
                    
'''

from LpdDevice.LpdDevice import LpdDevice
from networkConfiguration import networkConfiguration
import sys


def LpdReadoutTest(femHost=None, femPort=None):
    
    theDevice = LpdDevice()

    networkConfig = networkConfiguration()

    # Was either femHost or femPort NOT provided to this class?
    if (femHost == None) or (femPort == None):
        # At least one wasn't supplied from the command line; Use networkConfiguration class
        femHost = networkConfig.ctrl0SrcIp
        femPort = int(networkConfig.ctrlPrt)

    rc = theDevice.open(femHost, femPort)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return

    # Display "expert" variables?
    bDebug = True
    
    #Track number of configuration errors:
    errorCount = 0

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
#            FastCmdXmlString     = 'ConfigFiles/ManualReset_longExp_varImgsPerTrain.xml'    # check num img per train - 120 fine, 140 then mounted Tiles dont read out
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
            
            #TODO: ckd to check if worth having these comments out lines kicking about..
            # Config files taken from lpdFemGui:
            #SlowControlXmlString = '/u/ckd27546/workspace/xfel_workspace/LpdFemGui/config/AsicSlowParameters_lowpower.xml'
            #FastCmdXmlString = '/u/ckd27546/workspace/xfel_workspace/LpdFemGui/config/AutoResets_ShortExposures_asicv2_jacv1.xml'
            # Clone of jac's most recent xml files, for testing Two Tile System..
#            SlowControlXmlString = 'ConfigFiles/AsicSlow_FromJaq.xml'
#            FastCmdXmlString     = 'ConfigFiles/ManualReset_Fromjac.xml'

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
        errorCount += 1
    
    rc = theDevice.paramSet('femAsicFastCmdSequence', FastCmdXmlString)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicFastCmdSequence set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        errorCount += 1

    ######################################################
    # Start configuring variables using API calls
    ######################################################

    param = 'tenGig0SourceMac'
    rc = theDevice.paramSet(param, '62-00-00-00-00-01')
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0SourceIp'
    rc = theDevice.paramSet(param, networkConfig.tenGig0SrcIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0SourcePort'
    rc = theDevice.paramSet(param, 0)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestMac'
    rc = theDevice.paramSet(param, networkConfig.tenGig0DstMac)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestIp'
    rc = theDevice.paramSet(param, networkConfig.tenGig0DstIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestPort'
    rc = theDevice.paramSet(param, 61649)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
#    rc = theDevice.paramSet('femAsicEnableMask', [0x00FF0000, 0x00000000, 0x00000000, 0x000000FF])    # Enable 2 Tile System's ASICs
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF])    # Enable everything
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFF0000, 0x00000000, 0x0000FF00, 0x00000000])      # Supermodule with three tiles
    param = 'femAsicEnableMask'
    rc = theDevice.paramSet(param, 9999)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'femAsicPixelSelfTestOverride'
    rc = theDevice.paramSet(param, 0)   # per-pixel override of self-test enable: 1 = enabled
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'femAsicPixelFeedbackOverride'
    rc = theDevice.paramSet(param, 0)   # per-pixel override of feedback selection: 0 = high(10p), 1= low(50p)'
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'femPpcResetDelay'
    rc = theDevice.paramSet(param, 0)   # Delay after resetting ppc
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicDataType'
    rc = theDevice.paramSet(param, 0)   # 0=Normal Data, 1=Counting data, 2=Pseudo random
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicModuleType'
    rc = theDevice.paramSet(param, 0)   # 0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone'
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femDataSource'
    rc = theDevice.paramSet(param, 1)   # 0=ASIC (via PPC), 1=ASIC (from Rxblock), 2=frame generator, 3=PPC (preprogrammed)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicColumns'
    rc = theDevice.paramSet(param, 4)   # Time-slices per trigger (images per train) - combine with ASIC command XML tag
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicLocalClock'
    rc = theDevice.paramSet(param, 0)   # ASIC clock scaling 0=100 MHz, 1=scaled down clock (10 MHz)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicSlowedClock'
    rc = theDevice.paramSet(param, femAsicSlowedClockFlag)           # True for V1 asic, False for V2 asic
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicSlowLoadMode'
    rc = theDevice.paramSet(param, 0)   # ASIC control load mode 0=parallel, 1=serial
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicRxInvertData'
    rc = theDevice.paramSet(param, False)   # Invert ADC ASIC Data
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicRxFastStrobe'
    rc = theDevice.paramSet(param, True)    # Start ASIC capture using strobe derived from ASIC Command file
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicVersion'
    rc = theDevice.paramSet(param, AsicVersion) # 1 or 2
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    #TODO: Not implemented 
#    rc = theDevice.paramSet('femPpcMode', 0) # 0=single train shot with PPC reset, 1=Continuous readout
#    if rc != LpdDevice.ERROR_OK:
#        print "femPpcMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    param = 'tenGig0DataGenerator'
    rc = theDevice.paramSet(param, 1)   # Data generator 1=DataGen 2=PPC DDR2
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'tenGig0DataFormat'
    rc = theDevice.paramSet(param, 0)   # Data format type, 0=counting data (doesn't affect "normal" data")
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'tenGig0NumberOfFrames'
    rc = theDevice.paramSet(param, 1)   # Number of frames to send in each cycle
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    ######################################################
    # "Expert" variables
    ######################################################

    param = 'tenGigInterframeGap'
    rc = theDevice.paramSet(param, 0)   # 10GigE inter-frame gap timer (clock cycles)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'tenGigUdpPacketLen'
    rc = theDevice.paramSet(param, 8000)    # 10GigE UDP packet payload length'
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicGainOverride'
    rc = theDevice.paramSet(param, 9)   # (Default value is 0)   0 = algorithm ; 8 = x100 ; 9 = x10 ; 11 = x1
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femFastCtrlDynamic'
    rc = theDevice.paramSet(param, True)    # Enables Fast Control with Dynamic Vetoes
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femEnableTenGig'
    rc = theDevice.paramSet(param, True)    # Enables transmission of image data via 10GigE UDP interface
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicRxDelayOddChannels'
    rc = theDevice.paramSet(param, True)    # Delay odd ASIC data channels by one clock to fix alignment
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicSlowClockPhase'
    rc = theDevice.paramSet(param, 0)   # additional phase adjustment of slow clock rsync wrt ASIC reset
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femNumTestCycles'
    rc = theDevice.paramSet(param, 1)   # number of test cycles if LL Data Generator / PPC Data Direct selected
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'tenGigFarmMode'
    rc = theDevice.paramSet(param, 1)   # 1=disabled, 2=fixed IP,multi port, 3=farm mode with nic lists
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

#    rc = theDevice.paramSet('femI2cBus', 0x300)
#    if rc != LpdDevice.ERROR_OK:
#        print "femI2cBus set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    param = 'femDebugLevel'
    rc = theDevice.paramSet(param, 0)   # Set the debug level
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'tenGig0FrameLength'
    rc = theDevice.paramSet(param, 0x10000) # Frame length in bytes
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femExternalTriggerStrobeDelay'
    triggerDelay = (2+88)
    rc = theDevice.paramSet(param, triggerDelay)    # Fem external trigger strobe delay (in ASIC clock periods)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femDelaySensors'
    rc = theDevice.paramSet(param, 0xffff)  # delay timing of 16 sensors; bit = 1 adds 1 clock delay; sensor mod 1 is LSB
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicClockSource'
    rc = theDevice.paramSet(param, 0)   #  0=Fem local oscillator, 1=Clock sync with xray
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femBeamClockSource'
    rc = theDevice.paramSet(param, 0)   #  Xray sync clock source 0=XFEL, 1=PETRA
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femBeamTriggerSource'
    rc = theDevice.paramSet(param, 1)   #  0=XFEL Clock & Ctrl system, 1=Software
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femGainFromFastCmd'
    rc = theDevice.paramSet(param, 0)   #0=asicrx gain select fixed by register, 1=asicrx gain select taken from fast cmd file commands on the fly
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femBeamTriggerPetra'
    rc = theDevice.paramSet(param, 1)   # 0=XFEL reset line as for LCLS, 1=special trigger for Petra
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femExternalTriggerStrobeInhibit'
    rc = theDevice.paramSet(param, 0)   # Inhibit in ASIC clock cycles 
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    ######################################################
    # Check for errors before proceeding..
    ######################################################
    
    if errorCount > 0:
        print "================================"
        print "Detected %i error(s), aborting.." % errorCount
    else:
        # No errors encountered, proceeding

        ######################################################
        # Read back all the configured values
        ######################################################
        
        param = 'tenGig0SourceMac'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0SourceIp'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0SourcePort'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0DestMac'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0DestIp'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0DestPort'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0DataFormat'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0DataGenerator'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'tenGig0NumberOfFrames'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
        
        param = 'femAsicColumns'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femAsicDataType'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
        
        #TODO: Uncomment/restore relevant LpdFemClient code when Karabo fixes array bug
#        param = 'femAsicEnableMask'
#        (rc, value) = theDevice.paramGet(param)
#        if rc != LpdDevice.ERROR_OK:
#            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#        else:
#            print "{0:<32} = [{1:<8}, {1:<8}, {1:<8}, {1:<8}]".format(param,value[0], value[1], value[2], value[3])
    
        param = 'femAsicFastCmdSequence'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#        else:
#            print "{0:<32} = {1:<10}".format(param, value)
        
        param = 'femAsicLocalClock'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
        
        param = 'femAsicModuleType'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
        
        param = 'femAsicRxFastStrobe'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femAsicRxInvertData'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femAsicSlowControlParams'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#        else:
#            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femAsicSlowedClock'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femAsicSlowLoadMode'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femDataSource'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
        
#        param = 'femPpcMode'
#        (rc, value) = theDevice.paramGet(param)
#        if rc != LpdDevice.ERROR_OK:
#            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#        else:
#            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femAsicPixelSelfTestOverride'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print rc, theDevice.errorStringGet(), LpdDevice.ERROR_OK, "\n"
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
        
        param = 'femAsicPixelFeedbackOverride'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        param = 'femPpcResetDelay'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = {1:<10}".format(param, value)
    
        ######################################################
        # Display "Expert" variables' settings
        ######################################################
    
        if bDebug:
            param = 'tenGig0FrameLength'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
    
            param = 'tenGigFarmMode'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'tenGigInterframeGap'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'tenGigUdpPacketLen'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
    
            param = 'femAsicGainOverride'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
                
            param = 'femAsicRxDelayOddChannels'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femAsicSlowClockPhase'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femAsicVersion'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femDebugLevel'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femEnableTenGig'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
    
            param = 'femFastCtrlDynamic'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
#            param = 'femI2cBus'
#            (rc, value) = theDevice.paramGet(param)
#            if rc != LpdDevice.ERROR_OK:
#                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#            else:
#                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femNumTestCycles'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femDelaySensors'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femAsicClockSource'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
        
            param = 'femBeamTriggerSource'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
    
            param = 'femGainFromFastCmd'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)

            param = 'femBeamTriggerPetra'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)

            param = 'femExternalTriggerStrobeDelay'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
            
            param = 'femExternalTriggerStrobeInhibit'
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value)
    
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

