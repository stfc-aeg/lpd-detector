"""
    LpdFemGuiPowerTesting - Based upon LpdPowerTesting, tests the power card(s)

    Author: ckd27546,    Created: 22/07/2014
"""

from LpdDevice.LpdDevice import LpdDevice
from LpdFemTests.LpdPowerControl import LpdPowerControl
import sys, time

class LpdFemGuiPowerTesting:
    
    def __init__(self, femHost, femPort, messageSignal):
        
        self.femHost = femHost
        self.femPort = femPort
        #  Communicate test results to LpdFemGuiMainTestTab
        self.messageSignal = messageSignal

        self.theDevice = LpdDevice()
        
        rc = self.theDevice.open(self.femHost, self.femPort, asicModuleType=0)
    
        if rc != LpdDevice.ERROR_OK:
            self.messageSignal.emit("Power Analysis Error: Failed to open FEM device: %s" % (self.theDevice.errorStringGet()))
        else:
            #Debugging info really:
            print >> sys.stderr, "====================== %s:%s ======================" % (self.femHost, self.femPort)
        
    def testPowerCards(self):
        
        numSensors = 16
        numPowerCards = 2
        TVCparamsTypes = ['Temp', 'Voltage', 'Current'] # Redundant line?
    
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
                    self.messageSignal.emit("Power Analysis Error 1: %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet()))
                    errorCount += 1
                    if errorCount > 2:
                        self.messageSignal.emit("Power Analysis Error: Detected three errors, aborting..")
                        self.theDevice.close()
                        return
        
        miscParamTypes = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                      'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                      'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']
        
        for powerCard in range(numPowerCards):
            
            for paramType in miscParamTypes:
                paramName = paramType + str(powerCard)
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                initResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.messageSignal.emit("Power Analysis Error 2: %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet()))
                    errorCount += 1
                    if errorCount > 2:
                        self.messageSignal.emit("Power Analysis Error: Found three errors, aborting..")
                        self.theDevice.close()
                        return

        asicmodule = 0
        hvbias = 50
        thisFem = LpdPowerControl(self.femHost, self.femPort, asicmodule)

        print >> sys.stderr, "Executing first LpdPowerControl script.. (Setting high-voltage)"
    
        print >> sys.stderr, "Switching: HV off, ",    # Possibly redundant?
        thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)

        print >> sys.stderr, "LV off.. ",          # Possibly redundant?
        thisFem.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.OFF)
        
        print >> sys.stderr, "Setting HV bias to ", hvbias, " V.."
        thisFem.updateQuantity(quantity='sensorBias', newValue=hvbias)
    
        print >> sys.stderr, "Executing second LpdPowerControl script.. (Enabling high and low voltages)"
        
        print >> sys.stderr, "Switching: LV on, ",
        thisFem.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.ON)
        
        print >> sys.stderr, "HV on.."
        thisFem.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.ON)

        timeDelay = 3
        print >> sys.stderr, "Done! (Waiting " + str(timeDelay) + " seconds for voltages to stabilise..)\n"

        # Wait couple of seconds for voltages to stabilise
        time.sleep(timeDelay)
    
        
        for sensor in range(numSensors):
            
            for paramType in TVCparamsTypes:
                paramName = 'sensor' + str(sensor) + paramType
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                postResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.messageSignal.emit("Power Analysis Error 3: %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet()))
                    errorCount += 1
                    if errorCount > 2:
                        self.messageSignal.emit("Power Analysis Error: Detected three errors, aborting..")
                        self.theDevice.close()
                        return
        
        for powerCard in range(numPowerCards):
            
            for paramType in miscParamTypes:
                paramName = paramType + str(powerCard)
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                postResults[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.messageSignal.emit("Power Analysis Error 4: %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet()))
                    errorCount += 1
                    if errorCount > 2:
                        self.messageSignal.emit("Power Analysis Error: Found three errors, aborting..")
                        self.theDevice.close()
                        return
    
        # Define thresholds
        thresholdSensorTemperature = 49.9
        thresholdSensorCurrent = 1.67
    
        self.messageSignal.emit("    Fault Flag        = %s" % initResults['powerCardFault1'])
        
        # Analyse the results:
        (issuesRHS, issuesLHS) = (0, 0)
        self.messageSignal.emit("RHS Module Test Results:") # \n------------------")
        if initResults['powerCardFault1'] == 'Yes':
            self.messageSignal.emit("    Fault Flag        = %s" % initResults['powerCardFault1'])
            issuesRHS += 1
        if initResults['powerCardFemStatus1'] == 'Yes':
            self.messageSignal.emit("    Fem Status   Trip = %s" % initResults['powerCardFemStatus1'])
            issuesRHS += 1
        if initResults['powerCardExtStatus1'] == 'Yes':
            self.messageSignal.emit("    External     Trip = %s" % initResults['powerCardExtStatus1'])
            issuesRHS += 1
        if initResults['powerCardOverCurrent1'] == 'Yes':
            self.messageSignal.emit("    Over current Trip = %s" % initResults['powerCardOverCurrent1'])
            issuesRHS += 1
        if initResults['powerCardOverTemp1'] == 'Yes':
            self.messageSignal.emit("    Over temp    Trip = %s" % initResults['powerCardOverTemp1'])
            issuesRHS += 1

        if initResults['powerCardTemp1'] > 50.0: # RHS
            self.messageSignal.emit("RHS     PSU Card Temp   = %s   C" % initResults['powerCardTemp1'])
            issuesRHS += 1
        if initResults['sensor15Temp'] > thresholdSensorTemperature:
            self.messageSignal.emit('   Sensor 15 Temp: %5.2f  C' % initResults['sensor15Temp']) 
            issuesRHS += 1
        
        # Notify user if no issues encountered
        if issuesRHS == 0:
            self.messageSignal.emit("(No issues in RHS)")

        if postResults['sensor15Current'] > thresholdSensorCurrent:
            self.messageSignal.emit("   V Sensor 15 : Connected") #%.2f" % postResults['sensor15Current'], " A"
        else:
            self.messageSignal.emit("   V Sensor 15 : Not Connected")

        '''    -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-    '''
            
        self.messageSignal.emit("LHS Module Test Results:")
        if initResults['powerCardFault0'] == 'Yes': 
            self.messageSignal.emit("    Fault Flag        = %s" % initResults['powerCardFault0'])
            issuesLHS += 1
        if initResults['powerCardFemStatus0'] == 'Yes':
            self.messageSignal.emit("    Fem Status   Trip = %s" % initResults['powerCardFemStatus0'])
            issuesLHS += 1
        if initResults['powerCardExtStatus0'] == 'Yes':
            self.messageSignal.emit("    External     Trip = %s" % initResults['powerCardExtStatus0'])
            issuesLHS += 1
        if initResults['powerCardOverCurrent0'] == 'Yes':
            self.messageSignal.emit("    Over current Trip = %s" % initResults['powerCardOverCurrent0'])
            issuesLHS += 1
        if initResults['powerCardOverTemp0'] == 'Yes':
            self.messageSignal.emit("    Over temp    Trip = %s" % initResults['powerCardOverTemp0'])
            issuesLHS += 1
        if initResults['powerCardTemp0'] > 50.0:     # LHS
            self.messageSignal.emit("LHS     PSU Card Temp   = %s   C" % initResults['powerCardTemp0'])
            issuesLHS += 1

        if initResults['sensor0Temp'] > thresholdSensorTemperature:
            self.messageSignal.emit('LHS\t\t   Sensor 0 Temp: %5.2f  C' % initResults['sensor0Temp'])
            issuesLHS += 1
    
        # Notify user if no issues encountered
        if issuesLHS == 0:
            self.messageSignal.emit("(No issues in LHS)")
    
        if postResults['sensor0Current'] > thresholdSensorCurrent:
            self.messageSignal.emit("   V Sensor 0 : Connected") #%.2f" % postResults['sensor0Current'], " A"
        else:
            self.messageSignal.emit("   V Sensor 0 : Not Connected")

        bDebug = False
        if bDebug:
            print >> sys.stderr, "------------------------ Init Results: ------------------------"
            self.displayResult(initResults)
            print >> sys.stderr, "------------------------ Post Results: ------------------------"
            self.displayResult(postResults)
    
        print >> sys.stderr, "Closing Fem connection.. "        
        self.theDevice.close()
    
    def displayResult(self, results):
        ''' Debug function to display contents of results dictionary '''
    
        print >> sys.stderr, "    ~+~+~+~+~+~+~ RHS ~+~+~+~+~+~+~+~+~ LHS ~+~+~+~+~+~+~"
            
        print >> sys.stderr, "Status:"
        print >> sys.stderr, "    Low voltage  = ",
        if results['asicPowerEnable1']:
            print >> sys.stderr, "off.",
        else:
            print >> sys.stderr, "on.",
        print >> sys.stderr, "\t\t    Low voltage  = ",
        if results['asicPowerEnable0']:
            print >> sys.stderr, "off."
        else:
            print >> sys.stderr, "on."
            
        print >> sys.stderr, "    High voltage = ",
        if results['sensorBiasEnable1']:
            print >> sys.stderr, "off.",
        else:
            print >> sys.stderr, "on.",
        print >> sys.stderr, "\t\t    High voltage = ",
        if results['sensorBiasEnable0']:
            print >> sys.stderr, "off."
        else:
            print >> sys.stderr, "on."
            
        print >> sys.stderr, "    HV setting: %5.2f" % results['sensorBias1'] , "V", "\t\t    HV setting: %5.2f" % results['sensorBias0'], "V"
    
        print >> sys.stderr, "Flags:" 
        print >> sys.stderr, "    Fault Flag        = ", results['powerCardFault1'],       "\t\t    Fault Flag        = ", results['powerCardFault0']
        print >> sys.stderr, "    Fem Status   Trip = ", results['powerCardFemStatus1'],   "\t\t    Fem Status   Trip = ", results['powerCardFemStatus0']
        print >> sys.stderr, "    External     Trip = ", results['powerCardExtStatus1'],   "\t\t    External     Trip = ", results['powerCardExtStatus0']
        print >> sys.stderr, "    Over current Trip = ", results['powerCardOverCurrent1'], "\t\t    Over current Trip = ", results['powerCardOverCurrent0']
        print >> sys.stderr, "    Over temp    Trip = ", results['powerCardOverTemp1'],    "\t\t    Over temp    Trip = ", results['powerCardOverTemp0']
        print >> sys.stderr, "    Undertemp    Trip = ", results['powerCardUnderTemp1'],   "\t\t    Undertemp    Trip = ", results['powerCardUnderTemp0'], "\n"
    
        # Display temperature readings from PSU Card and Sensors
        print >> sys.stderr, "Temperature readings:"
        print >> sys.stderr, '   PSU Card Temp:  %.2f' %   results['powerCardTemp1'], '  C',
        print >> sys.stderr, '\t\t   PSU Card Temp: %.2f' % results['powerCardTemp0'], '  C'
    
        print >> sys.stderr, '   Sensor  8 Temp: %5.2f' %  results['sensor8Temp'], '  C', '\t\t   Sensor 0 Temp: %5.2f' % results['sensor0Temp'], '  C'
        print >> sys.stderr, '   Sensor  9 Temp: %5.2f' %  results['sensor9Temp'], '  C', '\t\t   Sensor 1 Temp: %5.2f' % results['sensor1Temp'], '  C'
        print >> sys.stderr, '   Sensor 10 Temp: %5.2f' % results['sensor10Temp'], '  C', '\t\t   Sensor 2 Temp: %5.2f' % results['sensor2Temp'], '  C'
        print >> sys.stderr, '   Sensor 11 Temp: %5.2f' % results['sensor11Temp'], '  C', '\t\t   Sensor 3 Temp: %5.2f' % results['sensor3Temp'], '  C'
        print >> sys.stderr, '   Sensor 12 Temp: %5.2f' % results['sensor12Temp'], '  C', '\t\t   Sensor 4 Temp: %5.2f' % results['sensor4Temp'], '  C'
        print >> sys.stderr, '   Sensor 13 Temp: %5.2f' % results['sensor13Temp'], '  C', '\t\t   Sensor 5 Temp: %5.2f' % results['sensor5Temp'], '  C'
        print >> sys.stderr, '   Sensor 14 Temp: %5.2f' % results['sensor14Temp'], '  C', '\t\t   Sensor 6 Temp: %5.2f' % results['sensor6Temp'], '  C'
        print >> sys.stderr, '   Sensor 15 Temp: %5.2f' % results['sensor15Temp'], '  C', '\t\t   Sensor 7 Temp: %5.2f' % results['sensor7Temp'], '  C'
    
        # Display Fem, Digital, sensors voltages and current
        print >> sys.stderr, "\nOutputs: "
    
        print >> sys.stderr, "   V FEM      : %.2f" % results['femVoltage1'], " V ", "%.2f" % results['femCurrent1'], " A",
        print >> sys.stderr, "\t   V FEM      : %.2f" % results['femVoltage0'], " V ", "%.2f" % results['femCurrent0'], " A"
        print >> sys.stderr, "   V Digital  : %.2f" % results['digitalVoltage1'], " V ", "%.2f" % results['digitalCurrent1'], " mA",
        print >> sys.stderr, "\t   V Digital  : %.2f" % results['digitalVoltage0'], " V ", "%.2f" % results['digitalCurrent0'], " mA\n"
    
        print >> sys.stderr, "   V Sensor 8  : %.2f"  % results['sensor8Voltage'], " V ", "%.2f" % results['sensor8Current'], " A",
        print >> sys.stderr, "\t   V Sensor 0 : %.2f" % results['sensor0Voltage'], " V ", "%.2f" % results['sensor0Current'], " A"
        print >> sys.stderr, "   V Sensor 9  : %.2f"  % results['sensor9Voltage'], " V ", "%.2f" % results['sensor9Current'], " A",
        print >> sys.stderr, "\t   V Sensor 1 : %.2f" % results['sensor1Voltage'], " V ", "%.2f" % results['sensor1Current'], " A"
        print >> sys.stderr, "   V Sensor 10 : %.2f"  % results['sensor10Voltage']," V ", "%.2f" % results['sensor10Current']," A",
        print >> sys.stderr, "\t   V Sensor 2 : %.2f" % results['sensor2Voltage'], " V ", "%.2f" % results['sensor2Current'], " A"
        print >> sys.stderr, "   V Sensor 11 : %.2f"  % results['sensor11Voltage']," V ", "%.2f" % results['sensor11Current']," A",
        print >> sys.stderr, "\t   V Sensor 3 : %.2f" % results['sensor3Voltage'], " V ", "%.2f" % results['sensor3Current'], " A"
        print >> sys.stderr, "   V Sensor 12 : %.2f"  % results['sensor12Voltage']," V ", "%.2f" % results['sensor12Current']," A",
        print >> sys.stderr, "\t   V Sensor 4 : %.2f" % results['sensor4Voltage'], " V ", "%.2f" % results['sensor4Current'], " A"
        print >> sys.stderr, "   V Sensor 13 : %.2f"  % results['sensor13Voltage']," V ", "%.2f" % results['sensor13Current']," A",
        print >> sys.stderr, "\t   V Sensor 5 : %.2f" % results['sensor5Voltage'], " V ", "%.2f" % results['sensor5Current'], " A"
        print >> sys.stderr, "   V Sensor 14 : %.2f"  % results['sensor14Voltage']," V ", "%.2f" % results['sensor14Current']," A",
        print >> sys.stderr, "\t   V Sensor 6 : %.2f" % results['sensor6Voltage'], " V ", "%.2f" % results['sensor6Current'], " A"
        print >> sys.stderr, "   V Sensor 15 : %.2f"  % results['sensor15Voltage']," V ", "%.2f" % results['sensor15Current']," A",
        print >> sys.stderr, "\t   V Sensor 7 : %.2f" % results['sensor7Voltage'], " V ", "%.2f" % results['sensor7Current'], " A\n"
    
        print >> sys.stderr, "   HV Bias    : %.2f" % results['sensorBiasVoltage1'], " V ",
        print >> sys.stderr, "%.2f" % results['sensorBiasCurrent1'], " uA",
        print >> sys.stderr, "\t   HV Bias    : %.2f" % results['sensorBiasVoltage0'], " V ",
        print >> sys.stderr, "%.2f" % results['sensorBiasCurrent0'], " uA"
    
        print >> sys.stderr, "-- -- -- -- -- -- -- -- --"

