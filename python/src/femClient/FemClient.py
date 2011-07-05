'''
Created on 22 Mar 2011

@author: tcn
'''

import socket
from femApi.femTransaction import FemTransaction

class FemClient():
    '''
    classdocs
    '''

    def __init__(self, hostAddr=None):
        print "Connecting to FEM at", hostAddr
        self.femSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.femSocket.connect(hostAddr)
    
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
        
    def read(self, theBus, theWidth, theAddr, theReadLen):
        self.send(theCmd=FemTransaction.CMD_ACCESS, theBus=theBus,
                  theWidth=theWidth, theState=FemTransaction.STATE_READ,
                  theAddr=theAddr, theReadLen=theReadLen)
        values = self.recv()
        return values
          
    def close(self):
        self.femSocket.close()
        self.femSocket = None
        
    
    