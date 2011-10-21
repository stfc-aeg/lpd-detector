'''
Created on Aug 2, 2011

@author: tcn45
'''

import struct
from operator import xor

class FemConfig():
    
    configFormat = '!H6B4B4B4B2B6B2BB'
    
    CONFIG_MAGIC_WORD = 0xface
    
    configAddress = 0

    @classmethod
    def configSize(cls):
        return struct.calcsize(FemConfig.configFormat)
    
    def __init__(self, net_mac=None, net_ip=None, net_mask=None, 
                        net_gw=None, temp_high=None, temp_crit=None, 
                        sw_major=None, sw_minor=None, fw_major=None, fw_minor=None,
                        hw_major=None, hw_minor=None, board_id=None, board_type=None, encoded=None):

        self.magicWord        = None
        self.net_mac          = [None] * 6
        self.net_ip           = [None] * 4
        self.net_mask         = [None] * 4
        self.net_gw           = [None] * 4
        self.temp_high        = None
        self.temp_crit        = None
        self.sw_major_version = None
        self.sw_minor_version = None
        self.fw_major_version = None
        self.fw_minor_version = None
        self.hw_major_version = None
        self.hw_minor_version = None
        self.board_id         = None
        self.board_type       = None
        self.checksum         = 0
        
        # If we are receiving a byte encoded config object, decode accordingly
        if encoded:
        
            self.encoded = encoded    
        
            (self.magicWord,
             self.net_mac[0], self.net_mac[1], self.net_mac[2], 
             self.net_mac[3], self.net_mac[4], self.net_mac[5],
             self.net_ip[0], self.net_ip[1], self.net_ip[2], self.net_ip[3],
             self.net_mask[0], self.net_mask[1], self.net_mask[2], self.net_mask[3],
             self.net_gw[0], self.net_gw[1], self.net_gw[2], self.net_gw[3],
             self.temp_high, self.temp_crit, 
             self.sw_major_version, self.sw_minor_version, 
             self.fw_major_version, self.fw_minor_version, 
             self.hw_major_version, self.hw_minor_version,
             self.board_id, self.board_type, self.checksum ) = struct.unpack(FemConfig.configFormat, encoded)
             
        # Otherwise fill the fields out from the arguments list, then encode to get packed
        # version with checksum     
        else:
            
            self.magicWord = FemConfig.CONFIG_MAGIC_WORD
            self.net_mac = net_mac
            self.net_ip  = net_ip
            self.net_mask = net_mask
            self.net_gw   = net_gw
            self.temp_high = temp_high
            self.temp_crit = temp_crit
            self.sw_major_version = sw_major
            self.sw_minor_version = sw_minor
            self.fw_major_version = fw_major
            self.fw_minor_version = fw_minor
            self.hw_major_version = hw_major
            self.hw_minor_version = hw_minor
            self.board_id = board_id
            self.board_type = board_type
            
            self.encode()
        
    def encode(self):
        
        # Caclulate checksum
        self.checksum = self.calculateChecksum()
        
        # Pack config into struct and update encoded version       
        self.encoded = struct.pack(FemConfig.configFormat, *(self.getConfig()))
 
        return self.encoded

    def calculateChecksum(self):
        
        # Pack config into struct and get encoded version
        encoded = struct.pack(FemConfig.configFormat, *(self.getConfig()))
        
        # Calculate checksum disregarding last byte, which is current checksum
        checksum = reduce(xor, map(ord, encoded[:-1]))
        
        return checksum        
    
    def getConfig(self):
        
        config =  [self.magicWord,
             self.net_mac[0], self.net_mac[1], self.net_mac[2], 
             self.net_mac[3], self.net_mac[4], self.net_mac[5],
             self.net_ip[0], self.net_ip[1], self.net_ip[2], self.net_ip[3],
             self.net_mask[0], self.net_mask[1], self.net_mask[2], self.net_mask[3],
             self.net_gw[0], self.net_gw[1], self.net_gw[2], self.net_gw[3],
             self.temp_high, self.temp_crit, 
             self.sw_major_version, self.sw_minor_version, 
             self.fw_major_version, self.fw_minor_version, 
             self.hw_major_version, self.hw_minor_version,
             self.board_id, self.board_type, self.checksum ]
        
        return config 
           
    def decode(self):
        return struct.unpack(FemConfig.configFormat, self.encoded)
        
    def __str__(self):

        showStr = 'Magic word  : ' + hex(self.magicWord)    + '\n' + \
                  'MAC Address : ' + self.net_mac_str()     + '\n' + \
                  'IP Address  : ' + self.net_ip_addr_str() + '\n' + \
                  'Netmask     : ' + self.net_ip_mask_str() + '\n' + \
                  'Gateway     : ' + self.net_ip_gw_str()   + '\n' + \
                  'High Temp   : ' + str(self.temp_high)    + 'C\n' + \
                  'Crit Temp   : ' + str(self.temp_crit)    + 'C\n' + \
                  'S/W version : ' + str(self.sw_major_version)  + '.' + str(self.sw_minor_version) + '\n' + \
                  'F/W version : ' + str(self.fw_major_version)  + '.' + str(self.fw_minor_version) + '\n' + \
                  'H/W version : ' + str(self.hw_major_version)  + '.' + str(self.hw_minor_version) + '\n' + \
                  'Board ID    : ' + str(self.board_id)          + '\n' + \
                  'Board Type  : ' + str(self.board_type)        + '\n' + \
                  'Checksum    : ' + hex(self.checksum)          + '\n'
        return showStr

    def net_mac_str(self):
        
        return ':'.join('%02X' % byte for byte in self.net_mac) 
    
    def net_ip_addr_str(self):
        
        return ".".join('%d' % byte for byte in self.net_ip)

    def net_ip_mask_str(self):
        
        return ".".join('%d' % byte for byte in self.net_mask)

    def net_ip_gw_str(self):
        
        return ".".join('%d' % byte for byte in self.net_gw)
    
if __name__ == '__main__':
    
    print "FemConfig object has length", FemConfig.configSize(), "bytes"
    
    mac_addr = [0x00, 0x0a, 0x35, 0x00, 0xbe, 0xef]
    ip_addr  = [192, 168, 1, 10]
    ip_mask  = [255, 255, 255, 0]
    ip_gw    = [192, 168, 1, 1]
    temp_high = 40
    temp_crit = 75
    sw_major = 1
    sw_minor = 2
    fw_major = 3
    fw_minor = 4
    hw_major = 5
    hw_minor = 6
    board_id = 1
    board_type = 3
    
    aConfig = FemConfig(mac_addr, ip_addr, ip_mask, ip_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor, hw_major, hw_minor,
                        board_id, board_type)
    
    print map(ord, aConfig.encode())
    print aConfig