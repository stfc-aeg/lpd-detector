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
    
    
    def __init__(self):
        '''
        Constructor for LpdProtoTest
        '''
            
        pass
        
    def SensorATempGet(self, device, channel):
        '''
        Get temperature value (in ADC counts) of channel in device
        '''
        
        adcValue = self.ad7998read(device, channel)
        tempValue = self.adcToTemp(adcValue)
        
    def SensorATempSet(self, device, channel, value):
        '''
        Set temperature value of channel in device
        '''
        
        adcValue = self.tempToAdc(value)
        ack = self.ad7998write(device, channel, adcValue)
    

    """ -=-=-=-=-=- Helper Functions -=-=-=-=-=- """
    
    def ad7998read(self, device, channel):
        '''
        '''
        pass
    
    def adcToTemp(self, adcValue):
        '''
        '''
        pass

    def tempToAdc(self, value):
        '''
        '''
        pass

    def ad7998write(self, device, channel, adcValue):
        '''
        '''
        pass


if __name__ == "__main__":
    
    print "hello"