"""
    LpdPowerTesting - Developing script(s) to test super-module's ASIC (and more?) modules

    Author: ckd27546,    Created: 22/05/2014
"""

from lpd.device import LpdDevice
from power_control import LpdPowerControl
import sys, argparse, time, os

class LpdPowerTesting:
    
    def __init__(self, femHost, femPort):
        
        self.femHost = femHost
        self.femPort = femPort

        self.theDevice = LpdDevice()
        
        rc = self.theDevice.open(self.femHost, self.femPort, asicModuleType=0)
    
        if rc != LpdDevice.ERROR_OK:
            print "Failed to open FEM device: %s" % (self.theDevice.errorStringGet())
            return
        else:
            print "====================== %s:%s ======================" % (self.femHost, self.femPort)
        
    def testPowerCards(self):
        
        numSensors = 16
        numPowerCards = 2
        TVCparamsTypes = ['Temp', 'Voltage', 'Current']
    
        # Count how many error encountered
        errorCount = 0

        initResults = {}    # Store results captured initially
        postResults = {}    # Store results captured after voltages switched on and allowed to stabilise
        TVCparamsTypes = ['Temp', 'Voltage', 'Current']
        
        for sensor in range(numSensors):
            
            for paramType in TVCparamsTypes:
                paramName = 'sensor' + str(sensor) + paramType
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                initResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    print "1.Unable to read parameter %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet())
                    errorCount += 1
                    if errorCount > 2:
                        print "Detected three errors, aborting.."
                        self.theDevice.close()
                        sys.exit()
        
        miscParamTypes = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                      'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                      'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']
        
        for powerCard in range(numPowerCards):
            
            for paramType in miscParamTypes:
                paramName = paramType + str(powerCard)
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                initResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    print "2.Unable to read parameter %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet())
                    errorCount += 1
                    if errorCount > 2:
                        print "Found three errors, aborting.."
                        self.theDevice.close()
                        sys.exit()
    

        asicmodule = 0
        hvbias = 50
        thisFem = LpdPowerControl(self.femHost, self.femPort, asicmodule)
        
        print "Executing first LpdPowerControl script.. (Setting high-voltage)"
    
        print "Switching: HV off, ",    # Possibly redundant?
        thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)
        print "LV off.. ",          # Possibly redundant?
        thisFem.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.OFF)
        print "Setting HV bias to ", hvbias, " V.."
        thisFem.updateQuantity(quantity='sensorBias', newValue=hvbias)
    
        print "Executing second LpdPowerControl script.. (Enabling high and low voltages)"
        
        print "Switching: LV on, ",
        thisFem.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.ON)
        print "HV on.."
        thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.ON)
    
        timeDelay = 3
        print "Done! (Waiting " + str(timeDelay) + " seconds for voltages to stabilise..)\n"

        # Wait couple of seconds for voltages to stabilise
        if __name__ == '__main__':
            # Called as script
            for loop in range(timeDelay):
                print ".",
                sys.stdout.flush()
                time.sleep(1)
            print ""
        else:
            # Called by another class
            time.sleep(3)
    
        
        for sensor in range(numSensors):
            
            for paramType in TVCparamsTypes:
                paramName = 'sensor' + str(sensor) + paramType
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                postResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    print "1.Unable to read parameter %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet())
                    errorCount += 1
                    if errorCount > 2:
                        print "Detected three errors, aborting.."
                        self.theDevice.close()
                        sys.exit()
        
        for powerCard in range(numPowerCards):
            
            for paramType in miscParamTypes:
                paramName = paramType + str(powerCard)
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                postResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    print "2.Unable to read parameter %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet())
                    errorCount += 1
                    if errorCount > 2:
                        print "Found three errors, aborting.."
                        self.theDevice.close()
                        sys.exit()
    
        # Define thresholds
        thresholdSensorTemperature = 49.9
        thresholdSensorCurrent = 1.67
    
        # Analyse the results:
        (issuesRHS, issuesLHS) = (0, 0)
        print "RHS Module Test Results: \n------------------"
        if initResults['powerCardFault1'] == 'Yes':
            print "    Fault Flag        = ", initResults['powerCardFault1']
            issuesRHS += 1
        if initResults['powerCardFemStatus1'] == 'Yes':
            print "    Fem Status   Trip = ", initResults['powerCardFemStatus1']
            issuesRHS += 1
        if initResults['powerCardExtStatus1'] == 'Yes':
            print "    External     Trip = ", initResults['powerCardExtStatus1']
            issuesRHS += 1
        if initResults['powerCardOverCurrent1'] == 'Yes':
            print "    Over current Trip = ", initResults['powerCardOverCurrent1']
            issuesRHS += 1
        if initResults['powerCardOverTemp1'] == 'Yes':
            print "    Over temp    Trip = ", initResults['powerCardOverTemp1']
            issuesRHS += 1
    #    if initResults['powerCardUnderTemp1'] == 'Yes':
    #        print "    Undertemp    Trip = ", initResults['powerCardUnderTemp1']    # Redundant - Always "tripped"
    
        if initResults['powerCardTemp1'] > 50.0: # RHS
            print "RHS     PSU Card Temp   = ", initResults['powerCardTemp1'], '  C'
            issuesRHS += 1
        if initResults['sensor8Temp'] > thresholdSensorTemperature:
            print '   Sensor  8 Temp: %5.2f' %  initResults['sensor8Temp'], '  C'
            issuesRHS += 1
        if initResults['sensor9Temp'] > thresholdSensorTemperature: 
            print '   Sensor  9 Temp: %5.2f' %  initResults['sensor9Temp'], '  C'
            issuesRHS += 1
        if initResults['sensor10Temp'] > thresholdSensorTemperature: 
            print '   Sensor 10 Temp: %5.2f' % initResults['sensor10Temp'], '  C'
            issuesRHS += 1
        if initResults['sensor11Temp'] > thresholdSensorTemperature: 
            print '   Sensor 11 Temp: %5.2f' % initResults['sensor11Temp'], '  C'
            issuesRHS += 1
        if initResults['sensor12Temp'] > thresholdSensorTemperature: 
            print '   Sensor 12 Temp: %5.2f' % initResults['sensor12Temp'], '  C'
            issuesRHS += 1
        if initResults['sensor13Temp'] > thresholdSensorTemperature: 
            print '   Sensor 13 Temp: %5.2f' % initResults['sensor13Temp'], '  C'
            issuesRHS += 1
        if initResults['sensor14Temp'] > thresholdSensorTemperature: 
            print '   Sensor 14 Temp: %5.2f' % initResults['sensor14Temp'], '  C' 
            issuesRHS += 1
        if initResults['sensor15Temp'] > thresholdSensorTemperature:
            print '   Sensor 15 Temp: %5.2f' % initResults['sensor15Temp'], '  C' 
            issuesRHS += 1
        
        # Notify user if no issues encountered
        if issuesRHS == 0:
            print "(No issues in RHS)"
    
#        if postResults['sensor8Current'] > thresholdSensorCurrent:
#            print "   V Sensor 8 : Connected" #%.2f" % postResults['sensor8Current'], " A"
#        else:
#            print "   V Sensor 8 : Not Connected"
#        if postResults['sensor9Current'] > thresholdSensorCurrent:
#            print "   V Sensor 9 : Connected" #%.2f" % postResults['sensor9Current'], " A"
#        else:
#            print "   V Sensor 9 : Not Connected"
#        if postResults['sensor10Current'] > thresholdSensorCurrent:
#            print "   V Sensor 10 : Connected" #%.2f" % postResults['sensor10Current'], " A"
#        else:
#            print "   V Sensor 10 : Not Connected"
#        if postResults['sensor11Current'] > thresholdSensorCurrent:
#            print "   V Sensor 11 : Connected" #%.2f" % postResults['sensor11Current'], " A"
#        else:
#            print "   V Sensor 11 : Not Connected"
#        if postResults['sensor12Current'] > thresholdSensorCurrent:
#            print "   V Sensor 12 : Connected" #%.2f" % postResults['sensor12Current'], " A"
#        else:
#            print "   V Sensor 12 : Not Connected"
#        if postResults['sensor13Current'] > thresholdSensorCurrent:
#            print "   V Sensor 13 : Connected" #%.2f" % postResults['sensor13Current'], " A"
#        else:
#            print "   V Sensor 13 : Not Connected"
#        if postResults['sensor14Current'] > thresholdSensorCurrent:
#            print "   V Sensor 14 : Connected" #%.2f" % postResults['sensor14Current'], " A"
#        else:
#            print "   V Sensor 14 : Not Connected"
        if postResults['sensor15Current'] > thresholdSensorCurrent:
            print "   V Sensor 15 : Connected" #%.2f" % postResults['sensor15Current'], " A"
        else:
            print "   V Sensor 15 : Not Connected"
    
    #    print "   V Sensor 8  : %.2f"  % postResults['sensor8Voltage'], " V ", "%.2f" % postResults['sensor8Current'], " A"
    #    print "   V Sensor 9  : %.2f"  % postResults['sensor9Voltage'], " V ", "%.2f" % postResults['sensor9Current'], " A"
    #    print "   V Sensor 10 : %.2f"  % postResults['sensor10Voltage']," V ", "%.2f" % postResults['sensor10Current']," A"
    #    print "   V Sensor 11 : %.2f"  % postResults['sensor11Voltage']," V ", "%.2f" % postResults['sensor11Current']," A"
    #    print "   V Sensor 12 : %.2f"  % postResults['sensor12Voltage']," V ", "%.2f" % postResults['sensor12Current']," A"
    #    print "   V Sensor 13 : %.2f"  % postResults['sensor13Voltage']," V ", "%.2f" % postResults['sensor13Current']," A"
    #    print "   V Sensor 14 : %.2f"  % postResults['sensor14Voltage']," V ", "%.2f" % postResults['sensor14Current']," A"
    #    print "   V Sensor 15 : %.2f"  % postResults['sensor15Voltage']," V ", "%.2f" % postResults['sensor15Current']," A"
    
        '''    -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-    '''
            
        print "\nLHS Module Test Results:\n------------------"
        if initResults['powerCardFault0'] == 'Yes': 
            print "    Fault Flag        = ", initResults['powerCardFault0']
            issuesLHS += 1
        if initResults['powerCardFemStatus0'] == 'Yes':
            print "    Fem Status   Trip = ", initResults['powerCardFemStatus0']
            issuesLHS += 1
        if initResults['powerCardExtStatus0'] == 'Yes':
            print "    External     Trip = ", initResults['powerCardExtStatus0']
            issuesLHS += 1
        if initResults['powerCardOverCurrent0'] == 'Yes':
            print "    Over current Trip = ", initResults['powerCardOverCurrent0']
            issuesLHS += 1
        if initResults['powerCardOverTemp0'] == 'Yes':
            print "    Over temp    Trip = ", initResults['powerCardOverTemp0']
            issuesLHS += 1
    #    if initResults['powerCardUnderTemp0'] == 'Yes':
    #        print "    Undertemp    Trip = ", initResults['powerCardUnderTemp0'], "\n"    # Redundant - Always "tripped"
        if initResults['powerCardTemp0'] > 50.0:     # LHS
            print "LHS     PSU Card Temp   = ", initResults['powerCardTemp0'], '  C'
            issuesLHS += 1
                
        if initResults['sensor0Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 0 Temp: %5.2f' % initResults['sensor0Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor1Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 1 Temp: %5.2f' % initResults['sensor1Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor2Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 2 Temp: %5.2f' % initResults['sensor2Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor3Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 3 Temp: %5.2f' % initResults['sensor3Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor4Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 4 Temp: %5.2f' % initResults['sensor4Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor5Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 5 Temp: %5.2f' % initResults['sensor5Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor6Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 6 Temp: %5.2f' % initResults['sensor6Temp'], '  C'
            issuesLHS += 1
        if initResults['sensor7Temp'] > thresholdSensorTemperature:
            print 'LHS\t\t   Sensor 7 Temp: %5.2f' % initResults['sensor7Temp'], '  C'
            issuesLHS += 1
    
        # Notify user if no issues encountered
        if issuesLHS == 0:
            print "(No issues in LHS)"
    
        if postResults['sensor0Current'] > thresholdSensorCurrent:
            print "   V Sensor 0 : Connected" #%.2f" % postResults['sensor0Current'], " A"
        else:
            print "   V Sensor 0 : Not Connected"
#        if postResults['sensor1Current'] > thresholdSensorCurrent:
#            print "   V Sensor 1 : Connected" #%.2f" % postResults['sensor1Current'], " A"
#        else:
#            print "   V Sensor 1 : Not Connected"
#        if postResults['sensor2Current'] > thresholdSensorCurrent:
#            print "   V Sensor 2 : Connected" #%.2f" % postResults['sensor2Current'], " A"
#        else:
#            print "   V Sensor 2 : Not Connected"
#        if postResults['sensor3Current'] > thresholdSensorCurrent:
#            print "   V Sensor 3 : Connected" #%.2f" % postResults['sensor3Current'], " A"
#        else:
#            print "   V Sensor 3 : Not Connected"
#        if postResults['sensor4Current'] > thresholdSensorCurrent:
#            print "   V Sensor 4 : Connected" #%.2f" % postResults['sensor4Current'], " A"
#        else:
#            print "   V Sensor 4 : Not Connected"
#        if postResults['sensor5Current'] > thresholdSensorCurrent:
#            print "   V Sensor 5 : Connected" #%.2f" % postResults['sensor5Current'], " A"
#        else:
#            print "   V Sensor 5 : Not Connected"
#        if postResults['sensor6Current'] > thresholdSensorCurrent:
#            print "   V Sensor 6 : Connected" #%.2f" % postResults['sensor6Current'], " A"
#        else:
#            print "   V Sensor 6 : Not Connected"
#        if postResults['sensor7Current'] > thresholdSensorCurrent:
#            print "   V Sensor 7 : Connected" #%.2f" % postResults['sensor7Current'], " A"
#        else:
#            print "   V Sensor 7 : Not Connected"

        bDebug = False
        if bDebug:
            print "------------------------ Init Results: ------------------------"
            self.displayResult(initResults)
            print "------------------------ Post Results: ------------------------"
            self.displayResult(postResults)
    
        print "Closing Fem connection.. "        
        self.theDevice.close()
    
    def displayResult(self, results):
        ''' Debug function to display contents of results dictionary '''
    
        print "    ~+~+~+~+~+~+~ RHS ~+~+~+~+~+~+~+~+~ LHS ~+~+~+~+~+~+~"
            
        print "Status:"
        print "    Low voltage  = ",
        if results['asicPowerEnable1']:
            print "off.",
        else:
            print "on.",
        print "\t\t    Low voltage  = ",
        if results['asicPowerEnable0']:
            print "off."
        else:
            print "on."
            
        print "    High voltage = ",
        if results['sensorBiasEnable1']:
            print "off.",
        else:
            print "on.",
        print "\t\t    High voltage = ",
        if results['sensorBiasEnable0']:
            print "off."
        else:
            print "on."
            
        print "    HV setting: %5.2f" % results['sensorBias1'] , "V", "\t\t    HV setting: %5.2f" % results['sensorBias0'], "V"
    
        print "Flags:" 
        print "    Fault Flag        = ", results['powerCardFault1'],       "\t\t    Fault Flag        = ", results['powerCardFault0']
        print "    Fem Status   Trip = ", results['powerCardFemStatus1'],   "\t\t    Fem Status   Trip = ", results['powerCardFemStatus0']
        print "    External     Trip = ", results['powerCardExtStatus1'],   "\t\t    External     Trip = ", results['powerCardExtStatus0']
        print "    Over current Trip = ", results['powerCardOverCurrent1'], "\t\t    Over current Trip = ", results['powerCardOverCurrent0']
        print "    Over temp    Trip = ", results['powerCardOverTemp1'],    "\t\t    Over temp    Trip = ", results['powerCardOverTemp0']
        print "    Undertemp    Trip = ", results['powerCardUnderTemp1'],   "\t\t    Undertemp    Trip = ", results['powerCardUnderTemp0'], "\n"
    
        # Display temperature readings from PSU Card and Sensors
        print "Temperature readings:"
        print '   PSU Card Temp:  %.2f' %   results['powerCardTemp1'], '  C',
        print '\t\t   PSU Card Temp: %.2f' % results['powerCardTemp0'], '  C'
    
        print '   Sensor  8 Temp: %5.2f' %  results['sensor8Temp'], '  C', '\t\t   Sensor 0 Temp: %5.2f' % results['sensor0Temp'], '  C'
        print '   Sensor  9 Temp: %5.2f' %  results['sensor9Temp'], '  C', '\t\t   Sensor 1 Temp: %5.2f' % results['sensor1Temp'], '  C'
        print '   Sensor 10 Temp: %5.2f' % results['sensor10Temp'], '  C', '\t\t   Sensor 2 Temp: %5.2f' % results['sensor2Temp'], '  C'
        print '   Sensor 11 Temp: %5.2f' % results['sensor11Temp'], '  C', '\t\t   Sensor 3 Temp: %5.2f' % results['sensor3Temp'], '  C'
        print '   Sensor 12 Temp: %5.2f' % results['sensor12Temp'], '  C', '\t\t   Sensor 4 Temp: %5.2f' % results['sensor4Temp'], '  C'
        print '   Sensor 13 Temp: %5.2f' % results['sensor13Temp'], '  C', '\t\t   Sensor 5 Temp: %5.2f' % results['sensor5Temp'], '  C'
        print '   Sensor 14 Temp: %5.2f' % results['sensor14Temp'], '  C', '\t\t   Sensor 6 Temp: %5.2f' % results['sensor6Temp'], '  C'
        print '   Sensor 15 Temp: %5.2f' % results['sensor15Temp'], '  C', '\t\t   Sensor 7 Temp: %5.2f' % results['sensor7Temp'], '  C'
    
        # Display Fem, Digital, sensors voltages and current
        print "\nOutputs: "
    
        print "   V FEM      : %.2f" % results['femVoltage1'], " V ", "%.2f" % results['femCurrent1'], " A",
        print "\t   V FEM      : %.2f" % results['femVoltage0'], " V ", "%.2f" % results['femCurrent0'], " A"
        print "   V Digital  : %.2f" % results['digitalVoltage1'], " V ", "%.2f" % results['digitalCurrent1'], " mA",
        print "\t   V Digital  : %.2f" % results['digitalVoltage0'], " V ", "%.2f" % results['digitalCurrent0'], " mA\n"
    
        print "   V Sensor 8  : %.2f"  % results['sensor8Voltage'], " V ", "%.2f" % results['sensor8Current'], " A",
        print "\t   V Sensor 0 : %.2f" % results['sensor0Voltage'], " V ", "%.2f" % results['sensor0Current'], " A"
        print "   V Sensor 9  : %.2f"  % results['sensor9Voltage'], " V ", "%.2f" % results['sensor9Current'], " A",
        print "\t   V Sensor 1 : %.2f" % results['sensor1Voltage'], " V ", "%.2f" % results['sensor1Current'], " A"
        print "   V Sensor 10 : %.2f"  % results['sensor10Voltage']," V ", "%.2f" % results['sensor10Current']," A",
        print "\t   V Sensor 2 : %.2f" % results['sensor2Voltage'], " V ", "%.2f" % results['sensor2Current'], " A"
        print "   V Sensor 11 : %.2f"  % results['sensor11Voltage']," V ", "%.2f" % results['sensor11Current']," A",
        print "\t   V Sensor 3 : %.2f" % results['sensor3Voltage'], " V ", "%.2f" % results['sensor3Current'], " A"
        print "   V Sensor 12 : %.2f"  % results['sensor12Voltage']," V ", "%.2f" % results['sensor12Current']," A",
        print "\t   V Sensor 4 : %.2f" % results['sensor4Voltage'], " V ", "%.2f" % results['sensor4Current'], " A"
        print "   V Sensor 13 : %.2f"  % results['sensor13Voltage']," V ", "%.2f" % results['sensor13Current']," A",
        print "\t   V Sensor 5 : %.2f" % results['sensor5Voltage'], " V ", "%.2f" % results['sensor5Current'], " A"
        print "   V Sensor 14 : %.2f"  % results['sensor14Voltage']," V ", "%.2f" % results['sensor14Current']," A",
        print "\t   V Sensor 6 : %.2f" % results['sensor6Voltage'], " V ", "%.2f" % results['sensor6Current'], " A"
        print "   V Sensor 15 : %.2f"  % results['sensor15Voltage']," V ", "%.2f" % results['sensor15Current']," A",
        print "\t   V Sensor 7 : %.2f" % results['sensor7Voltage'], " V ", "%.2f" % results['sensor7Current'], " A\n"
    
        print "   HV Bias    : %.2f" % results['sensorBiasVoltage1'], " V ",
        print "%.2f" % results['sensorBiasCurrent1'], " uA",
        print "\t   HV Bias    : %.2f" % results['sensorBiasVoltage0'], " V ",
        print "%.2f" % results['sensorBiasCurrent0'], " uA"
    
        print "-- -- -- -- -- -- -- -- --"

if __name__ == '__main__':
    
    # Define default values
    femHost = '192.168.2.2'
    femPort = 6969
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="LpdPowerTesting.py - Developing testing (ASIC) procedures. ",
                                     epilog="Default: femhost=192.168.2.2, femport=6969")

    parser.add_argument("--femhost",        help="Set fem host IP (e.g 192.168.2.2)",   type=str, default=femHost)
    parser.add_argument("--femport",        help="Set fem port (eg 6969)",              type=int, default=femPort)
    args = parser.parse_args()

    host     = args.femhost
    port     = args.femport

    instance = LpdPowerTesting(host, port)
    instance.testPowerCards()
