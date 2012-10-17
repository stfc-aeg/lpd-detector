'''
LpdProtoTest - XFEL LPD class sitting between the API and the FemC FemClient

             - Will be renamed LpdFemClient at some point in the future
            
Created 09 October 2012

@Author: ckd



  ADC channels:
    0 = HV volts    1 = 5V volts    2 = 1.2V volts
    3 = HV current  4 = 5V current  5 = 1.2V current
    6 = PSU temp    7 = not used
    8-15  = 2.5V volts (A-H)
    16-23 = 2.5V current (A-H)
    24-31 = Sensor temp (A-H)

  Bits:
    0 = [out] LV control (0=on)
    1 = [out] HV control (0=on)
    2 = unused
    3 = [in] External trip (1=tripped)
    4 = [in] Fault flag (1=tripped)
    5 = [in] Overcurrent (1=fault)
    6 = [in] High temperature (1=fault)
    7 = [in] Low temperature (1=fault)

'''

import sys

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction

class LpdProtoTest(FemClient):
    '''
    
    '''

    # ADC channel numbers
    HV_VOLTS_CHAN =      0
    V5_VOLTS_CHAN =      1
    V12_VOLTS_CHAN =     2
    HV_AMPS_CHAN =       3
    V5_AMPS_CHAN =       4
    V12_AMPS_CHAN =      5
    PSU_TEMP_CHAN =      6
    V25A_VOLTS_CHAN =    8
    V25B_VOLTS_CHAN =    9
    V25C_VOLTS_CHAN =   10
    V25D_VOLTS_CHAN =   11
    V25E_VOLTS_CHAN =   12
    V25F_VOLTS_CHAN =   13
    V25G_VOLTS_CHAN =   14
    V25H_VOLTS_CHAN =   15
    V25A_AMPS_CHAN =    16
    V25B_AMPS_CHAN =    17
    V25C_AMPS_CHAN =    18
    V25D_AMPS_CHAN =    19
    V25E_AMPS_CHAN =    20
    V25F_AMPS_CHAN =    21
    V25G_AMPS_CHAN =    22
    V25H_AMPS_CHAN =    23
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
    i2cPowerCardBus = 0x300

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
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSA_TEMP_CHAN)

    def sensorBTempGet(self):
        '''
            Get temperature from sensor B
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSB_TEMP_CHAN)
    
    def sensorCTempGet(self):
        '''
            Get temperature from Sensor C
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSC_TEMP_CHAN)
    
    def sensorDTempGet(self):
        '''
            Get temperature from Sensor D
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSD_TEMP_CHAN)
    
    
    def sensorETempGet(self):
        '''
            Get temperature from Sensor E
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSE_TEMP_CHAN)

    
    def sensorFTempGet(self):
        '''
            Get temperature from Sensor F
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSF_TEMP_CHAN)

    
    def sensorGTempGet(self):
        '''
            Get temperature from Sensor G
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSG_TEMP_CHAN)

    
    def sensorHTempGet(self):
        '''
            Get temperature from Sensor H
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[3], LpdProtoTest.SENSH_TEMP_CHAN)

    def powerCardTempGet(self):
        '''
            Get temperature from power card
        '''
        return self.sensorTempSixVoltScaleRead(0x22, LpdProtoTest.PSU_TEMP_CHAN)
    

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

    def sensorBiasEnableGet(self):
        '''
            Get the status of 'Sensor HV Bias Enable'
        
            Returns True if OFF; False if ON
        '''
        
        return self.pcf7485ReadOneBit(LpdProtoTest.HV_CTRL_BIT)
    
    def sensorBiasEnableSet(self, aValue):
        '''
            Set 'Sensor LV Bias Enable' (0/1 = on/off)
        '''
        
        self.pcf7485WriteOneBit(LpdProtoTest.HV_CTRL_BIT, aValue)
        
        
    def powerCardFemStatusGet(self):
        '''
            Get power card Fem status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.FEM_STATUS_BIT)) != 0]
    
    def powerCardExtStatusGet(self):
        '''
            Get power card External status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.EXT_TRIP_BIT)) != 0]
    
    def powerCardFaultStatusGet(self):
        '''
            Get power card Fault status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.FAULT_FLAG_BIT)) != 0]
    
    def powerCardOverCurrentStatusGet(self):
        '''
            Get power card Over Current status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.OVERCURRENT_BIT)) != 0]
    
    def powerCardOvertempStatusGet(self):
        '''
            Get power card Over Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.HIGH_TEMP_BIT)) != 0]
    
    def powerCardUndertempStatusGet(self):
        '''
            Get power card Under Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdProtoTest.flag_message[ (value & (1 << LpdProtoTest.LOW_TEMP_BIT)) != 0]
    
    def sensorBiasGet(self):
        '''
            Get Sensor HV Bias Voltage [V]
        '''
        return self.ad5321Read()
    
    def sensorBiasSet(self, aValue):
        '''
            Set Sensor HV Bias Voltage [V]
        '''
        
        self.ad55321Write(aValue)
    
    def femVoltageGet(self):
        '''
            Get Fem 5V Supply Voltage [V]
        '''
        return self.sensorSixVoltScaleRead(LpdProtoTest.AD7998ADDRESS[0], LpdProtoTest.V5_VOLTS_CHAN)
        
    def femCurrentGet(self):
        '''
            Get Fem 5V Supply Current [A]
        '''
        return self.sensorAmpereRead( LpdProtoTest.AD7998ADDRESS[0], LpdProtoTest.V5_AMPS_CHAN)

    def digitalVoltageGet(self):
        '''
            Get ASIC 1.2 Digital Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[0], LpdProtoTest.V12_VOLTS_CHAN)

    def digitalCurrentGet(self):
        '''
            Get ASIC 1.2V Digital Supply Current [myA]
        '''
        return self.sensorSevenHundredMilliAmpsScaleRead(LpdProtoTest.AD7998ADDRESS[0], LpdProtoTest.V12_AMPS_CHAN)

    def sensorAVoltageGet(self):
        '''
            Get Sensor A 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25A_VOLTS_CHAN)

    def sensorACurrentGet(self):
        '''
            Get Sensor A 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25A_AMPS_CHAN)

    def sensorBVoltageGet(self):
        '''
            Get Sensor B 2.5V Supply Voltage [V] 
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25B_VOLTS_CHAN)

    def sensorBCurrentGet(self):
        '''
            Get Sensor B 2.5V Supply Current [A]',
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25B_AMPS_CHAN)

    def sensorCVoltageGet(self):
        '''
            Get Sensor C 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25C_VOLTS_CHAN)

    def sensorCCurrentGet(self):
        '''
            Get Sensor C 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25C_AMPS_CHAN)

    def sensorDVoltageGet(self):
        '''
            Get Sensor D 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25D_VOLTS_CHAN)

    def sensorDCurrentGet(self):
        '''
            Get Sensor D 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25D_AMPS_CHAN)

    def sensorEVoltageGet(self):
        '''
            Get Sensor E 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25E_VOLTS_CHAN)

    def sensorECurrentGet(self):
        '''
            Get Sensor E 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25E_AMPS_CHAN)

    def sensorFVoltageGet(self):
        '''
            Get Sensor F 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25F_VOLTS_CHAN)

    def sensorFCurrentGet(self):
        '''
            Get Sensor F 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25F_AMPS_CHAN)

    def sensorGVoltageGet(self):
        '''
            Get Sensor G 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25G_VOLTS_CHAN)

    def sensorGCurrentGet(self):
        '''
            Get Sensor G 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25G_AMPS_CHAN)

    def sensorHVoltageGet(self):
        '''
            Get Sensor H 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdProtoTest.AD7998ADDRESS[1], LpdProtoTest.V25H_VOLTS_CHAN)

    def sensorHCurrentGet(self):
        '''
            Get Sensor H 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdProtoTest.AD7998ADDRESS[2], LpdProtoTest.V25H_AMPS_CHAN)
    
    
    def sensorBiasVoltageGet(self):
        '''
            Get Sensor bias voltage readback [V]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(LpdProtoTest.AD7998ADDRESS[0], LpdProtoTest.HV_VOLTS_CHAN)
    
    def sensorBiasCurrentGet(self): 
        '''
            Get Sensor bias current readback [uA]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(LpdProtoTest.AD7998ADDRESS[0], LpdProtoTest.HV_AMPS_CHAN)
    
    
    """ -=-=-=-=-=- Helper Functions -=-=-=-=-=- """

    def sensorAmpereRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in  address 'device',
                and converts adc counts into 10 amp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 10.0
        tempVal = (adcVal * scale / 4095.0)
        
        return tempVal

    def sensorSixVoltScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 6 V scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 6.0
        return (adcVal * scale / 4095.0)

    def sensorThreeVoltScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 3 V scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 3.0
        return (adcVal * scale / 4095.0)

    def sensorSevenHundredMilliAmpsScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor  voltage at 'channel' in address 'address',
                and converts adc counts into 700 milliamp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 700.0
        return (adcVal * scale / 4095.0)

    def sensorSixHundredMilliAmpsScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor voltage at 'channel' in address 'address',
                and converts adc counts into 600 milliamp scale
        '''
        adcVal = self.ad7998Read(device, channel)
        
        scale = 600.0
        return (adcVal * scale / 4095.0)

    def debugDisplay(self, var):
        '''
            Debug function to display decimal and hexadecimal value of 'var'.
        '''
        return var, "0x%X" % var,
        
    def sensorTempSixVoltScaleRead(self, device, channel):
        '''
            Helper function: Reads sensor temperature at 'channel' in  address 'device',
                and converts adc counts into six volts scale.
            Note: This function will become different from
                    sensorThreeVoltScaleRead(device, channel)
            because this function will later convert into degrees centigrade
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
        addr = LpdProtoTest.i2cPowerCardBus + device
        adcChannel = 0x80 + ((channel & 7) << 4)

        # Write operation, select ADC channel
        ack = self.i2cWrite(addr, adcChannel)
        
        # Read operation, read ADC value
        response = self.i2cRead(addr, 2)
        
        # Extract the received two bytes and return one integer
        value = (int((response[1] & 15) << 8) + int(response[2]))
#        print "[%4i" % value, "]",
        return value

    def ad5321Read(self):
        ''' 
            Read 2 bytes from ad5321 device 
        '''
        
        addr = LpdProtoTest.i2cPowerCardBus + 0x0C
        response = -1
        
        response = self.i2cRead(addr, 2)
        high = (response[1] & 15) << 8
        low = response[2]
        return high + low

    def ad55321Write(self, aValue):
        '''
            Write 'aAValue' (2 bytes) to ad5321 device
        '''
    
        response = -1
        # Construct address and payload (as a tuple)
        addr = LpdProtoTest.i2cPowerCardBus + 0x0C
        payload = ((aValue & 0xF00) >> 8), (aValue & 0xFF)

        # Write new ADC value to device
        ack = self.i2cWrite(addr, payload)
        
        # Verify write operation
        response = self.ad5321Read()
        return response
    
    def pcf7485ReadOneBit(self, id):
        ''' 
            Read one byte from PCF7485 device and determine if set.
        
            Note: bit 1 = 0, 2 = 1,  3 = 2, 4 = 4, 
                      5 = 8, 6 = 16, 7 = 32 8 = 64
            Therefore, id must be one of the following: [0, 1, 2, 4, 8, 16, 32, 64]
        '''
        
        addr = LpdProtoTest.i2cPowerCardBus + 0x38 
        
        response = self.i2cRead(addr, 1)
        
#        print "response = ", response, " type(response) = ", type(response)
        value = response[1]
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
        addr = LpdProtoTest.i2cPowerCardBus + 0x38
        response = self.i2cRead(addr, 1)
#        print "pcf7485ReadAllBits() response = ", self.debugDisplay(response[1])
        return response[1]

    def pcf7485WriteOneBit(self, id, value):
        ''' 
            Change bit 'id' to 'value' in PCF7485 device
        '''        
        # Read PCF7485's current value
        bit_register = self.pcf7485ReadAllBits()
        # Change bit 'id' to 'value'
        bit_register = (bit_register & ~(1 << id)) | (value << id) | 0xFC

        addr = LpdProtoTest.i2cPowerCardBus + 0x38
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

    def displayI2cOutputs(self):
        '''
             Displays all the i2c quantities
        '''
        
        print "Status:"
        print "    Low voltage: ", 
        if (self.asicPowerEnableGet()):
            print "off."
        else:
            print "on."
        
        print "    High voltage: ", 
        if (self.sensorBiasEnableGet()):
            print "off."
        else:
            print "on."
        print "    HV setting: ", self.sensorBiasGet()
    
        print "Flags:" 
        print "    Fault Flag        = ", self.powerCardFaultStatusGet() 
        print "    Fem Status   Trip = ", self.powerCardFemStatusGet() 
        print "    External     Trip = ", self.powerCardExtStatusGet()
        print "    Over current Trip = ", self.powerCardOverCurrentStatusGet()
        print "    Over temp    Trip = ", self.powerCardOvertempStatusGet()
        print "    Undertemp    Trip = ", self.powerCardUndertempStatusGet()
        print ".\n"
    
        
        print "Temperature readings: "
    
        powerCardTemp = self.powerCardTempGet()
        print "   PSU Card Temp: %.2f" % powerCardTemp, " V"
    
        sensorATemp = self.sensorATempGet()
        print "   Sensor A Temp: %.2f" % sensorATemp, " V"
        
        sensorBTemp = self.sensorBTempGet()
        print "   Sensor B Temp: %.2f" % sensorBTemp, " V"
    
        sensorCTemp = self.sensorCTempGet()
        print "   Sensor C Temp: %.2f" % sensorCTemp, " V"
        
        sensorDTemp = self.sensorDTempGet()
        print "   Sensor D Temp: %.2f" % sensorDTemp, " V"
        
        sensorETemp = self.sensorETempGet()
        print "   Sensor E Temp: %.2f" % sensorETemp, " V"
        
        sensorFTemp = self.sensorFTempGet()
        print "   Sensor F Temp: %.2f" % sensorFTemp, " V"
        
        sensorGTemp = self.sensorGTempGet()
        print "   Sensor G Temp: %.2f" % sensorGTemp, " V"
        
        sensorHTemp = self.sensorHTempGet()
        print "   Sensor H Temp: %.2f" % sensorHTemp, " V"
        print "\n"
        
        print "Outputs: "
        
        femVoltage = self.femVoltageGet()
        femCurrent = self.femCurrentGet()
        print "   V FEM      : %.2f" % femVoltage, " V %.2f" % femCurrent, " A"
        
        digitalVoltage = self.digitalVoltageGet()
        digitalCurrent = self.digitalCurrentGet()
        print "   V Digital  : %.2f" % digitalVoltage, " V %.2f" % digitalCurrent, " mA\n"
        
        sensorAVoltage = self.sensorAVoltageGet()
        sensorACurrent = self.sensorACurrentGet()
        print "   V Sensor A : %.2f" % sensorAVoltage, " V %.2f" % sensorACurrent, " A"
    
        sensorBVoltage = self.sensorBVoltageGet()
        sensorBCurrent = self.sensorBCurrentGet()
        print "   V Sensor B : %.2f" % sensorBVoltage, " V %.2f" % sensorBCurrent, " A"
    
        sensorCVoltage = self.sensorCVoltageGet()
        sensorCCurrent = self.sensorCCurrentGet()
        print "   V Sensor C : %.2f" % sensorCVoltage, " V %.2f" % sensorCCurrent, " A"
    
        sensorDVoltage = self.sensorDVoltageGet()
        sensorDCurrent = self.sensorDCurrentGet()
        print "   V Sensor D : %.2f" % sensorDVoltage, " V %.2f" % sensorDCurrent, " A"
    
        sensorEVoltage = self.sensorEVoltageGet()
        sensorECurrent = self.sensorECurrentGet()
        print "   V Sensor E : %.2f" % sensorEVoltage, " V %.2f" % sensorECurrent, " A"
    
        sensorFVoltage = self.sensorFVoltageGet()
        sensorFCurrent = self.sensorFCurrentGet()
        print "   V Sensor F : %.2f" % sensorFVoltage, " V %.2f" % sensorFCurrent, " A"
    
        sensorGVoltage = self.sensorGVoltageGet()
        sensorGCurrent = self.sensorGCurrentGet()
        print "   V Sensor G : %.2f" % sensorGVoltage, " V %.2f" % sensorGCurrent, " A"
    
        sensorHVoltage = self.sensorHVoltageGet()
        sensorHCurrent = self.sensorHCurrentGet()
        print "   V Sensor H : %.2f" % sensorHVoltage, " V %.2f" % sensorHCurrent, " A"
        print ""
    
        sensorBiasVoltage = self.sensorBiasVoltageGet()
        sensorBiasCurrent = self.sensorBiasCurrentGet()
        print "   HV Bias    : %.2f" % sensorBiasVoltage, " V %.2f" % sensorBiasCurrent, " uA"


if __name__ == "__main__":

    # Define FEM IP address and port
    host = '192.168.2.2'
    port = 6969
    
    # Create object and connect to Fem
    thisPrototype = LpdProtoTest((host , port))

    # Change the HV setting
    thisPrototype.sensorBiasSet(0)

#    # Switching on the low voltage
    thisPrototype.asicPowerEnableSet(LpdProtoTest.ON)
#    # Switch on the high voltage
#    thisPrototype.sensorBiasEnableSet(LpdProtoTest.ON)

    # Switch off the high voltage
#    thisPrototype.sensorBiasEnableSet(LpdProtoTest.OFF)
    # Switch off the low voltage.
#    thisPrototype.asicPowerEnableSet(LpdProtoTest.OFF)

    print "-=-=-=-=-=-=-=-=-=-=-=-=-"
    # Display all the i2c quantities
    thisPrototype.displayI2cOutputs()


    print "\nClosing Fem connection..\n"
    thisPrototype.close()
