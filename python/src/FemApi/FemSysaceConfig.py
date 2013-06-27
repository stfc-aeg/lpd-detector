'''
Created on Jun 25, 2013

@author: mt47
'''

import struct

class FemSysaceConfig():
    '''
    FEM SystemACE image metadata header 
    '''

    #configFormat = '!3I32s5I'
    configFormat = '!3I4I5I'

    HEADER_MAGIC_WORD = 0xB0BAFE77

    #def __init__(self, magic=None, imgSize=None, slot=None, strDesc=None, filedate=None, uploaddate=None, bytesWritten=None, crc=None, status=None, encoded=None):
    def __init__(self, magic=None, imgSize=None, slot=None, d1=None, d2=None, d3=None, d4=None, filedate=None, uploaddate=None, bytesWritten=None, crc=None, status=None, encoded=None):
        '''
        Constructor
        '''
        
        if encoded:
            
            self.encoded = encoded
            #(self.magic, self.imgSize, self.slot, self.strDesc, self.filedate, self.uploaddate, self.bytesWritten, self.crc, self.status) = struct.unpack(FemSysaceConfig.configFormat, encoded)
            (self.magic, self.imgSize, self.slot, self.d1, self.d2, self.d3, self.d4, self.filedate, self.uploaddate, self.bytesWritten, self.crc, self.status) = struct.unpack(FemSysaceConfig.configFormat, encoded)
            
        else:
            
            self.magic        = magic
            self.imgSize      = imgSize
            self.slot         = slot
            #self.strDesc      = strDesc
            self.d1           = d1
            self.d2           = d2
            self.d3           = d3
            self.d4           = d4
            self.filedate     = filedate
            self.uploaddate   = uploaddate
            self.bytesWritten = bytesWritten
            self.crc          = crc
            self.status       = status
            
            self.encode()
            
    def encode(self):
        
        self.encoded = struct.pack(FemSysaceConfig.configFormat, *(self.getConfig()))
        return self.encoded
    
    def decode(self):
        return struct.unpack(self.configFormat, self.encoded)
    
    def getConfig(self):
        
        #config = [self.magic, self.imgSize, self.slot, self.strDesc, self.filedate, self.uploaddate, self.bytesWritten, self.crc, self.status]
        config = [self.magic, self.imgSize, self.slot, self.d1, self.d2, self.d3, self.d4, self.filedate, self.uploaddate, self.bytesWritten, self.crc, self.status]
        return config
    
    def __str__(self):
    
        showStr = 'Magic         : ' + hex(self.magic)        + '\n' + \
                  'Image size    : ' + str(self.imgSize)      + '\n' + \
                  'Slot          : ' + str(self.slot)         + '\n' + \
                  'Description   : ' + str(self.d1)      + '\n' + \
                  'File date     : ' + str(self.filedate)     + '\n' + \
                  'Upload date   : ' + str(self.uploaddate)   + '\n' + \
                  'Bytes Written : ' + str(self.bytesWritten) + '\n' + \
                  'CRC           : ' + hex(self.crc)          + '\n' + \
                  'Status        : ' + str(self.status)       + '\n'
                  
        return showStr
    
    
if __name__ == '__main__':
    
    import binascii
#    from FemApi.FemTransaction import FemTransaction
    
    testImgSize = 64
    testSlot = 1
    #testDescription = "TEST_FIRMWARE_UPLOAD"
    testDescription = 0
    testFileDate = 1234567
    testUploadDate = 7654321
    
    testSysaceConfig = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, testImgSize, testSlot, testDescription, testFileDate, testUploadDate, 0, 0, 0)
    
    print "Test SystemACE config parameters:"
    print testSysaceConfig
    testPacked    = testSysaceConfig.encode()
    print "Packed config:", binascii.hexlify(testPacked)
    
    reverseConfig = FemSysaceConfig(encoded=testPacked)
    testUnpacked  = reverseConfig.decode()
    print testUnpacked, type(testUnpacked), [type(field) for field in testUnpacked]
    print "Unpacked reverse config:" , [hex(unpackedField) for unpackedField in testUnpacked]
    
