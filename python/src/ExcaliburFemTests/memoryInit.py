'''
Created on Feb 6, 2012

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
    
initPayload = tuple([0xdeadbeef]*1024)
print len(initPayload)

for index in range(8):
    theAddr = index * 1024
    theFem.write(FemTransaction.BUS_RAW_REG, FemTransaction.WIDTH_LONG, theAddr, initPayload)