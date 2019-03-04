
''' If not executed directly, assume it's being called from ../LpdFemGui/LpdFemGuiMainTestTab.py '''

if __name__ != "__main__":
    # Called from LpdFemGui code base
    from LpdReadoutConfig import *
    from LpdFemGui.LpdDataContainers import *#LpdFrameContainers
else:
    # Executed directly, e.g. "python AsicTesting.py file.hdf5 -t 1 -i 4 -m 15"
    from LpdFemGui.LpdReadoutConfig import *

import numpy as np
import h5py, time, sys
from matplotlib import cbook
import matplotlib.pyplot as plt
import matplotlib.text as text
import matplotlib
import argparse
import timeit, time

# Create decorator method to time code execution
def timingMethodDecorator(methodToDecorate):
    def wrapper(self, *args, **kwargs):
        startTime = timeit.default_timer()
        returnValues = methodToDecorate(self, *args, **kwargs)
        stopTime = timeit.default_timer()
        print "Function", methodToDecorate.__name__ + str("()"), "execution time:", stopTime - startTime, "second(s)."
        return returnValues
    return wrapper

class AsicTesting():
    ''' Used to develop the pixel manipulation necessary to support ASIC module testing '''

    def __init__(self, bEnableParser=True, **kwargs):
        
#        print "args", args
        print "kwargs", kwargs
        self.bDebug   = False
        self.module   = -1
        self.file_name = ""
        self.image    = -1
        self.train    = -1

        # Check whether bEnableParser supplied
        if bEnableParser:
            print "bEnableParser is true"
            # Ask the user for data file, image, train
            self.args = parseArgs()
            self.bDebug   = self.args.debug
            self.module   = self.args.module
            self.file_name = self.args.file_name
            self.image    = self.args.image
            self.train    = self.args.train
        else:
            print "bEnableParser is FALSE.: To validate the arguments.."
            # Do not use parser, validate supplied keywords
            if self.validateArguments(kwargs):
                print "argument successfully validated"
            else:
                print "could not validate arguments"
                
        (self.numRows, self.numCols) = (32, 128)
        
        self.moduleStd = -1.0
        self.moduleAverage = -1.0
        
        # Create the figure and title
        self.fig = plt.figure(1)
        self.ax = self.fig.add_subplot(111)

        (imgOffset, timeStamp, run_number, trainNumber, image_number) = self.obtainAsic()
        
        self.img = self.ax.imshow(self.moduleData, interpolation='nearest', vmin='0', vmax='4095')
        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        self.titleText = 'Run %d Train %d Image %d%sModule %d: %s' % (run_number, trainNumber, image_number, "\n", self.module, dateStr)
        self.mainTitle = plt.title(self.titleText)
        
        # Add a colour bar
        axc, kw = matplotlib.colorbar.make_axes(self.ax) #, orientation='horizontal')
        cb = matplotlib.colorbar.Colorbar(axc, self.img)
        
        # Set X and Y ticks to match data size
        (xStart, xStop, xStep)  = (16, 128, 16)
        (yStart, yStop, yStep)  = (8, 32, 8)
        (xlist, ylist) = ([], [])
        # Generate list of xticks to label the x axis
        for i in range(xStart, xStop, xStep):
            xlist.append(i)
        
        # Generate yticks for the y-axis
        for i in range(yStart, yStop, yStep):
            ylist.append(i)
        
        self.ax.set_xticks(xlist)
        self.ax.set_yticks(ylist)

# Uncommenting this block will place the title above the colour bar and not the plot..
#        # Set X and Y ticks to match data size
#        (xStart, xStop, xStep)  = (16, 128, 16)
#        (yStart, yStop, yStep)  = (8, 32, 8)
#        (xlist, ylist) = ([], [])
#        # Generate list of xticks to label the x axis
#        for i in range(xStart, xStop, xStep):
#            xlist.append(i)
#        
#        # Generate yticks for the y-axis
#        for i in range(yStart, yStop, yStep):
#            ylist.append(i)
#        
#        self.ax.set_xticks(xlist)
#        self.ax.set_yticks(ylist)

    def validateArguments(self, kwargs):
        ''' Check that the supplied dictionary contains the mandatory keys:
            file_name, train, image, module '''

        if not kwargs.has_key('file_name'):
            return False
        if not kwargs.has_key('train'):
            return False
        if not kwargs.has_key('image'):
            return False
        if not kwargs.has_key('module'):
            return False
        # All four arguments fine
#        self.bDebug   = kwargs['']
        self.module   = kwargs['module']
        self.file_name = kwargs['file_name']
        self.image    = kwargs['image']
        self.train    = kwargs['train']
        return True

    def obtainAsic(self):

        with h5py.File(self.file_name, 'r') as hdfFile:

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
                    print "ERROR: calculated image offset (%d) is larger than images stored in data (%d), quitting" \
                    % (imgOffset, imageNumber.size)
                    return
                # Read in the image array
                image = hdfFile['/lpd/data/image']
                imageData = image[imgOffset,:,:]    # Only read in the specified image
    
                # Determine row/col coordinates according to selected ASIC module
                (rowStart, colStart) = self.asicStartingRowColumn(self.module)
                self.moduleData  = imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols]
    
                self.moduleStd = np.std(self.moduleData)
                self.moduleAverage = np.mean(self.moduleData)
            except Exception as e:
                print "obtainAsic() Exception:", e
                time.sleep(3)
                
            return (imgOffset, timeStamp[imgOffset], meta.attrs['runNumber'], trainNumber[imgOffset], imageNumber[imgOffset]) 
    
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

    @timingMethodDecorator
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
    
    @timingMethodDecorator
    def testPixelsStandardDeviation(self):
        deviatedPixels = []
        for row in range(self.moduleData.shape[0]):
            for col in range(self.moduleData.shape[1]):
    
                bDiffers = self.checkPixelAgainstStd(row, col)
                if bDiffers:
                    deviatedPixels.append((row, col))
        return deviatedPixels

def parseArgs():

    parser = argparse.ArgumentParser(description="Various ASIC testing - Work in Progress.")

    parser.add_argument("file_name", help='Name of HDF5 data file to open')
    parser.add_argument("-t", "--train", type=int, default=0,
                        help="Select train number to plot")
    parser.add_argument("-i", "--image", type=int, default=0,
                        help="Select image number with train to plot")
    parser.add_argument("-m", "--module", type=int, default=0, 
                        help="ASIC module (0-15)")
    parser.add_argument("-d", "--debug", type=bool,default=False, choices=[False, True],
                        help="Programming Debug")
    args = parser.parse_args()
    print "*** type(args) =", type(args)
    return args

if __name__ == "__main__":
    
    asicTesting = AsicTesting()

    print "#=========================================================#"
    print "# Data Title:", asicTesting.titleText.replace("\n", " ")
    print "# File Name:", asicTesting.args.file_name
    print "#=========================================================#"
    
    ## Look for dead column(s)
    deadColumns = asicTesting.detectDeadColumns(30.0, True)   # Dead if column average below 30.0
#    deadColumns = asicTesting.detectDeadColumns(3250.0, False)   # Dead if column average Above 3500.0
    if deadColumns.__len__() > 0:
        print "There are ", deadColumns.__len__(), " dead column(s) in: ", deadColumns
        # Which ASIC and ADC numbers to they correspond to?
        for column in deadColumns:
            (ASIC, ADC) = asicTesting.identifyAdcLocations(column)
            print "Dead column detected in ASIC:", ASIC, "ADC:", ADC
#            print "Column: {0:>3} corresponds to ASIC: {0:>3} ADC {0:>2}".format(column, ASIC, ADC)
    else:
        print "There are no dead columns"

    dodgyPixels = asicTesting.testNeighboursForDodgyPixels()
    print "unique number of pixels:"
    lastRow = 0
    for pair in dodgyPixels:
        if lastRow != pair[0]:
                print ""
                lastRow = pair[0]
        print pair,
    print "\nThat's about", (dodgyPixels.__len__()/4.0), "dodgy pixels."

    deviatedPixels = asicTesting.testPixelsStandardDeviation()
    print "Deviated pixels: "
    lastRow = 0
    badPixelsString = ""
    for pair in deviatedPixels:
        if lastRow != pair[0]:
            print "row %d  detected pixel(s): %s" % (lastRow, badPixelsString)
            lastRow = pair[0]
            badPixelsString = ""
        badPixelsString += str(pair)
    print "row %d  detected pixel(s): %s" % (lastRow, badPixelsString)
    print "\nThat's", deviatedPixels.__len__(), "pixels."

    if asicTesting.bDebug:
        print "Debugging.."
        import pdb; pdb.set_trace()
    
    plt.show()
#    self.fig.canvas.draw()
#    asicTesting.show()