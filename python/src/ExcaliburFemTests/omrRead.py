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

theFem.rdmaWrite(0x48000000, (0xF0,))  # ASIC MUX select
theFem.rdmaWrite(0x48000002, (0x67,))  # OMR LSB
theFem.rdmaWrite(0x48000003, (0x2E0,)) # OMR MSB
theFem.rdmaWrite(0x48000001, (0x25,))  # Control register

response = theFem.rdmaRead(0x50000000, 8)
eFuseId = response[6]
omrVal = (response[7] << 32) | response[8]

print "MPX ASIC eFuse-ID  =", hex(eFuseId)
print "MPX ASIC OMR value =", hex(omrVal)