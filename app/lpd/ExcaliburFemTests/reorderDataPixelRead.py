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

theFem.rdmaWrite(0x30000001, (0x0,))	# Select , 1=raw data, 0=reordered data
theFem.rdmaWrite(0x48000000, (0x80,))    # ASIC MUX select
theFem.rdmaWrite(0x48000002, (0x3860,))  # OMR LSB
theFem.rdmaWrite(0x48000003, (0x0,))     # OMR MSB
theFem.rdmaWrite(0x48000006, (0xF,))
theFem.rdmaWrite(0x48000007, (0xF,))	# was 0x1
theFem.rdmaWrite(0x48000008, (0x1,))
theFem.rdmaWrite(0x4800000A, (0x5,))
theFem.rdmaWrite(0x4800000B, (0x2000,))
theFem.rdmaWrite(0x48000001, (0xE41,))
