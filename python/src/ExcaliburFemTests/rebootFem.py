#!/bin/env python2.7

from FemNodeList import *
from FemClient.FemClient import *

class Worker(object):

    def __init__(self):
        
        femList = FemNodeList()
        args = femList.parse_args()
        
        for (node, addr) in femList.selected():
            
            print "Connecting to FEM node", node, "at addr", addr, '...',
            try:
                
                # Connect to FEM
                theFem = FemClient((addr, femList.port), femList.timeout)
                
                # Send reboot command (default image)
                print "sending reboot command ...",
                theFem.commandSend(0, 0)
                print "done."
                
                # Close connection
                theFem.close()

            except FemClientError as errString:
                print "Error:", errString
                
            
            
if __name__ == '__main__':
    Worker()