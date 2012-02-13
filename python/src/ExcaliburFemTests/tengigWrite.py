'''
Created on Feb 7, 2012

@author: tcn45
'''

import sys
import time

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

modeString = []
args = defaults.parseArgs()

# Set data source mode. default or 0 = from DDR, 1 = LL frame gen
mode = 0 # 0 = data from DDR, 1 = data from LL frame gen
if len(args) > 0:
    mode = int(args[0])    
print "Data source mode is", mode
    
try:
    theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)
    
# Set up UDP IP block 0
print "Set up UDP block 0"
theFem.rdmaWrite(0x00000000, 0x00000062) # UDP Block 0 MAC Source Lower 32
theFem.rdmaWrite(0x00000001, 0x07001000) # UDP Block 0 MAC Source Upper 16/Dest Lower 16
theFem.rdmaWrite(0x00000002, 0x205F1043) # UDP Block 0 MAC Dest Upper 32
theFem.rdmaWrite(0x00000004, 0xDB00001C) # UDP Block 0 IP Ident / Header Length
theFem.rdmaWrite(0x00000006, 0x000A77B8) # UDP Block 0 IP Dest Addr / Checksum
theFem.rdmaWrite(0x00000007, 0x000A0202) # UDP Block 0 IP Dest Addr / Src Addr
theFem.rdmaWrite(0x00000008, 0x08000102) # UDP Block 0 IP Src Addr / Src Port
theFem.rdmaWrite(0x00000009, 0x0008D1F0) # UDP Block 0 UDP Length / Dest Port 
theFem.rdmaWrite(0x0000000C, 0x000003E6) # UDP Block 0 Packet Size    
theFem.rdmaWrite(0x0000000D, 0x00001000) # UDP Block 0 IFG Value
theFem.rdmaWrite(0x0000000F, 0x00000011) # UDP Block 0 IFG Enable

if mode == 0:
    
    theFem.rdmaWrite(0x30000001, 0x00000001) # Selects DDR memory

else:

    theFem.rdmaWrite(0x30000001, 0x00000000) # Selects LL frame gen
    
    # Set up LocalLink frame generator 0
    print "Set up LocalLink frame generator 0"
    theFem.rdmaWrite(0x10000001, 0x00000FFE) # DATA GEN 0 Data Length
    theFem.rdmaWrite(0x10000000, 0x00000001) #'DATA GEN 0 Control
    #theFem.rdmaWrite(0x10000002, 0x00000063) # DATA GEN 0 Frame Count
    theFem.rdmaWrite(0x10000002, 0x00000000)
    
    # Trigger data generator
    print "Triggering data generator"
    theFem.rdmaWrite(0x30000000, 0x00000000) #Trigger data generator
    theFem.rdmaWrite(0x30000000, 0x00000001) #Trigger data generator
    theFem.rdmaWrite(0x30000000, 0x00000000) #Trigger data generator

# Read local link monitor
print "Read local link monitor"
llMonVals = theFem.rdmaRead(0x38000010, 0xA)
print "Local link monitor result =", [hex(val) for val in llMonVals]
