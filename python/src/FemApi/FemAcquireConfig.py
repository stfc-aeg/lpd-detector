'''
Created on Mar 22, 2012

@author: tcn45
'''

from __future__ import print_function

import struct

class FemAcquireConfig():
    '''
    FEM acquire configuration payload 
    '''

    configFormat = '!IIIII'

    def __init__(self, mode=None, bufSize=None, bufCount=None, numAcq=None, coalesce=None, encoded=None):
        '''
        Constructor
        '''
        
        if encoded:
            
            self.encoded = encoded
            (self.mode, self.bufSize, self.bufCount, self.numAcq, self.coalesce) = struct.unpack(FemAcquireConfig.configFormat, encoded)
            
        else:
            
            self.mode     = mode
            self.bufSize  = bufSize
            self.bufCount = bufCount
            self.numAcq   = numAcq 
            self.coalesce = coalesce
            
            self.encode()
            
    def encode(self):
        
        self.encoded = struct.pack(FemAcquireConfig.configFormat, *(self.getConfig()))
        return self.encoded
    
    def decode(self):
        return struct.unpack(self.configFormat, self.encoded)
    
    def getConfig(self):
        
        config = [self.mode, self.bufSize, self.bufCount, self.numAcq, self.coalesce]
        return config
    
    def __str__(self):
    
        showStr = 'Mode         : ' + str(self.mode)     + '\n' + \
                  'Buffer size  : ' + hex(self.bufSize)  + '\n' + \
                  'Buffer count : ' + str(self.bufCount) + '\n' + \
                  'Num acquires : ' + str(self.numAcq)   + '\n' + \
                  'Coalesce     : ' + str(self.coalesce) + '\n'
                  
        return showStr
    
    
if __name__ == '__main__':
    
    import binascii
    from FemApi.FemTransaction import FemTransaction
    
    testMode     = FemTransaction.ACQ_MODE_NORMAL
    testBufSize  = 0x1234
    testBufCount = 64
    testNumAcqs  = 100
    testCoalesce = 1
    
    testAcqConfig = FemAcquireConfig(testMode, testBufSize, testBufCount, testNumAcqs, testCoalesce)
    
    print("Test acquire config parameters:")
    print(testAcqConfig)
    testPacked    = testAcqConfig.encode()
    print("Packed acq config:", binascii.hexlify(testPacked))
    
    reverseConfig = FemAcquireConfig(encoded=testPacked)
    testUnpacked  = reverseConfig.decode()
    print("Unpacked reverse config:" , [hex(unpackedField) for unpackedField in testUnpacked])
    