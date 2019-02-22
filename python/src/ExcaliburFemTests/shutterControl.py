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
    
theFem.rdmaWrite(0x48000000, (0x08,))    # ASIC MUX select
theFem.rdmaWrite(0x48000002, (0x38460,))  # OMR LSB
theFem.rdmaWrite(0x48000003, (0x0,))     # OMR MSB
theFem.rdmaWrite(0x48000006, (0xF,))	# Int. shutter duration (0)
theFem.rdmaWrite(0x48000007, (0xF,))	# Int. shutter duration (1)
theFem.rdmaWrite(0x48000008, (0x1,))
theFem.rdmaWrite(0x4800000A, (0x6,))	# Resolution counter, was 0x5
theFem.rdmaWrite(0x4800000B, (0x18000,))
theFem.rdmaWrite(0x48000009, (0xC,))     # ASIC counter depth (0xC = 12 bits)
theFem.rdmaWrite(0x48000001, (0x1E41,))	# 0xE41 for counter 0 read, 0x1641 for counter 1 read, 0x1E64 both
