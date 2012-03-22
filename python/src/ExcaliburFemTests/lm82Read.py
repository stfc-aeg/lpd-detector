'''
Created on Feb 13, 2012

@author: tcn45
'''

import sys
import time

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

args = defaults.parseArgs()
    
try:
    theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)

devAddr = 0x18
while 1:
    theFem.i2cWrite(devAddr, 0x1)
    response = theFem.i2cRead(devAddr, 1)
    print "FPGA temperature = %dC" % (response[4])
    time.sleep(2)
