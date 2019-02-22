'''
Created on Jun 25, 2013

@author: mt47
'''

from __future__ import print_function

import struct

class FemSysaceConfig():
    '''
    FEM SystemACE image metadata header 
    '''

    configFormat = '!3I32s5I'
    intConfigFormat = '!3I8I5I'

    HEADER_MAGIC_WORD = 0xB0BAFE77

    @classmethod
    def configSize(cls):
        return struct.calcsize(FemSysaceConfig.configFormat)

    def __init__(self, magic=None, imgSize=None, slot=None, strDesc=None, filedate=None, uploaddate=None, bytesWritten=None, crc=None, status=None, encoded=None):
        '''
        Constructor
        '''
        
        if encoded:
            
            self.encoded = encoded
            (self.magic, self.imgSize, self.slot, self.strDesc, self.filedate, self.uploaddate, self.bytesWritten, self.crc, self.status) = struct.unpack(FemSysaceConfig.configFormat, encoded)
            
        else:
            
            self.magic        = magic
            self.imgSize      = imgSize
            self.slot         = slot
            self.strDesc      = strDesc
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
    
    def decodeAsInt(self):
        return struct.unpack(self.intConfigFormat, self.encoded)
    
    def getConfig(self):
        
        config = [self.magic, self.imgSize, self.slot, self.strDesc, self.filedate, self.uploaddate, self.bytesWritten, self.crc, self.status]
        return config
    
    def updateCrc(self, crc=None):
        self.crc = crc
        self.encode()
    
    def __str__(self):
    
        showStr = 'Magic         : ' + hex(self.magic)        + '\n' + \
                  'Image size    : ' + str(self.imgSize)      + '\n' + \
                  'Slot          : ' + str(self.slot)         + '\n' + \
                  'Description   : ' + str(self.strDesc)      + '\n' + \
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
    testDescription = b'TEST_FIRMWARE_UPLOAD'
    #testDescription = 0
    testFileDate = 1234567
    testUploadDate = 7654321
    
    testSysaceConfig = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, testImgSize, testSlot, testDescription, testFileDate, testUploadDate, 0, 0, 0)
    
    print("Test SystemACE config parameters:")
    print(testSysaceConfig)
    testPacked    = testSysaceConfig.encode()
    print("Packed config:", binascii.hexlify(testPacked))
    
    reverseConfig = FemSysaceConfig(encoded=testPacked)
    testUnpacked  = reverseConfig.decode()
    print(testUnpacked, type(testUnpacked), [type(field) for field in testUnpacked])
    print("Unpacked reverse config:" , [unpackedField for unpackedField in testUnpacked])
    
