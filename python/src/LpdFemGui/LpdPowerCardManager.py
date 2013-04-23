'''
Created on Apr 18, 2013

@author: tcn45
'''

from LpdFemGui import *
import time

class LpdPowerCardManager(object):
    '''
    classdocs
    '''


    def __init__(self, guiMain, device):
        '''
        Constructor
        '''
        self.guiMain = guiMain
        self.device  = device
        
        self.lvEnabled = False
        self.hvEnabled = False
        self.hvBias = 0.0
        
    
    def updateState(self):
        
        if self.guiMain.deviceState != LpdFemGui.DeviceDisconnected:
            self.guiMain.msgPrint("Going to update power card state")
        else:
            self.guiMain.msgPrint("Not updating power state as device disconnected")
            
    
    def lvEnableSet(self, state):
        
        self.lvEnabled = state
        self.guiMain.msgPrint("LV state is now %s" % state)
        
    def lvEnableGet(self):
        
        return self.lvEnabled
    
    def hvEnableSet(self, state):
        
        self.hvEnabled = state
        self.guiMain.msgPrint("HV state is now %s" % state)
        
    def hvEnableGet(self):
        
        return self.hvEnabled
    
    def hvBiasSet(self, bias):
        
        self.guiMain.msgPrint("Entered hvBiasSet")
        time.sleep(3)
        self.hvBias = bias
        self.guiMain.msgPrint("HV bias is now %f" % bias)

    def hvBiasGet(self):
        
        return self.hvBias
    
    def statusUpdate(self):
        
        self.guiMain.msgPrint("Doing power update")
        time.sleep(1)
        