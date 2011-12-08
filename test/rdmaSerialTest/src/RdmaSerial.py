'''
Created on Aug 12, 2011

@author: tcn45
'''

import serial
import struct

class RdmaSerial():

    def __init__(self, serialDev=0, serialBaud=9600, serialTimeout=1):

        self.serial = serial.Serial(serialDev, serialBaud, timeout=serialTimeout)
        self.debug = False

    def read(self, address, comment=''):

        command = struct.pack('=BI', 0, address)
        self.serial.write(command)
        
        response = self.serial.read(4)
        decoded = struct.unpack('=I', response)[0]
        
        if self.debug:
            print 'R %08X : %08X %s' % (address, decoded, comment)
            
        return decoded

    def write(self, address, data, comment=''):

        if self.debug:
            print 'W %08X : %08X %s' % (address, data, comment)
            
        command = struct.pack('=BII', 1, address, data)
        self.serial.write(command)

        return

    def setDebug(self, enabled=True):
        self.debug = enabled

if __name__ == '__main__':

    rdmaFem = RdmaSerial('/dev/ttyUSB0', 115200, 1)

    for addr in range(0, 16):
        data = rdmaFem.read(addr)
        print '0x%02x : 0x%08x' % (addr, data)       