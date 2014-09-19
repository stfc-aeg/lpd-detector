
from LpdReadoutConfig import *
from LpdDataContainers import *
from LpdDevice.LpdDevice import LpdDevice
from LpdFemTests.LpdPowerControl import LpdPowerControl
from LpdFemGuiAsicWindow import *
# Needed to restore fem GUI state:
from LpdFemGui import *

import traceback        # Improves debugging
import numpy as np
import h5py, time, sys
from matplotlib import cbook
import matplotlib.pyplot as plt
import matplotlib.text as text
import matplotlib
import argparse
import timeit, time, os.path

# Create decorator method to time code execution
def timingMethodDecorator(methodToDecorate):
    def wrapper(self, *args, **kwargs):
        startTime = timeit.default_timer()
        returnValues = methodToDecorate(self, *args, **kwargs)
        stopTime = timeit.default_timer()
        print >> sys.stderr, "Function", methodToDecorate.__name__ + str("()"), "execution time:", stopTime - startTime, "second(s)."
        return returnValues
    return wrapper

class LpdAsicTester(object):
    ''' Perform ASIC modules analysis, creating/display in results analysis window '''

    RHS_MODULE = 15
    LHS_MODULE = 14 #0 # 0 is the REAL LHS module !
    
    def __init__(self, appMain, device):
        
        super(LpdAsicTester, self).__init__()    # Required for pyqtSignal
        
        self.appMain = appMain
        self.device = device
        
        # Established signals (and slots)
        self.messageSignal = self.appMain.mainWindow.testTab.messageSignal

        # Test session parameters
        self.currentParams = {}

        # Copy defaults from file (via LpdFemGui class)
        self.currentParams = self.appMain.cachedParams.copy()
        # Ensure a set of known defaults (common to all tests)
        self.currentParams['liveViewEnable']                = False
        self.currentParams['femAsicGainOverride']           = 3     # Copied into femAsicGain by LpdFemGui (!)
#        self.currentParams['femAsicGain']                   = 3    # Not used by LpdFemGui
        self.currentParams['femAsicPixelFeedbackOverride']  = 0     # 0=50pF, 1=5pF
        self.currentParams['fileWriteEnable']               = True

        self.currentParams['readoutParamFile']  = self.currentParams['testingReadoutParamFile']
        self.currentParams['setupParamFile']    = self.currentParams['testingSetupParamFile']

#        # Debug: Display default settings
#        parameters = ['readoutParamFile', 'femAsicGainOverride', 'testingReadoutParamFile', 'setupParamFile', 'testingSetupParamFile', 
#                      'cmdSequenceFile', 'pixelGain', 'femAsicPixelFeedbackOverride', 'testingShortExposureFile', 'fileWriteEnable', 
#                      'liveViewEnable', 'testingSetupParamFile', 'testingReadoutParamFile']
#        print >> sys.stderr, "--------------------\nLpdAsicTester settings:"
#        for key in self.currentParams.keys():
#            if key in parameters:
#                print >> sys.stderr, "  ", key, ":", self.currentParams[key]

        self.moduleString = "-1"
        self.moduleDescription = ""
        
        self.lvState   = [0, 0]
        self.hvState   = [0, 0]
        self.biasState = [0, 0]        

        self.hardwareDelay  = 3
        self.moduleNumber   = 0
        self.fileName       = ""
        self.image          = 0
        self.train          = 0

        (self.numRows, self.numCols) = (32, 128)
        
        self.moduleStd      = -1.0
        self.moduleAverage  = -1.0
        

    def msgPrint(self, message, bError=False):
        ''' Send message to LpdFemGuiMainTestTab to be displayed there '''
        self.messageSignal.emit(message, bError)

    def setModuleDescription(self, moduleDescription):
        ''' Enable LpdFemGuiMainTestTab to communicate module description, i.e. "00135"
            Note that RHS/LHS determined by moduleLhsSel/moduleRhsSel in the GUI '''
        self.moduleDescription = moduleDescription
    
    def verifyJsonFileNames(self):
        ''' Check that the user-specified filenames in the .json file are valid '''
        xmlFileNames = [self.currentParams['testingSetupParamFile'], self.currentParams['testingReadoutParamFile'],
                        self.currentParams['testingLongExposureFile'], self.currentParams['testingShortExposureFile'] ]
        bErrorOk = True
        for fileName in xmlFileNames:
            #print >> sys.stderr, "verifyJsonFileNames() checking filename: %s" % fileName
            if not os.path.isfile(fileName):
                self.msgPrint("Error inside .json File: Cannot find '%s'" % fileName, bError=True)
                bErrorOk = False
        return bErrorOk

    def executeSensorBondingTest(self, moduleNumber):
        ''' Execute the sequence of tests defined by Sensor Bonding specifications '''

        try:
            # Verify XML files specified in json file exist
            if not self.verifyJsonFileNames():
                self.msgPrint("File missing, exiting test prematurely", bError=True)
                return
            
            self.msgPrint("Using cmdSequenceFile:  %s" % self.currentParams['testingLongExposureFile'])
            self.msgPrint("Using readoutParamFile: %s" % self.currentParams['testingReadoutParamFile'])
            self.msgPrint("Using setupParamFile:   %s" % self.currentParams['testingSetupParamFile'])

            # Set moduleNumber and moduleString
            self.moduleNumber = moduleNumber
            self.setModuleType(moduleNumber)
            
#            powerCardResults = self.readPowerCards()
#            #print >> sys.stderr, "powerCardResult: ", powerCardResults
#            print >> sys.stderr, "sensorBias 0, 1: ", powerCardResults['sensorBias0'], powerCardResults['sensorBias1']

#            # Define ASIC command sequence files
#            longExposure = "/u/ckd27546/workspace/lpdSoftware/LpdFemGui/config/Command_LongExposure_V2.xml"
#            shortExposure = "/u/ckd27546/workspace/lpdSoftware/LpdFemGui/config/Command_ShortExposure_V2.xml"

#            # Debugging: Using a short exposure, look at data
#            self.currentParams['cmdSequenceFile'] = self.currentParams['testingShortExposureFile']  # "/u/ckd27546/workspace/lpdSoftware/LpdFemGui/config/Command_ShortExposure_V2.xml",
##            self.currentParams['cmdSequenceFile'] = shortExposure
#            self.appMain.deviceConfigure(self.currentParams)
#            # . Readout Data
#            self.msgPrint(". Readout Data - SHORT exposure time")
#            self.appMain.deviceRun(self.currentParams)
#            self.fileName = self.appMain.lastDataFile
#            self.msgPrint("Produced HDF5 file: '%s'" % self.fileName)            
#            # .Check for out of range pixels. Are these full ASICs? Columns or individual pixels.
#            numBadPixels = self.checkOutOfRangePixels(train=0, image=0, miscDescription="SHORT", bSuppressPixelInfo=True)
#            self.msgPrint("Pausing for five seconds..")
#            time.sleep(3)

            # Checking current LV, HV status; values saved to self.lvState[], self.hvState[]
            self.obtainPowerSuppliesState(self.appMain.pwrCard.powerStateGet())

            numFailedSections = 0
            
            # ASIC Bonding procedure:

            self.msgPrint("1. Power on")

            # Switch off supply/supplies if already on; 0=off, 1=on
            if self.lvState[0] == 0:
                self.msgPrint("Low voltage is off, switching it on..")
                self.toggleLvSupplies()
            
            if self.hvState[0] == 0:
                self.msgPrint("High voltage is off, switching it on..")
                self.toggleHvSupplies()
            
            self.msgPrint("2. Check as in ASIC bonding - [Skipping for now]")
            
#            powerCardResults = self.readPowerCards()
#            print >> sys.stderr, "sensorBias 0, 1: ", powerCardResults['sensorBias0'], powerCardResults['sensorBias1']
            
            self.msgPrint("3. Power on sensor bias (HV) - 200V")
            # Check HV bias level:
            powerCardResults = self.readPowerCards()
            #print >> sys.stderr, "Before HV changed: sensorBias 0, 1: ", powerCardResults['sensorBias0'], powerCardResults['sensorBias1']
            measuredBiasLevel = powerCardResults['sensorBias0']
            if not (199.0 < measuredBiasLevel  < 201.0):
                self.msgPrint("Bias level is %f V, changing it to be 200 V" % measuredBiasLevel)
                # Change the HV bias
                self.hvSetBias(200.0)

                self.msgPrint("Waiting 5 seconds for bias to reached 200V..")
                time.sleep(5)
                self.msgPrint("Bias now set to 200 V")
            else:
                self.msgPrint("Bias already 200 V")

            #powerCardResults = self.readPowerCards()
            #print >> sys.stderr, "After HV changed: sensorBias 0, 1: ", powerCardResults['sensorBias0'], powerCardResults['sensorBias1']

            self.msgPrint("4. Take data with long exposure command sequence")
            # Set long exposure XML file, configure device
            self.currentParams['cmdSequenceFile'] = self.currentParams['testingLongExposureFile']
            self.appMain.deviceConfigure(self.currentParams)
            
            # Readout Data
            self.appMain.deviceRun(self.currentParams)
            self.fileName = self.appMain.lastDataFile
            self.msgPrint("Produced HDF5 file: '%s'" % self.fileName)            

            if self.fileName == None:
                self.msgPrint("Error: No file received")
            else:
                self.msgPrint("5. Check/record unconnected pixels - Using leakage current check.")
                numUnconnectedPixels = self.checkLeakageCurrent()
                if numUnconnectedPixels != 0:
                    self.msgPrint("There are %d unconnected pixel(s), that's a FAIL" % numUnconnectedPixels)
                    numFailedSections += 1
                else:
                    self.msgPrint("There are no unconnected pixels, that's a PASS")
    
                self.msgPrint("6. Check/record shorted pixels")
                (numShortedPixelsMin, numShortedPixelsMax, adjacentPixelPairs, neighbourStr) = self.locateShortedPixels()
                # Does total number of shorted pixels exceed 0?
                # Min = pixel stuck at value 0, Max = pixel stuck at value 4095
                if (numShortedPixelsMin+numShortedPixelsMax) > 0:
                    # Any minimum adjacent to a maximum?
                    if neighbourStr.__len__() > 0:
                        self.msgPrint("Adjacent shorted pixels detected:%s" % neighbourStr)
                        self.msgPrint("That's a total of %d adjacent pair(s)." % adjacentPixelPairs)
                    
                    self.msgPrint("There are %d (value=0) and %d (value=4095) shorted pixel(s), that's a FAIL" % (numShortedPixelsMin, numShortedPixelsMax))
                    numFailedSections += 1
                else:
                    self.msgPrint("There are no shorted pixels, that's a PASS")
                    
                # Summarise; Report how many failures (if any)
                if numFailedSections == 0:
                    self.msgPrint("Module %s is fine, failing none of the tests." % self.moduleString)
                else:
                    self.msgPrint("Module %s is problematic, it failed %d test(s)." % (self.moduleString, numFailedSections))
    
                    # Summarise which test(s) failed
                    if numUnconnectedPixels > 0:
                        self.msgPrint("* Failed test 5. There are %d unconnected pixel(s)." % numUnconnectedPixels)
                    if (numShortedPixelsMin+numShortedPixelsMax) > 0:
                        self.msgPrint("* Failed test 6. There are %d and %d shorted pixel(s)." % (numShortedPixelsMin, numShortedPixelsMax))
                        # Any minimum adjacent to a maximum?
                        if neighbourStr.__len__() > 0:
                            self.msgPrint("     Forming a total of %d adjacent pair(s)." % adjacentPixelPairs)

            # Hack DAQ tab to restore it to ready state
            self.appMain.deviceState = LpdFemGui.DeviceReady
            self.appMain.runStateUpdate()

        except Exception as e:
            print >> sys.stderr, "\n", traceback.print_exc()
            self.msgPrint("Exception during Sensor Bonding testing: %s" % e, bError=True)

    def executeAsicBondingTest(self, moduleNumber):
        ''' Execute the sequence of tests defined by ASIC bond specifications '''
        
        try:
            # Verify XML files specified in json file exist
            if not self.verifyJsonFileNames():
                self.msgPrint("File missing, exiting test prematurely", bError=True)
                return

            self.msgPrint("Using cmdSequenceFile:  %s" % self.currentParams['testingShortExposureFile'])
            self.msgPrint("Using readoutParamFile: %s" % self.currentParams['testingReadoutParamFile'])
            self.msgPrint("Using setupParamFile:   %s" % self.currentParams['testingSetupParamFile'])

            # Set moduleNumber and moduleString
            self.moduleNumber = moduleNumber
            self.setModuleType(moduleNumber)

            # Checking current LV, HV status; values saved to self.lvState[], self.hvState[]
            self.obtainPowerSuppliesState(self.appMain.pwrCard.powerStateGet())
            
            # Assume both supplies switched off initially
            (bSwitchLvOn, bSwitchHvOn) = (True, True)

            numFailedSections = 0
            
            # ASIC Bonding procedure:

            self.msgPrint("1. Power on")

            # Switch off supply/supplies if already on; 0=off, 1=on
            if self.lvState[0] == 1:
                self.msgPrint("Low voltage is on, switching it off..")
                self.toggleLvSupplies()
            
            if self.hvState[0] == 1:
                self.msgPrint("High voltage is on, switching it off..")
                self.toggleHvSupplies()
                # Set bias to 0
                self.hvSetBias(0.0)
                # If bias was 200 V, need a longer delay here to allow the voltage drop
                if self.biasState[0] > 199.0:
                    self.msgPrint("HV bias was 200 V, Waiting 8 additional seconds..")
                    time.sleep(8)

            # 1.Power on

            if bSwitchLvOn:
                self.msgPrint("Low voltage is off, switching it on..")
                self.toggleLvSupplies()
            
            if bSwitchHvOn:
                # Set bias to 50
                self.hvSetBias(50.0)
                self.msgPrint("High voltage is off, switching it on..")
                self.toggleHvSupplies()
            
            # Record failed test message(s)
            errorMessages = []
            
            # 2. Check and record current (1A < I < 4A)

            self.msgPrint("2. Check and record current (1A < I < 4A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (1 < sensorCurrent < 4):
                passFailString = "FAIL"
                errorMessages.append("Failed Test 2. current: %.2f A (not 1A < I < 4A)" % sensorCurrent)
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)

            # Ensure short exposure XML file used
            self.currentParams['cmdSequenceFile'] = self.currentParams['testingShortExposureFile']

            # 3. Serial Load
            self.msgPrint("3. Serial Load")
            self.appMain.deviceConfigure(self.currentParams)
            #     Ensure serial load XML file selected (executing Configure proven redundant?)
            paramName = 'femAsicSetupLoadMode' # 0=Parallel, 1=Serial
            self.setApiValue(paramName, 1)

            # 4. Check and record current (8A < I <= 10A)
            self.msgPrint("4. Check and record current (8A < I <= 10A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (8 < sensorCurrent < 10):
                passFailString = "FAIL"
                errorMessages.append("Failed Test 4. current: %.2f A (not 8A < I <= 10A)" % sensorCurrent)
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)
            
            self.appMain.deviceConfigure(self.currentParams)

            # 5. Readout Data
            self.msgPrint("5. Readout Data")
            self.appMain.deviceRun(self.currentParams)
            self.fileName = self.appMain.lastDataFile
            self.msgPrint("Produced HDF5 file: '%s'" % self.fileName)
            
            if self.fileName == None:
                self.msgPrint("Error: No file received")
            else:
                # 6.Check for out of range pixels. Are these full ASICs? Columns or individual pixels.
                self.msgPrint("6. Check for out of range pixels")
                numBadPixels = self.checkOutOfRangePixels(train=0, image=0, miscDescription='[6. Pixels out of range]')
                if numBadPixels == 0:
                    self.msgPrint("6. Module %s has no bad pixels, that's a %s" % (self.moduleString, "PASS"))
                else:
                    self.msgPrint("6. Module %s has %d bad pixel(s), that's a %s" % (self.moduleString, numBadPixels, "FAIL"))
                    errorMessages.append("Failed Test 6. Module has %d out of range pixel(s)" % numBadPixels)
                    numFailedSections += 1
            
            # 7. Power off
            self.msgPrint("7. Power Off")

            self.toggleLvSupplies()
            time.sleep(3)
            self.toggleHvSupplies()
            time.sleep(3)

            # 8. Power on
            self.msgPrint("8. Power On")

            self.toggleLvSupplies()
            time.sleep(3)
            self.toggleHvSupplies()
            time.sleep(3)
            
            # 9. Check and record current (1A < I < 4A)
            self.msgPrint("9. Check and record current (1A < I < 4A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (1 < sensorCurrent < 4):
                passFailString = "FAIL"
                errorMessages.append("Failed Test 9. current: %.2f A (not 1A < I < 4A)" % sensorCurrent)
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)
            
            # 10. Parallel load
            self.msgPrint("10. Parallel Load")
            self.appMain.deviceConfigure(self.currentParams)
            # Ensure parallel XML file loading:
            paramName = 'femAsicSetupLoadMode' # 0=Parallel, 1=Serial
            self.setApiValue(paramName, 0)
            
            # 11. Check and record current (8A <I =< 10A)
            self.msgPrint("11. Check and record current (8A < I <= 10A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (8 < sensorCurrent < 10):
                passFailString = "FAIL"
                errorMessages.append("Failed Test 11. current: %.2f A (not 8A < I <= 10A)" % sensorCurrent)
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)

            # 12.Readout data
            self.msgPrint("12. Readout Data")
            self.appMain.deviceRun(self.currentParams)

            self.fileName = self.appMain.lastDataFile
            self.msgPrint("Produced HDF5 file: '%s'" % self.fileName)
            
            if self.fileName == None:
                self.msgPrint("Error: No file received")
            else:
                # 13. Check for out of range pixels. Are these full ASICs? Columns or individual pixels. Is there are any different compared to test 6?
                self.msgPrint("13. Check for out of range pixels")
                numBadPixels = self.checkOutOfRangePixels(train=0, image=0, miscDescription='[13. Pixels out arrange]')
                if numBadPixels == 0:
                    self.msgPrint("13. Module %s has no bad pixels, that's a %s" % (self.moduleString, "PASS"))
                else:
                    self.msgPrint("13. Module %s has %d bad pixel(s), that's a %s" % (self.moduleString, numBadPixels, "FAIL"))
                    errorMessages.append("Failed Test 13. Module has %d out of range pixel(s)" % numBadPixels)
                    numFailedSections += 1
            
            # Summarise; Report how many failures (if any)
            if numFailedSections == 0:
                self.msgPrint("Module %s is fine, failing none of the tests." % self.moduleString)
            else:
                self.msgPrint("Module %s is problematic, it failed %d test(s)." % (self.moduleString, numFailedSections))
                for errorLine in errorMessages:
                    self.msgPrint("* %s." % errorLine)

            # Hack DAQ tab to restore it to ready state
            self.appMain.deviceState = LpdFemGui.DeviceReady
            self.appMain.runStateUpdate()

        except Exception as e:
            print >> sys.stderr, "\n", traceback.print_exc()
            self.msgPrint("Exception during ASIC bonding test: %s" % e, bError=True)

    def locateShortedPixels(self):
        ''' Locate any pixel(s) have the value 0 or 4095 '''
        
        minimumValues = []
        maximumValues = []
        for row in range(self.numRows):
            for column in range(self.numCols):
                
                if self.moduleData[row][column] == 0:
                    #print >> sys.stderr, "A zero at [{0:>2}][{1:>3}]".format(row, column)
                    minimumValues.append( (row, column))
                elif self.moduleData[row][column] == 4095:
                    #print >> sys.stderr, "A Max at [{0:>2}][{1:>3}]".format(row, column)
                    maximumValues.append( (row, column))

        minCount = minimumValues.__len__()
        maxCount = maximumValues.__len__()

        # Assuming that there are at least one of each, look for neighbouring pair(s)
        neighbourStr = ""
        adjacentPixelPairs = 0
        maybeNewLine = ""
        if maxCount > 0 and minCount > 0:
            # Check all pixel pairs containing a zero, to see if they are adjacent to any pixel pair containing a maximum
            for (minRow, minColumn) in minimumValues:
                for (adjacentRow, adjacentColumn) in self.neighbours(minimumValues, minRow, minColumn):

                    if (adjacentRow, adjacentColumn) in maximumValues:
                        # Limit page width if more than three pairs detected
                        if (adjacentPixelPairs % 3 == 0):
                            maybeNewLine = "\n"
                        else:
                            maybeNewLine = ""

                        neighbourStr += "{0}Min: [{1:>2}][{2:>3}] & Max: [{3:>2}][{4:>3}].    ".format(maybeNewLine, minRow, minColumn, adjacentRow, adjacentColumn)
                        adjacentPixelPairs += 1

        return (minCount, maxCount, adjacentPixelPairs, neighbourStr)

    def neighbours(self, data, row, col):
        ''' Obtain neighbours within array, omitting diagonal ones '''
        for i in row-1, row, row+1:
            if i < 0 or i == self.numRows: continue    # Outside data's row
            for j in col-1, col, col+1:
                if j < 0 or j == self.numCols: continue # Outside data's column
                if i == row and j == col: continue      # diagonal neighbour
                if i == row-1 and j== col-1: continue   # diagonal
                if i == row-1 and j== col+1: continue   # diagonal
                if i == row+1 and j== col-1: continue   # diagonal
                if i == row+1 and j== col+1: continue   # diagonal
                #yield data[i][j]
                yield (i, j)

#    def setCachedValue(self, variable, value):
#        ''' Change cached value of the GUI variable (Do not confuse with setApiValue) '''
#        self.appMain.setCachedParam(variable, value)
#        
#    def getCachedValue(self, variable):
#        ''' Get cached value of the GUI variable (Do not confuse with getApiValue) '''
#        return self.appMain.getCachedParam(variable)
    
    def getApiValue(self, paramName):
        
        (rc, val) = self.device.paramGet(paramName)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("*Couldn't read %s, rc= %s" % (paramName, rc), bError=True)
        return val

    def setApiValue(self, paramName, newValue):
        
        rc = self.device.paramSet(paramName, newValue)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Error changing %s to %s, rc: %s" % (paramName, str(newValue), rc), bError=True)

    def hvSetBias(self, biasStr):
        ''' Change HV bias '''        
        try:
            hvBias = float(biasStr)
            self.appMain.pwrCard.hvBiasSet(hvBias)
            self.appMain.mainWindow.pwrTab.powerStatusUpdateDone()
            
        except ValueError:
            self.msgPrint("Exception setting HV bias: %s" % biasStr, bError=True)
            
        self.msgPrint("Waiting %d seconds for new bias to settle.." % (self.hardwareDelay+3))
        time.sleep(self.hardwareDelay+3)
    
    def toggleLvSupplies(self):

        currentState = self.appMain.pwrCard.lvEnableGet()        
        nextState = not currentState
        self.appMain.pwrCard.lvEnableSet(nextState)

        stateNow = self.appMain.pwrCard.lvEnableGet()
        if nextState != None and stateNow != nextState:
            self.msgPrint("ERROR: failed to switch LV enable to %d" % nextState, bError=True)
        else:
            self.appMain.mainWindow.pwrTab.powerBtnStateUpdate('lv', stateNow)
        self.appMain.mainWindow.pwrTab.powerStatusUpdateDone()
        time.sleep(self.hardwareDelay)
        
    def toggleHvSupplies(self):
        
        currentState = self.appMain.pwrCard.hvEnableGet()        
        nextState = not currentState
        self.appMain.pwrCard.hvEnableSet(nextState)

        stateNow = self.appMain.pwrCard.hvEnableGet()
        if nextState != None and  stateNow != nextState:
            self.msgPrint("ERROR: failed to switch HV enable to %d" % nextState, bError=True)
        else:
            self.appMain.mainWindow.pwrTab.powerBtnStateUpdate('hv', stateNow)
        self.appMain.mainWindow.pwrTab.powerStatusUpdateDone()
        time.sleep(self.hardwareDelay)
        
    def obtainPowerSuppliesState(self, powerState):

        # Loop over LHS and RHS power cards and update display
        for powerCard in range(self.appMain.pwrCard.numPowerCards):

            paramName = 'asicPowerEnable' + str(powerCard)
            self.lvState[powerCard] = powerState[paramName]    # 0 = Off, 1 = On

            paramName = 'sensorBiasEnable' + str(powerCard)
            self.hvState[powerCard] = powerState[paramName]    # 0 = Off, 1 = On

            paramName = 'sensorBias' + str(powerCard)
            self.biasState[powerCard] = powerState[paramName]
        
#        print >> sys.stderr, "LpdAsicTester.obtainPowerSuppliesState()"
#        print >> sys.stderr, "sensorBias0: ", powerState['sensorBias0']
#        print >> sys.stderr, "sensorBias1: ", powerState['sensorBias1']

        if self.lvState[0] != self.lvState[1]:
            self.msgPrint("LpdAsicTester Error: LV status mismatch between power card", bError=True)

        if self.hvState[0] != self.hvState[1]:
            self.msgPrint("LpdAsicTester Error: HV status mismatch between power card", bError=True)

    def checkLeakageCurrent(self):
        ''' Check leakage current by looking at image 0 and image 3, comparing differences pixel by pixel '''
        
        self.train = 0
        self.image = 0
        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.fileName):
            if not self.analyseFile():
                self.msgPrint("Error opening captured file: %s" % self.fileName, bError=True)
                return -1
        else:
            self.msgPrint("Analysis Error: File (%s) doesn't exist" % self.fileName, bError=True)
            return -1
        # Save module data, then repeat for image 3
        self.image0Data = self.moduleData
        
        # Repeat for image 3
        self.image = 3
        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.fileName):
            if not self.analyseFile():
                self.msgPrint("Error opening captured file: %s" % self.fileName, bError=True)
                return -1
        else:
            self.msgPrint("Analysis Error: File (%s) doesn't exist" % self.fileName, bError=True)
            return -1
        # Save module data
        self.image3Data = self.moduleData

        # Create empty array 
        leakageCurrentArray = np.zeros(32*128, dtype=np.uint16)
        leakageCurrentArray = np.reshape(leakageCurrentArray, (32, 128))

        # Note unconnected in an array (to fill the second plot: )
        unconnectedPixelsArray = np.zeros(32*128, dtype=np.uint16)
        unconnectedPixelsArray = np.reshape(unconnectedPixelsArray,(32, 128))

        # Assuming image 3 contain higher values that image 0; Are there any negative values?
        negativeValues = {}
        difference = 0
        threshold = 20
        # Simultaneously look for unconnected pixels
        numUnconnectedPixels = 0
        for row in range(self.numRows):
            for column in range(self.numCols):
                if self.image3Data[row][column] < self.image0Data[row][column]:
                    difference = self.image0Data[row][column] - self.image3Data[row][column]
                    negativeValues[(row, column)] = abs(difference)
                    #print >> sys.stderr, "DIFF @ [{0:>2}][{1:>2}] = {2:>4}, self.image3Data: {3:>4}, self.image0Data, {4:>4}".format(row, column, difference, self.image3Data[row][column], self.image0Data[row][column])
                else:
                    difference = self.image3Data[row][column] - self.image0Data[row][column]
                
                # If pixels differ by less than threshold, they are unconnected
                if difference < threshold:
                    unconnectedPixelsArray[row][column] = 1
                    numUnconnectedPixels += 1

        # Go through each pixel and subject image 0's value from image 3's value
        for row in range(self.numRows):
            for column in range(self.numCols):
                # Invert negative value(s) if present
                if (row, column) in negativeValues:
                    leakageCurrentArray[row][column] = negativeValues[(row, column)]
                    continue
                leakageCurrentArray[row][column] = self.image3Data[row][column] - self.image0Data[row][column]

        # Let's try plotting this in the existing ASIC window..
        # Signal hdf5 image (data)
        self.appMain.asicWindow.dataSignal.emit(self.moduleData, unconnectedPixelsArray, self.moduleDescription, self.moduleNumber, "Leakage Current")
        return numUnconnectedPixels
        
    def checkOutOfRangePixels(self, train, image, miscDescription="", bSuppressPixelInfo=False):
        ''' Check self.fileName's pixels, image 0 for out of range pixels 
            out of range being described as greater than 2 standard deviations '''
        self.train  = train
        self.image  = image

        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.fileName):
            if not self.analyseFile():
                self.msgPrint("Error opening captured file: %s" % self.fileName, bError=True)
                return -1
        else:
            self.msgPrint("Analysis Error: File (%s) doesn't exist" % self.fileName, bError=True)
            return -1

        # Check for bad pixel(s)
        deviatedPixels = self.testPixelsStandardDeviation()
        # Plot results
        self.plotFaultyPixels(deviatedPixels, miscDescription)
        
        numBadPixels = 0
        # Display bad pixels (unless suppressed)
        if not bSuppressPixelInfo:
            lastRow = 0
            badPixelsString = ""
            for pair in deviatedPixels:
                if lastRow != pair[0]:
                    self.msgPrint("Row %2d detected pixel(s) at column: %s" % (lastRow, badPixelsString[:-2]))
                    lastRow = pair[0]
                    badPixelsString = ""
                badPixelsString += str(pair[1]) + ", "
            
            numBadPixels = deviatedPixels.__len__()
            # If bad pixel(s) detected, display last row and number of bad pixels:
            if numBadPixels > 0:
                self.msgPrint("Row %2d detected pixel(s) at column: %s" % (lastRow, badPixelsString[:-2]))
            self.checkTheColumns()
        return numBadPixels

    def plotFaultyPixels(self, deviatedPixels, miscDescription):
        ''' Display plot of black/white image indicating faulty pixel(s) '''

        # Create empty array 
        faultyPixelsArray = np.zeros(32*128, dtype=np.uint16)
        faultyPixelsArray = np.reshape(faultyPixelsArray, (32, 128))

        for row, column in deviatedPixels:
            faultyPixelsArray[row][column] = 1

        # Signal hdf5 image (data)
        self.appMain.asicWindow.dataSignal.emit(self.moduleData, faultyPixelsArray, self.moduleDescription, self.moduleNumber, miscDescription)

    def analyseFile(self):
        ''' Open file, extracting one image along with meta data and calculate standard deviation and average '''

        with h5py.File(self.fileName, 'r') as hdfFile:

            try:            
                # Read in the train, image counter and timestamp arrays
                trainNumber = hdfFile['/lpd/data/trainNumber'][...]
                imageNumber = hdfFile['/lpd/data/imageNumber'][...]
                timeStamp   = hdfFile['/lpd/data/timeStamp'][...]
                # Get max train and image number form arrays
                self_maxTrainNumber = np.amax(trainNumber)
                self_maxImageNumber = np.amax(imageNumber)
                # Read in the metadata
                meta = hdfFile['/lpd/metadata']
                # Parse the readout configuration XML blob
                readoutConfig = LpdReadoutConfig(meta['readoutParamFile'][0])
                readoutParams = {}
                for (param, val) in readoutConfig.parameters():
                    readoutParams[param] = val
                # Get number of trains from metadata and check array against argument
                numTrains = meta.attrs['numTrains']
                # Calculate image offset into array and range check (should be OK)
                imgOffset = (self.train * (self_maxImageNumber + 1)) + self.image
                if imgOffset > imageNumber.size:
                    self.msgPrint("Analysis Error: Requested image (%d) exceeds number of images available (%d)" \
                    % (imgOffset, imageNumber.size), bError=True)
                    return False
                # Read in the image array
                image = hdfFile['/lpd/data/image']
                imageData = image[imgOffset,:,:]    # Only read in the specified image
    
                # Determine row/col coordinates according to selected ASIC module
                (rowStart, colStart) = self.asicStartingRowColumn(self.moduleNumber)
                self.moduleData  = imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols]
    
                self.moduleStd = np.std(self.moduleData)
                self.moduleAverage = np.mean(self.moduleData)
            except Exception as e:
                self.msgPrint("Analysis Error while processing file: %s" % e, bError=True)
                return False
            self.appMain.asicWindow.timeStampSignal.emit(timeStamp[imgOffset])
            self.appMain.asicWindow.trainSignal.emit(trainNumber[imgOffset])
            self.appMain.asicWindow.imageSignal.emit(imageNumber[imgOffset])
            return True 

    def checkTheColumns(self):
        ''' Print whether data contains dead column(s) or nonesafer '''
        # Look for dead column(s)
        deadColumns = self.detectDeadColumns()
        numDeadColumns = deadColumns.__len__()
        if numDeadColumns > 0:
            self.msgPrint("There are %d dead column(s)" % numDeadColumns)
            # Which ASIC and ADC numbers to they correspond to?
            for column in deadColumns:
                (ASIC, ADC) = self.identifyAdcLocations(column)
                self.msgPrint("Dead column detected in ASIC: %1d ADC: %2d" % (ASIC, ADC))
        else:
            self.msgPrint("There are no dead columns")
    

    def detectDeadColumns(self):
        ''' Check moduleData (32 x 128 ASIC) whether any dead column(s),
            if column average's is beyond 2 standard deviations of module's average
            Returns a(n empty) list containing column number(s) '''
        deadColumns = []
        for column in range(self.moduleData.shape[1]):
            columnTotal = 0
            for row in range(self.moduleData.shape[0]):
                columnTotal += self.moduleData[row][column]
            columnAverage = columnTotal/32.0

            difference = 0
            # Is column average greater than module average?
            if columnAverage > self.moduleAverage:
                difference = columnAverage - self.moduleAverage
            else:
                difference = self.moduleAverage - columnAverage
            
            # Does different exceeded 2 standard deviations?
            if difference > (2*self.moduleStd):
                deadColumns.append(column)
        return deadColumns
    
    def identifyAdcLocations(self, column):
        ''' Convert column number into ASIC, ADC location 
            Column ASIC ADCs
             0-15   0    0-15
            16-31   1    0-15
            32-47   2    0-15
            etc
        '''
        asicNum = -1
        adcNum = -1
        if (-1 < column < 16):
            asicNum = 0
        elif (15 < column < 32):
            asicNum = 1
        elif (31 < column < 48):
            asicNum = 2
        elif (47 < column < 64):
            asicNum = 3
        elif (63 < column < 80):
            asicNum = 4
        elif (79 < column < 96):
            asicNum = 5
        elif (95 < column < 112):
            asicNum = 6
        elif (111 < column < 128):
            asicNum = 7
        adcNum = column % 16
        return (asicNum, adcNum)

    def checkPixelAgainstStd(self, row, col):
        ''' Is 'pixel' outside +/- 2 standard deviations? '''
        bPixelDifferent = False
        
        pixel = self.moduleData[row][col]
        difference = 0 
        if pixel > self.moduleAverage:  difference = pixel - self.moduleAverage
        else:                           difference = self.moduleAverage - pixel

        # Does difference exceed 2 standard deviations?            
        if difference > (2*self.moduleStd):
            bPixelDifferent = True
        return bPixelDifferent

    def asicStartingRowColumn(self, module):
        ''' Determining upper left corner's row/col coordinates according to selected ASIC module '''
        
        (row, column) = (-1, -1)
        if module == 0:   (row, column) = (0, 128)    # ASIC module #1
        elif module == 1: (row, column) = (32, 128)   # ASIC module #2
        elif module == 2: (row, column) = (64, 128)   # ASIC module #3
        elif module == 3: (row, column) = (96, 128)   # ASIC module #4
        elif module == 4: (row, column) = (128, 128)  # ASIC module #5
        elif module == 5: (row, column) = (160, 128)  # ASIC module #6
        elif module == 6: (row, column) = (192, 128)  # ASIC module #7
        elif module == 7: (row, column) = (224, 128)  # ASIC module #8

        elif module == 15:(row, column) = (0, 0)      # ASIC module #16
        elif module == 14:(row, column) = (32, 0)     # ASIC module #15
        elif module == 13:(row, column) = (64, 0)     # ASIC module #14
        elif module == 12:(row, column) = (96, 0)     # ASIC module #13
        elif module == 11:(row, column) = (128, 0)    # ASIC module #12
        elif module == 10:(row, column) = (160, 0)    # ASIC module #11
        elif module == 9: (row, column) = (192, 0)    # ASIC module #10
        elif module == 8: (row, column) = (224, 0)    # ASIC module #9

        return (row, column)

#    @timingMethodDecorator
    def testPixelsStandardDeviation(self):
        deviatedPixels = []
        for row in range(self.moduleData.shape[0]):
            for col in range(self.moduleData.shape[1]):
    
                bDiffers = self.checkPixelAgainstStd(row, col)
                if bDiffers:
                    deviatedPixels.append((row, col))
        return deviatedPixels

    ''' Functions copied from LpdFemGuiPowerTesting '''

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdAsicTester.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdAsicTester.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

    def readPowerCards(self):
        ''' Read all sensors on both power card '''

        numSensors = 16
        numPowerCards = 2

        # Count how many error encountered
        errorCount = 0
        results = {}
        TVCparamsTypes = [#'Temp', 'Voltage', 
                          'Current']
        
        miscParamTypes = ['sensorBias'#, 'powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                      #, 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                      #'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp'
                      ]
        
        for sensor in range(numSensors):
            
            for paramType in TVCparamsTypes:
                paramName = 'sensor' + str(sensor) + paramType
                
                (rc, val) = self.device.paramGet(paramName)
    
                results[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.msgPrint("readPowerCards Exception: Reading %s returned: %d: %s" % (paramName, rc, self.device.errorStringGet()), bError=True)
                    errorCount += 1
                    if errorCount > 2:
                        self.msgPrint("readPowerCards Exception: Detected three errors, aborting..", bError=True)
                        return []
        
        for powerCard in range(numPowerCards):
            
            for paramType in miscParamTypes:
                paramName = paramType + str(powerCard)
                
                (rc, val) = self.device.paramGet(paramName)

                results[paramName] = val
                if rc != LpdDevice.ERROR_OK:    
                    self.msgPrint("readPowerCards Exception: Reading %s returned: %d: %s" % (paramName, rc, self.device.errorStringGet()), bError=True)
                    errorCount += 1
                    if errorCount > 2:
                        self.msgPrint("readPowerCards Exception: Found three errors, aborting..", bError=True)
                        return []
        return results

    def readCurrent(self):
        ''' Read moduleNumber's current (as required by Wafer Probing and ASIC Bonding Test Routines) '''

        #TODO: Sort out this dirty hack:
        sensorIdx = -1
        if self.moduleNumber == LpdAsicTester.LHS_MODULE:
            sensorIdx = 9
        if self.moduleNumber == LpdAsicTester.RHS_MODULE:
            sensorIdx = 8
        
        try:
            results = self.readPowerCards()
            sensorCurrent = results['sensor%sCurrent' %  sensorIdx]
        except Exception as e:
            self.msgPrint("Error: Couldn't read module's current: %s" % e, bError=True)
            return -1
        
        # Wait one second otherwise logging performed out of sequence
        time.sleep(1)
        #print >> sys.stderr, "Module %s current: %.2f A" % (self.moduleString, results['sensor%sCurrent' %  sensorIdx])
        return sensorCurrent

