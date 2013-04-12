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
    
    AsicVersion = 1    # 1 or 2
    xmlConfiguration = 1    # 0 = test, 1=short (normal) exposure, 2= long exposure (slowed down)

    if AsicVersion == 1:
        femAsicSlowedClockFlag = True    # must ensure fast cmd file corresponds with readout clock selection
        
        #### Current XML files ####
        if xmlConfiguration == 1:
            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters.xml'
            FastCmdXmlString     = 'ConfigFiles/ManualReset_longExposure_AsicControl.xml'
        elif xmlConfiguration == 2:
            SlowControlXmlString = 'ConfigFiles/preambleDelaySlowControl.xml'
            FastCmdXmlString     = 'ConfigFiles/playingWivLasers.xml' # SupdMod (or 2Tile), slowed down, can use laser pointer

        #### jac's new XML files ####
#        if xmlConfiguration == 1:
#            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters.xml'
#            FastCmdXmlString     = 'ConfigFiles/AutoResets_ShortExposures_AsicControl.xml'
#        elif xmlConfiguration == 2:
#            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters.xml'
#            FastCmdXmlString     = 'ConfigFiles/AutoResets_ShortExposures_AsicControl.xml'
#        else:
#            SlowControlXmlString = 'ConfigFiles/AsicSlowParameters_SingleFrameTestPulse.xml'
#            FastCmdXmlString = 'ConfigFiles/CmdsSingleFrameTestPulse.xml'
    elif AsicVersion == 2:
        print "AsicVersion == 2, XML files not yet configure.. Exiting"
        sys.exit()
        femAsicSlowedClockFlag = False    # must ensure fast cmd file corresponds with readout clock selection
        if xmlConfiguration == 1:
            SlowControlXmlString = 'ConfigFiles/'
            FastCmdXmlString     = 'ConfigFiles/'
        elif xmlConfiguration == 2:
            SlowControlXmlString = 'ConfigFiles/'
            FastCmdXmlString     = 'ConfigFiles/' 
        else:
            SlowControlXmlString = 'ConfigFiles/'
            FastCmdXmlString = 'ConfigFiles/'

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

#            'slow_params_file_name_xml'             : #'slow_control_config_jac.xml',            # used if slow_params_file_type = 1
#                                                      'preambleDelaySlowControl.xml',            # slow_control_config.xml  # standard
#            'fast_cmd_sensor_data_file_name_xml'    : 'SuperModuleNormalOperation.xml',          # Used for Super Module operation, with slowed down readout
#                                                    # 'SupModTest.xml'                           # Testing supermodule
#                                                    # 'fast_cmd_1f_with_slow_readout.xml',       # file created by jac
#                                                    # 'fast_readout_replacement_commands.xml',   # for real asic sensor data                                                    
#            'fast_cmd_pseudorandom_file_name_xml'   : 'fast_random_gaps.xml',                    # for pseudorandom asic data
#                                                      'superModRandomData.xml'                   # Configure  ASICs to output pseudorandom data

    ######################################################
    # Start configuring variables using API calls
    ######################################################
        
    rc = theDevice.paramSet('tenGig0SourceMac', '62-00-00-00-00-01')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('tenGig0SourceIp', '10.0.0.2')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('tenGig0SourcePort', 0)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('tenGig0DestMac', '00-07-43-10-65-A0')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('tenGig0DestIp', '10.0.0.1')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('tenGig0DestPort', 61649)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
#    rc = theDevice.paramSet('femAsicEnableMask', [0x00FF0000, 0x00000000, 0x00000000, 0x000000FF])    # Enable 2 Tile System's ASICs
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF])    # Enable everything
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFF0000, 0x00000000, 0x0000FF00, 0x00000000])      # Supermodule with three tiles
    rc = theDevice.paramSet('femAsicEnableMask', 9999)      # Supermodule with three tiles
    if rc != LpdDevice.ERROR_OK:
        print "femAsicEnableMask set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femPpcResetDelay', 2)
    if rc != LpdDevice.ERROR_OK:
        print "femPpcResetDelay set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicDataType', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicDataType set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicModuleType', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicModuleType set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femDataSource', 1) #0)
    if rc != LpdDevice.ERROR_OK:
        print "femDataSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicColumns', 4)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicColumns set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicLocalClock', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicLocalClock set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicSlowedClock', femAsicSlowedClockFlag)           # True for V1 asic, False for V2 asic
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowedClock set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicSlowLoadMode', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowLoadMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicRxInvertData', False)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxInvertData set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicRxFastStrobe', True)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxFastStrobe set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicVersion', AsicVersion) # 1 or 2
    if rc != LpdDevice.ERROR_OK:
        print "femAsicVersion set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femPpcMode', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femPpcMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0DataGenerator', 1)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DataGenerator set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0DataFormat', 0)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0DataFormat set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0NumberOfFrames', 1)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0NumberOfLength set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    ######################################################
    # "Expert" variables
    ######################################################

    rc = theDevice.paramSet('tenGigInterframeGap', 0)
    if rc != LpdDevice.ERROR_OK:
        print "tenGigInterframeGap set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGigUdpPacketLen', 8000)
    if rc != LpdDevice.ERROR_OK:
        print "tenGigUdpPacketLen set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicGainOverride', 8)  #8)        # (Default value is 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicGainOverride set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femFastCtrlDynamic', True)
    if rc != LpdDevice.ERROR_OK:
        print "femFastCtrlDynamic set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femEnableTenGig', True)
    if rc != LpdDevice.ERROR_OK:
        print "femEnableTenGig set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicRxDelayOddChannels', True)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicRxDelayOddChannels set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femAsicSlowClockPhase', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowClockPhase set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femNumTestCycles', 3)  #1)
    if rc != LpdDevice.ERROR_OK:
        print "femNumTestCycles set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGigFarmMode', 1)
    if rc != LpdDevice.ERROR_OK:
        print "tenGigFarmMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femI2cBus', 0x300)
    if rc != LpdDevice.ERROR_OK:
        print "femI2cBus set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('femDebugLevel', 0)
    if rc != LpdDevice.ERROR_OK:
        print "femDebugLevel set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    rc = theDevice.paramSet('tenGig0FrameLength', 0x10000)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0FrameLength set failed rc=%d : %s" % (rc, theDevice.errorStringGet())


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
    
    (rc, value) = theDevice.paramGet('femPpcMode')
    if rc != LpdDevice.ERROR_OK:
        print "femPpcMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "femPpcMode\t\t= %d" % value

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
    
        (rc, value) = theDevice.paramGet('femI2cBus')
        if rc != LpdDevice.ERROR_OK:
            print "femI2cBus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femI2cBus\t\t= %3X" % value
    
        (rc, value) = theDevice.paramGet('femNumTestCycles')
        if rc != LpdDevice.ERROR_OK:
            print "femNumTestCycles get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femNumTestCycles\t= %d" % value
    
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

