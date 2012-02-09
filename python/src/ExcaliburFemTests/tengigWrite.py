'''
Created on Feb 7, 2012

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

# Set up UDP IP block 1
#print "Set up UDP block 1"
#theFem.rdmaWrite(0x08000000, 0x00000062) # UDP Block 1 MAC Source Lower 32
#theFem.rdmaWrite(0x08000001, 0x07001000) # UDP Block 1 MAC Source Upper 16/Dest Lower 16
#theFem.rdmaWrite(0x08000002, 0x205F1043) # UDP Block 1 MAC Dest Upper 32
#theFem.rdmaWrite(0x08000004, 0xDB00001C) # UDP Block 1 IP Ident   / Header Length
#theFem.rdmaWrite(0x08000006, 0x000A77B8) # UDP Block 1 IP Dest Addr / Checksum
#theFem.rdmaWrite(0x08000007, 0x000A0202) # UDP Block 1 IP Dest Addr / Srd Addr
#theFem.rdmaWrite(0x08000008, 0x08000102) # UDP Block 1 IP Src Addr / Port
#theFem.rdmaWrite(0x08000009, 0x0008D1F0) # UDP Block 1 UDP Length
#theFem.rdmaWrite(0x0800000B, 0x00000004) # UDP Block 1 Header Mode Enable
#theFem.rdmaWrite(0x0800000C, 0x000003E6) # UDP Block 1 Packet Size    
#theFem.rdmaWrite(0x0800000D, 0x00000000) # UDP Block 1 IFG Value
#theFem.rdmaWrite(0x0800000F, 0x00000011) # UDP Block 1 IFG Enable
#print""

# Set up LocalLink frame generator 0
print "Set up LocalLink frame generator 0"
theFem.rdmaWrite(0x10000001, 0x00000FFE) # DATA GEN 0 Data Length
theFem.rdmaWrite(0x10000000, 0x00000001) #'DATA GEN 0 Control
theFem.rdmaWrite(0x10000002, 0x00000063) # DATA GEN 0 Frame Count

# Trigger data generator
print "Triggering data generator"
theFem.rdmaWrite(0x30000000, 0x00000000) #Trigger data generator
theFem.rdmaWrite(0x30000000, 0x00000001) #Trigger data generator
theFem.rdmaWrite(0x30000000, 0x00000000) #Trigger data generator

# Rread local link monitor
print "Read local link monitor"
llMonVals = theFem.rdmaRead(0x38000010, 0xA)
print "Local link monitor result =", [hex(val) for val in llMonVals]
