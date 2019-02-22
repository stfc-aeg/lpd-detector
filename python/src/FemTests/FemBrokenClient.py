'''
Created on Oct 17, 2011

@author: tcn45
'''

from FemClient.FemClient import *
import binascii

class FemBrokenClient(FemClient):
    '''
    classdocs
    '''


    def __init__(self, hostAddr=None, timeout=None):
        '''
        Constructor
        '''
        FemClient.__init__(self, hostAddr, timeout)
        
    def sendWithoutPayload(self, theTransaction):
        '''
        Sends a transaction to the FEM without the specified payload
        '''
        data = theTransaction.encode()
        headerLen = theTransaction.headerSize()
        
        self.femSocket.send(data[:headerLen])
        
    def sendPartialPayload(self, theTransaction, partialLen):
        '''
        Sends a transaction to the FEM with a partial payload, specified in partialLen
        '''
        data = theTransaction.encode()
        headerLen = theTransaction.headerSize()        
        partialLen = partialLen + headerLen
        
        self.femSocket.send(data[:partialLen])
        
    def sendExcessPayload(self, theTransaction, excessLen):
        ''' 
        Sends a transaction to the FEM with excess payload, padded with garbage bytes
        '''
        data = theTransaction.encode()
        data = data + ''.join(['a' for i in xrange(excessLen)])

        self.femSocket.send(data)