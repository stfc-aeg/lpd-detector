'''
LpdProtoTest - XFEL LPD class sitting between the API and the FemC FemClient

             - Will be renamed LpdFemClient at some point in the future
            
Created 09 October 2012

@Author: ckd
'''

import sys

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction

class LpdProtoTest(FemClient):
    '''
    
    '''

    # ADC channel numbers
    PSU_TEMP_CHAN =      6
    SENSA_TEMP_CHAN =   24
    SENSB_TEMP_CHAN =   25
    SENSC_TEMP_CHAN =   26
    SENSD_TEMP_CHAN =   27
    SENSE_TEMP_CHAN =   28
    SENSF_TEMP_CHAN =   29
    SENSG_TEMP_CHAN =   30
    SENSH_TEMP_CHAN =   31
    
    # Bit numbers for control bits
    HV_CTRL_BIT    = 0
    LV_CTRL_BIT    = 1

    # Values for control bits
    OFF = 1
    ON  = 0

    # Bit numbers for status bits
    FEM_STATUS_BIT = 2
    EXT_TRIP_BIT   = 3
    FAULT_FLAG_BIT = 4
    OVERCURRENT_BIT =5
    HIGH_TEMP_BIT  = 6
    LOW_TEMP_BIT   = 7
    
    # Values for status bits
    TRIPPED = 1
    FAULT   = 1
    NORMAL  = 0
    
    # Enumarate fault flag as either cleared (0) or tripped (1) 
    flag_message = ["No", "Yes"]

    # Fem has three internal i2c buses, power card uses bus 0x300
    i2cInternalBusOffset = 0x300

    AD7998ADDRESS = [0x22, 0x21, 0x24, 0x23]
    
    
    def __init__(self, hostAddr=None, timeout=None):
        '''
            Constructor for LpdProtoTest class
        '''
        
        # Call superclass initialising function
        super(LpdProtoTest, self).__init__(hostAddr, timeout)
        

    def sensorATempGet(self):
        '''
            Get temperature from sensor A
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSA_TEMP_CHAN)

    def sensorBTempGet(self):
        '''
            Get temperature from sensor B
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSB_TEMP_CHAN)
    
    def sensorCTempGet(self):
        '''
            Get temperature from Sensor C
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSC_TEMP_CHAN)
    
    def sensorDTempGet(self):
        '''
            Get temperature from Sensor D
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSD_TEMP_CHAN)
    
    
    def sensorETempGet(self):
        '''
            Get temperature from Sensor E
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSE_TEMP_CHAN)

    
    def sensorFTempGet(self):
        '''
            Get temperature from Sensor F
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSF_TEMP_CHAN)

    
    def sensorGTempGet(self):
        '''
            Get temperature from Sensor G
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSG_TEMP_CHAN)

    
    def sensorHTempGet(self):
        '''
            Get temperature from Sensor H
        '''
        
        return self.sensorTempRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSH_TEMP_CHAN)

    def powerCardTempGet(self):
        '''
            Get temperature from power card
        '''
        return self.sensorTempRead(0x22, LpdProtoTest.PSU_TEMP_CHAN)
    

    def asicPowerEnableGet(self):
        '''
            Get the status of 'ASIC LV Power Enable'
        
            Returns True if OFF; False if ON
        '''
        
        return self.pcf7485ReadOneBit(LpdProtoTest.LV_CTRL_BIT)
    
    def asicPowerEnableSet(self, aValue):
        '''
            Set 'ASIC LV Power Enable' (0/1 = on/off)
        '''
        
        self.pcf7485WriteOneBit(LpdProtoTest.LV_CTRL_BIT, aValue)

    def powerCardFemStatusGet(self):
        '''
            Get power card Fem status
        '''
        value = thisPrototype.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.FEM_STATUS_BIT)) != 0]
    
    def powerCardExtStatusGet(self):
        '''
            Get power card External status
        '''
        value = thisPrototype.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.EXT_TRIP_BIT)) != 0]
    
    def powerCardFaultStatusGet(self):
        '''
            Get power card Fault status
        '''
        value = thisPrototype.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.FAULT_FLAG_BIT)) != 0]
    
    def powerCardOverCurrentStatusGet(self):
        '''
            Get power card Over Current status
        '''
        value = thisPrototype.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.OVERCURRENT_BIT)) != 0]
    
    def powerCardOvertempStatusGet(self):
        '''
            Get power card Over Temp status
        '''
        value = thisPrototype.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.HIGH_TEMP_BIT)) != 0]
    
    def powerCardUndertempStatusGet(self):
        '''
            Get power card Under Temp status
        '''
        value = thisPrototype.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.LOW_TEMP_BIT)) != 0]
    

    """ -=-=-=-=-=- Helper Functions -=-=-=-=-=- """
    
    def debugDisplay(self, var):
        '''
            Debug function to display decimal and hexadecimal value of 'var'.
        '''
        return var, "0x%X" % var,
        
    def sensorTempRead(self, device, channel):
        '''
            Generic function: Reads sensor temperature at 'channel' in  address 'device',
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 3.0
        tempVal = (adcVal * scale / 4095.0)
        
        return tempVal

    def ad7998Read(self, device, channel):
        '''
            Read two bytes from 'channel' in ad7998 at address 'device'
        '''

        # Construct i2c address and ADC channel to be read
        addr = LpdProtoTest.i2cInternalBusOffset + device
        adcChannel = 0x80 + ((channel & 7) << 4)

        # Write operation, select ADC channel
        ack = self.i2cWrite(addr, adcChannel)
        
        # Read operation, read ADC value
        response = self.i2cRead(addr, 2)
        
        # Extract the received two bytes and return one integer
        return (int((response[4] & 15) << 8) + int(response[5]))
        
    def pcf7485ReadOneBit(self, id):
        ''' 
            Read one byte from PCF7485 device and determine if set.
        
            Note: bit 1 = 0, 2 = 1,  3 = 2, 4 = 4, 
                      5 = 8, 6 = 16, 7 = 32 8 = 64
            Therefore, id must be one of the following: [0, 1, 2, 4, 8, 16, 32, 64]
        '''
        
        addr = LpdProtoTest.i2cInternalBusOffset + 0x38 
        
        response = self.i2cRead(addr, 1)
        value = response[4]
        return (value & (1 << id)) != 0
        
    def pcf7485ReadAllBits(self):
        ''' 
            Read and return one byte from PCF7485 device
            
            If a bit is set that represents: 
                bit 0-1:    Disabled (HV, LV)
                bit 2-7:    A fault  (Fem Status, Ext trip, fault, etc)
                e.g.    
                    131:    Hv (1) & Lv (2) disabled, low temperature (128) alert

                Beware      bit 0 = 1, bit 1 = 2, bit 2 = 4, etc !!
                therefore   131 = 128 + 2 + 1 (bits: 7, 1, 0)
        '''
        addr = LpdProtoTest.i2cInternalBusOffset + 0x38
        response = self.i2cRead(addr, 1)
#        print "pcf7485ReadAllBits() response = ", self.debugDisplay(response[4])
        return response[4]

    def pcf7485WriteOneBit(self, id, value):
        ''' 
            Change bit 'id' to 'value' in PCF7485 device
        '''        
        # Read PCF7485's current value
        bit_register = self.pcf7485ReadAllBits()
        # Change bit 'id' to 'value'
        bit_register = (bit_register & ~(1 << id)) | (value << id) | 0xFC

        addr = LpdProtoTest.i2cInternalBusOffset + 0x38
        response = self.i2cWrite(addr, bit_register)
        
        #TODO: Check ack (i.e.'response') to verify successful write
    
    def adcToTemp(self, adcValue):
        '''
            Convert ADC value into temperature - Redundant?
        '''
        #TODO:Change scale from voltage to degrees Celsius
        scale = 3
        try:
            tempVal = float(adcValue * scale / 4095.0)
        except Exception as e:
            tempVal = -1.0
            print "adcToTemp() Exception: ", e

        return tempVal


if __name__ == "__main__":

    # Define FEM IP address and port
    host = '192.168.2.2'
    port = 6969
    
    # Create object and connect to Fem
    thisPrototype = LpdProtoTest((host , port))

        
    print "Flags:" 
    print "    Fault Flag `      = ", thisPrototype.powerCardFaultStatusGet() 
    print "    Fem Status   Trip = ", thisPrototype.powerCardFemStatusGet() 
    print "    External     Trip = ", thisPrototype.powerCardExtStatusGet()
    print "    Over current Trip = ", thisPrototype.powerCardOverCurrentStatusGet()
    print "    Over temp    Trip = ", thisPrototype.powerCardOvertempStatusGet()
    print "    Undertemp    Trip = ", thisPrototype.powerCardUndertempStatusGet()
    print ".\n"
    
    sys.exit()
    print "Temperature readings: "

    powerCardTemp = thisPrototype.powerCardTempGet()
    print "   PSU Card Temp: %.2f" % powerCardTemp

    sensorATemp = thisPrototype.sensorATempGet()
    print "   Sensor A Temp: %.2f" % sensorATemp 
    
    sensorBTemp = thisPrototype.sensorBTempGet()
    print "   Sensor B Temp: %.2f" % sensorBTemp 

    sensorCTemp = thisPrototype.sensorCTempGet()
    print "   Sensor C Temp: %.2f " % sensorCTemp
    
    sensorDTemp = thisPrototype.sensorDTempGet()
    print "   Sensor D Temp: %.2f" % sensorDTemp 
    
    sensorETemp = thisPrototype.sensorETempGet()
    print "   Sensor E Temp: %.2f" % sensorETemp 
    
    sensorFTemp = thisPrototype.sensorFTempGet()
    print "   Sensor F Temp: %.2f" % sensorFTemp 
    
    sensorGTemp = thisPrototype.sensorGTempGet()
    print "   Sensor G Temp: %.2f" % sensorGTemp 
    
    sensorHTemp = thisPrototype.sensorHTempGet()
    print "   Sensor H Temp: %.2f" % sensorHTemp 
    
    print "\n"
    print "Low voltage: ", 
    if (thisPrototype.asicPowerEnableGet()):
        print "off."
    else:
        print "on."
        
    print "Switching on the low voltage.."
    thisPrototype.asicPowerEnableSet(LpdProtoTest.ON)
    
    print ""
    print "Low voltage: ", 
    if (thisPrototype.asicPowerEnableGet()):
        print "off."
    else:
        print "on."
        
    print "Switching off the low voltage..\n"
    thisPrototype.asicPowerEnableSet(LpdProtoTest.OFF)
    
    