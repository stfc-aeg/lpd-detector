'''
    LpdReadoutTest.py - Readout a system using the API
                    
'''

from LpdDevice.LpdDevice import LpdDevice
from EthernetUtility import EthernetUtility 
import argparse, sys
from datetime import datetime

# New imports
from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

############# Copied in XML Parser class ###########

class LpdReadoutConfigError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
class LpdReadoutConfig():
    
    def __init__(self, xmlObject, fromFile=False):
        
        if fromFile == True:
            self.tree = ElementTree.parse(xmlObject)
            self.root = self.tree.getroot()
        else:
            self.tree = None;
            self.root = ElementTree.fromstring(xmlObject)

        if self.root.tag != 'lpd_readout_config':
            raise LpdReadoutConfigError('Root element is not an LPD configuration tree')
        
    def parameters(self):
        
        for child in self.root:
            
            param = child.tag
            paramType = child.get('type', default="str")
            valStr = child.get('val', default=None)
            
            if valStr == None:
                raise LpdReadoutConfigError("Parameter %s has no value specified" % param)
            try:
                valStr = valStr.split(",")
                valLength = len( valStr)
                val = []

                for idx in range(valLength):

                    if paramType == 'int':
                        val.append( int(valStr[idx], 0))
                    elif paramType == 'bool':
                        if valStr[idx] == 'True':
                            val.append( True)
                        elif valStr[idx] == 'False':
                            val.append( False)
                        else:
                            raise LpdReadoutConfigError("Parameter %s has illegal boolean value %s" % (param, valStr[idx]))
                    elif paramType == 'str':
                        val.append( str(valStr[idx]))
                    else:
                        raise LpdReadoutConfigError("Parameter %s has illegal type %s" % (param, paramType) )

                if valLength == 1:
                    if paramType == 'int':
                        val = val[0]
                    elif paramType == 'bool':
                        val = val[0]
                    elif paramType == 'str':
                        val = val[0]

            except ValueError:
                raise LpdReadoutConfigError("Parameter %s with value %s cannot be converted to type %s" % (param, valStr[idx], paramType))

            yield (param, val)
   
####################################################

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

    ###################################################################
    
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
#            asicCmdSequence = 'Config/CmdSequence/Command_ShortExposure_V2_multipleImages.xml'
        elif xmlConfig == 2:
#            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicSetupParams = 'Config/SetupParams/Setup_LowPower_128Asics.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_V2.xml'
#            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_MultipleImages_512.xml'
        elif xmlConfig == 3:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/asic_pseudo_random_asicv2.xml'
        elif xmlConfig == 4:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/short_exposure_all_3gains_asicv2_B.xml'
        elif xmlConfig == 5:
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
            asicCmdSequence = 'Config/CmdSequence/long_exposure_all_3gains_asicv2_C.xml'
        elif xmlConfig == 6:
            asicSetupParams = 'Config/SetupParams/Setup_Chessboard.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_ShortExposure_V2.xml'
        else:
            asicSetupParams = "Config/SetupParams/Setup_Serial_8through1.xml"    # Left to right: ascending order
            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_V2.xml'
#        asicSetupParams = "Config/SetupParams/Setup_Serial_1through8.xml"    # Left to right: ascending order
#        asicSetupParams = "Config/SetupParams/Setup_Serial_8through1.xml"    # Left to right: ascending order
            asicSetupParams = "Config/SetupParams/Setup_Serial_XFEL.xml"
#            asicSetupParams = "Config/SetupParams/Setup_Serial_KLASSE.xml"

    configFilename = 'Config/readoutConfiguration.xml'

    print "================    XML Filenames   ================"
    print asicSetupParams
    print asicCmdSequence
    print configFilename

    ###################################################################

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

    #########################################################
    # Set variables using XML configuration file
    #########################################################

    basicConfig = LpdReadoutConfig(configFilename, fromFile=True)
    for (paramName, paramVal) in basicConfig.parameters():
        rc = theDevice.paramSet(paramName, paramVal)
        if rc != LpdDevice.ERROR_OK:
            print "Error %d: configuring %s to value: " % (rc, paramName), paramVal
            errorCount += 1
    
    ############################################################
    # Set variables using API calls that are machine specific
    #########################################################
    
    param = 'tenGig0SourceIp'
    rc = theDevice.paramSet(param, tenGigSourceIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestMac'
    rc = theDevice.paramSet(param, tenGigDestMac)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
    
    param = 'tenGig0DestIp'
    rc = theDevice.paramSet(param, tenGigDestIp)
    if rc != LpdDevice.ERROR_OK:
        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        errorCount += 1
        
#    rc = theDevice.paramSet('femAsicEnableMask', [0x00FF0000, 0x00000000, 0x00000000, 0x000000FF])    # Enable 2 Tile System's ASICs
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF])    # Enable everything
#    rc = theDevice.paramSet('femAsicEnableMask', [0xFFFF0000, 0x00000000, 0x0000FF00, 0x00000000])    # Supermodule with three tiles
#    param = 'femAsicEnableMask'
#    rc = theDevice.paramSet(param, 9999)
#    if rc != LpdDevice.ERROR_OK:
#        print "%s set failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#        errorCount += 1
    

    #########################################################
    # Check for errors before proceeding..
    #########################################################
    
    if errorCount > 0:
        print "================================"
        print "Detected %i error(s), aborting.." % errorCount
    else:
        # No errors encountered, proceeding

        #########################################################
        # Read back the "Expert" Level variables settings
        #########################################################
    
        if bDebug:

            print "================ 'Expert' Variables ================"
            paramExpertVariables = ['tenGig0SourceMac', 'tenGig0SourceIp', 'tenGig0SourcePort', 'tenGig0DestMac', 'tenGig0DestIp', 'tenGig0DestPort', 'tenGig0DataFormat',
                                    'tenGig0DataGenerator', 'tenGig0FrameLength', 'tenGig0NumberOfFrames', 'tenGigFarmMode', 'tenGigInterframeGap', 'tenGigUdpPacketLen', 
                                    'femAsicSetupClockPhase', 'femAsicVersion', 'femDebugLevel', 'femEnableTenGig',
                                    'femStartTrainPolarity', 'femVetoPolarity']

        for param in paramExpertVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value.__repr__())

        #########################################################
        # Read back all User Level variables
        #########################################################
        
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
            
        #########################################################
        # Configure the FEM
        #########################################################

        rc = theDevice.configure()
        if rc != LpdDevice.ERROR_OK:
            print "configure() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
            theDevice.close()
            sys.exit()

        # Acquire image data
        rc = theDevice.start()
        if rc != LpdDevice.ERROR_OK:
            print "run() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
            theDevice.close()
            sys.exit()
    
        # Stop transaction
        rc = theDevice.stop()
        if rc != LpdDevice.ERROR_OK:
            print "stop() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
            theDevice.close()
            sys.exit()

    print "Closing Fem connection.. "
    print "Debug timestamp: %s" % str( datetime.now())[11:-4]        
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

#    while 1:
#        LpdReadoutTest(tenGig, femHost, femPort, destIp)
    LpdReadoutTest(tenGig, femHost, femPort, destIp)
