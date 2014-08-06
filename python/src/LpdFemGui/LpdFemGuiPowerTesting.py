"""
    LpdFemGuiPowerTesting - Based upon LpdPowerTesting, tests the power card(s)

    Author: ckd27546,    Created: 22/07/2014
"""

from LpdDevice.LpdDevice import LpdDevice
from LpdFemTests.LpdPowerControl import LpdPowerControl
import sys, time

class LpdFemGuiPowerTesting:

    RHS_MODULE = 15
    LHS_MODULE = 14 #0 # 0 is the REAL LHS module !

    def __init__(self, femHost, femPort, messageSignal, loggingSignal):
        
        self.femHost = femHost
        self.femPort = femPort

        self.moduleString = "-1"

        #  Communicate test results to LpdFemGuiMainTestTab
        self.messageSignal = messageSignal
        self.loggingSignal = loggingSignal

        self.theDevice = LpdDevice()
        
        rc = self.theDevice.open(self.femHost, self.femPort, asicModuleType=0)
    
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Power Analysis Error: Failed to open FEM device: %s" % (self.theDevice.errorStringGet()), bError=True)
        else:
            #Debugging info really:
            print >> sys.stderr, "====================== %s:%s ======================" % (self.femHost, self.femPort)
            

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdFemGuiPowerTesting.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdFemGuiPowerTesting.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

    def testPowerCards(self, moduleNumber):
        ''' ORPHANED! Comment to be added here '''
        
        #TODO: No longer called from LpdFemGuiAnalysis.performAnalysis !
        
        # Set moduleNumber and moduleString (e.g. 0/LHS)
        self.setModuleType(moduleNumber)

        self.msgPrint("Module %s: Testing power card in progress ..." % self.moduleString)

        # Read sensors on both power cards
        try:
            initResults = self.readPowerCards()
        except Exception:
            self.msgPrint("Power Analysis Error: (1) Couldn't read power card parameter(s)")
            self.theDevice.close()
            return
        
        asicmodule = 0
        hvbias = 50
        powerControl = LpdPowerControl(self.femHost, self.femPort, asicmodule)

        print >> sys.stderr, "Setting high-voltage"
    
        print >> sys.stderr, "Switching: HV off, ",    # Possibly redundant?
        powerControl.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.OFF)

        print >> sys.stderr, "LV off.. ",          # Possibly redundant?
        powerControl.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.OFF)
        
        print >> sys.stderr, "Setting HV bias to ", hvbias, " V.."
        powerControl.updateQuantity(quantity='sensorBias', newValue=hvbias)
    
        print >> sys.stderr, "Enabling high and low voltages"
        
        print >> sys.stderr, "Switching: LV on, ",
        powerControl.updateQuantity(quantity='asicPowerEnable', newValue=LpdPowerControl.ON)
        
        print >> sys.stderr, "HV on.."
        powerControl.updateQuantity(quantity='sensorBiasEnable', newValue=LpdPowerControl.ON)

        timeDelay = 3
        print >> sys.stderr, "Done! (Waiting " + str(timeDelay) + " seconds for voltages to stabilise..)\n"

        # Wait couple of seconds for voltages to stabilise
        time.sleep(timeDelay)
        
        # Read sensors on both power cards (Now that voltages have been enabled)
        try:
            postResults = self.readPowerCards()
        except Exception:
            self.msgPrint("Power Analysis Error: (2) Couldn't read power card parameter(s)")
            self.theDevice.close()
            return

        # Define thresholds
        thresholdSensorTemperature = 49.9
        thresholdSensorCurrent = 1.67

        # Analyse the results:
        issues = self.retrieveFaultFlags(initResults, postResults, thresholdSensorTemperature, thresholdSensorCurrent)

        bDebug = False
        if bDebug:
            print >> sys.stderr, "------------------------ Init Results: ------------------------"
            self.displayResult(initResults)
            print >> sys.stderr, "------------------------ Post Results: ------------------------"
            self.displayResult(postResults)

        self.msgPrint("Power card testing completed - Reported %d issues" % issues)
        print >> sys.stderr, "Closing Fem connection.. " 
        self.theDevice.close()

    def readPowerCards(self):
        ''' Read all sensors on both power card '''

        numSensors = 16
        numPowerCards = 2

        # Count how many error encountered
        errorCount = 0
        results = {}
        TVCparamsTypes = ['Temp', 'Voltage', 'Current']
        
        miscParamTypes = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                      'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                      'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']
        
        for sensor in range(numSensors):
            
            for paramType in TVCparamsTypes:
                paramName = 'sensor' + str(sensor) + paramType
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                results[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.msgPrint("Power Analysis Error: %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet()), bError=True)
                    errorCount += 1
                    if errorCount > 2:
                        self.msgPrint("Power Analysis Error: Detected three errors, aborting..", bError=True)
                        self.theDevice.close()
                        raise Exception
        
        for powerCard in range(numPowerCards):
            
            for paramType in miscParamTypes:
                paramName = paramType + str(powerCard)
                
                (rc, val) = self.theDevice.paramGet(paramName)
    
                results[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.msgPrint("Power Analysis Error: %s rc=%d: %s" % (paramName, rc, self.theDevice.errorStringGet()), bError=True)
                    errorCount += 1
                    if errorCount > 2:
                        self.msgPrint("Power Analysis Error: Found three errors, aborting..", bError=True)
                        self.theDevice.close()
                        raise Exception
        return results
    
    def retrieveFaultFlags(self, initResults, postResults, thresholdSensorTemperature, thresholdSensorCurrent):
        ''' ORPHANED! Retrieve test results and comparing against thresholds and report any breach(es) '''
        
        if self.moduleNumber == 15:
            powerCardNumber = str(1)
        elif self.moduleNumber == 0:   
            powerCardNumber = str(0)
        else:
            self.msgPrint("Power Card Analysis Error: Unknown module (neither RHS nor LHS) specified!", bError=True)
            return -1
        issues = 0
        
        self.msgPrint("%s Module Test Results:" % self.moduleString)
        if initResults['powerCardFault'+powerCardNumber] == 'Yes':
            self.msgPrint("    Fault Flag        = %s" % initResults['powerCardFault'+powerCardNumber])
            issues += 1
        if initResults['powerCardFemStatus'+powerCardNumber] == 'Yes':
            self.msgPrint("    Fem Status   Trip = %s" % initResults['powerCardFemStatus'+powerCardNumber])
            issues += 1
        if initResults['powerCardExtStatus'+powerCardNumber] == 'Yes':
            self.msgPrint("    External     Trip = %s" % initResults['powerCardExtStatus'+powerCardNumber])
            issues += 1
        if initResults['powerCardOverCurrent'+powerCardNumber] == 'Yes':
            self.msgPrint("    Over current Trip = %s" % initResults['powerCardOverCurrent'+powerCardNumber])
            issues += 1
        if initResults['powerCardOverTemp'+powerCardNumber] == 'Yes':
            self.msgPrint("    Over temp    Trip = %s" % initResults['powerCardOverTemp'+powerCardNumber])
            issues += 1

        if initResults['powerCardTemp'+powerCardNumber] > 50.0:
            self.msgPrint("        PSU Card Temp   = %s   C" % initResults['powerCardTemp'+powerCardNumber])
            issues += 1
        if initResults['sensor15Temp'] > thresholdSensorTemperature:
            self.msgPrint('       Sensor Temp: %5.2f  C' % initResults['sensor%sTemp' % self.moduleNumber])
            issues += 1

        # Debugging info:
        self.msgPrint("        PSU Card Temp   = %s   C" % initResults['powerCardTemp'+powerCardNumber])

        # Notify user if no issues encountered
        if issues == 0:
            self.msgPrint("(No issues in %s module)" % self.moduleString)

        if postResults['sensor%sCurrent' % self.moduleNumber] > thresholdSensorCurrent:
            self.msgPrint("       %s Module : Connected" % self.moduleString)
        else:
            self.msgPrint("       %s Module : Not Connected" % self.moduleString)
        return issues

    def readCurrent(self, moduleNumber):
        ''' Read moduleNumber's current (as required by Wafer Probing and ASIC Bonding Test Routines)
            moduleNumber mandatory as function called directly from LpdFemGuiMainTestTab '''

        # Set moduleNumber and moduleString
        self.setModuleType(moduleNumber)

        self.msgPrint("Testing power card: %s" % self.moduleString)

        #TODO: Sort out this dirty hack:
        sensorIdx = -1
        if self.moduleNumber == LpdFemGuiPowerTesting.LHS_MODULE:
            sensorIdx = 9
        if self.moduleNumber == LpdFemGuiPowerTesting.RHS_MODULE:
            sensorIdx = 8
        
        try:
            results = self.readPowerCards()
        except Exception:
            self.msgPrint("Power Analysis Error: (2) Couldn't read power card parameter(s)")
            self.theDevice.close()
            return

        self.msgPrint("Module %s current: %.2f A" % (self.moduleString, results['sensor%sCurrent' %  sensorIdx]))
        # Log same results:
        self.loggingSignal.emit("Module %s current: %.2f A" % (self.moduleString, results['sensor%sCurrent' %  sensorIdx]))

    def msgPrint(self, message, bError=False):
        ''' Send message to LpdFemGuiMainTestTab to be displayed there '''
        self.messageSignal.emit(message, bError)

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

