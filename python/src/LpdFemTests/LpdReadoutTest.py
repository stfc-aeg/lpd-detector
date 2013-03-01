'''
    LpdReadoutTest.py - Readout a system using the API
                    
'''

from LpdDevice.LpdDevice import LpdDevice
from networkConfiguration import networkConfiguration
import sys


def LpdReadoutTest(femHost=None, femPort=None):
    
    theDevice = LpdDevice()

    # Was either femHost and femPort NOT provided to this class?
    if (femHost == None) or (femPort == None):
        # At least one wasn't supplied from the command line; Use networkConfiguration class
        networkConfig = networkConfiguration()
        femHost = networkConfig.ctrl0SrcIp
        femPort = int(networkConfig.ctrlPrt)

    rc = theDevice.open(femHost, femPort)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return

    bDebug = True

    # Need to configure fast and slow control whether doing readout or debugging..

    #TODO: Temporary hack, pass filename instead of XML string
    # Read Slow Control (LpdAsicControl) XML file into a string
#    ff = open('ConfigFiles/preambleDelaySlowControl.xml', 'r')
#    xmlString = ff.read(-1)
#    ff.close ()
#    xmlString = 'ConfigFiles/preambleDelaySlowControl.xml'
    xmlString = 'ConfigFiles/selfTestPixel232.xml'
    
    rc = theDevice.paramSet('femAsicSlowControlParams', xmlString)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowControlParams set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    #TODO: Temporary hack, pass filename instead of XML string
    # Read Asic Command Sequence (LpdAsicCommandSequence) XML file into a string
#    ff = open('ConfigFiles/playingWivLasers.xml', 'r')
#    xmlString = ff.read(-1)
#    ff.close ()
    xmlString = 'ConfigFiles/SuperModuleNormalOperation.xml'# SupMod - normal readout
#    xmlString = 'ConfigFiles/playingWivLasers.xml' # SupdMod (or 2Tile), slowed down, can use laser pointer
    
    rc = theDevice.paramSet('femAsicFastCmdSequence', xmlString)
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
    # Only do Set/Get calls if developing...
    #    (configure() & start() called in else statement) 
    ######################################################
    if bDebug:
        # Start configuring variables using API calls
    
        rc = theDevice.paramSet('tenGig0SourceMac', '62-00-00-00-00-01')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0SourceMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0SourceMac \t= %s." % value
    
        
        rc = theDevice.paramSet('tenGig0SourceIp', '10.0.0.2')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0SourceIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0SourceIp \t= %s." % value
    
        
        rc = theDevice.paramSet('tenGig0SourcePort', 0)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0SourcePort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourcePort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0SourcePort \t= %s." % value
    
        
        rc = theDevice.paramSet('tenGig0DestMac', '00-07-43-10-65-A0')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0DestMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0DestMac \t\t= %s." % value
    
        
        rc = theDevice.paramSet('tenGig0DestIp', '10.0.0.1')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0DestIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0DestIp \t\t= %s." % value
    
        
        rc = theDevice.paramSet('tenGig0DestPort', 61649)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0DestPort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestPort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0DestPort \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1SourceMac', 13)
#        if rc != LpdDevice.ERROR_OK:
#            print "tenGig1SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourceMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourceMac \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1SourceIp', 13)
#        if rc != LpdDevice.ERROR_OK:
#            print "tenGig1SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourceIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourceIp \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1SourcePort', 13)
#        if rc != LpdDevice.ERROR_OK:
#            print "tenGig1SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourcePort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourcePort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourcePort \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1DestMac', 13)
#        if rc != LpdDevice.ERROR_OK:
#            print "tenGig1DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestMac \t\t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1DestIp', 13)
#        if rc != LpdDevice.ERROR_OK:
#            print "tenGig1DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestIp \t\t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1DestPort', 13)
#        if rc != LpdDevice.ERROR_OK:
#            print "tenGig1DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestPort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestPort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestPort \t= %s." % value
    
    
        rc = theDevice.paramSet('tenGigInterframeGap', 0)
        if rc != LpdDevice.ERROR_OK:
            print "tenGigInterframeGap set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGigInterframeGap')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigInterframeGap get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigInterframeGap \t= %d." % value
    
        
        rc = theDevice.paramSet('tenGigUdpPacketLen', 8000)
        if rc != LpdDevice.ERROR_OK:
            print "tenGigUdpPacketLen set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGigUdpPacketLen')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigUdpPacketLen get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigUdpPacketLen \t= %d." % value

        
#        rc = theDevice.paramSet('femAsicEnableMask', [0xFF000000, 0x00000000, 0x00000000, 0x0000FF00])    # Enable 2 Tile System's ASICs
#        rc = theDevice.paramSet('femAsicEnableMask', [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF])    # Enable everything
        rc = theDevice.paramSet('femAsicEnableMask', [0xFFFF0000, 0x00000000, 0x0000FF00, 0x00000000])      # Supermodule with three tiles
        if rc != LpdDevice.ERROR_OK:
            print "femAsicEnableMask set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicEnableMask')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicEnableMask get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicEnableMask \t= [%8X, %8X, %8X, %8X]" %  (value[0], value[1], value[2], value[3])

        # (Default value is 0)
        rc = theDevice.paramSet('femAsicGainOverride', 8)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicGainOverride set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicGainOverride')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicGainOverride get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicGainOverride \t= %d." % value

        rc = theDevice.paramSet('femAsicModuleType', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicModuleType set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicModuleType')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicModuleType get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicModuleType \t= %d." % value

        rc = theDevice.paramSet('femDataSource', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femDataSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femDataSource')
        if rc != LpdDevice.ERROR_OK:
            print "femDataSource get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femDataSource \t\t= %d." % value

        rc = theDevice.paramSet('femFastCtrlDynamic', True)
        if rc != LpdDevice.ERROR_OK:
            print "femFastCtrlDynamic set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femFastCtrlDynamic')
        if rc != LpdDevice.ERROR_OK:
            print "femFastCtrlDynamic get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femFastCtrlDynamic \t= ", value

        rc = theDevice.paramSet('femEnableTenGig', True)
        if rc != LpdDevice.ERROR_OK:
            print "femEnableTenGig set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femEnableTenGig')
        if rc != LpdDevice.ERROR_OK:
            print "femEnableTenGig get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femEnableTenGig \t= ", value

        rc = theDevice.paramSet('femAsicColumns', 4)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicColumns set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicColumns')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicColumns get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicColumns \t\t= %d" % value

        rc = theDevice.paramSet('femFastCtrlDynamic', True)
        if rc != LpdDevice.ERROR_OK:
            print "femFastCtrlDynamic set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femFastCtrlDynamic')
        if rc != LpdDevice.ERROR_OK:
            print "femFastCtrlDynamic get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femFastCtrlDynamic \t= ", value

        (rc, value) = theDevice.paramGet('femAsicSlowControlParams')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowControlParams get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#        else:
#            print "femAsicSlowControlParams:\n", value
    
        (rc, value) = theDevice.paramGet('femAsicFastCmdSequence')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicFastCmdSequence get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#        else:
#            print "femAsicFastCmdSequence:\n", value

    
        rc = theDevice.paramSet('femAsicDataType', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicDataType set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femAsicDataType')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicDataType get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicDataType\t\t= ", value
    
        rc = theDevice.paramSet('femAsicLocalClock', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicLocalClock set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicLocalClock')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicLocalClock get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicLocalClock\t= ", value
    
        rc = theDevice.paramSet('femAsicSlowLoadMode', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowLoadMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicSlowLoadMode')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowLoadMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicSlowLoadMode\t= ", value
    
        rc = theDevice.paramSet('femAsicRxInvertData', False)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxInvertData set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femAsicRxInvertData')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxInvertData get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicRxInvertData\t= ", value

        rc = theDevice.paramSet('femAsicRxFastStrobe', True)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxFastStrobe set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femAsicRxFastStrobe')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxFastStrobe get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicRxFastStrobe\t= ", value

        rc = theDevice.paramSet('femAsicRxDelayOddChannels', True)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxDelayOddChannels set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicRxDelayOddChannels')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicRxDelayOddChannels get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicRxDelayOddChannels\t= ", value

        rc = theDevice.paramSet('femAsicSlowClockPhase', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowClockPhase set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femAsicSlowClockPhase')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowClockPhase get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicSlowClockPhase\t= ", value

        rc = theDevice.paramSet('femAsicSlowedClock', False)    #True)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowedClock set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femAsicSlowedClock')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowedClock get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicSlowedClock\t= ", value

        rc = theDevice.paramSet('femPpcMode', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femPpcMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femPpcMode')
        if rc != LpdDevice.ERROR_OK:
            print "femPpcMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femPpcMode\t\t= ", value

        rc = theDevice.paramSet('femPpcResetDelay', 2)
        if rc != LpdDevice.ERROR_OK:
            print "femPpcResetDelay set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femPpcResetDelay')
        if rc != LpdDevice.ERROR_OK:
            print "femPpcResetDelay get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femPpcResetDelay\t= ", value

        rc = theDevice.paramSet('femNumTestCycles', 1)
        if rc != LpdDevice.ERROR_OK:
            print "femNumTestCycles set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femNumTestCycles')
        if rc != LpdDevice.ERROR_OK:
            print "femNumTestCycles get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femNumTestCycles\t= ", value

        rc = theDevice.paramSet('tenGigFarmMode', 1)
        if rc != LpdDevice.ERROR_OK:
            print "tenGigFarmMode set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('tenGigFarmMode')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigFarmMode get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigFarmMode\t\t= ", value

        rc = theDevice.paramSet('femI2cBus', 0x300)
        if rc != LpdDevice.ERROR_OK:
            print "femI2cBus set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

        (rc, value) = theDevice.paramGet('femI2cBus')
        if rc != LpdDevice.ERROR_OK:
            print "femI2cBus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femI2cBus\t\t=  %3X" % value
        
#        time.sleep(2)
#    else:

        # Configure the FEM
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

