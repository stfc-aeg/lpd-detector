'''
    LpdPowerControl - parser providing control of low voltage, high voltage and high voltage bias [via I2C]
    
    @author: ckd
'''

from __future__ import print_function

import argparse, sys

from lpd.device import LpdDevice


class LpdPowerControl(object):

    # Values for control bits
    OFF = 0
    ON  = 1
    
    def __init__(self, hostAddr=None, port=None, asicModule=None, legacyPowerCard=False):

#        moduleType = ""
        if asicModule == 0:
#            moduleType = "supermodule"
            self.numberPowerCards = 2
        elif asicModule == 1:
#            moduleType = "standalone fem"
            self.numberPowerCards = 1
        elif asicModule == 2:
#            moduleType = "2-tile"
            self.numberPowerCards = 1
#        print "~+~+~ Connecting to host: %s, port: %i, asicmodule: %s" % (hostAddr, port, moduleType), " ~+~+~"

        # Call superclass initialising function
        self.theDevice = LpdDevice()
        rc = self.theDevice.open(hostAddr, port, asicModuleType=asicModule, legacyPowerCard=legacyPowerCard)
        
        if rc != LpdDevice.ERROR_OK:
            print("Failed to open FEM device: %s" % (self.theDevice.errorStringGet()))
            sys.exit()
        
    def updateQuantity(self, quantity, newValue):
        ''' 
        update the ASIC parameter 'quantity' with the value ' newValue'
        '''
        for powerCard in range(self.numberPowerCards):
            
            paramName = quantity + str(powerCard)
            rc = self.theDevice.paramSet(paramName, newValue)
            
            if rc!= self.theDevice.ERROR_OK:
                print("Unable to set parameter '%s' to '%d', Error number %d: %s." % (paramName, newValue, rc, self.theDevice.errorStringGet()))

    def close(self):
        print("Closing down Fem connection..")
        self.theDevice.close()


if __name__ == "__main__":

    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="To switch on the LV, the syntax is: 'python LpdPowerControl.py --lv 1' ",
                                     epilog="Note: If the script is executed without any given flag,  the corresponding supply will be switched OFF. Sadly, this is a limitation inherit to Python's parse module.")

    parser.add_argument("--asicmodule", help="Set ASIC Module (0=supermodule, 1=fem, 2=2-tile system)", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--femhost",    help="Set fem host IP (e.g.  192.168.2.2)",         type=str, default='192.168.2.2')
    parser.add_argument("--femport",    help="Set fem port (eg 61649)",                     type=int, default=6969)
    parser.add_argument("--lv",         help="Switch LV on (1) or off (0)", type=int, choices=[0, 1], default=0)
    parser.add_argument("--hv",         help="Switch HV on (1) or off (0)", type=int, choices=[0, 1], default=0)
    parser.add_argument("--hvbias",     help="Set HV bias level (in volts) - BIAS ONLY CHANGED: if HV switched off (using --hv 0 flag)", type=int, default=-1)
    parser.add_argument("--legacy",         help="Use legacy power card support",       action='store_true')
    
    args = parser.parse_args()

    # Define FEM IP address, port etc
    host        = args.femhost
    port        = args.femport
    asicModule  = args.asicmodule
    lv          = args.lv
    hv          = args.hv
    hvbias      = args.hvbias
    legacy      = args.legacy

    # Connect to fem..
    powerControl = LpdPowerControl(host, port, asicModule, legacy)
    
    # Only use if they decided to switch off lv but switch on hv
    if (lv == 0) and (hv):
        print("Illegal choice: You decided to switch on HV while switching off LV; Aborting..")
        powerControl.close()
        sys.exit()
    if (lv == 1) and (hv == 1) and (hvbias > -1):
        print("Illegal choice: Switching on LV, HV and changing HV bias; Aborting..")
        powerControl.close()
        sys.exit()
    
    # Execute according to supplied flags
    if lv:
        print("Switching: LV on, ", end=' ')
        powerControl.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.ON)
        
        # Is HV set to be switched on?
        if hv:
            # Yes - switch HV on
            print("HV on..")
            powerControl.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.ON)

        else:
            # No - switch HV off
            print("HV off.. ", end=' ')
            powerControl.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)

            # Change bias, if bias specified
            if hvbias > -1:
                print("Setting HV bias to ", hvbias, " V..")
                powerControl.updateQuantity(quantity='sensorBias', newValue=hvbias)
            else:
                print("")
    else:
        # Switch off lv, BUT Switch off HV first
        
        print("Switching: HV off, ", end=' ')
        powerControl.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)

        print("LV off.. ", end=' ')
        powerControl.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.OFF)
        
        if hvbias > -1:
            print("Setting HV bias to ", hvbias, " V..")
            powerControl.updateQuantity(quantity='sensorBias', newValue=hvbias)
        else:
            print("")

