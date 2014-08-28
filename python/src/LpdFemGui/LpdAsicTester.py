
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
        print "Function", methodToDecorate.__name__ + str("()"), "execution time:", stopTime - startTime, "second(s)."
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

        self.moduleString = "-1"

        self.lvState = [0, 0]
        self.hvState = [0, 0]        

        self.hardwareDelay = 3
        self.moduleNumber   = 0
        self.fileName = ""
        self.image    = 0
        self.train    = 0

        (self.numRows, self.numCols) = (32, 128)
        
        self.moduleStd = -1.0
        self.moduleAverage = -1.0

    def msgPrint(self, message, bError=False):
        ''' Send message to LpdFemGuiMainTestTab to be displayed there '''
        self.messageSignal.emit(message, bError)

    def executeAsicBondingTest(self, moduleNumber):
        ''' execute the sequence of tests defined by ASIC bond specifications '''
        
        try:
            originalCachedParams = {}
            cachedParamName = 'liveViewEnable'
            # Switch off live view flag - if set
            state = self.appMain.getCachedParam(cachedParamName)
            if state != None:
                if state == True:
                    self.appMain.mainWindow.daqTab.liveViewSelect(False)
                    # Only save original setting if enabled
                    originalCachedParams[cachedParamName] = state

#            print >> sys.stderr, "date: ", state, " and now: ", self.appMain.getCachedParam(cachedParamName)
#            print >> sys.stderr, "originalCachedParams: ", originalCachedParams

            # Obtain original parameter value(s) (before changing them..)
            originalParamValues = {}
            
            paramName = 'femAsicSetupLoadMode'
            value = self.obtainParameterValue(paramName)
            originalParamValues[paramName] = value
                        
            # Set moduleNumber and moduleString
            self.moduleNumber = moduleNumber
            self.setModuleType(moduleNumber)

            # Checking current LV, HV status
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
            else:
                print >> sys.stderr, "low voltage already off"
            
            if self.hvState[0] == 1:
                self.msgPrint("High voltage is on, switching it off..")
                self.toggleHvSupplies()
                # Set bias to 0
                self.hvSetBias(0.0)
            else:
                print >> sys.stderr, "high-voltage already off"  

            # 1.Power on

            if bSwitchLvOn:
                self.msgPrint("Low voltage is off, switching it on..")
                self.toggleLvSupplies()
            else:
                print >> sys.stderr, "Boolean says do not touch low voltage"
            
            if bSwitchHvOn:
                # Set bias to 50
                self.hvSetBias(50.0)
                self.msgPrint("High voltage is off, switching it on..")
                self.toggleHvSupplies()
            else:
                print >> sys.stderr, "Boolean says do not touch high-voltage"

            # 2. Check and record current (1A < I < 4A)
            self.msgPrint("2. Check and record current (1A < I < 4A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (1 < sensorCurrent < 4):
                passFailString = "FAIL"
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)
            
            # 3. Serial Load
            self.msgPrint("3. Serial Load")
            self.appMain.deviceConfigure()
            #     Ensure serial load XML file selected (executing Configure proven redundant?)
            paramName = 'femAsicSetupLoadMode' # 0=Parallel, 1=Serial
            self.changeParameterValue(paramName, 1)
    
            # 4. Check and record current (8A < I <= 10A)
            self.msgPrint("4. Check and record current (8A < I <= 10A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (8 < sensorCurrent < 10):
                passFailString = "FAIL"
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)
            
            # 5. Readout Data
            self.msgPrint("5. Readout Data")
            self.appMain.deviceRun()
            self.fileName = self.appMain.lastDataFile
            self.msgPrint("Produced HDF5 file: '%s'" % self.fileName)
            
            # 6.Check for out of range pixels. Are these full ASICs? Columns or individual pixels.
            self.msgPrint("6. Check for out of range pixels")
            numBadPixels = self.performAnalysis(train=0, image=0)
            if numBadPixels == 0:
                self.msgPrint("Module %s has no bad pixels, that's a %s" % (self.moduleString, "PASS"))
            else:
                self.msgPrint("Module %s has %d bad pixel(s), that's a %s" % (self.moduleString, numBadPixels, "FAIL"))
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
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)
            
            # 10. Parallel load
            self.msgPrint("10. Parallel Load")
            self.appMain.deviceConfigure()
            # Ensure parallel XML file loading:
            paramName = 'femAsicSetupLoadMode' # 0=Parallel, 1=Serial
            self.changeParameterValue(paramName, 0)
            
            # 11. Check and record current (8A <I =< 10A)
            self.msgPrint("11. Check and record current (8A < I <= 10A)")
            sensorCurrent = self.readCurrent()
            passFailString = "PASS"
            if not (8 < sensorCurrent < 10):
                passFailString = "FAIL"
                numFailedSections += 1
            self.msgPrint("Module %s current: %.2f A, that's a %s" % (self.moduleString, sensorCurrent, passFailString))
            time.sleep(1)

            # 12.Readout data
            self.msgPrint("12. Readout Data")
            self.appMain.deviceRun()

            self.fileName = self.appMain.lastDataFile
            self.msgPrint("Produced HDF5 file: '%s'" % self.fileName)
            
            # 13. Check for out of range pixels. Are these full ASICs? Columns or individual pixels. Is there are any different compared to test 6?
            self.msgPrint("13. Check for out of range pixels")
            numBadPixels = self.performAnalysis(train=0, image=0) #, moduleNumber, fileName)
            if numBadPixels == 0:
                self.msgPrint("Module %s has no bad pixels, that's a %s" % (self.moduleString, "PASS"))
            else:
                self.msgPrint("Module %s has %d bad pixel(s), that's a %s" % (self.moduleString, numBadPixels, "FAIL"))
                numFailedSections += 1
            
            # Summarise; Report how many failures (if any)
            if numFailedSections == 0:
                self.msgPrint("Module %s is fine, failing none of the tests." % self.moduleString)
            else:
                self.msgPrint("Module %s is problematic, it failed %d test(s)." % (self.moduleString, numFailedSections))

            # Restore parameter value(s) changed by this function
            for paramName in originalParamValues.keys():
                self.changeParameterValue(paramName, originalParamValues[paramName])

            # Restore cached parameter(s) change by this function
            cachedParamName = 'liveViewEnable'
            if cachedParamName in originalCachedParams:
                #print >> sys.stderr, "    * Going to restore: ", cachedParamName, originalCachedParams[cachedParamName]
                self.appMain.setCachedParam(cachedParamName, originalCachedParams[cachedParamName])

            # Hack DAQ tab to restore it to ready state
            self.appMain.deviceState = LpdFemGui.DeviceReady
            self.appMain.runStateUpdate()

        except Exception as e:
            print >> sys.stderr, "\n", traceback.print_exc()
            self.msgPrint("Exception during ASIC bonding test: %s" % e, bError=True)


    def obtainParameterValue(self, paramName):
        
        #print >> sys.stderr, " *** Reading %s.." % paramName
        (rc, val) = self.device.paramGet(paramName)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("*Couldn't read %s, rc= %s" % (paramName, rc), bError=True)
        return val

    def changeParameterValue(self, paramName, newValue):

        rc = self.device.paramSet(paramName, newValue)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Error changing %s to %d, rc: %s" % (paramName, 1, rc), bError=True)

    def hvSetBias(self, newBias):
        
        self.hvBiasSetUpdate_(newBias)
        self.msgPrint("Waiting %d seconds for new bias to settle.." % (self.hardwareDelay+3))
        time.sleep(self.hardwareDelay+3)
        
    def hvBiasSetUpdate_(self, biasStr):
        
        try:
            hvBias = float(biasStr)
            self.appMain.pwrCard.hvBiasSet(hvBias)
            self.hvBiasSetDone_()
            
        except ValueError:
            self.msgPrint("Exception setting HV bias: %s" % biasStr, bError=True)
            
    def hvBiasSetDone_(self):

        self.appMain.mainWindow.pwrTab.powerStatusUpdateDone()        
    
    def toggleLvSupplies(self):

        #self.msgPrint("Enable low voltage, then wait %d seconds" % str(self.hardwareDelay))
        self.lvEnableToggle_()
        time.sleep(self.hardwareDelay)

    def lvEnableToggle_(self):
        ''' Modified from LpdFemGuiMainPowerTab's '''
        currentState = self.appMain.pwrCard.lvEnableGet()        
        nextState = not currentState
        self.appMain.pwrCard.lvEnableSet(nextState)
        self.lvEnableToggleDone_(nextState)

    def lvEnableToggleDone_(self, requestedState=None):
        ''' Modified from LpdFemGuiMainPowerTab's '''
        stateNow = self.appMain.pwrCard.lvEnableGet()
        if requestedState != None and stateNow != requestedState:
            self.msgPrint("ERROR: failed to switch LV enable to %d" % requestedState, bError=True)
        else:
            self.appMain.mainWindow.pwrTab.powerBtnStateUpdate('lv', stateNow)
        self.appMain.mainWindow.pwrTab.powerStatusUpdateDone()
        
    def toggleHvSupplies(self):
        
        self.hvEnableToggle_()
        time.sleep(self.hardwareDelay)

    def hvEnableToggle_(self):
        ''' Modified from LpdFemGuiMainPowerTab's '''
        currentState = self.appMain.pwrCard.hvEnableGet()        
        nextState = not currentState
        self.appMain.pwrCard.hvEnableSet(nextState)
        self.hvEnableToggleDone_(nextState)
        
    def hvEnableToggleDone_(self, requestedState = None):
        ''' Modified from LpdFemGuiMainPowerTab's '''
        stateNow = self.appMain.pwrCard.hvEnableGet()
        if requestedState != None and  stateNow != requestedState:
            self.msgPrint("ERROR: failed to switch HV enable to %d" % requestedState, bError=True)
        else:
            self.appMain.mainWindow.pwrTab.powerBtnStateUpdate('hv', stateNow)
        self.appMain.mainWindow.pwrTab.powerStatusUpdateDone()

    def obtainPowerSuppliesState(self, powerState):

        # Loop over LHS and RHS power cards and update display
        for powerCard in range(self.appMain.pwrCard.numPowerCards):

            paramName = 'asicPowerEnable' + str(powerCard)
            self.lvState[powerCard] = powerState[paramName]    # 0 = Off, 1 = On

            paramName = 'sensorBiasEnable' + str(powerCard)
            self.hvState[powerCard] = powerState[paramName]    # 0 = Off, 1 = On

        if self.lvState[0] != self.lvState[1]:
            self.msgPrint("LpdAsicTester Error: LV status mismatch between power card", bError=True)

        if self.hvState[0] != self.hvState[1]:
            self.msgPrint("LpdAsicTester Error: HV status mismatch between power card", bError=True)

    def performAnalysis(self, train, image):
        ''' Analyse fileName using train, image '''
        self.train          = train
        self.image          = image
        
        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.fileName):
            if self.analyseFile():
                # Signal whether RHS/LHS module selected - This can be moved somewhere else, can't it?
                self.appMain.asicWindow.moduleSignal.emit(self.moduleNumber)
            else:
                self.msgPrint("Error opening captured file: %s" % self.fileName, bError=True)
                return -1
        else:
            self.msgPrint("Analysis Error: File (%s) doesn't exist" % self.fileName, bError=True)
            return -1

        # Check for bad pixel(s)
        deviatedPixels = self.testPixelsStandardDeviation()

        #print >> sys.stderr, " *** LpdAsicTester performanalysis() - Need to restore ***"
        
        lastRow = 0
        badPixelsString = ""
        for pair in deviatedPixels:
            if lastRow != pair[0]:
                self.msgPrint("Row %d  detected pixel(s): %s" % (lastRow, badPixelsString))
#                print >> sys.stderr, "Row %d  detected pixel(s): %s" % (lastRow, badPixelsString)
                lastRow = pair[0]
                badPixelsString = ""
            badPixelsString += str(pair)
        
        numBadPixels = deviatedPixels.__len__()
        # If bad pixel(s) detected, display last row and number of bad pixels:
        if numBadPixels > 0:
            self.msgPrint("Row %d detected pixel(s): %s" % (lastRow, badPixelsString))

        self.plotFaultyPixels(deviatedPixels)
        return numBadPixels
        
    def plotFaultyPixels(self, deviatedPixels):
        ''' Display plot of black/white (well, blue/red) image indicating faulty pixel(s) '''

        # Create empty array 
        self.faultyPixelsArray = np.zeros(32*128, dtype=np.uint16)
        self.faultyPixelsArray = np.reshape(self.faultyPixelsArray, (32, 128))

        for row, column in deviatedPixels:
            self.faultyPixelsArray[row][column] = 1

        # Signal hdf5 image (data)
        self.appMain.asicWindow.dataSignal.emit(self.moduleData, self.faultyPixelsArray, self.moduleNumber)


    def analyseFile(self):

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
                    #print >> sys.stderr, "Analysis Error: Requested image (%d) exceeds number of images available (%d)" \
                    #% (imgOffset, imageNumber.size)
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
                #print >> sys.stderr, "Analysis Error while processing file: %s" % e
                return False
            self.appMain.asicWindow.timeStampSignal.emit(timeStamp[imgOffset])
            self.appMain.asicWindow.trainSignal.emit(trainNumber[imgOffset])
            self.appMain.asicWindow.imageSignal.emit(imageNumber[imgOffset])
            return True 
    
    def detectDeadColumns(self, threshold, bLowThreshold):
        ''' Check moduleData (32 x 128 ASIC) whether any dead column(s),
            if column average's below threshold (bLowThreshold = True)
            or average exceeds threshold (bLowThreshold = False)
            Returns a(n empty) list containing column number(s) '''
        deadColumns = []
        for column in range(self.moduleData.shape[1]):    
            columnTotal = 0
            for row in range(self.moduleData.shape[0]):
                columnTotal += self.moduleData[row][column]
            columnAverage = columnTotal/32.0

            # If it's bLowThreshold, is the average less than that?
            if bLowThreshold:
                if columnAverage < threshold:
                    deadColumns.append(column)
            else:   # Not bLowThreshold, does average exceed the threshold?
                if columnAverage > threshold:
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
        
#    def neighbours(self, data, row, col):
#        ''' Obtain neighbours within array, omitting diagonal ones '''
#        for i in row-1, row, row+1:
#            if i < 0 or i == len(data): continue    # Outside data's row
#            for j in col-1, col, col+1:
#                if j < 0 or j == len(data[i]): continue # Outside data's column
#                if i == row and j == col: continue      # diagonal neighbour
#                if i == row-1 and j== col-1: continue   # diagonal
#                if i == row-1 and j== col+1: continue   # diagonal
#                if i == row+1 and j== col-1: continue   # diagonal
#                if i == row+1 and j== col+1: continue   # diagonal
#                yield data[i][j]
    
#    def checkPixelsDifferent(self, row, col, adjacent, threshold):
#        ''' Is the difference between pixel (at row/col coordinate) and it's 'adjacent' neighbour greater than threshold? '''
#        bPixelDifferent = False
#        difference = 0
#        pixel = self.moduleData[row][col]
#        if pixel > adjacent:    difference = pixel - adjacent
#        else:                   difference = adjacent - pixel
#        
#        if difference < 0:
#            difference *= -1
#            
#        if difference > threshold:
#            #print "pixel: ", pixel, " adjacent: ", adjacent, " different by: ", difference,
#            bPixelDifferent = True
#        return bPixelDifferent
    
    def checkPixelAgainstStd(self, row, col):
        ''' Is 'pixel' outside +/- 2 standard deviations? '''
        bPixelDifferent = False
        
        pixel = self.moduleData[row][col]
        difference = 0 
        if pixel > self.moduleAverage:  difference = pixel - self.moduleAverage
        else:                           difference = self.moduleAverage - pixel

        # Does difference exceed 2 standard deviations?            
        if difference > (2*self.moduleStd):
            #print "pixel: ", pixel, " adjacent: ", adjacent, " different by: ", difference,
            #print "pixel:", pixel, "mean: ", self.moduleAverage, "std:", self.moduleStd, "LOGIC:", difference > (2*self.moduleStd)
            bPixelDifferent = True
        return bPixelDifferent
            
#    def addUniquePixel(self, pixelList, row, col):
#        ''' Signal whether (row, col) tuple already in pixelList '''
#        bTuple = True
#        for (i, j) in pixelList:
#            if row == i and col == j:
#                bTuple = False
#        return bTuple

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
#    def testNeighboursForDodgyPixels(self):
#
#        dodgyPixels = []        
#        for row in range(self.moduleData.shape[0]):
#            for col in range(self.moduleData.shape[1]):
#                for neighbour in self.neighbours(self.moduleData, row, col):
#    
#                    bDiffers = self.checkPixelsDifferent(row, col, neighbour, 400)
#                    if bDiffers:
#                        #print " original pixel[" + str(row) + "][" + str(col) + "]=" + str(self.moduleData[row][col]) + " "
#                        if self.addUniquePixel(dodgyPixels, row, col):
#                            dodgyPixels.append((row, col))
#        return dodgyPixels
    
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
        TVCparamsTypes = ['Temp', 'Voltage', 'Current']
        
        miscParamTypes = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                      'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                      'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']
        
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

