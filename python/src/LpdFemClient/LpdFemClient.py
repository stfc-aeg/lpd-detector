'''
LpdFemClient - XFEL LPD class sitting between the API and the FemClient


         
Created 16 October 2012

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

class LpdFemClient(FemClient):
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
            Constructor for LpdFemClient class
        '''
        
        # Call superclass initialising function
        super(LpdFemClient, self).__init__(hostAddr, timeout)
        
        #TODO: Remove these dummy variables when they become redundant
        self.tenGig0SourceMacDummy = 0
        self.tenGig0SourceIpDummy = 0
        self.tenGig0SourcePortDummy = 0
        self.tenGig0DestMacDummy = 0          
        self.tenGig0DestIpDummy = 0   
        self.tenGig0DestPortDummy = 0     
        self.tenGig1SourceMacDummy = 0
        self.tenGig1SourceIpDummy = 0 
        self.tenGig1SourcePortDummy = 0
        self.tenGig1DestMacDummy = 0  
        self.tenGig1DestIpDummy = 0  
        self.tenGig1DestPortDummy = 0 
        self.tenGigInterframeGapDummy = 0        
        self.tenGigUdpPacketLenDummy = 0              
        self.femSendPpcResetDummy              = 0
        self.femFastCtrlDynamicDummy           = 0
        self.femSetupSlowCtrlBramDummy         = 0
        self.femEnableTenGigDummy              = 0
        self.femDataSourceDummy                = 0
        self.femAsicCountingDataDummy          = 0
        self.femAsicModuleTypeDummy            = 0
        self.femAsicRxStartDelayDummy          = 0
        self.femNumLocalLinkFramesDummy        = 0
        self.femAsicFastCmdRegSizeDummy        = 0
        self.femAsicEnableMaskDummy            = 0
        self.femAsicColumnsDummy               = 0
        self.femAsicColumnsPerFrameDummy       = 0
        self.femAsicGainOverrideDummy          = 0
        self.femAsicSlowControlParamsDummy     = 0
        self.femAsicFastCmdSequenceDummy       = 0
        self.femAsicPixelFeedbackOverrideDummy = 0
        self.femAsicPixelSelfTestOverrideDummy = 0
        self.femReadoutOperatingModeDummy      = 0
             
    def sensorATempGet(self):
        '''
            Get temperature from sensor A
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSA_TEMP_CHAN)

    def sensorBTempGet(self):
        '''
            Get temperature from sensor B
        '''
        
#        raise FemClientError('You idiot', 666)
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSB_TEMP_CHAN)
    
    def sensorCTempGet(self):
        '''
            Get temperature from Sensor C
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSC_TEMP_CHAN)
    
    def sensorDTempGet(self):
        '''
            Get temperature from Sensor D
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSD_TEMP_CHAN)
    
    
    def sensorETempGet(self):
        '''
            Get temperature from Sensor E
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSE_TEMP_CHAN)

    
    def sensorFTempGet(self):
        '''
            Get temperature from Sensor F
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSF_TEMP_CHAN)

    
    def sensorGTempGet(self):
        '''
            Get temperature from Sensor G
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSG_TEMP_CHAN)

    
    def sensorHTempGet(self):
        '''
            Get temperature from Sensor H
        '''
        
        return self.sensorTempSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[3], LpdFemClient.SENSH_TEMP_CHAN)

    def powerCardTempGet(self):
        '''
            Get temperature from power card
        '''
        return self.sensorTempSixVoltScaleRead(0x22, LpdFemClient.PSU_TEMP_CHAN)
    

    def asicPowerEnableGet(self):
        '''
            Get the status of 'ASIC LV Power Enable'
        
            Returns True if OFF; False if ON
        '''
        
        return self.pcf7485ReadOneBit(LpdFemClient.LV_CTRL_BIT)
    
    def asicPowerEnableSet(self, aEnable):
        '''
            Set 'ASIC LV Power Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.pcf7485WriteOneBit(LpdFemClient.LV_CTRL_BIT, value )

    def sensorBiasEnableGet(self):
        '''
            Get the status of 'Sensor HV Bias Enable'
        
            Returns True if OFF; False if ON
        '''
        
        return self.pcf7485ReadOneBit(LpdFemClient.HV_CTRL_BIT)
    
    def sensorBiasEnableSet(self, aEnable):
        '''
            Set 'Sensor LV Bias Enable' (0/1 = on/off)
        '''
        value = 1 - int(aEnable)
        self.pcf7485WriteOneBit(LpdFemClient.HV_CTRL_BIT, value )
        
        
    def powerCardFemStatusGet(self):
        '''
            Get power card Fem status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.FEM_STATUS_BIT)) != 0]
    
    def powerCardExtStatusGet(self):
        '''
            Get power card External status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.EXT_TRIP_BIT)) != 0]
    
    def powerCardFaultGet(self):
        '''
            Get power card Fault status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.FAULT_FLAG_BIT)) != 0]
    
    def powerCardOverCurrentGet(self):
        '''
            Get power card Over Current status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.OVERCURRENT_BIT)) != 0]
    
    def powerCardOverTempGet(self):
        '''
            Get power card Over Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.HIGH_TEMP_BIT)) != 0]
    
    def powerCardUnderTempGet(self):
        '''
            Get power card Under Temp status
        '''
        value = self.pcf7485ReadAllBits()
        return LpdFemClient.flag_message[ (value & (1 << LpdFemClient.LOW_TEMP_BIT)) != 0]
    
    def sensorBiasGet(self):
        '''
            Get Sensor HV Bias Voltage [V]
        '''
        return self.ad5321Read()
    
    def sensorBiasSet(self, aValue):
        '''
            Set Sensor HV Bias Voltage [V]
        '''
        #TODO: Need to to proper scaling aValue -> ADC count
        self.ad55321Write( int(aValue) )
    
    def femVoltageGet(self):
        '''
            Get Fem 5V Supply Voltage [V]
        '''
        return self.sensorSixVoltScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V5_VOLTS_CHAN)
        
    def femCurrentGet(self):
        '''
            Get Fem 5V Supply Current [A]
        '''
        return self.sensorAmpereRead( LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V5_AMPS_CHAN)

    def digitalVoltageGet(self):
        '''
            Get ASIC 1.2 Digital Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V12_VOLTS_CHAN)

    def digitalCurrentGet(self):
        '''
            Get ASIC 1.2V Digital Supply Current [myA]
        '''
        return self.sensorSevenHundredMilliAmpsScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.V12_AMPS_CHAN)

    def sensorAVoltageGet(self):
        '''
            Get Sensor A 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25A_VOLTS_CHAN)

    def sensorACurrentGet(self):
        '''
            Get Sensor A 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25A_AMPS_CHAN)

    def sensorBVoltageGet(self):
        '''
            Get Sensor B 2.5V Supply Voltage [V] 
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25B_VOLTS_CHAN)

    def sensorBCurrentGet(self):
        '''
            Get Sensor B 2.5V Supply Current [A]',
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25B_AMPS_CHAN)

    def sensorCVoltageGet(self):
        '''
            Get Sensor C 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25C_VOLTS_CHAN)

    def sensorCCurrentGet(self):
        '''
            Get Sensor C 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25C_AMPS_CHAN)

    def sensorDVoltageGet(self):
        '''
            Get Sensor D 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25D_VOLTS_CHAN)

    def sensorDCurrentGet(self):
        '''
            Get Sensor D 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25D_AMPS_CHAN)

    def sensorEVoltageGet(self):
        '''
            Get Sensor E 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25E_VOLTS_CHAN)

    def sensorECurrentGet(self):
        '''
            Get Sensor E 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25E_AMPS_CHAN)

    def sensorFVoltageGet(self):
        '''
            Get Sensor F 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25F_VOLTS_CHAN)

    def sensorFCurrentGet(self):
        '''
            Get Sensor F 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25F_AMPS_CHAN)

    def sensorGVoltageGet(self):
        '''
            Get Sensor G 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25G_VOLTS_CHAN)

    def sensorGCurrentGet(self):
        '''
            Get Sensor G 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25G_AMPS_CHAN)

    def sensorHVoltageGet(self):
        '''
            Get Sensor H 2.5V Supply Voltage [V]
        '''
        return self.sensorThreeVoltScaleRead(LpdFemClient.AD7998ADDRESS[1], LpdFemClient.V25H_VOLTS_CHAN)

    def sensorHCurrentGet(self):
        '''
            Get Sensor H 2.5V Supply Current [A]
        '''
        return self.sensorAmpereRead(LpdFemClient.AD7998ADDRESS[2], LpdFemClient.V25H_AMPS_CHAN)
    
    
    def sensorBiasVoltageGet(self):
        '''
            Get Sensor bias voltage readback [V]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.HV_VOLTS_CHAN)
    
    def sensorBiasCurrentGet(self): 
        '''
            Get Sensor bias current readback [uA]
        '''
        return self.sensorSixHundredMilliAmpsScaleRead(LpdFemClient.AD7998ADDRESS[0], LpdFemClient.HV_AMPS_CHAN)
    
    def tenGig0SourceMacGet(self):
        '''
            Get tenGig0SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0SourceMacDummy

    def tenGig0SourceMacSet(self, aValue):
        '''
            Set tenGig0SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0SourceMacDummy = aValue

    
    def tenGig0SourceIpGet(self):
        '''
            Get tenGig0SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0SourceIpDummy

    def tenGig0SourceIpSet(self, aValue):
        '''
            Set tenGig0SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0SourceIpDummy = aValue

    def tenGig0SourcePortGet(self):
        '''
            Get tenGig0SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0SourcePortDummy

    def tenGig0SourcePortSet(self, aValue):
        '''
            Set tenGig0SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0SourcePortDummy = aValue

    def tenGig0DestMacGet(self):
        '''
            Get tenGig0DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0DestMacDummy

    def tenGig0DestMacSet(self, aValue):
        '''
            Set tenGig0DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0DestMacDummy = aValue

    def tenGig0DestIpGet(self):
        '''
            Get tenGig0DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0DestIpDummy

    def tenGig0DestIpSet(self, aValue):
        '''
            Set tenGig0DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0DestIpDummy = aValue

    def tenGig0DestPortGet(self):
        '''
            Get tenGig0DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig0DestPortDummy

    def tenGig0DestPortSet(self, aValue):
        '''
            Set tenGig0DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig0DestPortDummy = aValue

    def tenGig1SourceMacGet(self):
        '''
            Get tenGig1SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1SourceMacDummy

    def tenGig1SourceMacSet(self, aValue):
        '''
            Set tenGig1SourceMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1SourceMacDummy = aValue

    def tenGig1SourceIpGet(self):
        '''
            Get tenGig1SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1SourceIpDummy

    def tenGig1SourceIpSet(self, aValue):
        '''
            Set tenGig1SourceIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1SourceIpDummy = aValue

    def tenGig1SourcePortGet(self):
        '''
            Get tenGig1SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1SourcePortDummy

    def tenGig1SourcePortSet(self, aValue):
        '''
            Set tenGig1SourcePort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1SourcePortDummy = aValue

    def tenGig1DestMacGet(self):
        '''
            Get tenGig1DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1DestMacDummy

    def tenGig1DestMacSet(self, aValue):
        '''
            Set tenGig1DestMac
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1DestMacDummy = aValue

    def tenGig1DestIpGet(self):
        '''
            Get tenGig1DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1DestIpDummy

    def tenGig1DestIpSet(self, aValue):
        '''
            Set tenGig1DestIp
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1DestIpDummy = aValue

    def tenGig1DestPortGet(self):
        '''
            Get tenGig1DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGig1DestPortDummy

    def tenGig1DestPortSet(self, aValue):
        '''
            Set tenGig1DestPort
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGig1DestPortDummy = aValue

    def tenGigInterframeGapGet(self):
        '''
            Get tenGigInterframeGap
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGigInterframeGapDummy

    def tenGigInterframeGapSet(self, aValue):
        '''
            Set tenGigInterframeGap
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGigInterframeGapDummy = aValue

    def tenGigUdpPacketLenGet(self):
        '''
            Get tenGigUdpPacketLen
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.tenGigUdpPacketLenDummy

    def tenGigUdpPacketLenSet(self, aValue):
        '''
            Set tenGigUdpPacketLen
        '''
        #TODO: This function needs to be updated to handle actual data
        self.tenGigUdpPacketLenDummy = aValue

    def femSendPpcResetGet(self):
        '''
            Get femSendPpcReset
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femSendPpcResetDummy

    def femSendPpcResetSet(self, aValue):
        '''
            Set femSendPpcReset
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femSendPpcResetDummy = aValue

    def femFastCtrlDynamicGet(self):
        '''
            Get femFastCtrlDynamic
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femFastCtrlDynamicDummy

    def femFastCtrlDynamicSet(self, aValue):
        '''
            Set femFastCtrlDynamic
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femFastCtrlDynamicDummy = aValue

    def femSetupSlowCtrlBramGet(self):
        '''
            Get femSetupSlowCtrlBram
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femSetupSlowCtrlBramDummy

    def femSetupSlowCtrlBramSet(self, aValue):
        '''
            Set femSetupSlowCtrlBram
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femSetupSlowCtrlBramDummy = aValue

    def femEnableTenGigGet(self):
        '''
            Get femEnableTenGig
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femEnableTenGigDummy

    def femEnableTenGigSet(self, aValue):
        '''
            Set femEnableTenGig
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femEnableTenGigDummy = aValue

    def femDataSourceGet(self):
        '''
            Get femDataSource
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femDataSourceDummy

    def femDataSourceSet(self, aValue):
        '''
            Set femDataSource
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femDataSourceDummy = aValue

    def femAsicCountingDataGet(self):
        '''
            Get femAsicCountingData
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicCountingDataDummy

    def femAsicCountingDataSet(self, aValue):
        '''
            Set femAsicCountingData
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicCountingDataDummy = aValue

    def femAsicModuleTypeGet(self):
        '''
            Get femAsicModuleType
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicModuleTypeDummy

    def femAsicModuleTypeSet(self, aValue):
        '''
            Set femAsicModuleType
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicModuleTypeDummy = aValue

    def femAsicRxStartDelayGet(self):
        '''
            Get femAsicRxStartDelay
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicRxStartDelayDummy

    def femAsicRxStartDelaySet(self, aValue):
        '''
            Set femAsicRxStartDelay
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicRxStartDelayDummy = aValue

    def femNumLocalLinkFramesGet(self):
        '''
            Get femNumLocalLinkFrames
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femNumLocalLinkFramesDummy

    def femNumLocalLinkFramesSet(self, aValue):
        '''
            Set femNumLocalLinkFrames
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femNumLocalLinkFramesDummy = aValue

    def femAsicFastCmdRegSizeGet(self):
        '''
            Get femAsicFastCmdRegSize
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicFastCmdRegSizeDummy

    def femAsicFastCmdRegSizeSet(self, aValue):
        '''
            Set femAsicFastCmdRegSize
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicFastCmdRegSizeDummy = aValue

    def femAsicEnableMaskGet(self):
        '''
            Get femAsicEnableMask
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicEnableMaskDummy

    def femAsicEnableMaskSet(self, aValue):
        '''
            Set femAsicEnableMask
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicEnableMaskDummy = aValue

    def femAsicColumnsGet(self):
        '''
            Get femAsicColumns
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicColumnsDummy

    def femAsicColumnsSet(self, aValue):
        '''
            Set femAsicColumns
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicColumnsDummy = aValue

    def femAsicColumnsPerFrameGet(self):
        '''
            Get femAsicColumnsPerFrame
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicColumnsPerFrameDummy

    def femAsicColumnsPerFrameSet(self, aValue):
        '''
            Set femAsicColumnsPerFrame
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicColumnsPerFrameDummy = aValue

    def femAsicGainOverrideGet(self):
        '''
            Get femAsicGainOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicGainOverrideDummy

    def femAsicGainOverrideSet(self, aValue):
        '''
            Set femAsicGainOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicGainOverrideDummy = aValue

    def femAsicSlowControlParamsGet(self):
        '''
            Get femAsicSlowControlParams
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicSlowControlParamsDummy

    def femAsicSlowControlParamsSet(self, aValue):
        '''
            Set femAsicSlowControlParams
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicSlowControlParamsDummy = aValue

    def femAsicFastCmdSequenceGet(self):
        '''
            Get femAsicFastCmdSequence
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicFastCmdSequenceDummy

    def femAsicFastCmdSequenceSet(self, aValue):
        '''
            Set femAsicFastCmdSequence
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicFastCmdSequenceDummy = aValue

    def femAsicPixelFeedbackOverrideGet(self):
        '''
            Get femAsicPixelFeedbackOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicPixelFeedbackOverrideDummy
                    
    def femAsicPixelFeedbackOverrideSet(self, aValue):
        '''
            Set femAsicPixelFeedbackOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicPixelFeedbackOverrideDummy = aValue
            
    def femAsicPixelSelfTestOverrideGet(self):
        '''
            Get femAsicPixelSelfTestOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femAsicPixelSelfTestOverrideDummy
                    
    def femAsicPixelSelfTestOverrideSet(self, aValue):
        '''
            Set femAsicPixelSelfTestOverride
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femAsicPixelSelfTestOverrideDummy = aValue

    def femReadoutOperatingModeGet(self):
        '''
            Get femReadoutOperatingMode
        '''
        #TODO: This function needs to be updated to handle actual data
        return self.femReadoutOperatingModeDummy

    def femReadoutOperatingModeSet(self, aValue):
        '''
            Set femReadoutOperatingMode
        '''
        #TODO: This function needs to be updated to handle actual data
        self.femReadoutOperatingModeDummy = aValue


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
        addr = LpdFemClient.i2cPowerCardBus + device
        adcChannel = 0x80 + ((channel & 7) << 4)

        # Write operation, select ADC channel
        ack = self.i2cWrite(addr, adcChannel)
        
        # Read operation, read ADC value
        response = self.i2cRead(addr, 2)
        
        # Extract the received two bytes and return one integer
        value = (int((response[0] & 15) << 8) + int(response[1]))
#        print "[%4i" % value, "]",
        return value

    def ad5321Read(self):
        ''' 
            Read 2 bytes from ad5321 device 
        '''
        
        addr = LpdFemClient.i2cPowerCardBus + 0x0C
        response = -1
        
        response = self.i2cRead(addr, 2)
        high = (response[0] & 15) << 8
        low = response[1]
        return high + low

    def ad55321Write(self, aValue):
        '''
            Write 'aAValue' (2 bytes) to ad5321 device
        '''
    
        response = -1
        # Construct address and payload (as a tuple)
        addr = LpdFemClient.i2cPowerCardBus + 0x0C
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
        
        addr = LpdFemClient.i2cPowerCardBus + 0x38 
        
        response = self.i2cRead(addr, 1)
        
#        print "response = ", response, " type(response) = ", type(response)
        value = response[0]
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
        addr = LpdFemClient.i2cPowerCardBus + 0x38
        response = self.i2cRead(addr, 1)
#        print "pcf7485ReadAllBits() response = ", self.debugDisplay(response[0])
        return response[0]

    def pcf7485WriteOneBit(self, id, value):
        ''' 
            Change bit 'id' to 'value' in PCF7485 device
        '''        
        # Read PCF7485's current value
        bit_register = self.pcf7485ReadAllBits()
        # Change bit 'id' to 'value'
        bit_register = (bit_register & ~(1 << id)) | (value << id) | 0xFC

        addr = LpdFemClient.i2cPowerCardBus + 0x38
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
