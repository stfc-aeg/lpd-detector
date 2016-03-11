'''
    Author: ckd27546
    
    Support for legacy LPD power card - new version is supported by LpdPowerCard.py
    
    A helper class to handle I2C function calls initiated and completed by LpdFemClient
    That is: The API requests a set/get function call from LpdFemClient. 
            LpdFemClient constructs a function call targeted to LpdPowerCard
            which in turn requests the appropriate low-level I2C function from LpdFemClient.
'''

from __future__ import print_function

from LpdFemClient import *#LpdFemClient, FemClientError


from math import ceil, log

class LpdPowerCard(object):

    # ADC channel numbers
    HV_VOLTS_CHAN   =  0
    V5_VOLTS_CHAN   =  1
    V12_VOLTS_CHAN  =  2
    HV_AMPS_CHAN    =  3
    V5_AMPS_CHAN    =  4
    V12_AMPS_CHAN   =  5
    PSU_TEMP_CHAN   =  6
    V25A_VOLTS_CHAN =  8
    V25B_VOLTS_CHAN =  9
    V25C_VOLTS_CHAN = 10
    V25D_VOLTS_CHAN = 11
    V25E_VOLTS_CHAN = 12
    V25F_VOLTS_CHAN = 13
    V25G_VOLTS_CHAN = 14
    V25H_VOLTS_CHAN = 15
    V25A_AMPS_CHAN  = 16
    V25B_AMPS_CHAN  = 17
    V25C_AMPS_CHAN  = 18
    V25D_AMPS_CHAN  = 19
    V25E_AMPS_CHAN  = 20
    V25F_AMPS_CHAN  = 21
    V25G_AMPS_CHAN  = 22
    V25H_AMPS_CHAN  = 23
    SENSA_TEMP_CHAN = 24
    SENSB_TEMP_CHAN = 25
    SENSC_TEMP_CHAN = 26
    SENSD_TEMP_CHAN = 27
    SENSE_TEMP_CHAN = 28
    SENSF_TEMP_CHAN = 29
    SENSG_TEMP_CHAN = 30
    SENSH_TEMP_CHAN = 31
    
    # Bit numbers for control bits
    HV_CTRL_BIT     =  0
    LV_CTRL_BIT     =  1

    # Bit numbers for status bits
    FEM_STATUS_BIT  =  2
    EXT_TRIP_BIT    =  3
    FAULT_FLAG_BIT  =  4
    OVERCURRENT_BIT =  5
    HIGH_TEMP_BIT   =  6
    LOW_TEMP_BIT    =  7

    # Values for control bits
    OFF             =  1
    ON              =  0

    # Values for status bits
    TRIPPED         =  1
    FAULT           =  1
    NORMAL          =  0
    
    # Enumerate fault flag as either cleared (0) or tripped (1) 
    flag_message    = ["No", "Yes"]
    
    # i2c device addresses
    AD7998ADDRESS   = [0x22, 0x21, 0x24, 0x23]
    
    # Beta is utilised as an argument for calling the calculateTemperature() 
    #    but it's effectively fixed by the hardware design
    Beta            = 3474
    
    # Map powerCard addresses to scale
    powerCardMapping = {0:600, 1:6.0, 2:3.0, 3:600, 4:10.0, 5:700, 6:3.0}
    
    def __init__(self, fem, i2cBus):
        '''
        Constructor for LpdPowerCard
        
        @param fem Reference to the FEM object utilising this helper class
        @param powerCardIdent  Is this RHS=0 (always present) or LHS=1 (supermodule only) power card
        '''

        self.fem = fem
        
        self.femI2cBus = (i2cBus << 8)
    
    def sensorTempGet(self, sensorIdx):
        
        adcVal = self.ad7998Read(self.AD7998ADDRESS[3], self.SENSA_TEMP_CHAN + sensorIdx)
        
        scale = 3.0
        voltage = (adcVal * scale / 4095.0)
        # Calculate resistance from voltage
        resistance = self.calculateResistance(voltage)
        # Calculate temperature from resistance and return it
        return self.calculateTemperature(resistance)
        
    def sensorVoltageGet(self, sensorIdx):
 
        adcVal = self.ad7998Read(self.AD7998ADDRESS[1], self.V25A_VOLTS_CHAN + sensorIdx)
        scale = 3.0
        return (adcVal * scale / 4095.0)

    def sensorCurrentGet(self, sensorIdx):

        adcVal = self.ad7998Read(self.AD7998ADDRESS[2], self.V25A_AMPS_CHAN + sensorIdx)
        scale = 10.0
        currentValue = (adcVal * scale / 4095.0)
        return currentValue

    def sensorBiasGet(self):
        '''
            Get Sensor HV Bias Voltage [V]
            Reads high voltage bias level and converts
                from ADC counts into voltage
        '''
        addr = self.femI2cBus | 0x0C
        response = self.fem.i2cRead(addr, 2)
        high = (response[0] & 15) << 8
        low = response[1]
        value = high + low
        return float( value * 500 / 4095.0)

    def powerCardTempGet(self):
        '''
            Get temperature from power card
            Helper function: Reads sensor temperature at 'channel' in  address 'device',
                and converts adc counts into six volts scale.
        '''
        adcVal = self.ad7998Read(self.AD7998ADDRESS[0], self.PSU_TEMP_CHAN)
        scale = 3.0
        voltage = (adcVal * scale / 4095.0)
        # Calculate resistance from voltage
        resistance = self.calculateResistance(voltage)
        # Calculate temperature from resistance
        return self.calculateTemperature(resistance)
    
    def powerCardFemStatusGet(self):
        '''
            Get power card Fem status
        '''
        value = self.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.FEM_STATUS_BIT)) != 0]
    
    def powerCardExtStatusGet(self):
        '''
            Get power card External status
        '''
        value = self.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.EXT_TRIP_BIT)) != 0]
    
    def powerCardFaultGet(self):
        '''
            Get power card Fault status
        '''
        value = self.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.FAULT_FLAG_BIT)) != 0]
    
    def powerCardOverCurrentGet(self):
        '''
            Get power card Over Current status
        '''
        value = self.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.OVERCURRENT_BIT)) != 0]
    
    def powerCardOverTempGet(self):
        '''
            Get power card Over Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.HIGH_TEMP_BIT)) != 0]
    
    def powerCardUnderTempGet(self):
        '''
            Get power card Under Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.LOW_TEMP_BIT)) != 0]

    def sensorBiasSet(self, aValue):
        '''
            Set Sensor HV Bias Voltage [V]
        '''
        adcValue = int( ceil( aValue/0.122) )
        # Construct address and payload (as a tuple)
        addr = self.femI2cBus | 0x0C
        payload = ((adcValue & 0xF00) >> 8), (adcValue & 0xFF)
        # Write new ADC value to device
        self.fem.i2cWrite(addr, payload)

    def sensorBiasEnableGet(self):
        '''
            Get the status of 'Sensor HV Bias Enable'
        
            Returns True if OFF; False if ON
        '''
        value = 1 - self.pcf7485ReadOneBit(LpdPowerCard.HV_CTRL_BIT) 
        return value
    
    def sensorBiasEnableSet(self, aEnable):
        '''
            Set 'Sensor HV Bias Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.pcf7485WriteOneBit(LpdPowerCard.HV_CTRL_BIT, value)
        
    def asicPowerEnableGet(self):
        '''
            Get the status of 'ASIC LV Power Enable'
        
            Returns True if OFF; False if ON
        '''
        value = 1 - self.pcf7485ReadOneBit(LpdPowerCard.LV_CTRL_BIT)
        return value
    
    def asicPowerEnableSet(self, aEnable):
        '''
            Set 'ASIC LV Power Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.pcf7485WriteOneBit(LpdPowerCard.LV_CTRL_BIT, value)

    def femVoltageGet(self):
        '''
            Get Fem 5V Supply Voltage [V]
        '''
        adcVal = self.ad7998Read(self.AD7998ADDRESS[0], self.V5_VOLTS_CHAN)
        scale = 6.0
        return (adcVal * scale / 4095.0)

    def femCurrentGet(self):
        '''
            Get Fem 5V Supply Current [A]
        '''
        adcVal = self.ad7998Read(self.AD7998ADDRESS[0], self.V5_AMPS_CHAN)
        scale = 10.0
        return (adcVal * scale / 4095.0)

    def digitalVoltageGet(self):
        '''
            Get ASIC 1.2 Digital Supply Voltage [V]
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 3 V scale
        '''
        adcVal = self.ad7998Read(self.AD7998ADDRESS[0], self.V12_VOLTS_CHAN)
        scale = 3.0
        return (adcVal * scale / 4095.0)

    def digitalCurrentGet(self):
        '''
            Get ASIC 1.2V Digital Supply Current [mA]
            Helper function: Reads sensor  voltage at 'channel' in address 'address',
                and converts adc counts into 700 milliamp scale
        '''
        adcVal = self.ad7998Read(self.AD7998ADDRESS[0], self.V12_AMPS_CHAN)
        scale = 700.0
        return (adcVal * scale / 4095.0)

    def sensorBiasVoltageGet(self):
        '''
            Get Sensor bias voltage readback [V]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(self.AD7998ADDRESS[0], self.HV_VOLTS_CHAN)
    
    def sensorBiasCurrentGet(self): 
        '''
            Get Sensor bias current readback [uA]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(self.AD7998ADDRESS[0], self.HV_AMPS_CHAN)
    
    ########################################################
    """     -=-=-=-=-=- Helper Functions -=-=-=-=-=-     """
    ########################################################

    def sensorSixHundredMilliAmpsScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 600 milliamp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        scale = 600.0
        return (adcVal * scale / 4095.0)

    def ad7998Read(self, device, channel):
        '''
            Read two bytes from 'channel' in ad7998 at address 'device'
        '''
        # Construct i2c address and ADC channel to be read
        addr = self.femI2cBus | device
        adcChannel = 0x80 + ((channel & 7) << 4)
        # Write operation, select ADC channel
        self.fem.i2cWrite(addr, adcChannel)
        # Read operation, read ADC value
        response = self.fem.i2cRead(addr, 2)
        # Extract the received two bytes and return as one integer
        return (int((response[0] & 15) << 8) + int(response[1]))

    def pcf7485ReadOneBit(self, bitId):
        ''' 
            Read one byte from PCF7485 device and determine if set.
            Note: bit 1 = 0, 2 = 1,  3 = 2, 4 = 4, 
                      5 = 8, 6 = 16, 7 = 32 8 = 64
            Therefore, bitId must be one of the following: [0, 1, 2, 4, 8, 16, 32, 64]
        '''
        addr = self.femI2cBus | 0x38 
        response = self.fem.i2cRead(addr, 1)
        value = response[0]
        return (value & (1 << bitId)) != 0
        
    def pcf7485ReadAllBits(self):
        ''' 
            Read and return one byte from PCF7485 device
            
            If a bit is set, that represents: 
                bit 0-1:    Disabled (HV, LV)
                bit 2-7:    A fault  (Fem Status, Ext trip, fault, etc)
                e.g.    
                    131:    Hv (1) & Lv (2) disabled, low temperature (128) alert

                Beware      bit 0 = 1, bit 1 = 2, bit 2 = 4, etc !!
                therefore   131 = 128 + 2 + 1 (bits: 7, 1, 0)
        '''
        addr = self.femI2cBus | 0x38
        response = self.fem.i2cRead(addr, 1)
        return response[0]

    def pcf7485WriteOneBit(self, bitId, value):
        ''' 
            Change bit 'bitId' to 'value' in PCF7485 device
        '''            
        addr = self.femI2cBus | 0x38
        # Read PCF7485's current value
        bit_register = self.pcf7485ReadAllBits()
        # Change bit 'bitId' to 'value'
        bit_register = (bit_register & ~(1 << bitId)) | (value << bitId) | 0xFC
        self.fem.i2cWrite(addr, bit_register)
        
    def calculateTemperature(self, resistanceOne):
        ''' 
            Calculate temperature in thermistor using Beta and resistance
                e.g. calculateTemperature(3630, 26000) = 3.304 degrees Celsius 
        '''

        # Define constants since resistance and temperature is already known for one point
        resistanceZero = 10000
        tempZero = 25.0
        invertedTemperature = (1.0 / (273.1500 + tempZero)) + ( (1.0 / LpdPowerCard.Beta) * log(float(resistanceOne) / float(resistanceZero)) )
        # Invert the value to obtain temperature (in Kelvin) and subtract 273.15 to obtain Celsius
        return (1 / invertedTemperature) - 273.15

    def calculateResistance(self, aVoltage):
        '''
            Calculates the resistance for a given voltage (Utilised by the temperature sensors, on board as well as each ASIC module)
        '''
        # Define the supply voltage and the size of resistor inside potential divider
        vCC = 5
        resistance = 15000
        # Calculate resistance of the thermistor
        return ((resistance * aVoltage) / (vCC-aVoltage))

if __name__ == "__main__":
    
    theFem = LpdFemClient(('192.168.2.2', 6969), 5, 2)
    
    theFem.sensorBias0Set(25)
    print(theFem.sensorBiasGet())
    
