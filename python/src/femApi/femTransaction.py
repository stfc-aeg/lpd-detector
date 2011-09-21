'''
Created on 28 Mar 2011

@author: tcn
'''

import struct  

class FemTransaction():
    '''
    FEM communication protocol transaction
    '''
    
    headerFormat = '!IBBBBII'
    
    TRANSACTION_MAGIC_WORD = 0xdeadbeef
    
    CMD_UNSUPPORTED      = 0
    CMD_ACCESS           = 1
    
    BUS_UNSUPPORTED      = 0
    BUS_EEPROM           = 1
    BUS_I2C              = 2
    BUS_RAW_REG          = 3
    BUS_RDMA             = 4
    
    WIDTH_UNSUPPORTED    = 0
    WIDTH_BYTE           = 1
    WIDTH_WORD           = 2
    WIDTH_LONG           = 3
    
    STATE_UNSUPPORTED    = 0
    STATE_READ           = 1
    STATE_WRITE          = 2
    STATE_ACKNOWLEDGE    = 64
    STATE_NO_ACKNOWLEDGE = 128
    
    widthEncoding =  { WIDTH_UNSUPPORTED : (0, 'x'),
                       WIDTH_BYTE        : (1, 'B'),
                       WIDTH_WORD        : (2, 'H'),
                       WIDTH_LONG        : (4, 'I')}
  
    @classmethod
    def headerSize(cls):
        return struct.calcsize(FemTransaction.headerFormat)
       
    def __init__(self, cmd=None, bus=None, width=None, state=None, addr=None, payload=None, readLen=None, encoded=None):
 
        # Initialise format string to header format and create empty payload format string       
        self.formatStr = FemTransaction.headerFormat
        self.payloadFormatStr = ''
        
        # Initialise remaining payload counter to zero and incomplete flag
        self.payloadRemaining = 0
        self.incomplete = True
        
        # If we are receving a byte encoded transaction, decode accordingly
        if encoded:

            self.encoded = encoded
            
            # Decode the headerStruct first
            headerStructLen = FemTransaction.headerSize()  
            
            (self.magicWord, self.command, self.bus, self.width, 
             self.state, self.address, self.payloadLen) =  struct.unpack(self.formatStr, encoded[0:headerStructLen])
            
            #TODO: sanity check decoded headerStruct
            
            # If this is a read transaction then we have a fixed length payload, which is the read length
            if (self.command == FemTransaction.CMD_ACCESS) and (self.state == FemTransaction.STATE_READ):

                (payloadMult, self.payloadFormatStr) = FemTransaction.widthEncoding[FemTransaction.WIDTH_LONG]
            
            else:

                (payloadMult, payloadFormat) = FemTransaction.widthEncoding[self.width]
                payloadItems = self.payloadLen / payloadMult   
                self.payloadFormatStr = str(payloadItems) + payloadFormat
                            

            # Calculate how much of the payload is not yet received
            self.payloadRemaining = self.payloadLen - (len(self.encoded) - headerStructLen)
            if self.payloadRemaining > 0:
                self.incomplete = True
            else:
                payloadFormat = '!' + self.payloadFormatStr
                self.payload = struct.unpack(payloadFormat, self.encoded[headerStructLen:])
                self.incomplete = False
            
         
        # Otherwise, build the transaction from the other fields, ready for encoding              
        else:
            
            self.magicWord = FemTransaction.TRANSACTION_MAGIC_WORD
            
            self.command = cmd or FemTransaction.CMD_UNSUPPORTED
            self.bus     = bus or FemTransaction.BUS_UNSUPPORTED
            self.width   = width or FemTransaction.WIDTH_UNSUPPORTED
            self.state   = state or FemTransaction.STATE_UNSUPPORTED
            self.address = addr or 0

            # If this is a read transaction then we have a fixed length payload, which is the read length            
            if (self.command == FemTransaction.CMD_ACCESS) and (self.state == FemTransaction.STATE_READ):
                
                (self.payloadLen, self.payloadFormatStr) = FemTransaction.widthEncoding[FemTransaction.WIDTH_LONG]
                self.payload = (readLen,)

            else:          
                if not payload:
                    #TODO: How can a write have no payload - exception?
                    self.payloadLen = 0
                    self.payload = ()
                else:
                    (payloadMult, payloadFormat) = FemTransaction.widthEncoding[self.width]
                    self.payloadLen = len(payload) * payloadMult
                    self.payloadFormatStr = str(len(payload)) + payloadFormat
                    self.payload = tuple(payload)
         
        self.formatStr = self.formatStr + self.payloadFormatStr       

    def append(self, data=None):

        if self.incomplete:
            
            dataLen = len(data)
            if dataLen > self.payloadRemaining:
                print "Too much data"
                #TODO exception
            else:
                self.encoded = self.encoded + data
                self.payloadRemaining = self.payloadRemaining - dataLen
                if self.payloadRemaining == 0:
                    payloadFormat = '!' + self.payloadFormatStr
                    headerStructLen = FemTransaction.headerSize()
                    self.payload = struct.unpack(payloadFormat, self.encoded[headerStructLen:])
                    self.incomplete = False
                
        else:
            #TODO raise exception?
            pass
        
                
    def encode(self):
        transaction = (self.magicWord, self.command, self.bus, self.width, self.state, self.address, self.payloadLen) + self.payload
        return struct.pack(self.formatStr, *(transaction))

    def decode(self):
        return struct.unpack(self.formatStr, self.encoded)

if __name__ == '__main__':
    
    import binascii
   
    testAddr = 0x1000 
    testPayload = 0x1234, 0x5678, 0xfaced00f
    testTransaction = FemTransaction(cmd=FemTransaction.CMD_ACCESS, bus=FemTransaction.BUS_RAW_REG, 
                                     width=FemTransaction.WIDTH_LONG, state=FemTransaction.STATE_WRITE,  
                                     addr=testAddr, payload=testPayload)
    testPacked = testTransaction.encode()
    print "Packed transaction : ", binascii.hexlify(testPacked)
    
    reverseTransaction = FemTransaction(encoded=testPacked)
    testUnpacked = reverseTransaction.decode()
    print 'Unpacked reverse transaction:', [hex(unpackedField) for unpackedField in testUnpacked]
    print 'Unpacked payload:', [hex(payloadField) for payloadField in reverseTransaction.payload]
    
    assert testPayload == reverseTransaction.payload
        