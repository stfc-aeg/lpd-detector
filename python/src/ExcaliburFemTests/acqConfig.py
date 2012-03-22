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
    
theFem.acquireSend(FemTransaction.CMD_ACQ_CONFIG, FemTransaction.ACQ_MODE_NORMAL, 0x18000, 0, 10)
theFem.acquireSend(FemTransaction.CMD_ACQ_START)
