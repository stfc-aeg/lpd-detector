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

theFem.acquireSend(FemTransaction.CMD_ACQ_CONFIG, FemTransaction.ACQ_MODE_NORMAL, 0x60000, 0, 0)
theFem.acquireSend(FemTransaction.CMD_ACQ_START)
time.sleep(1.0)

theFem.rdmaWrite(0x30000001, 0x00000001) # Raw data
    
theFem.rdmaWrite(0x48000000, (0x80,))    # ASIC MUX select (was 0x0F)
theFem.rdmaWrite(0x48000002, (0x460,))  # OMR LSB
theFem.rdmaWrite(0x48000003, (0x0,))     # OMR MSB
theFem.rdmaWrite(0x48000006, (0x2800,))	# shutter counter 1250=3ms 2800=6ms with RC=0x7F
theFem.rdmaWrite(0x48000007, (0xF,))	# was 0xF
theFem.rdmaWrite(0x48000008, (0x3,))    # Frame loop counter = number of frames to acquire
theFem.rdmaWrite(0x4800000A, (0x7F,))	# shutter resolution counter
theFem.rdmaWrite(0x4800000B, (0x18000,))
theFem.rdmaWrite(0x4800000C, (0x7,))    # Test pulse count
theFem.rdmaWrite(0x48000009, (0xC,))     # ASIC counter depth (0xC = 12 bits)
theFem.rdmaWrite(0x48000001, (0x4A41,)) # normal C0 read with TP enabled (bit 14)

time.sleep(1.0)
theFem.acquireSend(FemTransaction.CMD_ACQ_STOP)
