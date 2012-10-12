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
    CMD_INTERNAL         = 2
    CMD_ACQUIRE          = 3
    CMD_PERSONALITY      = 4
    
    BUS_UNSUPPORTED      = 0
    BUS_EEPROM           = 1
    BUS_I2C              = 2
    BUS_RAW_REG          = 3
    BUS_RDMA             = 4
    BUS_SPI              = 5
    BUS_DIRECT           = 6
    
    WIDTH_UNSUPPORTED    = 0
    WIDTH_BYTE           = 1
    WIDTH_WORD           = 2
    WIDTH_LONG           = 3
    
    STATE_UNSUPPORTED    = 0
    STATE_READ           = 1
    STATE_WRITE          = 2
    STATE_ACKNOWLEDGE    = 32
    STATE_NO_ACKNOWLEDGE = 64
    
    CMD_ACQ_UNSUPPORTED   = 0
    CMD_ACQ_CONFIG        = 1
    CMD_ACQ_START         = 2
    CMD_ACQ_STOP          = 3
    CMD_ACQ_STATUS        = 4
    
    ACQ_MODE_UNSUPPORTED  = 0
    ACQ_MODE_NORMAL       = 1
    ACQ_MODE_BURST        = 2
    ACQ_MODE_RX_ONLY      = 3
    ACQ_MODE_TX_ONLY      = 4
    ACQ_MODE_UPLOAD       = 5
 
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
            
            # If this is an encoded access command, i.e. a read or write transaction, then the payload has a fixed
            # integer length field at the start specifying the transaction length
            payloadInitLen = 0                    
            if self.command == FemTransaction.CMD_ACCESS:
            
                (payloadMult, self.payloadFormatStr) = FemTransaction.widthEncoding[FemTransaction.WIDTH_LONG]
                payloadInitLen = 4
            
            # Build the remaining payload format specifier
            if (self.payloadLen -payloadInitLen) > 0:
                (payloadMult, payloadFormat) = FemTransaction.widthEncoding[self.width]
                payloadItems = (self.payloadLen - payloadInitLen) / payloadMult
                self.payloadFormatStr = self.payloadFormatStr + str(payloadItems) + payloadFormat
                    

            # Calculate how much of the payload is not yet received
            self.payloadRemaining = self.payloadLen - (len(self.encoded) - headerStructLen)
            if self.payloadRemaining > 0:
                #print "Payload remaining =", self.payloadRemaining
                self.incomplete = True
            else:
                if (self.payloadLen > 0):
                    payloadFormat = '!' + self.payloadFormatStr
                    self.payload = struct.unpack(payloadFormat, self.encoded[headerStructLen:])
                else:
                    self.payload = ()
                self.incomplete = False
            
         
        # Otherwise, build the transaction from the other fields, ready for encoding              
        else:
            
            self.magicWord = FemTransaction.TRANSACTION_MAGIC_WORD
            
            self.command = cmd or FemTransaction.CMD_UNSUPPORTED
            self.bus     = bus or FemTransaction.BUS_UNSUPPORTED
            self.width   = width or FemTransaction.WIDTH_UNSUPPORTED
            self.state   = state or FemTransaction.STATE_UNSUPPORTED
            self.address = addr or 0

            # If This is an internal command, there is no payload
            if (self.command == FemTransaction.CMD_INTERNAL):

                self.payloadLen = 0
                self.payload = ()
                
            # If this is a read transaction then we have a fixed length payload, which is the read length            
            elif (self.command == FemTransaction.CMD_ACCESS) and (self.state == FemTransaction.STATE_READ):
                
                (self.payloadLen, self.payloadFormatStr) = FemTransaction.widthEncoding[FemTransaction.WIDTH_LONG]
                self.payload = (readLen,)

            # If this is an ack of a read or write transaction then the first word of the payload is the read length, which
            # should be encoded as a long followed by the rest of the payload at the appropriate width
            elif (self.command == FemTransaction.CMD_ACCESS) and (self.state & FemTransaction.STATE_ACKNOWLEDGE):
                
                (self.payloadLen, self.payloadFormatStr) = FemTransaction.widthEncoding[FemTransaction.WIDTH_LONG]
                (payloadMult, payloadFormat) = FemTransaction.widthEncoding[self.width]
                self.payloadLen = self.payloadLen + ((len(payload)-1) * payloadMult)
                self.payloadFormatStr = self.payloadFormatStr + str(len(payload) - 1) + payloadFormat
                self.payload = tuple(payload)
            
            else:          
                if payload == None:
                    #TODO: How can a write have no payload - exception?
                    self.payloadLen = 0
                    self.payload = ()
                else:
                    (payloadMult, payloadFormat) = FemTransaction.widthEncoding[self.width]
                    if type(payload) == int:
                        payload = (payload,)
                    
                    self.payload = tuple(payload)
                    self.payloadLen = len(self.payload) * payloadMult
                    self.payloadFormatStr = str(len(self.payload)) + payloadFormat

                    #print self.width, payloadMult, payloadFormat, self.payloadLen, self.payloadFormatStr, self.payload
         
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
    
    def decodeErrorResponse(self):
        
        (errNo,) = struct.unpack('!I', self.encoded[16:20])
        errStr = "".join(self.encoded[20:])
        
        return (errNo, errStr)
    
    def __str__(self):
        
        showStr = 'Magic word     : ' + hex(self.magicWord)  + '\n' + \
                  'Command        : ' + str(self.command)    + '\n' + \
                  'Bus            : ' + str(self.bus)        + '\n' + \
                  'Width          : ' + str(self.width)      + '\n' + \
                  'State          : ' + str(self.state)      + '\n' + \
                  'Address        : ' + str(self.address)    + '\n' + \
                  'Payload length : ' + str(self.payloadLen) + '\n'
        
        if self.payloadLen:
            showStr = showStr + \
                   'Payload        : ' + str([hex(val) for val in self.payload])
        
        return showStr
                  

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
        