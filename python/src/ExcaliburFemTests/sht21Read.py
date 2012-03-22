'''
Created on Feb 9, 2012

@author: tcn45
'''
import sys
import time

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import  *

def sht21Temp(theFem, deviceAddress):
    
    # Trigger temperature measurement without hold
    theFem.i2cWrite(deviceAddress, 0xf3)
    
    # Wait 100ms
    time.sleep(0.1)
    
    # Read three bytes back
    response = theFem.i2cRead(deviceAddress, 3)
    print [hex(val) for val in response]
    
    # Calculate temperature
    rawVal = (response[4] << 8) | response[5]
    temp = -46.85 + (175.72 * (rawVal / 65536.0)) 
    
    return temp

def sht21Humidity(theFem, deviceAddress):

    # Trigger humidity measurement without hold
    theFem.i2cWrite(deviceAddress, 0xf5)
    
    # Wait 50ms
    time.sleep(0.05)
    
    # Read three bytes back
    response = theFem.i2cRead(deviceAddress, 3)
    
    # Calculate humidity
    rawVal = (response[4] << 8) | response[5]
    humidity = -6.0 + (125.0 * (rawVal / 65536.0)) 
        
    return humidity

if __name__ == '__main__':
    
    defaults.parseArgs()

    try:
        theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
    except FemClientError as errString:
        print "Error: FEM connection failed:", errString
        sys.exit(1)
        
    deviceAddress = 0x340
    
    temp = sht21Temp(theFem, deviceAddress)
    humidity = sht21Humidity(theFem, deviceAddress)
    
    print "SHT21 temperature = %.1fC humidity = %.1f%%" % (temp, humidity)
