'''
    LpdReadoutTest.py - Readout a super module system containing one tile, using the API
'''

from LpdDevice.LpdDevice import LpdDevice

def lpdTest():
    
    theDevice = LpdDevice()
   
#    rc = theDevice.open('127.0.0.1', 5000)
    rc = theDevice.open('192.168.2.2', 6969)    # Kiribati, devgpu02
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return
    
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

    (rc, bRet) = theDevice.paramGet('configure')
    if rc != LpdDevice.ERROR_OK:
        print "configure() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
 
    (rc, bRet) = theDevice.paramGet('run')
    if rc != LpdDevice.ERROR_OK:
        print "run() failed rc=%d : %s" % (rc, theDevice.errorStringGet())
 

    print "Closing Fem connection.. "        
    theDevice.close()


if __name__ == '__main__':
    
    lpdTest()
