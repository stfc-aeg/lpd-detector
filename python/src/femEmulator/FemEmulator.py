'''
Created on 22 Mar 2011

@author: tcn
'''
import SocketServer
from femApi.femTransaction import FemTransaction
import binascii

class FemEmulator(SocketServer.BaseRequestHandler):
    
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        
        return
        
    def setup(self):
        print self.client_address, 'connected'
        self.accessCache = {}
        #self.request.send('hi ' + str(self.client_address) + '\n')
        
    def handle(self):
        initRecvLen = FemTransaction.headerSize()
        while(1):
            data = self.request.recv(initRecvLen)
            if not data:
                return
            print self.client_address, 'sent', binascii.hexlify(data), 'size', len(data)
            theTrans = FemTransaction(encoded=data)
            while theTrans.incomplete:
                payloadRecvLen = theTrans.payloadRemaining
                data = self.request.recv(payloadRecvLen)
                print self.client_address, 'sent', binascii.hexlify(data), 'size', len(data)
                # TODO deal with data != payloadRecvLen
                theTrans.append(data)
                
            self.decodeTransaction(theTrans)
            
    def finish(self):
        print self.client_address, 'disconnected'
        #self.request.send('bye ' + str(self.client_address) + '\n')
        
    def decodeTransaction(self, theTransaction):
        
        print [hex(field) for field in theTransaction.decode()]
        
        # Handle FEM access commands
        if theTransaction.command == FemTransaction.CMD_ACCESS:
            
            if theTransaction.state == FemTransaction.STATE_WRITE:
                for offset in range(len(theTransaction.payload)):
                    self.accessCache[theTransaction.address + offset] = theTransaction.payload[offset]
                    print offset, theTransaction.address + offset, theTransaction.payload[offset], self.accessCache[theTransaction.address + offset]
                    
            if theTransaction.state == FemTransaction.STATE_READ:
                (payloadWidth, payloadFormat) = FemTransaction.widthEncoding[theTransaction.width]
                result = []
                for offset in range(theTransaction.payload[0]):
                    if self.accessCache.has_key(theTransaction.address + offset):
                        result.append(self.accessCache[theTransaction.address + offset])
                    else:
                        result.append(0)
                print result, len(tuple(result))
                response = FemTransaction(cmd=FemTransaction.CMD_ACCESS, bus = theTransaction.bus,
                                          width=theTransaction.width, state=FemTransaction.STATE_ACKNOWLEDGE,
                                          addr = theTransaction.address, payload=tuple(result))
                data = response.encode()
                self.request.send(data)
                 
if __name__ == '__main__':
    server = SocketServer.ThreadingTCPServer(('0.0.0.0', 5000), FemEmulator)
    server.serve_forever()