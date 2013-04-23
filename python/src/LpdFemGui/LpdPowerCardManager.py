'''
Created on Apr 18, 2013

@author: tcn45
'''

from LpdFemGui import *
from LpdDevice.LpdDevice import *
import time, sys

class LpdPowerCardManager(object):
    '''
    classdocs
    '''


    def __init__(self, appMain, device):
        '''
        Constructor
        '''
        self.appMain = appMain
        self.device  = device
        
        self.lvEnabled = False
        self.hvEnabled = False
        self.hvBias = 0.0
        
        # Specify number of power cards present
        # TODO - tie this to the module type
        self.numPowerCards = 2
        self.numSensorsPerCard = 8
        self.numSensors = self.numSensorsPerCard * self.numPowerCards
        
        self.cardParamList = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                              'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                              'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']
        
        self.sensorParamList = ['Temp', 'Voltage', 'Current']
        
        self.powerState = {}
        
    def lvEnableSet(self, state):
        
        self.lvEnabled = state
        self.appMain.msgPrint("LV state is now %s" % state)
        
    def lvEnableGet(self):
    
        lvEnables = []
        for powerCard in range(self.numPowerCards):
            enableParamName = 'asicPowerEnable' + str(powerCard)
            (rc, enableVal) = self.device.paramGet(enableParamName)
            if rc != LpdDevice.ERROR_OK:
                self.appMain.msgPrint("Unable to retrieve power card %d LV enable status (rc=%d): %s", powerCard, rc, self.device.errorStringGet())
            lvEnables.append(enableVal)
        
        self.lvEnabled = True
        for enable in lvEnables:
            if enable == True:
                self.lvEnabled = False
                         
        return self.lvEnabled
    
    def hvEnableSet(self, state):
        
        self.hvEnabled = state
        
    def hvEnableGet(self):
        
        hvEnables = []
        for powerCard in range(self.numPowerCards):
            enableParamName = 'sensorBiasEnable' + str(powerCard)
            (rc, enableVal) = self.device.paramGet(enableParamName)
            if rc != LpdDevice.ERROR_OK:
                self.appMain.msgPrint("Unable to retrieve power card %d HV enable status (rc=%d): %s", powerCard, rc, self.device.errorStringGet())
            hvEnables.append(enableVal)
        
        self.hvEnabled = True
        for enable in hvEnables:
            if enable == True:
                self.hvEnabled = False
                         
        return self.hvEnabled
    
    def hvBiasSet(self, bias):
        
        self.appMain.msgPrint("Entered hvBiasSet")
        time.sleep(3)
        self.hvBias = bias
        self.appMain.msgPrint("HV bias is now %f" % bias)

    def hvBiasGet(self):
        
        return self.hvBias
    
    def statusUpdate(self):

        try:        
            self.powerState = {}
            if self.appMain.deviceState != self.appMain.DeviceDisconnected:
            
                # Loop over card parameters for each card and load into results
                for powerCard in range(self.numPowerCards):
                    for param in self.cardParamList:
                        
                        paramName = param + str(powerCard)
                        (rc, val) = self.device.paramGet(paramName)
                        if  rc != LpdDevice.ERROR_OK:
                            self.appMain.msgPrint("Unable to read parameter %s (rc=%d) : %s" % 
                                                  (paramName, rc, self.device.errorStringGet()))
                            
                        self.powerState[paramName] = val
                
                # Loop over sensor parameters and append into results
                for sensor in range(self.numSensors):
                    for param in self.sensorParamList:
                        
                        paramName = 'sensor' + str(sensor) + param
                        (rc, val) = self.device.paramGet(paramName)
                        if rc != LpdDevice.ERROR_OK:
                            self.appMain.msgPrint("Unable to read sensor parameter %s (rc=%d) : %s" %
                                                  (paramName, rc, self.device.errorStringGet()))
                            
                        self.powerState[paramName] = val
            else:
                pass
                #self.appMain.msgPrint("Not updating power state as device disconnected")
        
        except Exception as e:
            print >> sys.stderr, "Power card status update got exception:", e
                
    def powerStateGet(self):
        
        return self.powerState
    
        