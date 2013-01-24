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
    
        rc = theDevice.paramSet('tenGig0SourceMac', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0SourceMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0SourceMac =%s." % value
    
        
        rc = theDevice.paramSet('tenGig0SourceIp', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0SourceIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0SourceIp =%s." % value
    
        
        rc = theDevice.paramSet('tenGig0SourcePort', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0SourcePort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0SourcePort =%d." % value
    
        
        rc = theDevice.paramSet('tenGig0DestMac', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0DestMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0DestMac =%s." % value
    
        
        rc = theDevice.paramSet('tenGig0DestIp', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0DestIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0DestIp =%s." % value
    
        
        rc = theDevice.paramSet('tenGig0DestPort', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig0DestPort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig0DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig0DestPort =%d." % value
    
        
        rc = theDevice.paramSet('tenGig1SourceMac', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourceMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourceMac =%s." % value
    
        
        rc = theDevice.paramSet('tenGig1SourceIp', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourceIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourceIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourceIp =%s." % value
    
        
        rc = theDevice.paramSet('tenGig1SourcePort', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1SourcePort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1SourcePort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1SourcePort =%d." % value
    
        
        rc = theDevice.paramSet('tenGig1DestMac', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestMac')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestMac set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestMac =%s." % value
    
        
        rc = theDevice.paramSet('tenGig1DestIp', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestIp')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestIp set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestIp =%s." % value
    
        
        rc = theDevice.paramSet('tenGig1DestPort', 13)
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGig1DestPort')
        if rc != LpdDevice.ERROR_OK:
            print "tenGig1DestPort set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGig1DestPort =%d." % value
    
    
        
        rc = theDevice.paramSet('tenGigInterframeGap', 0)
        if rc != LpdDevice.ERROR_OK:
            print "tenGigInterframeGap set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGigInterframeGap')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigInterframeGap set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigInterframeGap =%d." % value
    
        
        rc = theDevice.paramSet('tenGigUdpPacketLen', 0)
        if rc != LpdDevice.ERROR_OK:
            print "tenGigUdpPacketLen set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
        (rc, value) = theDevice.paramGet('tenGigUdpPacketLen')
        if rc != LpdDevice.ERROR_OK:
            print "tenGigUdpPacketLen set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
        else:
            print "tenGigUdpPacketLen =%d." % value

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
