'''
Created on 22 Mar 2011

@author: tcn
'''

from __future__ import print_function

import socket
from FemApi.FemTransaction import FemTransaction
from FemApi.FemConfig import FemConfig
from FemApi.FemAcquireConfig import FemAcquireConfig

import binascii
from types import *
import sys

class FemClientError(Exception):
    
    ERRNO_NO_ERROR       = 0
    ERRNO_SOCK_CLOSED    = 1
    ERRNO_SOCK_ERROR     = 2
    ERRNO_WRITE_MISMATCH = 3
    ERRNO_READ_MISMATCH  = 4
    
    def __init__(self, msg, errno=ERRNO_NO_ERROR):
        self.msg = msg
        self.errno = errno
        
    def __str__(self):
        return str(self.msg)
    
class FemClient(object):
    '''
    classdocs
    '''

    def __init__(self, hostAddr=None, timeout=None):
        #print("Connecting to FEM at", hostAddr)
        self.femSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.femSocket.settimeout(timeout)
        self.femSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024)
        try:
            self.femSocket.connect(hostAddr)
        except socket.timeout:
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError("Socket connection timed out")

        except socket.error as e:
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError(str(e))
    
    def send(self, theCmd=None, theBus=None, theWidth=None, theState=None, 
             theAddr=None, thePayload=None, theReadLen=None, theTransaction=None):

        if theTransaction == None:
            #print("Sending cmd: ", theCmd, "bus:", theBus, "width:", theWidth, "addr:", theAddr, "values: ", thePayload)
        
            theTransaction = FemTransaction(cmd=theCmd, bus=theBus, width=theWidth, state=theState, 
                                           addr=theAddr, payload=thePayload, readLen=theReadLen)
        data = theTransaction.encode()
        try:
            self.femSocket.sendall(data)
        except socket.error as e:
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError("Socket error on send: %s" % (str(e)), FemClientError.ERRNO_SOCK_ERROR)
        
    def recv(self):
        initRecvLen = FemTransaction.headerSize()
        try:
            data = self.femSocket.recv(initRecvLen)
        except socket.error as e:
            if self.femSocket:
                self.femSocket.close()
            raise FemClientError("Socket error on recv: %s"  % (str(e)), FemClientError.ERRNO_SOCK_ERROR)
        
        if not data:
            raise FemClientError("FEM has closed socket connection", FemClientError.ERRNO_SOCK_CLOSED)
        
        response = FemTransaction(encoded=data)
        #print("Response payload length:", response.payloadLen)
        
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

        # Test if the read transaction was NACKed. If so, decode the error response
        # from the FEM and raise a matching exception
        if response.state & FemTransaction.STATE_NO_ACKNOWLEDGE:
            (errorNo, errorStr) = response.decodeErrorResponse()
            raise FemClientError("FEM write transaction failed: %s" % errorStr, errorNo)

        # Determine payload length - len() only works on a sequence object so trap 
        # any exception and then default length to 1
        try:
            payloadLen = len(thePayload)
        except TypeError:
            payloadLen = 1
            
        # Check that the write length acknowledged matches the length of the payload
        if payloadLen != response.payload[0]:
            raise FemClientError("FEM write transaction length mismatch: request %d, got %d" % (payloadLen, response.payload[0]), 
                                 FemClientError.ERRNO_READ_MISMATCH)
                    
    def read(self, theBus, theWidth, theAddr, theReadLen):
        self.send(theCmd=FemTransaction.CMD_ACCESS, theBus=theBus,
                  theWidth=theWidth, theState=FemTransaction.STATE_READ,
                  theAddr=theAddr, theReadLen=theReadLen)
        response = self.recv()
        
        # Test if the read transaction was NACKed. If so, decode the error response
        # from the FEM and raise a matching exception
        if response.state & FemTransaction.STATE_NO_ACKNOWLEDGE:
            (errorNo, errorStr) = response.decodeErrorResponse()
            raise FemClientError("FEM read transaction failed: %s" % errorStr, errorNo)

        # Check if the read length requested matches that in the response payload
        if theReadLen != response.payload[0]:
            raise FemClientError("FEM read transaction length mismatch: request %d, got %d" % (theReadLen, response.payload[0]), 
                                 FemClientError.ERRNO_READ_MISMATCH)
            
        # Return the read values excluding the read length
        return response.payload[1:]
    
    def configRead(self):
        
        bus     = FemTransaction.BUS_EEPROM
        width   = FemTransaction.WIDTH_BYTE
        address = FemConfig.configAddress
        length  = FemConfig.configSize()
        values = self.read(bus, width, address, length)

        if sys.version_info > (3,):
            encoded = bytes(values)
        else:
            encoded = ''.join([chr(x) for x in values])

        theConfig = FemConfig(encoded=encoded)
        
        return theConfig
    
    def configWrite(self, theConfig=None):
        
        bus     = FemTransaction.BUS_EEPROM
        width   = FemTransaction.WIDTH_BYTE
        address = FemConfig.configAddress
        payload = bytearray(theConfig.encode())
        self.write(bus, width, address, payload) 
  
    def commandSend(self, theCmd, theArg = 0):
        
        cmd   = FemTransaction.CMD_INTERNAL
        bus   = theArg
        width = FemTransaction.WIDTH_LONG
        state = FemTransaction.STATE_WRITE
        addr  = theCmd
        self.send(cmd, bus, width, state, addr)
        response = self.recv()
        return response
    
    def rdmaWrite(self, theAddr, thePayload):
                
        bus   = FemTransaction.BUS_RDMA
        width = FemTransaction.WIDTH_LONG
        self.write(bus, width, theAddr, thePayload)
    
    def rdmaRead(self, theAddr, theReadLen):
        
        bus = FemTransaction.BUS_RDMA
        width = FemTransaction.WIDTH_LONG
        values = self.read(bus, width, theAddr, theReadLen)
        return values
 
    def rawWrite(self, theAddr, thePayload):
                
        bus   = FemTransaction.BUS_RAW_REG
        width = FemTransaction.WIDTH_LONG
        self.write(bus, width, theAddr, thePayload)
       
    def rawRead(self, theAddr, theReadLen):
        
        bus = FemTransaction.BUS_RAW_REG
        width = FemTransaction.WIDTH_LONG
        values = self.read(bus, width, theAddr, theReadLen)
        return values
    
    def i2cWrite(self, theAddr, thePayload):
        
        bus   = FemTransaction.BUS_I2C
        width = FemTransaction.WIDTH_BYTE
        self.write(bus, width, theAddr, thePayload)
    
    def i2cRead(self, theAddr, theReadLen):
        
        bus   = FemTransaction.BUS_I2C
        width = FemTransaction.WIDTH_BYTE
        values = self.read(bus, width, theAddr, theReadLen)
        return values
    
    def acquireSend(self, theCmd, theMode=None, theBufSize=None, theBufCount=None, theNumAcqs=None, theCoalesce=None):
        
        payload=None
        
        if theCmd == FemTransaction.CMD_ACQ_CONFIG:
            acqConfig = FemAcquireConfig(theMode, theBufSize, theBufCount, theNumAcqs, theCoalesce)
            payload = acqConfig.decode()
            pass       
        
        cmd   = FemTransaction.CMD_ACQUIRE
        bus   = FemTransaction.BUS_UNSUPPORTED
        width = FemTransaction.WIDTH_LONG
        state = FemTransaction.STATE_UNSUPPORTED
        addr  = theCmd

        self.send(theCmd=cmd, theBus=bus, theWidth=width, theState=state, theAddr=addr, thePayload=payload)
        response = self.recv()
        if response.state & FemTransaction.STATE_NO_ACKNOWLEDGE:
            (errorNo, errorStr) = response.decodeErrorResponse()
            raise FemClientError("FEM acquire command send failed: %s" % errorStr, errorNo)

        return response.payload
    
    def personalitySend(self, thePersCmd, thePayload=None):
        
        cmd   = FemTransaction.CMD_PERSONALITY
        bus   = FemTransaction.BUS_RAW_REG
        width = FemTransaction.WIDTH_LONG
        state = FemTransaction.STATE_WRITE
        addr  = thePersCmd
        
        self.send(cmd, bus, width, state, addr, thePayload)
        response = self.recv()
        return response
    
    def close(self):
        self.femSocket.close()
        self.femSocket = None
        
    # jac aug 2017
    def directWrite(self, theAddr, thePayload):
                
        bus   = FemTransaction.BUS_RAW_REG
        width = FemTransaction.WIDTH_BYTE
        self.write(bus, width, theAddr, thePayload)
    
    
