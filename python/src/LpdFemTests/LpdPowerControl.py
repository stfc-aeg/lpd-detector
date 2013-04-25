'''
    LpdPowerControl - parser providing control to low voltage, high voltage and high voltage bias
    
    @author: ckd
'''

import argparse

from FemClient.FemClient import  *
from FemApi.FemTransaction import FemTransaction

from LpdDevice.LpdDevice import LpdDevice


class LpdPowerControl(object):

    
    # Values for control bits
    OFF = 0
    ON  = 1
    
    def __init__(self, hostAddr=None, port=None, asicModule=None):

        print "~+~+~ Connecting to host: %s, port: %i, asicmodule: " % (hostAddr, port),
        if asicModule == 0:
            print "supermodule",
            self.numberPowerCards = 2
        elif asicModule == 1:
            print "standalone fem",
            self.numberPowerCards = 1
        elif asicModule == 2:
            print "2-tile",
            self.numberPowerCards = 1
        else:
            print "Unknown!",   # Value not allowed by parser
            self.numberPowerCards = 0
        print " ~+~+~"
    
        # Call superclass initialising function
        self.theDevice = LpdDevice()
        rc = self.theDevice.open(hostAddr, port, asicModuleType=asicModule)
        
        if rc != LpdDevice.ERROR_OK:
            print "Failed to open FEM device: %s" % (self.theDevice.errorStringGet())
            sys.exit()
        

    def updateQuantity(self, quantity, newValue):
        ''' 
        update the ASIC parameter 'quantity' with the value ' newValue'
        '''
        for powerCard in range(self.numberPowerCards):
            
            paramName = quantity + str(powerCard)
            rc = self.theDevice.paramSet(paramName, newValue)
            
            if rc!= self.theDevice.ERROR_OK:
                print "Unable to set parameter '%s' to '%d', Error number %d: %s." % (paramName, newValue, rc, self.theDevice.errorStringGet())

    def close(self):
        print "Closing down Fem connection.."
        self.theDevice.close()



if __name__ == "__main__":

    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="To switch on the LV, the syntax is: 'python LpdI2ctest.py --lv 1' ",
                                     epilog="Note: If the script is executed without any given flag,  the corresponding supply will be switched OFF. Sadly, this is a limitation inherit to Python's parse module.")

    parser.add_argument("--asicmodule", help="Set ASIC Module (0=supermodule, 1=fem, 2=2-tile system)", type=int, choices=[0, 1, 2])
    parser.add_argument("--lv", help="switch LV on (1) or off (0)", type=int, choices=[0, 1])
    parser.add_argument("--hv", help="switch HV on (1) or off (0)", type=int, choices=[0, 1])
    parser.add_argument("--hvbias", help="set HV bias level (in volts) - BIAS ONLY CHANGED: if HV switched off (using --hv 0 flag)", type=int)
    args = parser.parse_args()
    
    # Define FEM IP address and port
    host = '192.168.2.2'
    # Determine name of current machine
    fullDomainName = socket.gethostname()
    # Only need hostname, not domain part
    hostName = fullDomainName.partition('.')[0]

    port = 6969

    asicModule = -1
    if args.asicmodule is not None:
        asicModule =  args.asicmodule

    hvBias = 0
    if args.hvbias is not None:
        hvBias = args.hvbias

    # Connect to fem..
    thisFem = LpdPowerControl(host, port, asicModule)
    
    # Only use if they decided to switch off lv but switch on hv
    if (args.lv == 0) and (args.hv):
        print "Illegal choice: You decided to switch on HV while switching off LV; Aborting.."
        sys.exit()
    if (args.lv == 1) and (args.hv == 1) and (args.hvbias != None):
        print "Illegal choice: Switching on LV, HV and changing HV bias; Aborting.."
        sys.exit()
            
    # Execute according to supplied flags
    if args.lv:
        print "Switching low voltage on.."
        thisFem.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.ON)
        
        # Is HV set to be switched on?
        if args.hv:
            # Yes - switch HV on
            print "Switching high voltage on.."
            thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.ON)

        else:
            # No - switch HV off
            print "Switching high voltage off.. "
            thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)

            # Change bias, if bias specified
            if args.hvbias > -1:
                print "Changing HV bias to ", args.hvbias, " V.."
                thisFem.updateQuantity(quantity='sensorBias', newValue=hvBias)
    else:
        # Switch off lv, BUT Switch off HV first
        
        print "Switching high voltage off.. "
        thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)

        print "Switching low voltage off.. "
        thisFem.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.OFF)
        
        if args.hvbias > -1:
            print "Changing HV bias to ", args.hvbias, " V.."
            thisFem.updateQuantity(quantity='sensorBias', newValue=hvBias)
            
    # Close fem connection
    thisFem.close()
    
    