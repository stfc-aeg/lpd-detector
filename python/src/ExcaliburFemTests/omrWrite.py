'''
Created on Feb 2, 2012

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

theFem.rdmaWrite(0x48000000, (0xFF,))
theFem.rdmaWrite(0x48000002, (0x67,))
theFem.rdmaWrite(0x48000003, (0x2E0,))
theFem.rdmaWrite(0x48000001, (0x33,))

response = theFem.rdmaRead(0x50000000, 8)
print "OMR write response =", [hex(val) for val in response]