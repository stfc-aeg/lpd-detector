'''
Created on 22 Mar 2011

@author: tcn
'''

import socket
from FemApi.FemTransaction import FemTransaction
from FemApi.FemConfig import FemConfig
from FemApi.FemAcquireConfig import FemAcquireConfig

import binascii
from types import *

class FemClientError(Exception):
    
    ERRNO_NO_ERROR    = 0
    ERRNO_SOCK_CLOSED = 1
    ERRNO_SOCK_ERROR  = 2
    
    def __init__(self, msg, errno=ERRNO_NO_ERROR):
        self.msg = msg
        self.errno = errno
        
    def __str__(self):
        return repr(self.msg)
    
class FemClient(object):
    '''
    classdocs
    '''

    def __init__(self, hostAddr=None, timeout=None):
        #print "Connecting to FEM at", hostAddr
        self.femSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.femSocket.settimeout(timeout)
        self.femSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024)
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
    
    def send(self, theCmd=None, theBus=None, theWidth=None, theState=None, 
             theAddr=None, thePayload=None, theReadLen=None, theTransaction=None):

        if theTransaction == None:
            #print "Sending cmd: ", theCmd, "bus:", theBus, "width:", theWidth, "addr:", theAddr, "values: ", thePayload
        
            theTransaction = FemTransaction(cmd=theCmd, bus=theBus, width=theWidth, state=theState, 
                                           addr=theAddr, payload=thePayload, readLen=theReadLen)
        data = theTransaction.encode()
        try:
            self.femSocket.sendall(data)
        except socket.error, (errno, sockErrStr):
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError("Socket error %d : %s" % (errno, sockErrStr), FemClientError.ERRNO_SOCK_ERROR)
        
    def recv(self):
        initRecvLen = FemTransaction.headerSize()
        try:
            data = self.femSocket.recv(initRecvLen)
        except socket.error, (errno, sockErrStr):
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError("Socket error %d : %s"  % (errno, sockErrStr), FemClientError.ERRNO_SOCK_ERROR)
        
        if not data:
            raise FemClientError("FEM has closed socket connection", FemClientError.ERRNO_SOCK_CLOSED)
        
        response = FemTransaction(encoded=data)
        while response.incomplete:
            payloadRecvLen = response.payloadRemaining
            data = self.femSocket.recv(payloadRecvLen)
            response.append(data)

        return response
       
    def write(self, theBus, theWidth, theAddr, thePayload):
        self.send(theCmd=FemTransaction.CMD_ACCESS, theBus=theBus, 
                 theWidth=theWidth, theState=FemTransaction.STATE_WRITE, 
                 theAddr=theAddr, thePayload=thePayload)
        response = self.recv()
        return response.payload
        
    def read(self, theBus, theWidth, theAddr, theReadLen):
        self.send(theCmd=FemTransaction.CMD_ACCESS, theBus=theBus,
                  theWidth=theWidth, theState=FemTransaction.STATE_READ,
                  theAddr=theAddr, theReadLen=theReadLen)
        response = self.recv()
        return response.payload
    
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
        response = self.write(bus, width, address, payload) 
        return response
  
    def commandSend(self, theCmd):
        
        cmd   = FemTransaction.CMD_INTERNAL
        bus   = FemTransaction.BUS_RAW_REG
        width = FemTransaction.WIDTH_LONG
        state = FemTransaction.STATE_WRITE
        addr  = theCmd
        self.send(cmd, bus, width, state, addr)
        response = self.recv()
        return response
    
    def rdmaWrite(self, theAddr, thePayload):
                
        bus   = FemTransaction.BUS_RDMA
        width = FemTransaction.WIDTH_LONG
        ack = self.write(bus, width, theAddr, thePayload)
        #TODO: check if response is OK
        return ack
    
    def rdmaRead(self, theAddr, theReadLen):
        
        bus = FemTransaction.BUS_RDMA
        width = FemTransaction.WIDTH_LONG
        values = self.read(bus, width, theAddr, theReadLen)
        return values
    
    def i2cWrite(self, theAddr, thePayload):
        
        bus   = FemTransaction.BUS_I2C
        width = FemTransaction.WIDTH_BYTE
        ack = self.write(bus, width, theAddr, thePayload)
        return ack
    
    def i2cRead(self, theAddr, theReadLen):
        
        bus   = FemTransaction.BUS_I2C
        width = FemTransaction.WIDTH_BYTE
        values = self.read(bus, width, theAddr, theReadLen)
        return values
    
    def acquireSend(self, theCmd, theMode=None, theBufSize=None, theBufCount=None, theNumAcqs=None):
        
        payload=None
        
        if theCmd == FemTransaction.CMD_ACQ_CONFIG:
            acqConfig = FemAcquireConfig(theMode, theBufSize, theBufCount, theNumAcqs)
            payload = acqConfig.decode()
            pass       
        
        cmd   = FemTransaction.CMD_ACQUIRE
        bus   = FemTransaction.BUS_UNSUPPORTED
        width = FemTransaction.WIDTH_LONG
        state = FemTransaction.STATE_UNSUPPORTED
        addr  = theCmd

        self.send(theCmd=cmd, theBus=bus, theWidth=width, theState=state, theAddr=addr, thePayload=payload)
        response = self.recv()
        return response.payload
    
    def close(self):
        self.femSocket.close()
        self.femSocket = None
        
    
    
