'''
Created on Feb 6, 2012

@author: tcn45
'''
import sys
import time

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

defaults.parseArgs()

try:
    theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)

theFem.acquireSend(FemTransaction.CMD_ACQ_CONFIG, FemTransaction.ACQ_MODE_NORMAL, 0x60000, 4, 4)
theFem.acquireSend(FemTransaction.CMD_ACQ_START)
time.sleep(1.0)

#theFem.rdmaWrite(0x30000001, 0x00000001) # Raw data

theFem.rdmaWrite(0x30000001, 0x00000000) # Reordered data    

# Set up and trigger C1 read 
theFem.rdmaWrite(0x48000000, (0x80,))    # ASIC MUX select (was 0x3F)
theFem.rdmaWrite(0x48000002, (0x464,))   # OMR LSB : 0x460=C0 0x464=C1 0x40460 for C0 row 0 only, (0x3BC60), 0x60
theFem.rdmaWrite(0x48000003, (0x0,))     # OMR MSB
theFem.rdmaWrite(0x48000006, (0x1,))	# was 0xF
theFem.rdmaWrite(0x48000007, (0x1,))	# was 0xF
theFem.rdmaWrite(0x48000008, (0x1,))
theFem.rdmaWrite(0x4800000A, (0x1,))	# was 0x5
theFem.rdmaWrite(0x4800000B, (0x18000,)) # was 0x7000
theFem.rdmaWrite(0x48000009, (0xC,))     # ASIC counter depth (0xC = 12 bits)
theFem.rdmaWrite(0x48000001, (0x3041,)) # 0x2841 = C0, 0x3041= C1 

time.sleep(1.0)

# Set up and trigger C0 read
theFem.rdmaWrite(0x48000002, (0x460,))   # OMR LSB : 0x460=C0 0x464=C1
theFem.rdmaWrite(0x48000001, (0x2841,))

time.sleep(1.0)

theFem.acquireSend(FemTransaction.CMD_ACQ_STOP)

