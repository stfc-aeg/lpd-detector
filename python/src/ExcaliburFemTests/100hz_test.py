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
    
#theFem.rdmaWrite(0x30000001, 0x00000000) # Re-ordered data
theFem.rdmaWrite(0x30000001, 0x00000001) # RAW data

theFem.rdmaWrite(0x48000000, (0xFF,))    # ASIC MUX select (was 0x0F)
theFem.rdmaWrite(0x48000002, (0x3860,))   # OMR LSB (0x3860), (0x460)
theFem.rdmaWrite(0x48000003, (0x0,))     # OMR MSB
theFem.rdmaWrite(0x48000006, (0x12,))	 # SHUTTER COUNTER (1250=3ms, 189C=4ms, 1EC2=5ms, 2800=6.502ms, 30D4=8ms, with RC=7F)
theFem.rdmaWrite(0x48000007, (0xF,))	 # was 0xF
theFem.rdmaWrite(0x48000008, (0x1,))	 # numtriggers
theFem.rdmaWrite(0x4800000A, (0x7F,))	 # was 0x5 - RESOLUTION COUNTER
theFem.rdmaWrite(0x4800000B, (0x2000,))
theFem.rdmaWrite(0x48000009, (0xC,))     # ASIC counter depth (0xC = 12 bits)
theFem.rdmaWrite(0x48000001, (0x1A41,))	# (0xE41)
