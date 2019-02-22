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
    
# Set up the DMA controller for pixel config upload
#theFem.acquireSend(FemTransaction.CMD_ACQ_CONFIG, FemTransaction.ACQ_MODE_UPLOAD, 0x18000, 8, 0x30000000)
#theFem.acquireSend(FemTransaction.CMD_ACQ_START)

# Send a pixel config write transaction to the ASIC(s)
theFem.rdmaWrite(0x48000000, (0x80,))    # ASIC MUX select (was 0x3F)
theFem.rdmaWrite(0x48000002, (0x2,))     # OMR LSB (0x2=C0, 0x6=C1)
theFem.rdmaWrite(0x48000003, (0x0,))     # OMR MSB
theFem.rdmaWrite(0x48000001, (0x2B,))    # Ctrl register setup and command

# Stop the DMA controller
#theFem.acquireSend(FemTransaction.CMD_ACQ_STOP)
