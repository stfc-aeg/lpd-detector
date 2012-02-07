'''
Created on Feb 3, 2012

@author: tcn45
'''

import sys

from ExcaliburFemTests.defaults import *
from FemClient.FemClient import  *

try:
    theFem = FemClient((femHost, femPort), femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)

for device in range(2):
    
    devAddr = 0x321 + device
    
    for chan in range(4):
        
        addrPtr = 1 << (chan+4)
        theFem.i2cWrite(devAddr, (0x0, addrPtr))
        response = theFem.i2cRead(devAddr, 2)
        #print [hex(val) for val in response]
        adcVal = ((response[4] << 8) | response[5]) & 0x7FF
        print "Device", device, "channel", chan, "value", adcVal