'''
Created on 22 Mar 2011

@author: tcn
'''

from struct import Struct

class FemHeader(Struct):
    '''
    FEM network interface header implementation
    '''

    CMD_UNSUPPORTED     =  0
    CMD_GPIO_DIR_READ   =  1
    CMD_GPIO_DIR_WRITE  =  2
    CMD_GPIO_READ       =  3
    CMD_GPIO_WRITE      =  4
    CMD_I2C_READ_BYTE   =  5
    CMD_I2C_WRITE_BYTE  =  6
    CMD_RAW_REG32_READ  =  7
    CMD_RAW_REG32_WRITE =  8
    CMD_RAW_REG16_READ  =  9
    CMD_RAW_REG16_WRITE = 10
    CMD_RAW_REG8_READ   = 11
    CMD_RAW_REG8_WRITE  = 12
      
    def __init__(self, headerVals=None):
        '''
        Constructor
        '''
        Struct.__init__(self, format='=IIII')
        self.values = headerVals
        
    def setValues(self, headerVals=None):
        self.values = headerVals
        
    def getValues(self):
        return self.values
    
    def setBinary(self, binaryVals=None):
        if binaryVals:
            self.values = self.unpack(binaryVals)
        else:
            self.values = None
            
    def getBinary(self):
        if self.values:
            return self.pack(*(self.values))
        else:
            return None
        
if __name__ == "__main__":
    
    import binascii
    
    values1 = (1, 2, 3, 0xdeadbeef)
    testHdr = FemHeader(values1)
    testPacked1 = testHdr.getBinary()
    print 'Original values : ', values1, ' Packed hdr : ', binascii.hexlify(testPacked1)
    
    values2 = (5, 6, 7, 0xfaceface)
    testHdr.setValues(values2)
    testPacked2 = testHdr.getBinary()
    print 'Original values : ', values2, ' Packed hdr : ', binascii.hexlify(testPacked2)
    
    testHdr.setBinary(testPacked1)
    unpackedVals = testHdr.getValues()
    print 'Packed hdr : ', binascii.hexlify(testPacked1), ' Values : ', unpackedVals
