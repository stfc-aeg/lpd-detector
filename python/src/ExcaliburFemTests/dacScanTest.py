'''
Created on Feb 6, 2012

@author: tcn45
'''
import sys

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

def setDac(aVal):
    
    dacWord7 = aVal << 14
    
    theFem.rdmaWrite(0x48000000, (0x80,))  # ASIC MUX select
    theFem.rdmaWrite(0x48000002, (0x61,))  # OMR LSB
    theFem.rdmaWrite(0x48000003, (0x20,)) # OMR MSB
    theFem.rdmaWrite(0x50000000, (0x0, 0x0, 0x0,   # DAC values
                                  0x0, 0x0, 0x0, 
                                  dacWord7, 0x0))
    theFem.rdmaWrite(0x48000001, (0x23,))  # Control register

    response = theFem.rdmaRead(0x50000000, 8)
    #print "DAC values written =", [hex(val) for val in response]

def readAdc(aDevice, aChan):
    
    devAddr = 0x321 + aDevice
    
    addrPtr = 1 << (aChan + 4)
    theFem.i2cWrite(devAddr, (0x0, addrPtr))
    response = theFem.i2cRead(devAddr, 2)
    adcVal = ((response[4] << 8) | response[5]) & 0x7FF
    #print "Device", aDevice, "channel", aChan, "value", adcVal
    
    return adcVal

if __name__ == '__main__':
    
    defaults.parseArgs()
    
    try:
        theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
    except FemClientError as errString:
        print "Error: FEM connection failed:", errString
        sys.exit(1)
        
    for dacVal in range(0,500,25):
        setDac(dacVal)
        adcVal = readAdc(0, 1)
        print "DAC: %4d ADC: %4d" %  (dacVal, adcVal)
    
