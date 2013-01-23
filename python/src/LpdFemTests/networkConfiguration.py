'''
Created on 21 January 2013

@author: ckd27546
'''

# Import Python standard modules
import socket

class networkConfiguration(object):
    
    def __init__(self):
        
        # Determine name of current machine
        fullDomainName = socket.gethostname()
        # Only need hostname, not domain part
        hostname = fullDomainName.partition('.')[0]
        
        if hostname == 'te7burntoak':
            
            self.ctrl0SrcIp     = '192.168.2.2'
            self.ctrl0DstIp     = '192.168.2.1'
            self.tenGig0SrcIp   = '192.168.7.2'
            self.tenGig0DstMac  = '00-07-43-06-31-A3'
            self.tenGig0DstIp   = '192.168.7.1'

        elif hostname == 'devgpu02':

            self.ctrl0SrcIp     = '192.168.2.2'
            self.ctrl0DstIp     = '192.168.2.1'
            self.tenGig0SrcIp   = '10.0.0.2'
            self.tenGig0DstMac  = '00-07-43-10-65-A0'
            self.tenGig0DstIp   = '10.0.0.1'

        else:
        
            # What defaults to choose?
            print "No default values yet chosen !"

        # Variables common to all machines
        self.tenGig0SrcMac = '62-00-00-00-00-01'
#        self.tenGig0SrcIp
        self.tenGig0SrcPrt = '8'
        # Target PC:
#        self.tenGig0DstMac
#        self.tenGig0DstIp
        self.tenGig0DstPrt  = '61649'
        
        self.ctrlPrt = 6969
        
        
if __name__ == '__main__':
    
        netConf = networkConfiguration()
        
#        fem.open((netConf.ctrlAddress, netConf.port))
        