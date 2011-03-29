'''
Created on 22 Mar 2011

@author: tcn
'''
import SocketServer
from femApi.femHeader import FemHeader
import binascii

class FemEmulator(SocketServer.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.femHdr = FemHeader()
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return
        
    def setup(self):
        print self.client_address, 'connected'
        #self.request.send('hi ' + str(self.client_address) + '\n')
        
    def handle(self):
        while(1):
            data = self.request.recv(1024)
            if not data:
                return
            print self.client_address, 'sent', binascii.hexlify(data), 'size', len(data)
            #self.femHdr.setBinary(data)
            #print self.client_address, 'sent', self.femHdr.getValues()
            #self.request.send(data)
            
    def finish(self):
        print self.client_address, 'disconnected'
        #self.request.send('bye ' + str(self.client_address) + '\n')
    
if __name__ == '__main__':
    server = SocketServer.ThreadingTCPServer(('0.0.0.0', 5000), FemEmulator)
    server.serve_forever()