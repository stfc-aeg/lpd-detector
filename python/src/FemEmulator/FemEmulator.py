'''
Created on 22 Mar 2011

@author: tcn
'''
import socket
import SocketServer
from FemApi.FemTransaction import FemTransaction
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
        
        timedOut = False
        initRecvLen = FemTransaction.headerSize()
        while(1):

            print 'At top of handle recv loop'
            try:
                data = self.request.recv(initRecvLen)
            except socket.error as (errnum, errstring):
                print 'Got socket exception, errno', errnum, ':', errstring
            else:
                
                if not data:
                    # Client closed connection, return from handler
                    return
    
                print self.client_address, 'sent header', binascii.hexlify(data), 'size', len(data)
                try:
                    theTrans = FemTransaction(encoded=data)
                except:
                    print "Failed to decode transaction header"
                else:
                    while theTrans.incomplete:
                        payloadRecvLen = theTrans.payloadRemaining
                        self.request.settimeout(1.0)
                        timedOut = False
                        try:
                            
                            print 'Waiting for payload length', payloadRecvLen
                            data = self.request.recv(payloadRecvLen)
                            if len(data) == 0:
                                return
                        
                            print self.client_address, 'sent payload', binascii.hexlify(data), 'size', len(data)
                            # TODO deal with data != payloadRecvLen
                            theTrans.append(data)
                            
                        except socket.timeout:
                            print "Payload receive timeout"
                            timedOut = True
                            break
                        
                    if not timedOut:
                        self.decodeTransaction(theTrans)
                        
                    self.request.settimeout(None)
            
    def handle_timeout(self):
        print "."
            
    def finish(self):
        print self.client_address, 'disconnected'
        #self.request.send('bye ' + str(self.client_address) + '\n')
        
    def decodeTransaction(self, theTransaction):
        
        print [hex(field) for field in theTransaction.decode()]
        response = None
    
        # Handle FEM access commands
        if theTransaction.command == FemTransaction.CMD_ACCESS:
            
            if theTransaction.state == FemTransaction.STATE_WRITE:
                for offset in range(len(theTransaction.payload)):
                    self.accessCache[theTransaction.address + offset] = theTransaction.payload[offset]
                    print offset, theTransaction.address + offset, theTransaction.payload[offset], self.accessCache[theTransaction.address + offset]
                
                response = FemTransaction(cmd = theTransaction.command, bus = theTransaction.bus,
                                          width = theTransaction.width, state=FemTransaction.STATE_ACKNOWLEDGE,
                                          addr = theTransaction.address, payload=tuple([1]))
                    
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

        elif theTransaction.command == FemTransaction.CMD_INTERNAL:
       
            print 'Got internal command', hex(theTransaction.address)
            response = FemTransaction(cmd=theTransaction.command, bus = theTransaction.bus, 
                                      width=theTransaction.width, state=FemTransaction.STATE_ACKNOWLEDGE,
                                      addr = theTransaction.address, payload=())
            
        if response:
            data = response.encode()
            self.request.send(data)
                 
if __name__ == '__main__':
    server = SocketServer.TCPServer(('0.0.0.0', 5000), FemEmulator)
    server.serve_forever()