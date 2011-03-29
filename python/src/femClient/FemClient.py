'''
Created on 22 Mar 2011

@author: tcn
'''

import socket
import binascii
from femApi.femHeader import FemHeader
from femApi.femTransaction import FemTransaction

class FemClient():
    '''
    classdocs
    '''

    def __init__(self, hostAddr=None):
        print "Connecting to FEM at", hostAddr
        self.femSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.femSocket.connect(hostAddr)
    
    def send(self, values):
        print "Sending values", values
        femHdr = FemHeader(values)
        data = femHdr.getBinary()
        self.femSocket.send(data)
        data = self.femSocket.recv(1024)
        femHdr.setBinary(data)
        values = femHdr.getValues()
        print "Received raw ", binascii.hexlify(data)
        print "Received vals", values 
    
    def write(self, theCmd, theAddr, theValues):
        print "Writing cmd: ", theCmd, "addr:", theAddr, "values: ", theValues
        writeTransaction = FemTransaction(theCmd, theAddr, theValues)
        data = writeTransaction.getBinary()
        self.femSocket.send(data)
        #data = self.femSocket.recv(1024)
        #print "Received raw ", binascii.hexlify(data)
          
    def close(self):
        self.femSocket.close()
        self.femSocket = None
        
    
    