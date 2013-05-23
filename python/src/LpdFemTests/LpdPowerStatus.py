'''
    Use the API to read out all sensors connected through I2C bus
    
    Author: ckd27546
'''

from LpdDevice.LpdDevice import LpdDevice
import sys

def LpdPowerStatus():
    
    theDevice = LpdDevice()
    
    rc = theDevice.open('192.168.2.2', 6969, asicModuleType=2)  # 0=supermodule, 1=fem, 2=2 tile
    
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return

    paramTypes = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                  'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                  'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']

    # Count how many error encountered
    errorCount = 0

    results = {}
    for powerCard in range(1):
        
        for paramType in paramTypes:
            paramName = paramType + str(powerCard)
            
            (rc, val) = theDevice.paramGet(paramName)

            results[paramName] = val
            if rc != LpdDevice.ERROR_OK:    
                print "Unable to read parameter %s rc=%d: %s" % (paramName, rc, theDevice.errorStringGet())
                errorCount += 1
                if errorCount > 2:
                    print "Detected three errors, aborting.."
                    theDevice.close()
                    sys.exit()

    paramTypes = ['Temp', 'Voltage', 'Current']
    numSensors = 2
    
    for sensor in range(numSensors):
        
        for paramType in paramTypes:
            paramName = 'sensor' + str(sensor) + paramType
            
            (rc, val) = theDevice.paramGet(paramName)

            results[paramName] = val
            if rc != LpdDevice.ERROR_OK:    
                print "Unable to read parameter %s rc=%d: %s" % (paramName, rc, theDevice.errorStringGet())
                errorCount += 1
                if errorCount > 2:
                    print "Found three errors, aborting.."
                    theDevice.close()
                    sys.exit()
    
    print "Status:"
    print "    Low voltage  = ",
    if results['asicPowerEnable0']:
        print "off."
    else:
        print "on."
        
    print "    High voltage = ",
    if results['sensorBiasEnable0']:
        print "off."
    else:
        print "on."

    print "    HV setting: %5.2f" % results['sensorBias0'] , "V"

    print "Flags:" 
    print "    Fault Flag        = ", results['powerCardFault0']
    print "    Fem Status   Trip = ", results['powerCardFemStatus0']
    print "    External     Trip = ", results['powerCardExtStatus0']
    print "    Over current Trip = ", results['powerCardOverCurrent0']
    print "    Over temp    Trip = ", results['powerCardOverTemp0']
    print "    Undertemp    Trip = ", results['powerCardUnderTemp0'], "\n"


    # Display temperature readings from PSU Card and Sensors
    print "Temperature readings:"
    print '   PSU Card Temp:  %.2f' %   results['powerCardTemp0'], '  C'

    print '   Sensor 0 Temp: %5.2f' % results['sensor0Temp'], '  C'
    print '   Sensor 1 Temp: %5.2f' % results['sensor1Temp'], '  C'

    # Display Fem, Digital, sensors voltages and current
    print "\nOutputs: "
    
    print "   V FEM      : %.2f" % results['femVoltage0'], " V ", "%.2f" % results['femCurrent0'], " A"
    print "   V Digital  : %.2f" % results['digitalVoltage0'], " V ", "%.2f" % results['digitalCurrent0'], " mA\n"

    print "   V Sensor 0 : %.2f" % results['sensor0Voltage'], " V ", "%.2f" % results['sensor0Current'], " A"
    print "   V Sensor 1 : %.2f" % results['sensor1Voltage'], " V ", "%.2f" % results['sensor1Current'], " A\n"

    print "   HV Bias    : %.2f" % results['sensorBiasVoltage0'], " V ",
    print "%.2f" % results['sensorBiasCurrent0'], " uA\n"

    print "Closing Fem connection.. "        
    theDevice.close()

if __name__ == '__main__':

    # Modified to only target the RHS Power Card (Two Tile System's power card)      
    LpdPowerStatus()
    
