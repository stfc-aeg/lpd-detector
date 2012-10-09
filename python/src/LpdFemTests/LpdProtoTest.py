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
        
        pass
    
    def SensorATempSet(self, device, channel, value):
        '''
        Set temperature value of channel in device
        '''
        
        pass
    


if __name__ == "__main__":
    
    print "hello"