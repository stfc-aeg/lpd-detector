'''
    LpdReadoutTest.py - Readout a super module system containing one tile, using the API
'''

import sys
from LpdDevice.LpdDevice import LpdDevice
from networkConfiguration import *

def lpdTest(femHost=None, femPort=None):
    
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

    # Configure the FEM
    rc = theDevice.configure()
    if rc != LpdDevice.ERROR_OK:
        print "configure() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
 
    # Acquire image data
    rc = theDevice.start()
    if rc != LpdDevice.ERROR_OK:
        print "run() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
 

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

    lpdTest(femHost, femPort)
