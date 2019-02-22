'''
Created on Feb 6, 2012

@author: tcn45
'''
import sys
import time

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

THRESHOLD_0 =  1
FBK         = 22
CAS         = 23
TP_REFA     = 24
TP_REFB     = 25


def setDac(aDac, aVal):
    
    dacWord = [0] * 8
    
    if aDac == THRESHOLD_0: 
        dacWord[6] = aVal << 14
        
    elif aDac == FBK:
        dacWord[0] = aVal >> 2
        dacWord[1] = (aVal & 0x3) << 30
        
    elif aDac == CAS:
        dacWord[0] = aVal << 6
        
    elif aDac == TP_REFA:
        dacWord[0] = aVal << 14
        
    elif aDac == TP_REFB:
        dacWord[0] = aVal << 23
        
    omr_msb = aDac << 5 
    theFem.rdmaWrite(0x48000000, (0x80,))  # ASIC MUX select
    theFem.rdmaWrite(0x48000002, (0x61,))  # OMR LSB
    theFem.rdmaWrite(0x48000003, omr_msb)    # OMR MSB - SenseDac mux select
    theFem.rdmaWrite(0x50000000, tuple(dacWord))
    theFem.rdmaWrite(0x48000001, (0x23,))  # Control register

    response = theFem.rdmaRead(0x50000000, 8)
    #print "DAC values written =", [hex(val) for val in response[1:]]

def readAdc(aDevice, aChan):
    
    devAddr = 0x321 + aDevice
    
    addrPtr = 1 << (aChan + 4)
    theFem.i2cWrite(devAddr, (0x0, addrPtr))
    time.sleep(0.1)
    response = theFem.i2cRead(devAddr, 2)
    adcVal = ((response[4] << 8) | response[5]) & 0xFFF
    #print "Device", aDevice, "channel", aChan, "value", adcVal
    
    return adcVal

if __name__ == '__main__':
    
    args = defaults.parseArgs()

    if len(args) > 0:
        theDac = int(args[0])
    else: 
        theDac = 1
        
    try:
        theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
    except FemClientError as errString:
        print "Error: FEM connection failed:", errString
        sys.exit(1)
    
    if theDac < 9:
        dacMax = 512
    elif theDac < 24:
        dacMax = 256
    else:
        dacMax = 512
    
    try:          
        for dacVal in range(0,dacMax,10):
            setDac(theDac, dacVal)
            time.sleep(0.1)
            adcVal = readAdc(0, 1)
            print "DAC: %4d ADC: %4d" %  (dacVal, adcVal)            
    except FemClientError as e:
        print "Error:", e
        
        
