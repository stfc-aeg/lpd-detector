'''
rebootFem.py

Reloads Fem from CF ace file.

Created 2017

@author: John Coughlan
'''

######################################################
#
# 24/08/17  John Coughlan
#
# Corrected to permit reboot from ace slot 0
#
# 22/08/17  John Coughlan
#
# Updated to python 3
#   removed import of defaults
#
# 22/08/17  John Coughlan
#
# Added cmd line arguments.
#
######################################################
 
#!/bin/env python2.7

from __future__ import print_function, division

import sys, os.path, time, binascii, argparse

#import ExcaliburFemTests.defaults as defaults
#from . import defaults
import defaults

#from .FemNodeList import *
from FemClient.FemClient import *


def rebootFem(femHost, femPort, slot):

    crc = 0
    
    if (femHost == None):
        print("Error: No FEM IP address specified!")
        sys.exit(1)
    if (slot == None):
        print("Error: No SystemACE slot specified (1-7)!")
        sys.exit(1)
    
    
    if (slot < 0 or slot > 7):
        print("Error: Illegal SystemACE slot number = %d ; permitted 1-7" %(slot))
        sys.exit(1)
        
    # Connect to FEM
    timeout = defaults.femTimeout
    try:
        theFem = FemClient((femHost, femPort), timeout)
    except FemClientError as errString:
        print("Error: FEM connection failed:", errString)
        sys.exit(1)
    
    print("")
    print("SystemACE slot:     ", slot)
    
    # Send reboot command (default image)
    print("sending Reboot command ... ace_slot = %d" %(slot))
    theFem.commandSend(0, slot)
    print("done.")
    
    # Close connection
    theFem.close()

    return
            
            
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="rebootFem.py - Reboots FEM from ace image slot # on CF.", epilog="All parameters other than port are required.")
    parser.add_argument("--ip_addr", "-a", help="Set fem host IP (e.g. 192.168.2.2)", type=str, required=True, action='store')
    parser.add_argument("--udp_port", "-p", help="[Optional] Set fem port (e.g. 6969)", type=int, default=6969, action='store')
    parser.add_argument("--ace_slot", "-s", help="SystemACE slot number", type=int, choices=list(range(8)), required=True, action='store')
    args = parser.parse_args()

    rebootFem(args.ip_addr, args.udp_port, args.ace_slot)
