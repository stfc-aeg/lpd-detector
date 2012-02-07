'''
Created on Feb 7, 2012

@author: tcn45
'''

import sys

from ExcaliburFemTests.defaults import *
from FemClient.FemClient import  *

try:
    theFem = FemClient((femHost, femPort), femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)
    
# Set up UDP IP block 0
print "Set up UDP block 0"
theFem.rdmaWrite(0x00000000, (0x00000062,)) #UDP Block 0 MAC Source Lower 32')
theFem.rdmaWrite(0x00000001, (0x07001000,)) #UDP Block 0 MAC Source Upper 16/Dest Lower 16')
theFem.rdmaWrite(0x00000002, (0x205F1043,)) #UDP Block 0 MAC Dest Upper 32')
theFem.rdmaWrite(0x00000006, (0x000A77B8,)) #UPB Block 0 IP Dest Addr / Checksum')
theFem.rdmaWrite(0x00000007, (0x000A0202,)) #UPB Block 0 IP Dest Addr / Srd Addr')
theFem.rdmaWrite(0x00000008, (0x08000102,)) #UPB Block 0 IP Src Addr / Port')
theFem.rdmaWrite(0x0000000C, (0x000003E6,)) #UDP Block 0 Packet Size')    
theFem.rdmaWrite(0x00000004, (0xDB00001C,)) #UDP Block 0 IP Header Length')
theFem.rdmaWrite(0x00000009, (0x0008D1F0,)) #UDP Block 0 UDP Length')
theFem.rdmaWrite(0x0000000F, (0x00000011,)) #UDP Block 0 IFG Enable')
theFem.rdmaWrite(0x0000000D, (0x00000000,)) #UDP Block 0 IFG Value')
print ""

# Set up UDP IP block 1
print "Set up UDP block 1"
theFem.rdmaWrite(0x08000000, (0x00000062,)) #UDP Block 1 MAC Source Lower 32')
theFem.rdmaWrite(0x08000001, (0x07001000,)) #UDP Block 1 MAC Source Upper 16/Dest Lower 16')
theFem.rdmaWrite(0x08000002, (0x205F1043,)) #UDP Block 1 MAC Dest Upper 32')
theFem.rdmaWrite(0x08000006, (0x000A77B8,)) #UPB Block 1 IP Dest Addr / Checksum')
theFem.rdmaWrite(0x08000007, (0x000A0202,)) #UPB Block 1 IP Dest Addr / Srd Addr')
theFem.rdmaWrite(0x08000008, (0x08000102,)) #UPB Block 1 IP Src Addr / Port')
theFem.rdmaWrite(0x0800000C, (0x000003E6,)) #UDP Block 1 Packet Size')    
theFem.rdmaWrite(0x08000004, (0xDB00001C,)) #UDP Block 1 IP Header Length')
theFem.rdmaWrite(0x08000009, (0x0008D1F0,)) #UDP Block 1 UDP Length')
theFem.rdmaWrite(0x0800000B, (0x00000004,)) #UDP Block 1 Header Mode Enable')
theFem.rdmaWrite(0x0800000F, (0x00000011,)) #UDP Block 1 IFG Enable')
theFem.rdmaWrite(0x0800000D, (0x00000000,)) #UDP Block 1 IFG Value')
print""