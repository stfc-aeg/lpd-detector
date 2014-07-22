
from LpdReadoutConfig import *
from LpdDataContainers import *
from LpdFemGuiAnalysisWindow import *
from LpdFemGuiPowerTesting import *

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

class LpdFemGuiAnalysis(QtGui.QMainWindow):
    ''' Perform ASIC modules analysis, creating/display in results analysis window '''

    femDeviceParamsSignal = QtCore.pyqtSignal(str, int)
    
    def __init__(self, messageSignal):
        
        super(LpdFemGuiAnalysis, self).__init__()    # Required for pyqtSignal
        
        self.messageSignal = messageSignal
        try:
            self.module   = 0
            self.fileName = "" #"/u/ckd27546/workspace/tinkering/lpdData-03154.hdf5"
            self.image    = 0
            self.train    = 0

            self.analysisWindow = LpdFemGuiAnalysisWindow()
#            self.analysisWindow.show()    # Hide window for now while testing

            
        except Exception as e:
            print "LpdFemGuiAnalysis initialisation exception: %s" % e
            
        (self.numRows, self.numCols) = (32, 128)
        
        self.moduleStd = -1.0
        self.moduleAverage = -1.0

        self.femDeviceParamsSignal.connect(self.setFemDeviceParams)

    def setFemDeviceParams(self, femHost, femPort):
        
        self.femHost = femHost
        self.femPort = femPort
        print >> sys.stderr, "received: ", femHost, femPort

    def performAnalysis(self, train, image, module, fileName):
        
        self.train    = train
        self.image    = image
        self.module   = module
        self.fileName = fileName
        
        # Check hdf5 filename exist before opening it
        if os.path.isfile(self.fileName):
            if self.analyseFile():
                self.analysisWindow.moduleSignal.emit(self.module)
                self.analysisWindow.dataSignal.emit(self.moduleData)
            else:
                # Error already printed during function call, return silently here
                return
        else:
            self.messageSignal.emit("Analysis Error: File (%s) doesn't exist" % self.fileName)
            return

        # Conduct power card tests
        self.powerTesting = LpdFemGuiPowerTesting(self.femHost, self.femPort, self.messageSignal)
        self.powerTesting.testPowerCards()

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
                    self.messageSignal.emit("Analysis Error: Requested image (%d) exceeds number of images available (%d)" \
                    % (imgOffset, imageNumber.size))
                    return False
                # Read in the image array
                image = hdfFile['/lpd/data/image']
                imageData = image[imgOffset,:,:]    # Only read in the specified image
    
                # Determine row/col coordinates according to selected ASIC module
                (rowStart, colStart) = self.asicStartingRowColumn(self.module)
                self.moduleData  = imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols]
    
                self.moduleStd = np.std(self.moduleData)
                self.moduleAverage = np.mean(self.moduleData)
            except Exception as e:
                self.messageSignal.emit("Analysis Error while processing file: %s" % e)
                return False
            self.analysisWindow.timeStampSignal.emit(timeStamp[imgOffset])
            self.analysisWindow.runNumberSignal.emit(meta.attrs['runNumber'])
            self.analysisWindow.trainSignal.emit(trainNumber[imgOffset])
            self.analysisWindow.imageSignal.emit(imageNumber[imgOffset])
#            (imgOffset, timeStamp[imgOffset], meta.attrs['runNumber'], trainNumber[imgOffset], imageNumber[imgOffset])
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
#        print  "identifyAdcLocations, received column:", column, " producing asicNum:", asicNum, "adcNum:", adcNum
        return (asicNum, adcNum)
        
    def neighbours(self, data, row, col):
        ''' Obtain neighbours within array, omitting diagonal ones '''
        for i in row-1, row, row+1:
            if i < 0 or i == len(data): continue    # Outside data's row
            for j in col-1, col, col+1:
                if j < 0 or j == len(data[i]): continue # Outside data's column
                if i == row and j == col: continue      # diagonal neighbour
                if i == row-1 and j== col-1: continue   # diagonal
                if i == row-1 and j== col+1: continue   # diagonal
                if i == row+1 and j== col-1: continue   # diagonal
                if i == row+1 and j== col+1: continue   # diagonal
                yield data[i][j]
    
    def checkPixelsDifferent(self, row, col, adjacent, threshold):
        ''' Is the difference between pixel (at row/col coordinate) and it's 'adjacent' neighbour greater than threshold? '''
        bPixelDifferent = False
        difference = 0
        pixel = self.moduleData[row][col]
        if pixel > adjacent:    difference = pixel - adjacent
        else:                   difference = adjacent - pixel
        
        if difference < 0:
            difference *= -1
            
        if difference > threshold:
#            print "pixel: ", pixel, " adjacent: ", adjacent, " different by: ", difference,
            bPixelDifferent = True
        return bPixelDifferent
    
    def checkPixelAgainstStd(self, row, col):
        ''' Is 'pixel' outside +/- 2 standard deviations? '''
        bPixelDifferent = False
        
        pixel = self.moduleData[row][col]
        difference = 0 
        if pixel > self.moduleAverage:  difference = pixel - self.moduleAverage
        else:                           difference = self.moduleAverage - pixel

        # Does difference exceed 2 standard deviations?            
        if difference > (2*self.moduleStd):
#            print "pixel: ", pixel, " adjacent: ", adjacent, " different by: ", difference,
#            print "pixel:", pixel, "mean: ", self.moduleAverage, "std:", self.moduleStd, "LOGIC:", difference > (2*self.moduleStd)
            bPixelDifferent = True
        return bPixelDifferent
            
    def addUniquePixel(self, pixelList, row, col):
        ''' Signal whether (row, col) tuple already in pixelList '''
        bTuple = True
        for (i, j) in pixelList:
            if row == i and col == j:
                bTuple = False
        return bTuple

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
    def testNeighboursForDodgyPixels(self):

        dodgyPixels = []        
        for row in range(self.moduleData.shape[0]):
            for col in range(self.moduleData.shape[1]):
                for neighbour in self.neighbours(self.moduleData, row, col):
    
                    bDiffers = self.checkPixelsDifferent(row, col, neighbour, 400)
                    if bDiffers:
                        #print " original pixel[" + str(row) + "][" + str(col) + "]=" + str(self.moduleData[row][col]) + " "
                        if self.addUniquePixel(dodgyPixels, row, col):
                            dodgyPixels.append((row, col))
        return dodgyPixels
    
#    @timingMethodDecorator
    def testPixelsStandardDeviation(self):
        deviatedPixels = []
        for row in range(self.moduleData.shape[0]):
            for col in range(self.moduleData.shape[1]):
    
                bDiffers = self.checkPixelAgainstStd(row, col)
                if bDiffers:
                    deviatedPixels.append((row, col))
        return deviatedPixels
