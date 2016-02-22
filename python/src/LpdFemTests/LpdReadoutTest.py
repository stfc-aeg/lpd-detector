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

def LpdReadoutTest(tenGig, femHost, femPort, destIp, destMac, srcIp):
    
    theDevice = LpdDevice()

    if tenGig:
        # Define IP & Mac addresses from tenGig's PC interface
        tenGigConfig   = EthernetUtility("eth%i" % tenGig)

        tenGigDestIp   = tenGigConfig.ipAddressGet()
        if (tenGigDestIp is None):
            print "Error extracting destination IP for network card eth%i" % tenGig
            return

        tenGigDestMac  = tenGigConfig.macAddressGet()
        tenGigSourceIp = tenGigConfig.obtainDestIpAddress(tenGigDestIp) #  e.g. If PC address: 10.0.0.1 then dest address: 10.0.0.2
        
        # Check address variables
        if (tenGigDestMac is None) or (tenGigSourceIp is None):
            print "Error obtaining DestMac and/or SourceIp."
            return
    else:
        # Define addresses from destIp, destMac, srcIp
        tenGigDestIp   = destIp
        tenGigDestMac  = destMac
        tenGigSourceIp = srcIp

    rc = theDevice.open(femHost, femPort)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device [%s:%s]: %s" % (femHost, femPort, theDevice.errorStringGet())
        return
    else:
        print "\nConnected to FEM device %s:%s" % (femHost, femPort)

    # Display "expert" variables?
    bDebug = True
    
    #Track number of configuration errors:
    errorCount = 0

    ###################################################################
    
    AsicVersion = 2    # 1 or 2
    xmlConfig   = 1   # 0=test, 1=short exposure, 2=long exposure, 3=pseudorandom, 4=all 3 gain readout with short exposure, 5=all 3 gain readout with long exposure
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
            asicSetupParams = 'Config/SetupParams/Setup_LowPower.xml'
#            asicSetupParams = 'Config/SetupParams/Setup_LowPower_128Asics.xml'
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

    #configFilename = 'Config/readoutConfiguration.xml'
    vetoFilename   = 'Config/VetoPatterns/veto_file_test.xml'
#    asicSetupParams = "/u/ckd27546/workspace/lpdSoftware/LpdFemTests/Config/SetupParams/Setup_Matt.xml"    # Left to right: ascending order
#    asicCmdSequence = '/u/ckd27546/workspace/lpdSoftware/LpdFemGui/config/Command_LongExposure_V2.xml'
    configFilename = '/u/ckd27546/workspace/lpdSoftware/LpdFemGui/config/Johns_settings.xml'
    configFilename ='/u/ckd27546/workspace/lpdSoftware/LpdFemGui/config/superModuleReadout.xml'
    
    print "================    XML Filenames   ================"
    print asicSetupParams
    print asicCmdSequence
    print configFilename
    print vetoFilename
    
    ###################################################################

    rc = theDevice.paramSet('femAsicSetupParams', asicSetupParams)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSetupParams set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        errorCount += 1
    
    rc = theDevice.paramSet('femAsicCmdSequence', asicCmdSequence)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicCmdSequence set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        errorCount += 1

    rc = theDevice.paramSet('cccVetoPatternFile', vetoFilename)
    if rc != LpdDevice.ERROR_OK:
        print "cccVetoPatternFile set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
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

#     print "================  Set in Fem: Source & Destination Variables ================"
# 
#     paramExpertVariables = ['tenGig0SourceMac', 'tenGig0SourceIp', 'tenGig0SourcePort', 'tenGig0DestMac', 'tenGig0DestIp', 'tenGig0DestPort']
# 
#     for param in paramExpertVariables:
#         (rc, value) = theDevice.paramGet(param)
#         if rc != LpdDevice.ERROR_OK:
#             print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#         else:
#             print "{0:<32} = {1:<10}".format(param, value.__repr__())

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
                                    'femStartTrainPolarity', 'femVetoPolarity', 'femPpcMode',
                                    'cccSystemMode', 'cccEmulationMode', 'cccProvideNumberImages', 'cccVetoStartDelay', 'cccStopDelay', 'cccResetDelay',
                                    'cccEmulatorFixedRateStarts', 'cccEmulatorIntervalBetweenFixedRateStarts','cccEmulatorNumFixedRateStarts', 
                                    'femAsicTestDataPatternType', 'femPpcEmulatePipeline', 'femPpcImageReordering',  
                                    'femTrainIdInitLsw', 'femTrainIdInitMsw']

        for param in paramExpertVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value.__repr__())
 
        # Read back 'femLpdClientVersion' separately (hexadecimal display)
        param = 'femLpdClientVersion'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = 0x{1:<8X}".format(param, value)
     
        #########################################################
        # Read back all User Level variables
        #########################################################

        paramUserVariables = ['femAsicClockSource', 'femAsicDataType', 'femAsicGain', 'femAsicGainOverride', 'femAsicLocalClock', 'femAsicModuleType', 
                              'femAsicPixelFeedbackOverride', 'femAsicPixelSelfTestOverride', 'femAsicRxCmdWordStart', 'femAsicSetupLoadMode',
                              'femStartTrainSource', 'femDataSource', 'femInvertAdcData', 'numberImages', 'numberTrains', 'femStartTrainDelay', 'femStartTrainInhibit']
 
        print "================ 'User'   Variables ================"
 
        for param in paramUserVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
            else:
                print "{0:<32} = {1:<10}".format(param, value.__repr__())
 
        param = 'femAsicEnableMask'
        (rc, value) = theDevice.paramGet(param)
        if rc != LpdDevice.ERROR_OK:
            print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
        else:
            print "{0:<32} = [{1:<8X}, {2:<8X}, {3:<8X}, {4:<8X}]".format(param, value[0], value[1], value[2], value[3])
     
        # Check XML string variables read back, but don't display their [long-winded] XML strings
        paramUserExtraVariables = ['femAsicCmdSequence',  'femAsicSetupParams', 'cccVetoPatternFile'] 

        for param in paramUserExtraVariables:
            (rc, value) = theDevice.paramGet(param)
            if rc != LpdDevice.ERROR_OK:
                print "%s get failed rc=%d : %s" % (param, rc, theDevice.errorStringGet())
#            else:
#                print "{0:<32} = {1:<10}".format(param, value)
            
        #########################################################
        # Configure the FEM
        #########################################################

        print "- - - - - - - - - - - - - - - - - - - - - - - -  Configure - - - - - - - - - - - - - - - - - - - - - - - - "
        rc = theDevice.configure()
        if rc != LpdDevice.ERROR_OK:
            print "configure() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
            theDevice.close()
            sys.exit()
 
        # Acquire image data
        print "- - - - - - - - - - - - - - - - - - - - - - - -  Start     - - - - - - - - - - - - - - - - - - - - - - - - "
        rc = theDevice.start()
        if rc != LpdDevice.ERROR_OK:
            print "run() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
            theDevice.close()
            sys.exit()
     
        # Stop transaction
        print "- - - - - - - - - - - - - - - - - - - - - - - -  Stop      - - - - - - - - - - - - - - - - - - - - - - - - "
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
    tenGig  = None  # If nowt specified, default: eth2    [on devgpu02: 10.0.0.1; 00-07-43-10-65-A0]
    srcIp   = None  # FEM's IP, entered directly (thus not the address above tenGig's) 
    #srcMac  = None # Redundant (Always 62-00-00-00-00-01 ?)
    destIp  = None  # PC's IP, overrides tenGig's
    destMac = None  # PC's Mac, overrides tenGig's
    
    # Create parser object and arguments
    ex1 = "python LpdReadoutTest.py --tengig 7"
    ex2 = "python LpdReadoutTest.py --destip 192.0.0.100 --destmac 00-07-43-10-65-A0 --srcip 192.0.0.102"
    parser = argparse.ArgumentParser(description="LpdReadoutTest.py - configure and readout an LPD detector. ",
                                     epilog="Defaults: tengig=(eth)1, destip=10.0.0.2, femhost=192.168.2.2, femport=6969\nExample 1: %s\nExample 2: %s\n" % (ex1, ex2)) 

    parser.add_argument("--femhost",    help="Set fem host IP (e.g. 192.168.2.2)",          type=str, default=femHost)
    parser.add_argument("--femport",    help="Set fem port (eg 61649)",                     type=int, default=femPort)
    parser.add_argument("--tengig",     help="Set tenGig ethernet card (e.g. 2 for eth2)",  type=int, default=tenGig)
    parser.add_argument("--srcip",      help="Set source IP (eg 10.0.0.2)",                 type=str, default=srcIp)    # Source = FEM
    #parser.add_argument("--srcmac",     help="Set source MAC (eg 52-54-00-83-96-BD)",  type=str, default=srcMac)
    parser.add_argument("--destip",     help="Set destination IP (eg 10.0.0.1)",            type=str, default=destIp)   # Destination = PC
    parser.add_argument("--destmac",    help="Set destination MAC (eg 00-07-43-10-65-A0)",  type=str, default=destMac)  # New, to be implemented fully
    args = parser.parse_args()

    # Copy value(s) for the provided arguments
    if args.femhost:        femHost = args.femhost
    if args.femport:        femPort = args.femport
    if args.tengig:         tenGig  = args.tengig
    if args.srcip:          srcIp   = args.srcip
    if args.destip:         destIp  = args.destip
    if args.destmac:        destMac = args.destmac

#     print "\nParser debugging..\nfemHost: %s\n femPort: %s\n tenGig: %s\n srcIp: %s\n destIp: %s\n destMac: %s\n"  % (femHost, femPort, tenGig, srcIp, destIp, destMac)
#     print ""
    # If no command line arguments (apart from femhost, femport), give tenGig default value
    if (srcIp == None) and (destIp == None) and (destMac == None) and (tenGig == None):
        tenGig = 1
        
    # Catch illegal selections
    if ((destIp == None) and destMac) or (destIp and (destMac == None)):
        print "\n  *** Illegal selection: Either specify both destination IP and Mac or neither address"
    else:
        if (destIp) and (srcIp== None):
            print "\n  *** Illegal selection: Cannot specify destination IP & Mac without a source IP"
        else:
            LpdReadoutTest(tenGig, femHost, femPort, destIp, destMac, srcIp)
