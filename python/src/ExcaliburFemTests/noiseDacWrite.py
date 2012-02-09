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

theFem.rdmaWrite(0x48000000, (0x80,))  # ASIC MUX select
theFem.rdmaWrite(0x48000002, (0x61,))  # OMR LSB
theFem.rdmaWrite(0x48000003, (0x20,)) # OMR MSB
theFem.rdmaWrite(0x50000000, (0x80401013, 0x601AFFCC, 0xA020220C,   # DAC values
                              0xB225BE85, 0x25A01008, 0x04020100, 
                              0x0, 0x0))
theFem.rdmaWrite(0x48000001, (0x23,))  # Control register

response = theFem.rdmaRead(0x50000000, 8)
print "DAC values written =", [hex(val) for val in response]

