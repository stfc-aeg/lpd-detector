'''
Created on Feb 2, 2012

@author: tcn45
'''

import optparse

femHost = '192.168.0.14'
femPort = 6969
femTimeout = 1.0

def parseArgs():
    
    global femHost, femPort, femTimeout
    
    parser = optparse.OptionParser()
    parser.add_option("-a", "--address", dest="address", type="string", default=None,
                      help="set FEM host IP address")
    parser.add_option("-p", "--port", dest="port", type="int", default=None,
                      help="set FEM host port")
    parser.add_option("-t", "--timeout", dest="timeout", type="float", default=None,
                      help="set FEM transaction timeout")
    
    (options, args) = parser.parse_args()
    
    if options.address != None:
        femHost = options.address
        
    if options.port != None:
        femPort = options.port
        
    if options.timeout != None:
        femTimeout = options.timeout

    return args