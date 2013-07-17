'''
    LpdSlimmedReadoutTest.py - Readout based upon LpdReadoutTest.py - but migrating all the API params to a stand alone XML file.

    Authour: ckd27546
    Date: 09/05/2013
'''

from LpdDevice.LpdDevice import LpdDevice
import sys

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
                if paramType == 'int':
                    val = int(valStr, 0)
                elif paramType == 'bool':
                    if valStr == 'True':
                        val = True
                    elif valStr == 'False':
                        val = False
                    else:
                        raise LpdReadoutConfigError("Parameter %s has illegal boolean value %s" % (param, valStr))
                elif paramType == 'str':
                    val = str(valStr)
                else:
                    raise LpdReadoutConfigError("Parameter %s has illegal type %s" % (param, paramType) )
            except ValueError:
                raise LpdReadoutConfigError("Parameter %s with value %s cannot be converted to type %s" % (param, valStr, paramType))

            yield (param, val)
   

####################################################

def LpdReadoutTest(femHost='192.168.2.2', femPort=6969):
    
    theDevice = LpdDevice()

    rc = theDevice.open(femHost, femPort)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return

    ################################################################
    
    AsicVersion = 2    # 1 or 2
    xmlConfig   = 2    # 0 = test, 1=short (normal) exposure, 2= long exposure (slowed down)

    if AsicVersion == 1:
        
        if xmlConfig == 1:
            asicSetupParams = 'Config/SetupParams/Setup.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure_what.xml'
        elif xmlConfig == 2:
            asicSetupParams = 'Config/SetupParams/Setup_Preamble.xml'
            asicCmdSequence = 'Config/CmdSequence/Command_LongExposure.xml'
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

    print asicSetupParams
    print asicCmdSequence
    
    configFilename = 'Config/readoutConfiguration.xml'

    print configFilename
    print ""
    
    ################################################################

    rc = theDevice.paramSet('femAsicSetupParams', asicSetupParams)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicSlowControlParams set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    rc = theDevice.paramSet('femAsicCmdSequence', asicCmdSequence)
    if rc != LpdDevice.ERROR_OK:
        print "femAsicFastCmdSequence set failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    ######################################################
    # Start configuring variables using API calls
    ######################################################

    basicConfig = LpdReadoutConfig(configFilename, fromFile=True)
    for (paramName, paramVal) in basicConfig.parameters():
        rc = theDevice.paramSet(paramName, paramVal)
        if rc != LpdDevice.ERROR_OK:
            print "Error %d: configuring %s to value: " % (rc, paramName), paramVal

    basicConfig = LpdReadoutConfig(configFilename, fromFile=True)
    for (paramName, paramVal) in basicConfig.parameters():
        (rc, paramVal) = theDevice.paramGet(paramName)
        if rc != LpdDevice.ERROR_OK:
            print "Error %d: configuring %s to value: " % (rc, paramName), paramVal
        else:
            print "{0:<32} = {1:<10}".format(paramName, paramVal.__repr__())

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
        femHost = '192.168.2.2'
        femPort = 6969

    LpdReadoutTest(femHost, femPort)


