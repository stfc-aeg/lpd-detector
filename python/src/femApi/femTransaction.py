'''
Created on 28 Mar 2011

@author: tcn
'''

from struct import Struct

class FemTransaction(Struct):
    '''
    FEM communication protocol transaction
    '''
    
    TRANSACTION_MAGIC_WORD = 0xdeadbeef
    
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

    def __init__(self, theCmd=None, theAddr=None, thePayload=None):
        
        formatStr ='!IIII'
        self.magicWord = FemTransaction.TRANSACTION_MAGIC_WORD
        
        if not theCmd:
            self.commandWord = FemTransaction.CMD_UNSUPPORTED
        else:
            self.commandWord = theCmd
         
        if not theAddr:
            self.address = 0
        else:
            self.address = theAddr
                  
        if not thePayload:
            self.payloadLen = 0
        else:
            self.payload = tuple(thePayload)
            self.payloadLen = len(thePayload) * 4 # TODO: remove this hardcoding!!
            formatStr = formatStr + str(len(thePayload)) + 'I'
        
        Struct.__init__(self, format=formatStr)
        
    def getBinary(self):
        transaction = (self.magicWord, self.commandWord, self.payloadLen, self.address) + self.payload
        return self.pack(*(transaction))

        
if __name__ == '__main__':
    
    import binascii
    
    testPayload = 0x1234, 0x5678, 0xfaced00f
    testTransaction = FemTransaction(FemTransaction.CMD_RAW_REG32_WRITE, testPayload)
    testPacked = testTransaction.getBinary()
    print testPacked.__class__
    print "Packed transaction : ", binascii.hexlify(testPacked)
    