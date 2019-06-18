"""
    LpdSuperModulePowerStatus - Readout both power cards from a supermodule system

    Author: ckd27546
"""
from __future__ import print_function

from lpd.device import LpdDevice
import sys, argparse

def powerCardTest(femHost, femPort, legacyPowerCard):
    
    theDevice = LpdDevice()
    
    rc = theDevice.open(femHost, femPort, asicModuleType=0, legacyPowerCard=legacyPowerCard)

    if rc != LpdDevice.ERROR_OK:
        print("Failed to open FEM device: %s" % (theDevice.errorStringGet()))
        return
    else:
        print("====================== %s:%s ======================" % (femHost, femPort))
    
    numSensors = 16
    numPowerCards = 2
    paramTypes = ['Temp', 'Voltage', 'Current']
 
    # Count how many error encountered
    errorCount = 0
   
    results = {}
    
    for sensor in range(numSensors):
        
        for paramType in paramTypes:
            paramName = 'sensor' + str(sensor) + paramType
            
            (rc, val) = theDevice.paramGet(paramName)

            results[paramName] = val
            if rc != LpdDevice.ERROR_OK:    
                print("Unable to read parameter %s rc=%d: %s" % (paramName, rc, theDevice.errorStringGet()))
                errorCount += 1
                if errorCount > 2:
                    print("Detected three errors, aborting..")
                    theDevice.close()
                    sys.exit()
    
    paramTypes = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                  'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                  'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']
    
    for powerCard in range(numPowerCards):
        
        for paramType in paramTypes:
            paramName = paramType + str(powerCard)
            
            (rc, val) = theDevice.paramGet(paramName)

            results[paramName] = val
            if rc != LpdDevice.ERROR_OK:    
                print("Unable to read parameter %s rc=%d: %s" % (paramName, rc, theDevice.errorStringGet()))
                errorCount += 1
                if errorCount > 2:
                    print("Found three errors, aborting..")
                    theDevice.close()
                    sys.exit()
     
    print("    ~+~+~+~+~+~+~ RHS ~+~+~+~+~+~+~+~+~ LHS ~+~+~+~+~+~+~")
    
    print("Status:")
    print("    Low voltage  = ", "on." if results['asicPowerEnable1'] else 'off.', '\t\t', end=' ')
    print("    Low voltage  = ", "on." if results['asicPowerEnable0'] else 'off.')
    print("    High voltage = ", "on." if results['sensorBiasEnable1'] else 'off.', '\t\t', end=' ')
    print("    High voltage = ", "on." if results['sensorBiasEnable0'] else 'off.')
        
    print("    HV setting: %5.2f" % results['sensorBias1'] , "V", "\t\t    HV setting: %5.2f" % results['sensorBias0'], "V")

    print("Flags:") 
    print("    Fault Flag        = ", results['powerCardFault1'],       "\t\t    Fault Flag        = ", results['powerCardFault0'])
    print("    Fem Status   Trip = ", results['powerCardFemStatus1'],   "\t\t    Fem Status   Trip = ", results['powerCardFemStatus0'])
    print("    External     Trip = ", results['powerCardExtStatus1'],   "\t\t    External     Trip = ", results['powerCardExtStatus0'])
    print("    Over current Trip = ", results['powerCardOverCurrent1'], "\t\t    Over current Trip = ", results['powerCardOverCurrent0'])
    print("    Over temp    Trip = ", results['powerCardOverTemp1'],    "\t\t    Over temp    Trip = ", results['powerCardOverTemp0'])
    print("    Undertemp    Trip = ", results['powerCardUnderTemp1'],   "\t\t    Undertemp    Trip = ", results['powerCardUnderTemp0'], "\n")

    # Display temperature readings from PSU Card and Sensors
    print("Temperature readings:")
    print('   PSU Card Temp:  %.2f' %   results['powerCardTemp1'], '  C', end=' ')
    print('\t\t   PSU Card Temp: %.2f' % results['powerCardTemp0'], '  C')

    print('   Sensor  8 Temp: %5.2f' %  results['sensor8Temp'], '  C', '\t\t   Sensor 0 Temp: %5.2f' % results['sensor0Temp'], '  C')
    print('   Sensor  9 Temp: %5.2f' %  results['sensor9Temp'], '  C', '\t\t   Sensor 1 Temp: %5.2f' % results['sensor1Temp'], '  C')
    print('   Sensor 10 Temp: %5.2f' % results['sensor10Temp'], '  C', '\t\t   Sensor 2 Temp: %5.2f' % results['sensor2Temp'], '  C')
    print('   Sensor 11 Temp: %5.2f' % results['sensor11Temp'], '  C', '\t\t   Sensor 3 Temp: %5.2f' % results['sensor3Temp'], '  C')
    print('   Sensor 12 Temp: %5.2f' % results['sensor12Temp'], '  C', '\t\t   Sensor 4 Temp: %5.2f' % results['sensor4Temp'], '  C')
    print('   Sensor 13 Temp: %5.2f' % results['sensor13Temp'], '  C', '\t\t   Sensor 5 Temp: %5.2f' % results['sensor5Temp'], '  C')
    print('   Sensor 14 Temp: %5.2f' % results['sensor14Temp'], '  C', '\t\t   Sensor 6 Temp: %5.2f' % results['sensor6Temp'], '  C')
    print('   Sensor 15 Temp: %5.2f' % results['sensor15Temp'], '  C', '\t\t   Sensor 7 Temp: %5.2f' % results['sensor7Temp'], '  C')

    # Display Fem, Digital, sensors voltages and current
    print("\nOutputs: ")

    print("   V FEM      : %.2f" % results['femVoltage1'], " V ", "%.2f" % results['femCurrent1'], " A", end=' ')
    print("\t   V FEM      : %.2f" % results['femVoltage0'], " V ", "%.2f" % results['femCurrent0'], " A")
    print("   V Digital  : %.2f" % results['digitalVoltage1'], " V ", "%.2f" % results['digitalCurrent1'], " mA", end=' ')
    print("\t   V Digital  : %.2f" % results['digitalVoltage0'], " V ", "%.2f" % results['digitalCurrent0'], " mA\n")

    print("   V Sensor 8  : %.2f"  % results['sensor8Voltage'], " V ", "%.2f" % results['sensor8Current'], " A", end=' ')
    print("\t   V Sensor 0 : %.2f" % results['sensor0Voltage'], " V ", "%.2f" % results['sensor0Current'], " A")
    print("   V Sensor 9  : %.2f"  % results['sensor9Voltage'], " V ", "%.2f" % results['sensor9Current'], " A", end=' ')
    print("\t   V Sensor 1 : %.2f" % results['sensor1Voltage'], " V ", "%.2f" % results['sensor1Current'], " A")
    print("   V Sensor 10 : %.2f"  % results['sensor10Voltage']," V ", "%.2f" % results['sensor10Current']," A", end=' ')
    print("\t   V Sensor 2 : %.2f" % results['sensor2Voltage'], " V ", "%.2f" % results['sensor2Current'], " A")
    print("   V Sensor 11 : %.2f"  % results['sensor11Voltage']," V ", "%.2f" % results['sensor11Current']," A", end=' ')
    print("\t   V Sensor 3 : %.2f" % results['sensor3Voltage'], " V ", "%.2f" % results['sensor3Current'], " A")
    print("   V Sensor 12 : %.2f"  % results['sensor12Voltage']," V ", "%.2f" % results['sensor12Current']," A", end=' ')
    print("\t   V Sensor 4 : %.2f" % results['sensor4Voltage'], " V ", "%.2f" % results['sensor4Current'], " A")
    print("   V Sensor 13 : %.2f"  % results['sensor13Voltage']," V ", "%.2f" % results['sensor13Current']," A", end=' ')
    print("\t   V Sensor 5 : %.2f" % results['sensor5Voltage'], " V ", "%.2f" % results['sensor5Current'], " A")
    print("   V Sensor 14 : %.2f"  % results['sensor14Voltage']," V ", "%.2f" % results['sensor14Current']," A", end=' ')
    print("\t   V Sensor 6 : %.2f" % results['sensor6Voltage'], " V ", "%.2f" % results['sensor6Current'], " A")
    print("   V Sensor 15 : %.2f"  % results['sensor15Voltage']," V ", "%.2f" % results['sensor15Current']," A", end=' ')
    print("\t   V Sensor 7 : %.2f" % results['sensor7Voltage'], " V ", "%.2f" % results['sensor7Current'], " A\n")

    print("   HV Bias    : %.2f" % results['sensorBiasVoltage1'], " V ", end=' ')
    print("%.2f" % results['sensorBiasCurrent1'], " uA", end=' ')
    print("\t   HV Bias    : %.2f" % results['sensorBiasVoltage0'], " V ", end=' ')
    print("%.2f" % results['sensorBiasCurrent0'], " uA")

    print("-- -- -- -- -- -- -- -- --")

    print("Closing Fem connection.. ")        
    theDevice.close()

if __name__ == '__main__':
    
    # Define default values
    femHost = '192.168.2.2'
    femPort = 6969
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="LpdSuperModulePowerStatus.py - Readout power card data from a FEM. ",
                                     epilog="Default: femhost=192.168.2.2, femport=6969")

    parser.add_argument("--femhost",        help="Set fem host IP (e.g 192.168.2.2)",   type=str, default=femHost)
    parser.add_argument("--femport",        help="Set fem port (eg 6969)",              type=int, default=femPort)
    parser.add_argument("--legacy",         help="Use legacy power card support",       action='store_true')
    
    args = parser.parse_args()

    host     = args.femhost
    port     = args.femport
    legacy   = args.legacy

    powerCardTest(host, port, legacy)
    
