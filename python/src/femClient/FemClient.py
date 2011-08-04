'''
Created on 22 Mar 2011

@author: tcn
'''

import socket
from femApi.femTransaction import FemTransaction
from femApi.femConfig import FemConfig

import binascii

class FemClientError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
    
class FemClient():
    '''
    classdocs
    '''

    def __init__(self, hostAddr=None, timeout=None):
        print "Connecting to FEM at", hostAddr
        self.femSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.femSocket.settimeout(timeout)
        try:
            self.femSocket.connect(hostAddr)
        except socket.timeout:
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError("Socket connection timed out")

        except socket.error, (errno, sockErrStr):
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError(sockErrStr)
    
    def send(self, theCmd, theBus, theWidth, theState, theAddr, thePayload=None, theReadLen=None):
        #print "Sending cmd: ", theCmd, "bus:", theBus, "width:", theWidth, "addr:", theAddr, "values: ", thePayload
        theTransaction = FemTransaction(cmd=theCmd, bus=theBus, width=theWidth, state=theState, 
                                          addr=theAddr, payload=thePayload, readLen=theReadLen)
        data = theTransaction.encode()
        self.femSocket.send(data)
  
    def recv(self):
        initRecvLen = FemTransaction.headerSize()
        data = self.femSocket.recv(initRecvLen)
        if not data:
            return None
        response = FemTransaction(encoded=data)
        while response.incomplete:
            payloadRecvLen = response.payloadRemaining
            data = self.femSocket.recv(payloadRecvLen)
            response.append(data)

        return response.payload
       
    def write(self, theBus, theWidth, theAddr, thePayload):
        self.send(theCmd=FemTransaction.CMD_ACCESS, theBus=theBus, 
                 theWidth=theWidth, theState=FemTransaction.STATE_WRITE, 
                 theAddr=theAddr, thePayload=thePayload)
        ack = self.recv()
        return ack
        
    def read(self, theBus, theWidth, theAddr, theReadLen):
        self.send(theCmd=FemTransaction.CMD_ACCESS, theBus=theBus,
                  theWidth=theWidth, theState=FemTransaction.STATE_READ,
                  theAddr=theAddr, theReadLen=theReadLen)
        values = self.recv()
        return values
    
    def configRead(self):
        
        bus     = FemTransaction.BUS_EEPROM
        width   = FemTransaction.WIDTH_BYTE
        address = FemConfig.configAddress
        length  = FemConfig.configSize()
        values = self.read(bus, width, address, length)
        encoded = ''.join([chr(x) for x in values[4:]])
        theConfig = FemConfig(encoded=encoded)
        
        return theConfig
    
    def configWrite(self, theConfig=None):
        
        bus     = FemTransaction.BUS_EEPROM
        width   = FemTransaction.WIDTH_BYTE
        address = FemConfig.configAddress
        payload = bytearray(theConfig.encode())
        ack = self.write(bus, width, address, payload) 
        return ack
    
    def close(self):
        self.femSocket.close()
        self.femSocket = None
        
    
    