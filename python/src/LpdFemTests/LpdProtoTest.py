'''
LpdProtoTest - XFEL LPD class sitting between the API and the FemC FemClient

             - Will be renamed LpdFemClient at some point in the future
            
Created 09 October 2012

@Author: ckd
'''

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction

class LpdProtoTest(FemClient):
    '''
    
    '''

    # ADC channel numbers
    PSU_TEMP_CHAN =      6
    SENSB_TEMP_CHAN =   25
    SENSC_TEMP_CHAN =   26
    
    # Bit numbers for control bits
    HV_CTRL_BIT    = 0
    LV_CTRL_BIT    = 1

    # Values for control bits
    OFF = 1
    ON  = 0
    
    # Fem has three internal i2c buses, power card uses bus 0x300
    i2cInternalBusOffset = 0x300

    # ad7998 device addresses = [0x22, 0x21, 0x24, 0x23]
    
    
    def __init__(self, hostAddr=None, timeout=None):
        '''
            Constructor for LpdProtoTest class
        '''
        
        # Call superclass initialising function
        super(LpdProtoTest, self).__init__(hostAddr, timeout)
        

    def sensorBTempGet(self):
        '''
            Get temperature from sensor B
        '''
        
        return self.sensorTempRead(0x23, LpdProtoTest.SENSB_TEMP_CHAN)
    
    def sensorCTempGet(self):
        '''
            Get temperature from Sensor C
        '''
        
        return self.sensorTempRead(0x23, LpdProtoTest.SENSC_TEMP_CHAN)
    
        
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
        '''
        addr = LpdProtoTest.i2cInternalBusOffset + 0x38
        response = self.i2cRead(addr, 1)

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
    
    sensorBTemp = thisPrototype.sensorBTempGet()
    print "Sensor B Temp: %.2f" % sensorBTemp 

    sensorCTemp = thisPrototype.sensorCTempGet()
    print "Sensor C Temp: %.2f " % sensorCTemp
    
    powerCardTemp = thisPrototype.powerCardTempGet()
    print "PSU Card Temp: %.2f" % powerCardTemp
    
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
    