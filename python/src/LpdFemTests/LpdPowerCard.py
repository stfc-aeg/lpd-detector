'''
    Author: CKD27546
    
    A helper class to handle I2C function calls initiated and completed by LpdFemClient
    That is: The API requests a set/get function call from LpdFemClient. 
            LpdFemClient constructs a function call targeted to LpdPowerCard
            which in turn requests the appropriate low-level I2C function from LpdFemClient.
'''

from LpdFemClient.LpdFemClient import *#LpdFemClient, FemClientError


from math import ceil

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
    
    def __init__(self, fem, idPowerCard):
        '''

        
        @param fem Reference to the FEM object utilising this helper class
        @param idPowerCard  Is this RHS=0 (always present) or LHS=1 (supermodule only) power card
        '''

        self.fem = fem
        # Construct femI2cBus from idPowerCard
        if idPowerCard == 0:
            # RHS
            self.femI2cBus = (1 << 9)
        else:
            # LHS
            self.femI2cBus = (3 << 8)
        #TODO: Add all the remaining variables:
        self.paramList = ['sensorBias','sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 'powerCardOverCurrent', 
                          'powerCardOverTemp', 'powerCardUnderTemp', 'powerCardTemp', 'sensorATemp', 'sensorBTemp', 'sensorCTemp', 'sensorDTemp', 'sensorETemp', 
                          'sensorFTemp', 'sensorGTemp', 'sensorHTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorAVoltage', 
                          'sensorACurrent', 'sensorBVoltage', 'sensorBCurrent', 'sensorCVoltage', 'sensorCCurrent', 'sensorDVoltage', 'sensorDCurrent', 
                          'sensorEVoltage', 'sensorECurrent', 'sensorFVoltage', 'sensorFCurrent', 'sensorGVoltage', 'sensorGCurrent', 'sensorHVoltage', 
                          'sensorHCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent']
    
    def sensorATempGet(self):
        '''
            Get temperature from sensor A
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSA_TEMP_CHAN)

    def sensorBTempGet(self):
        '''
            Get temperature from sensor B
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSB_TEMP_CHAN)
    
    def sensorCTempGet(self):
        '''
            Get temperature from Sensor C
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSC_TEMP_CHAN)
    
    def sensorDTempGet(self):
        '''
            Get temperature from Sensor D
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSD_TEMP_CHAN)
    
    def sensorETempGet(self):
        '''
            Get temperature from Sensor E
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSE_TEMP_CHAN)

    def sensorFTempGet(self):
        '''
            Get temperature from Sensor F
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSF_TEMP_CHAN)
    
    def sensorGTempGet(self):
        '''
            Get temperature from Sensor G
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSG_TEMP_CHAN)

    def sensorHTempGet(self):
        '''
            Get temperature from Sensor H
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[3], self.SENSH_TEMP_CHAN)

    def powerCardTempGet(self):
        '''
            Get temperature from power card
        '''
        return self.fem.sensorTemperatureRead(self.AD7998ADDRESS[0], self.PSU_TEMP_CHAN)
        
    def powerCardFemStatusGet(self):
        '''
            Get power card Fem status
        '''
        value = self.fem.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.FEM_STATUS_BIT)) != 0]
    
    def powerCardExtStatusGet(self):
        '''
            Get power card External status
        '''
        value = self.fem.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.EXT_TRIP_BIT)) != 0]
    
    def powerCardFaultGet(self):
        '''
            Get power card Fault status
        '''
        value = self.fem.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.FAULT_FLAG_BIT)) != 0]
    
    def powerCardOverCurrentGet(self):
        '''
            Get power card Over Current status
        '''
        value = self.fem.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.OVERCURRENT_BIT)) != 0]
    
    def powerCardOverTempGet(self):
        '''
            Get power card Over Temp status
        '''
        value = self.fem.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.HIGH_TEMP_BIT)) != 0]
    
    def powerCardUnderTempGet(self):
        '''
            Get power card Under Temp status
        '''
        value = self.fem.pcf7485ReadAllBits()
        return self.flag_message[ (value & (1 << self.LOW_TEMP_BIT)) != 0]

    def sensorBiasGet(self):
        '''
            Get Sensor HV Bias Voltage [V]
        '''
        return self.fem.sensorBiasLevelRead()
    
    def sensorBiasSet(self, aValue):
        '''
            Set Sensor HV Bias Voltage [V]
        '''
        self.fem.ad55321Write( int( ceil( aValue/0.122) ) )

    def sensorBiasEnableGet(self):
        '''
            Get the status of 'Sensor HV Bias Enable'
        
            Returns True if OFF; False if ON
        '''
        return self.fem.pcf7485ReadOneBit(LpdPowerCard.HV_CTRL_BIT)
    
    def sensorBiasEnableSet(self, aEnable):
        '''
            Set 'Sensor LV Bias Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.fem.pcf7485WriteOneBit(LpdPowerCard.HV_CTRL_BIT, value)
        
    def asicPowerEnableGet(self):
        '''
            Get the status of 'ASIC LV Power Enable'
        
            Returns True if OFF; False if ON
        '''
        return self.fem.pcf7485ReadOneBit(LpdPowerCard.LV_CTRL_BIT)
    
    def asicPowerEnableSet(self, aEnable):
        '''
            Set 'ASIC LV Power Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.fem.pcf7485WriteOneBit(LpdPowerCard.LV_CTRL_BIT, value)

    def femVoltageGet(self):
        '''
            Get Fem 5V Supply Voltage [V]
        '''
        return self.fem.sensorSixVoltScaleRead(self.AD7998ADDRESS[0], self.V5_VOLTS_CHAN)
        
    def femCurrentGet(self):
        '''
            Get Fem 5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead( self.AD7998ADDRESS[0], self.V5_AMPS_CHAN)

    def digitalVoltageGet(self):
        '''
            Get ASIC 1.2 Digital Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[0], self.V12_VOLTS_CHAN)

    def digitalCurrentGet(self):
        '''
            Get ASIC 1.2V Digital Supply Current [myA]
        '''
        return self.fem.sensorSevenHundredMilliAmpsScaleRead(self.AD7998ADDRESS[0], self.V12_AMPS_CHAN)

    def sensorAVoltageGet(self):
        '''
            Get Sensor A 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25A_VOLTS_CHAN)

    def sensorACurrentGet(self):
        '''
            Get Sensor A 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25A_AMPS_CHAN)

    def sensorBVoltageGet(self):
        '''
            Get Sensor B 2.5V Supply Voltage [V] 
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25B_VOLTS_CHAN)

    def sensorBCurrentGet(self):
        '''
            Get Sensor B 2.5V Supply Current [A]',
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25B_AMPS_CHAN)

    def sensorCVoltageGet(self):
        '''
            Get Sensor C 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25C_VOLTS_CHAN)

    def sensorCCurrentGet(self):
        '''
            Get Sensor C 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25C_AMPS_CHAN)

    def sensorDVoltageGet(self):
        '''
            Get Sensor D 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25D_VOLTS_CHAN)

    def sensorDCurrentGet(self):
        '''
            Get Sensor D 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25D_AMPS_CHAN)

    def sensorEVoltageGet(self):
        '''
            Get Sensor E 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25E_VOLTS_CHAN)

    def sensorECurrentGet(self):
        '''
            Get Sensor E 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25E_AMPS_CHAN)

    def sensorFVoltageGet(self):
        '''
            Get Sensor F 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25F_VOLTS_CHAN)

    def sensorFCurrentGet(self):
        '''
            Get Sensor F 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25F_AMPS_CHAN)

    def sensorGVoltageGet(self):
        '''
            Get Sensor G 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25G_VOLTS_CHAN)

    def sensorGCurrentGet(self):
        '''
            Get Sensor G 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25G_AMPS_CHAN)

    def sensorHVoltageGet(self):
        '''
            Get Sensor H 2.5V Supply Voltage [V]
        '''
        return self.fem.sensorThreeVoltScaleRead(self.AD7998ADDRESS[1], self.V25H_VOLTS_CHAN)

    def sensorHCurrentGet(self):
        '''
            Get Sensor H 2.5V Supply Current [A]
        '''
        return self.fem.sensorAmpereRead(self.AD7998ADDRESS[2], self.V25H_AMPS_CHAN)
    
    def sensorBiasVoltageGet(self):
        '''
            Get Sensor bias voltage readback [V]
        '''
        return self.fem.sensorSixHundredMilliAmpsScaleRead(self.AD7998ADDRESS[0], self.HV_VOLTS_CHAN)
    
    def sensorBiasCurrentGet(self): 
        '''
            Get Sensor bias current readback [uA]
        '''
        return self.fem.sensorSixHundredMilliAmpsScaleRead(self.AD7998ADDRESS[0], self.HV_AMPS_CHAN)
    

if __name__ == "__main__":
    
    theFem = LpdFemClient(('192.168.2.2', 6969), 5, 2)
    
    theFem.sensorBiasSet(25)
    print theFem.sensorBiasGet()