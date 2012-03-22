'''
Created on Feb 2, 2012

@author: tcn45
'''
import sys

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

args = defaults.parseArgs()

try:
    theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)


if len(args) > 0:
    clock = int(args[0])
else:
    clock = 1
    
if clock == 0:
    print "Selecting XTAL clock:",
else:
    print "Selecting TFG2 clock:",

theFem.rdmaWrite(0x30000007, (clock))
response = theFem.rdmaRead(0x30000007, 1)

if response[1] == clock:
    print "OK"
else:
    print "FAILED"

