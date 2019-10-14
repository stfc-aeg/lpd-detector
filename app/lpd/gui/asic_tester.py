
from readout_config import LpdReadoutConfig
from lpd.device import LpdDevice
# Needed to restore fem GUI state:
from lpd.gui.state import LpdFemState

import traceback        # Improves debugging
import numpy as np
import h5py, time, sys
from matplotlib import cbook
import matplotlib.pyplot as plt
import matplotlib.text as text
import matplotlib
import argparse
import timeit, time, os.path
from lpd.analysis import analysis_creation
import gui
import main_power_tab
from main_power_tab import LpdFemGuiMainPowerTab


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

    RHS_MODULE = 10 #15
    LHS_MODULE = 12 #0 # 0 is the REAL LHS module !
    
    def __init__(self, app_main, device):
        
        super(LpdAsicTester, self).__init__()    # Required for pyqtSignal
        self.app_main = app_main
        self.device = device
        self.lpdFemGui = gui.LpdFemGui
        
        # Established signals (and slots)
        self.messageSignal = self.app_main.mainWindow.testTab.messageSignal

        # Test session parameters
        self.currentParams = {}

        # Copy defaults from file (via LpdFemGui class)
        self.currentParams = self.app_main.cached_params.copy()
        # Ensure a set of known defaults (common to all tests)
        self.currentParams['liveViewEnable']                = False
        self.currentParams['femAsicGainOverride']           = 100   # Copied into femAsicGain by LpdFemGui.deviceConfigure() !
                                                                    # LpdDeviceParameters' femAsicGainOverride is different!
        self.currentParams['femAsicPixelFeedbackOverride']  = 1     # 0=50pF, 1=5pF
        self.currentParams['numTrain']                      = 10
        self.currentParams['fileWriteEnable']               = True
        self.currentParams['arduinoShutterEnable']          = False
        self.currentParams['readoutParamFile']              = self.currentParams['testingReadoutParamFile']
        self.currentParams['setupParamFile']                = self.currentParams['testingSetupParamFile']
        self.currentParams['run_number']                    = self.currentParams['runNumber']

        self.moduleString = "-1"
        self.moduleDescription = ""
        self.tilePosition = ""
        self.miniConnector = 0
        
        self.lvState   = [0, 0]
        self.hvState   = [0, 0]
        self.biasState = [0, 0]        

        self.hardwareDelay  = 3
        self.moduleNumber   = 0
        self.file_name       = ""
        self.image          = 0
        self.train          = 0
        self.maxImageNumber = 0
        self.maxTrainNumber = 0
        (self.numRows, self.numCols) = (32, 128)
        
        self.moduleStd      = -1.0
        self.moduleAverage  = -1.0
        self.runNumber      = 0
        

    def msgPrint(self, message, bError=False):
        ''' Send message to LpdFemGuiMainTestTab to be displayed there '''
        self.messageSignal.emit(message, bError)

    def setModuleDescription(self, moduleDescription):
        ''' Enable LpdFemGuiMainTestTab to communicate module description, i.e. "00135"
            Note that RHS/LHS determined by moduleLhsSel/moduleRhsSel in the GUI '''
        self.moduleDescription = moduleDescription

    def setMiniConnector(self, miniConnector):
        '''Set the mini connector for tile analysis''' 
        self.miniConnector = miniConnector
    
    def setHvEditBox(self, hv):
        '''Set the hv input for the test tab'''
        self.hv = hv
    
    def verifyJsonFileNames(self):
        ''' Check that the user-specified filenames in the .json file are valid '''
        xmlFileNames = [self.currentParams['testingSetupParamFile'], self.currentParams['testingReadoutParamFile'],
                        self.currentParams['testingLongExposureFile'], self.currentParams['testingShortExposureFile'] ]
        bErrorOk = True
        for fileName in xmlFileNames:
            if not os.path.isfile(fileName):
                self.msgPrint("Error inside .json File: Cannot find '%s'" % fileName, bError=True)
                bErrorOk = False
        return bErrorOk

    def executeBondingTest(self, moduleNumber, originalConnectorId, testType):
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
            self.setModuleType(moduleNumber)

            #increment run numbers
            self.runNumber = self.app_main.getCachedParam('runNumber')+1
            self.app_main.setCachedParam('runNumber', self.runNumber)
            
            # Checking current LV, HV status; values saved to self.lvState[], self.hvState[]
            self.obtainPowerSuppliesState(self.app_main.pwr_card.powerStateGet())
           
            # ASIC Bonding procedure:
            self.msgPrint("1: Power on")

            # Switch off supply/supplies if already on; 0=off, 1=on           
            if self.hvState[0] == 1:
                self.msgPrint("High voltage is on, switching it off..")
                self.toggleHvSupplies()
                # Set bias to 0
                self.hvSetBias(0.0)
                # If bias was 200 V, need a longer delay here to allow the voltage drop
                if self.biasState[0] > 199.0:
                    self.msgPrint("HV bias was 200 V, Waiting 8 additional seconds..")
                    time.sleep(8)

            if self.lvState[0] == 1:
                self.msgPrint("Low voltage is on, switching it off..")
                self.toggleLvSupplies()

            # Power on
            self.msgPrint("Low voltage is off, switching it on..")
            self.toggleLvSupplies()
            self.msgPrint("High voltage is off, switching it on..")
            self.toggleHvSupplies()
            
            # Check HV bias level:
            if testType == "ASIC":
                self.msgPrint("2: Power on sensor bias (HV) 50V")
                self.hvSetBias(50.0) 
            elif testType == "Sensor": 
                self.msgPrint("2: Power on sensor bias (HV) %s V" % self.hv)
                powerCardResults = self.readPowerCards()
                measuredBiasLevel = powerCardResults['sensorBias0']

                try: 
                    timeout = time.time() + 30
                    while not (float(self.hv)-2 < measuredBiasLevel  < float(self.hv)+2):
                        powerCardResults = self.readPowerCards()
                        measuredBiasLevel = powerCardResults['sensorBias0']           
                        self.msgPrint("Bias level is %f V, changing it to be %s v" %(measuredBiasLevel, str(self.hv)))
                        #change the HV bias 
                        self.hvSetBias(float(self.hv), do_sleep=False)                    
                        time.sleep(1)
                        if timeout < time.time() or (float(self.hv)-2 < measuredBiasLevel  < float(self.hv)+2) :        
                            break
                except Exception as e:
                    self.msgPrint(" Exception: %s" % e)      
                self.msgPrint("Bias now set to %s V" % self.hv)

            #Get the pre configuration current to print on analysis pdf 
            powerCardResults = self.readPowerCards()
            self.preConfigCurrent = powerCardResults['sensor%iCurrent'%originalConnectorId]

            if testType == "ASIC":
                self.msgPrint("3. Take data with short exposure command sequence")
                # Ensure short exposure XML file used
                self.currentParams['cmdSequenceFile'] = self.currentParams['testingShortExposureFile']
            elif testType == "Sensor": 
                self.msgPrint("3. Take data with long exposure command sequence")
                # Set long exposure XML file, configure device
                self.currentParams['cmdSequenceFile'] = self.currentParams['testingLongExposureFile']
            
            # Ensure XML file load in parallel:
            self.msgPrint("Parallel Load")
            paramName = 'femAsicSetupLoadMode' # 0=Parallel, 1=Serial
            self.setApiValue(paramName, 0)
            self.app_main.deviceConfigure(self.currentParams)

            #Get the post configuration currents 
            powerCardResults = self.readPowerCards()
            self.postConfigCurrent = powerCardResults['sensor%iCurrent'%originalConnectorId]
            
            # Readout Data
            self.msgPrint("Readout Data")
            self.app_main.deviceRun(self.currentParams)
            self.file_name = self.app_main.last_data_file
            self.msgPrint("Produced HDF5 file: '%s'" % self.file_name)

            #Pass data to the analysis pdf creator
            self.msgPrint("Creating data analysis pdf")
            self.analysisPath = self.app_main.getCachedParam('analysisPdfPath')
            pdf_name = analysis_creation.DataAnalyser(self.analysisPath, self.moduleDescription, self.runNumber, testType, self.tilePosition , self.miniConnector , self.file_name, self.preConfigCurrent, self.postConfigCurrent, self.hv)
            self.msgPrint("PDF created: %s" % pdf_name)

            # Hack DAQ tab to restore it to ready state
            self.app_main.device_state = LpdFemState.DeviceReady
            self.app_main.runStateUpdate()

        except Exception as e:
            print >> sys.stderr, "\n", traceback.print_exc()
            self.msgPrint("Exception during %s Bonding testing: %s" % (testType, e), bError=True)


    def locateShortedPixels(self):
        ''' Locate any pixel(s) have the value 0 or 4095 '''
        
        minimumValues = []
        maximumValues = []
        for row in range(self.numRows):
            for column in range(self.numCols):
                
                if self.moduleData[row][column] == 0:
                    minimumValues.append( (row, column))
                elif self.moduleData[row][column] == 4095:
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
    
    def getApiValue(self, paramName):
        
        (rc, val) = self.device.paramGet(paramName)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("*Couldn't read %s, rc= %s" % (paramName, rc), bError=True)
        return val

    def setApiValue(self, paramName, newValue):
        
        rc = self.device.paramSet(paramName, newValue)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Error changing %s to %s, rc: %s" % (paramName, str(newValue), rc), bError=True)

    def hvSetBias(self, biasStr, do_sleep=True):
        ''' Change HV bias '''        
        try:
            self.hvBias = float(biasStr)
            self.app_main.pwr_card.hvBiasSet(self.hvBias)
            self.app_main.mainWindow.pwrTab.powerStatusUpdateDone()
            
        except ValueError:
            self.msgPrint("Exception setting HV bias: %s" % biasStr, bError=True)
        
        if do_sleep:
            self.msgPrint("Waiting %d seconds for new bias to settle.." % (self.hardwareDelay+3))
            time.sleep(self.hardwareDelay+3)
    
    def toggleLvSupplies(self):

        currentState = self.app_main.pwr_card.lvEnableGet()        
        nextState = not currentState
        self.app_main.pwr_card.lvEnableSet(nextState)

        stateNow = self.app_main.pwr_card.lvEnableGet()
        if nextState != None and stateNow != nextState:
            self.msgPrint("ERROR: failed to switch LV enable to %d" % nextState, bError=True)
        else:
            self.app_main.mainWindow.pwrTab.powerBtnStateUpdate('lv', stateNow)
        self.app_main.mainWindow.pwrTab.powerStatusUpdateDone()
        time.sleep(self.hardwareDelay)
        
    def toggleHvSupplies(self):
        
        currentState = self.app_main.pwr_card.hvEnableGet()        
        nextState = not currentState
        self.app_main.pwr_card.hvEnableSet(nextState)

        stateNow = self.app_main.pwr_card.hvEnableGet()
        if nextState != None and  stateNow != nextState:
            self.msgPrint("ERROR: failed to switch HV enable to %d" % nextState, bError=True)
        else:
            self.app_main.mainWindow.pwrTab.powerBtnStateUpdate('hv', stateNow)
        self.app_main.mainWindow.pwrTab.powerStatusUpdateDone()
        time.sleep(self.hardwareDelay)
        
    def obtainPowerSuppliesState(self, powerState):

        # Loop over LHS and RHS power cards and update display
        for powerCard in range(self.app_main.pwr_card.numPowerCards):

            #paramName = 'asicPowerEnable' + str(powerCard)
            #self.lvState[powerCard] = powerState[paramName]    # 0 = Off, 1 = On
            self.lvState[powerCard] = 1

            #paramName = 'sensorBiasEnable' + str(powerCard)
            #self.hvState[powerCard] = powerState[paramName]    # 0 = Off, 1 = On
            self.hvState[powerCard] = 1
            
            #paramName = 'sensorBias' + str(powerCard)
            #self.biasState[powerCard] = powerState[paramName]
            self.biasState[powerCard] = 1

        if self.lvState[0] != self.lvState[1]:
            self.msgPrint("LpdAsicTester Error: LV status mismatch between power card", bError=True)

        if self.hvState[0] != self.hvState[1]:
            self.msgPrint("LpdAsicTester Error: HV status mismatch between power card", bError=True)

    def checkLeakageCurrent(self):
        ''' Check leakage current by looking at the first and the last image, comparing differences pixel by pixel '''
        # Open datafile to find maximum train and image number
        self.train = 0
        self.image = 0
        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.file_name):
            if not self.analyseFile():
                self.msgPrint("Error opening captured file: %s" % self.file_name, bError=True)
                return -1

            # Open again looking for the very last image (of the last train)
            self.train = self.maxTrainNumber
            self.image = self.maxImageNumber
            self.analyseFile()
        else:
            self.msgPrint("Analysis Error: File (%s) doesn't exist" % self.file_name, bError=True)
            return -1

        # Note unconnected in an array (to fill the second plot)
        unconnectedPixelsArray = np.zeros(32*128, dtype=np.uint16)
        unconnectedPixelsArray = np.reshape(unconnectedPixelsArray,(32, 128))

        # Note threshold in an array (to fill the third plot)
        thresholdPixelsArray = np.zeros(32*128, dtype=np.uint16)
        thresholdPixelsArray = np.reshape(thresholdPixelsArray,(32, 128))

        numImagesPerTrain = self.maxImageNumber+1   # Numbering begins from  0..
        
        (rowStart, colStart) = self.asicStartingRowColumn(self.moduleNumber)
        
        # Open the current data file, reading in the data but skipping the first train
        leakageFile = h5py.File(self.file_name, 'r')
        leakageData = (leakageFile['/lpd/data/image'][numImagesPerTrain:,rowStart:rowStart+self.numRows, colStart:colStart+self.numCols] & 0xFFF)
        resultArray = np.zeros((numImagesPerTrain, self.numRows, self.numCols))

        # Work out the average of each image across the trains
        for trig in range(numImagesPerTrain):
            resultArray[trig,::] = np.mean(leakageData[trig::numImagesPerTrain,::],0)

        self.firstImageAveraged = resultArray[0,:,:]    
        self.lastImageAveraged = resultArray[numImagesPerTrain-1,:,:]

#        (posCount, negCount) = (0, 0)
        # The first image generally contains higher values than the last
        difference = 0
        threshold = 300
        numUnconnectedPixels = 0

        for row in range(self.numRows):
            for column in range(self.numCols):
                difference = self.firstImageAveraged[row][column] - self.lastImageAveraged[row][column]
                unconnectedPixelsArray[row][column] = abs(difference)
                # If pixels differ by less than threshold, they are unconnected
                if difference < threshold:
                    thresholdPixelsArray[row][column] = 1
                    numUnconnectedPixels += 1
                
#                if difference > 0:
#                    posCount += 1
#                else:
#                    negCount += 1
#        print >> sys.stderr, "positive versus negative: %d versus %d" % (posCount, negCount)

        # Signal hdf5 image (data)
        self.app_main.asic_window.dataSignal.emit(self.moduleData, unconnectedPixelsArray, thresholdPixelsArray, self.moduleDescription, self.moduleNumber, threshold, "Leakage Current")
        return numUnconnectedPixels
        
    def checkOutOfRangePixels(self, train, image, miscDescription="", bSuppressPixelInfo=False):
        ''' Check self.file_name's pixels, image 0 for out of range pixels 
            out of range being described as greater than 2 standard deviations '''
        self.train  = train
        self.image  = image

        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.file_name):
            if not self.analyseFile():
                self.msgPrint("Error opening captured file: %s" % self.file_name, bError=True)
                return -1
        else:
            self.msgPrint("Analysis Error: File (%s) doesn't exist" % self.file_name, bError=True)
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
        self.app_main.asic_window.dataSignal.emit(self.moduleData, faultyPixelsArray, faultyPixelsArray, self.moduleDescription, self.moduleNumber, -1, miscDescription)

    def analyseFile(self):
        ''' Open file, extracting one image along with meta data and calculate standard deviation and average '''

        with h5py.File(self.file_name, 'r') as hdfFile:

            try:            
                # Read in the train, image counter and timestamp arrays
                trainNumber = hdfFile['/lpd/data/trainNumber'][...]
                imageNumber = hdfFile['/lpd/data/imageNumber'][...]
                timeStamp   = hdfFile['/lpd/data/timeStamp'][...]
                # Get max train and image number form arrays
                self.maxImageNumber = np.amax(imageNumber)
                self.maxTrainNumber = np.amax(trainNumber)
#                print >> sys.stderr, "self_MaxImageNumber: ", self.maxImageNumber
#                print >> sys.stderr, "self_MaxTrainNumber: ", self.maxTrainNumber
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
                imgOffset = (self.train * (self.maxImageNumber + 1)) + self.image
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
            self.app_main.asic_window.timeStampSignal.emit(timeStamp[imgOffset])
            self.app_main.asic_window.trainSignal.emit(trainNumber[imgOffset])
            self.app_main.asic_window.imageSignal.emit(imageNumber[imgOffset])
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
        self.tilePosition = self.moduleString

    def readPowerCards(self):
        ''' Read all sensors on both power card '''

        numSensors = 16
        numPowerCards = 2

        # Count how many error encountered
        errorCount = 0
        results = {}
        TVCparamsTypes = [#'Temp', 'Voltage', 
                          'Current']
        
        miscParamTypes = ['sensorBias'#, 'powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 'digitalCurrent',
                          #'sensorBiasVoltage', 'sensorBiasCurrent', 'sensorBiasEnable', 'asicPowerEnable', 'powerCardFault', 
                          #'powerCardFemStatus', 'powerCardExtStatus', 'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp'
                          ]
        
        # Fix while PowerCard is absent:
        (results['sensorBias0'], results['sensorBias1']) = (-1, -1)
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
                        return results #[]
        
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
                        return results #[]
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