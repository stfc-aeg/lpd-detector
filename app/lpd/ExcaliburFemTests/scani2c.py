'''
Created on Feb 9, 2012

@author: tcn45
'''
import sys

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

defaults.parseArgs()

try:
    theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)
    
baseAddress = 0x300

for offset in range(127):
    
    deviceAddress = baseAddress + offset
    #print hex(deviceAddress)
    response = theFem.i2cRead(deviceAddress, 1)
    if len(response) > 4:
        print hex(deviceAddress), len(response), [hex(val) for val in response]
        print "Found I2C device at address", '0x{:X}'.format(deviceAddress)
