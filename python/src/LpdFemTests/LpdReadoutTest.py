'''
    LpdReadoutTest.py - Readout a system using the API
                        The number of modules in the system is set by LpdFemClient.
                    
'''

from LpdDevice.LpdDevice import LpdDevice
from networkConfiguration import *
import sys


def LpdReadoutTest(femHost=None, femPort=None):
    
    theDevice = LpdDevice()

    # Was either femHost and femPort NOT provided to this class?
    if (femHost == None) or (femPort == None):
        # Either or both were not supplied from the command line; Use networkConfiguration class
        networkConfig = networkConfiguration()
        femHost = networkConfig.ctrl0SrcIp
        femPort = int(networkConfig.ctrlPrt)

    rc = theDevice.open(femHost, femPort)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return

    bDebug = False
    
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
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourceMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourceMac \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1SourceIp', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourceIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourceIp \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1SourcePort', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourcePort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourcePort get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourcePort \t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1DestMac', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestMac \t\t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1DestIp', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestIp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestIp \t\t= %s." % value
    
        
#        rc = theDevice.paramSet('tenGig1DestPort', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
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

        rc = theDevice.paramSet('femAsicFastCmdRegSize', 22)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicFastCmdRegSize set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicFastCmdRegSize')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicFastCmdRegSize get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicFastCmdRegSize \t= %d." % value

#        rc = theDevice.paramSet('femAsicEnableMask', [1, 2, 3, 4])
        if rc != LpdDevice.ERROR_OK:
            print "femAsicEnableMask set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicEnableMask')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicEnableMask get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicEnableMask \t= ", value

        rc = theDevice.paramSet('femAsicGainOverride', 8)
        if rc != LpdDevice.ERROR_OK:
            print "femAsicGainOverride set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicGainOverride')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicGainOverride get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicGainOverride \t= %d." % value

        rc = theDevice.paramSet('femDataSource', 0)
        if rc != LpdDevice.ERROR_OK:
            print "femDataSource set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femDataSource')
        if rc != LpdDevice.ERROR_OK:
            print "femDataSource get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femDataSource \t\t= %d." % value

#        rc = theDevice.paramSet('femAsicSlowControlParams', "<xml../>")
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowControlParams set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicSlowControlParams')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicSlowControlParams get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicSlowControlParams =%s." % value

#        rc = theDevice.paramSet('femAsicFastCmdSequence', "<xml../>")
        if rc != LpdDevice.ERROR_OK:
            print "femAsicFastCmdSequence set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('femAsicFastCmdSequence')
        if rc != LpdDevice.ERROR_OK:
            print "femAsicFastCmdSequence get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "femAsicFastCmdSequence =%s." % value


    else:

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

