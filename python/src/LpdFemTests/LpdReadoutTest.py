'''
    LpdReadoutTest.py - Readout a system using the API
                    
'''

from LpdDevice.LpdDevice import LpdDevice
from EthernetUtility import EthernetUtility 
import argparse, sys


def LpdReadoutTest(tenGig, femHost, femPort, destIp):
    
    theDevice = LpdDevice()

    tenGigConfig   = EthernetUtility("eth%i" % tenGig)
    tenGigDestIp   = tenGigConfig.ipAddressGet()
    tenGigDestMac  = tenGigConfig.macAddressGet()
    # Determine destination IP from tenGig unless supplied by parser
    if destIp:
        tenGigSourceIp = destIp
    else:
        tenGigSourceIp = tenGigConfig.obtainDestIpAddress(tenGigDestIp)
        
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
    xmlConfig   = 2   # 0=test, 1=short exposure, 2=long exposure, 3=pseudorandom, 4=all 3 gain readout with short exposure, 5=all 3 gain readout with long exposure
	# (also for pseudo random  select that in asic data type and disable fast strobe for asicrx start)

    if AsicVersion == 1:

        if xmlConfig == 1:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_ShortExposure_V1.xml'
        elif xmlConfig == 2:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_V1.xml' 
        elif xmlConfig == 3:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/asic_pseudo_random_asicv1.xml'
        else:
            asicSetupParams = 'Config/SetupParams/Setup_SingleFrame.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_SingleFrame.xml'
    elif AsicVersion == 2:

        if xmlConfig == 1:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_ShortExposure_V2.xml'
        elif xmlConfig == 2:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_V2.xml' 
#            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_100Images.xml'    # check num img per train - 120 fine, 140 then mounted Tiles dont read out
        elif xmlConfig == 3:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/asic_pseudo_random_asicv2.xml'
        elif xmlConfig == 4:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/short_exposure_all_3gains_asicv2_B.xml'
        elif xmlConfig == 5:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/long_exposure_all_3gains_asicv2_C.xml'

    print "================    XML Filenames   ================"
    print asicSetupParams
    print asicCmdSequence
    
    ################################################################

# The second of the two command sequence configurations provided by Matt:
#        asicCmdSequence = 'Config/CmdSequence/AutoResets_ShortExposures_AsicControl.xml'

    #TODO: Temporary hack, pass filename instead of XML string
    # Read Slow Control (LpdAsicControl) XML file into a string
#    ff = open('Config/preambleDelaySlowControl.xml', 'r')
#    asicSetupParams = ff.read(-1)
#    ff.close ()
    
    #TODO: Temporary hack, pass filename instead of XML string
    # Read Asic Command Sequence (LpdAsicCommandSequence) XML file into a string
#    ff = open('Config/playingWivLasers_jacv3.xml', 'r')
#    asicCmdSequence = ff.read(-1)
#    ff.close ()

    rc = theDevice.paramSet('femAsicSetupParams', asicSetupParams)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSetupParams set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        errorCount += 1
    
    rc = theDevice.paramSet('femAsicCmdSequence', asicCmdSequence)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicCmdSequence set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
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
    rc = theDevice.paramSet(param, tenGigSourceIp)   #networkConfig.tenGig0SrcIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0SourcePort'
    rc = theDevice.paramSet(param, 0)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestMac'
    rc = theDevice.paramSet(param, tenGigDestMac)   #networkConfig.tenGig0DstMac)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestIp'
    rc = theDevice.paramSet(param, tenGigDestIp)    #networkConfig.tenGig0DstIp)
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
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFF0000, 0x00000000, 0x0000FF00, 0x00000000])    # Supermodule with three tiles
    param = 'femAsicEnableMask'
    rc = theDevice.paramSet(param, 9999)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'femAsicPixelSelfTestOverride'
    rc = theDevice.paramSet(param, -1)   # per-pixel override of self-test enable: 0=Disable, 1=Enabled [-1=Don't Care/XML decides]
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'femAsicPixelFeedbackOverride'
    rc = theDevice.paramSet(param, -1)   # per-pixel override of feedback selection: 0= low(50p), 1= high(5p) [-1=Don't Care/XML decices] # Verified 4/7/2013, ckd
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

    param = 'numberImages'
    rc = theDevice.paramSet(param, 4)   # Images per trigger - combine with ASIC command XML tag
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicLocalClock'
    rc = theDevice.paramSet(param, 0)   # ASIC clock scaling 0=100 MHz, 1=scaled down clock (10 MHz)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicSetupLoadMode'
    rc = theDevice.paramSet(param, 0)   # ASIC control load mode 0=parallel, 1=serial
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femInvertAdcData'
    rc = theDevice.paramSet(param, False)   # True = Invert ADC ASIC Data, False = Don't
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicRxCmdWordStart'
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

    param = 'femAsicGain'
    rc = theDevice.paramSet(param, 2)   # (Default value is 0)   0 = algorithm ; 3 = x100 ; 2 = x10 ; 1 = x1
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femEnableTenGig'
    rc = theDevice.paramSet(param, True)    # Enables transmission of image data via 10GigE UDP interface
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicSetupClockPhase'
    rc = theDevice.paramSet(param, 0)   # additional phase adjustment of slow clock rsync wrt ASIC reset
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'numberTrains'
    rc = theDevice.paramSet(param, 5)   # number of test cycles if LL Data Generator / PPC Data Direct selected
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

    param = 'femStartTrainDelay'
    triggerDelay = (2+88)
    rc = theDevice.paramSet(param, triggerDelay)    # Fem external trigger strobe delay (in ASIC clock periods)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicClockSource'
    rc = theDevice.paramSet(param, 0)   #  0=Fem local oscillator, 1=Clock sync with xray
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femStartTrainSource'
    rc = theDevice.paramSet(param, 1)   #  0=XFEL Clock & Ctrl command/reset, 1=Software, 2=LCLS, 3=PETRA III
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femAsicGainOverride'
    rc = theDevice.paramSet(param, False)   #False=asicrx gain select fixed by register, True=asicrx gain select taken from fast cmd file commands on the fly
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femStartTrainInhibit'
    rc = theDevice.paramSet(param, 0)   # Inhibit in ASIC clock cycles 
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femStartTrainPolarity'
    rc = theDevice.paramSet(param, 1)   #  0=Don't invert, 1=Invert
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1

    param = 'femVetoPolarity'
    rc = theDevice.paramSet(param, 0)   #  0=Don't invert, 1=Invert
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
        # Read back the "Expert" Level variables settings
        ######################################################
    
        if bDebug:

            print "================ 'Expert' Variables ================"
            paramExpertVariables = ['tenGig0SourceMac', 'tenGig0SourceIp', 'tenGig0SourcePort', 'tenGig0DestMac', 'tenGig0DestIp', 'tenGig0DestPort', 'tenGig0DataFormat',
                                    'tenGig0DataGenerator', 'tenGig0FrameLength', 'tenGig0NumberOfFrames', 'tenGigFarmMode', 'tenGigInterframeGap', 'tenGigUdpPacketLen', 
                                    'femAsicSetupClockPhase', 'femAsicVersion', 'femDebugLevel', 'femEnableTenGig',
                                    'femStartTrainPolarity', 'femVetoPolarity']
            #TODO: Remove if redundant?
#            param = 'femI2cBus'

        for param in paramExpertVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value.__repr__())
        


        ######################################################
        # Read back all User Level variables
        ######################################################
        
        paramUserVariables = ['femAsicClockSource', 'femAsicDataType', 'femAsicGain', 'femAsicGainOverride', 'femAsicLocalClock', 'femAsicModuleType', 
                              'femAsicPixelFeedbackOverride', 'femAsicPixelSelfTestOverride', 'femAsicRxCmdWordStart', 'femAsicSetupLoadMode',
                              'femStartTrainSource', 'femDataSource', 'femInvertAdcData', 'numberImages', 'numberTrains', 'femStartTrainDelay', 'femStartTrainInhibit']
        #TODO: Add when implemented? [if implemented..]
#        param = 'femPpcMode'

        print "================ 'User'   Variables ================"

        for param in paramUserVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value.__repr__())

        
        #TODO: Uncomment/restore relevant LpdFemClient code when Karabo fixes array bug
#        param = 'femAsicEnableMask'
#        (rc, value) = theDevice.paramGet(param)
#        if rc != LpdDevice.ERROR_OK:
#            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#        else:
#            print "{0:<32} = [{1:<8}, {1:<8}, {1:<8}, {1:<8}]".format(param,value[0], value[1], value[2], value[3])
    
        # Check XML string variables read back, but don't display their [long-winded] XML strings
        paramUserExtraVariables = ['femAsicCmdSequence',  'femAsicSetupParams'] 


        for param in paramUserExtraVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#            else:
#                print "{0:<32} = {1:<10}".format(param, value)
        
    
    
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

    # Default values
    femHost = '192.168.2.2'
    femPort = 6969  # oneGig port
    tenGig  = 2     # eth2 on devgpu02
    destIp  = None  # Default: Assume tenGig destination IP is one increment above eth2's IP
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="LpdReadoutTest.py - configure and readout an LPD detector. ",
                                     epilog="Defaults: tenGig=(eth)2, destip=10.0.0.2, femhost=192.168.2.2, femport=6969")

    parser.add_argument("--tengig",     help="Set tenGig ethernet card (e.g. 2 for eth2)",  type=int, default=tenGig)
    parser.add_argument("--destip",     help="Set destination IP (eg 10.0.0.2)",            type=str, default=destIp)
    parser.add_argument("--femhost",    help="Set fem host IP (e.g.  192.168.2.2)",         type=str, default=femHost)
    parser.add_argument("--femport",    help="Set fem port (eg 61649)",                     type=int, default=femPort)
    args = parser.parse_args()

    # Copy value(s) for the provided arguments
    if args.tengig != None:
        tenGig = args.tengig

    if args.femhost:
        femHost = args.femhost

    if args.femport:
        femPort = args.femport

    if args.destip:
        destIp = args.destip

    LpdReadoutTest(tenGig, femHost, femPort, destIp)

