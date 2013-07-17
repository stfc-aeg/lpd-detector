'''
Created on Jun 3, 2013

Build a raw array with dummy data and then exercise the decoding algorithm and display execution time
(was used to adapt the faster supermodule algorithm to cut processing time of the Two Tile readout script)

@author: ckd27546
'''

import os, sys, time, socket, datetime

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.cm as cm
import matplotlib.pyplot
import matplotlib

from PyQt4 import QtCore, QtGui


# Enable or disable debugging
bDebug = False

bNewRetrieveFunc = True

# Define variables used as arguments by
# Subplot function call: subplot(plotRows, plotCols, plotMaxPlots)
#    where max number of plotMaxPlots = plotRows * plotCols
plotRows = 4
plotCols = 1
plotMaxPlots = plotRows * plotCols

class RxThread(QtCore.QThread):
    
    def __init__(self, rxSignal):
        
        QtCore.QThread.__init__(self)
        self.rxSignal = rxSignal

    def __del__(self):
        self.wait()
        
    def run(self):
        
        for idx in range(4):    
            time.sleep(0.5)
            self.rxSignal.emit(None)
    
class BlitQT(FigureCanvas):

    ''' Change font size '''
    matplotlib.rcParams.update({'font.size': 8})
    
    dataRxSignal = QtCore.pyqtSignal(object)

    def __init__(self):
        FigureCanvas.__init__(self, Figure())

        # Time code execution
        self.timeStart = []
        self.timeStop = []

        # Define plotted image dimensions: 
        self.nrows = 32
        self.ncols = 256     # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors in 2-Tile System: 16 x 16 = 256 columns
        self.imageSize = self.nrows * self.ncols

        # Create an array to contain 8192 elements (32 x 16 x 16)
        self.imageArray= np.zeros(self.imageSize, dtype=np.uint16)
        
        # Create a list to contain payload of all UDP packets
        self.rawImageData = ""

        # Generate list of xticks, yticks to label the x, y axis
        xlist = []
        for i in range(16, 256, 16):
            xlist.append(i)
            
        ylist = []
        for i in range(8, 32, 8):
            ylist.append(i)
        
        print "Simulating Two Tile System: Initialising; Preparing graphics.."
        
        # Create a list for axes object and one for image objects, to store that info for each image
        self.ax = []
        self.img = []
        
        # Because subplotting has been selected, need a list of axes to cover multiple subplots
        for idx in range(plotMaxPlots):

            axesObject =  self.figure.add_subplot(plotRows, plotCols, idx+1)
            self.ax.extend([axesObject])

            self.ax[idx].set_xticks(xlist)
            self.ax[idx].set_yticks(ylist)
            
            # Set the title of each plot temporarily
            self.ax[idx].set_title("Image %i" % idx)
                            
            self.cnt = 0
            self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)
                        
            imgObject = self.ax[idx].imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')
            self.img.extend([imgObject])

            # http://stackoverflow.com/questions/2539331/how-do-i-set-a-matplotlib-colorbar-extents
            axc, kw = matplotlib.colorbar.make_axes(self.ax[idx])
            cb = matplotlib.colorbar.Colorbar(axc, self.img[idx])

            # Set the colour bar
            self.img[idx].colorbar = cb

            # Add vertical lines to differentiate between the ASICs
            for i in range(16, self.ncols, 16):
                self.ax[idx].vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')

            # Add vertical lines to differentiate between the two tiles
            self.ax[idx].vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
            
            self.draw()

        self.bFoundEof = False

        self.dataRxSignal.connect(self.handleDataRx)
                
        self.tstart = time.time()

        self.rxThread = RxThread(self.dataRxSignal)
        self.rxThread.start()

    def handleDataRx(self):
        
        # Only process image data when End Of File encountered
        if self.bFoundEof:
                        
            # Create empty array to store 16 bit elements (eg 32 Bit array * 2)
            #     Each 32-bit word contain 2 pixels
            self._16BitWordArray = np.zeros(65536*4, dtype='i2')
            
#            self._16BitWordArray[256*32 + 128] = 2000
            for index in range(len(self._16BitWordArray)):
                self._16BitWordArray[index] = 2000+ (index % 42)* (index % 42)

            # Define variables that increase with each loop iteration
            currentPlot = 0
            bNextImageAvailable = True
            
            # Loop over the specified number of plots
            while bNextImageAvailable and currentPlot < plotMaxPlots:
                
                dataBeginning = 65536*currentPlot

                t1 = time.time()
                self.timeStart.append(t1)

                # Get the first image of the image
                if bNewRetrieveFunc:
                    bNextImageAvailable = self.retrieveFirstImage(dataBeginning)
                else:
                    bNextImageAvailable = self.retrieveFirstTwoTileImageFromAsicData(dataBeginning)
                    
                t2 = time.time()
                self.timeStop.append(t2)
                
                # The first image, imageArray, has now been stripped from the image
                # Reshape image into 32 x 256 pixel array
                try:
                    self.data = self.imageArray.reshape(self.nrows, self.ncols)
                except Exception as e:
                    print "handleDataRx() failed to reshape imageArray: ", e, "\nExiting.."
                    print "len(self.data),  self.nrows, self.ncols = ", len(self.data),  self.nrows, self.ncols
                    exit()
                
                # Mask out gain bits from data
                self.data = self.data & 0xfff

                frameNumber = 0                
                # Display plot information
#                print "Train %i Image %i" % (frameNumber, currentPlot), " data left: %9i" % len( self._16BitWordArray[dataBeginning:] )
                
                # Set title as train number, current image number
                self.ax[currentPlot].set_title("NewFunc: %s Train %i Image %i" % (bNewRetrieveFunc, frameNumber, currentPlot*3))
                
                # Load image into figure
                self.img[currentPlot].set_data(self.data)

                self.ax[currentPlot].draw_artist(self.img[currentPlot])
                self.blit(self.ax[currentPlot].bbox)

                # Increment currentPlot
                currentPlot += 1

            else:
                # Finished this train - work out timings..
                if len(self.timeStart) != len(self.timeStop):
                    print "Missmatch between timeStart %i and timeStop %i" % (len(self.timeStart), len(self.timeStop))
                else:
#                    if bNewRetrieveFunc:
#                        print "New Func ",
#                    else:
#                        print "Old Func ",
                    delta = 0
                    sum = 0
                    for idx in range(len(self.timeStart)):
                        delta = self.timeStop[idx] - self.timeStart[idx]
                        sum += delta
                    print "Average time executing function: ", (sum / len(self.timeStop))

#            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        else:
            # Didn't find End Of File within this packet, check next packet..
            pass
  
        if self.cnt == 0:
            self.draw()
            self.bFoundEof = True
        else:
            self.cnt += 1

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
#        Restructured functions to operate on numpy arrays
#
#  -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# ~~~~~~~~~~~~ #

    def retrieveFirstTwoTileImageFromAsicData(self, dataBeginning):
        """ ORIGINAL TWO TILE'S FUNCTION !
            Extracts one image beginning at argument dataBeginning in the member array 
            self._16BitWordArray array. Returns boolean bImageAvailable indicating whether
            the current image is the last image in the data
        """
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        # Counter variables
        imageIndex = 0
        rawCounter = 0
        # Distance within the 64 word table that defines order of ASIC read out
        lookupTableAsicDistance = 0

        # Iterate over 32 rows
        for row in range(32):
            
            # Iterate over 16 columns
            for column in range(16):

                # Go in reverse order from ASIC 32-25, 112-105
                lookupTableAsicDistance = 32-1
                try:
                    
                    # Iterate over the 16 ASICs
                    for asicOffset in range(16):
                        
                        imageIndex = 15 + (16 * asicOffset) - column + (self.ncols * row)
                        rawDataOffset = lookupTableAsicDistance + (pixelDistance * rawCounter)
                        
                        self.imageArray[ imageIndex ] = self._16BitWordArray[dataBeginning + rawDataOffset]
                    
                        # Need to update lookupTableAsicDistance manually for ASIC 122
                        if asicOffset is 7:
                            lookupTableAsicDistance = 112-1
                        else:
                            lookupTableAsicDistance -= 1
                            
                    # Increment counter for rawDataOffset after columns*ASICs (16 ASICs) 
                    rawCounter += 1
                    
                except IndexError:
                    # If end of array reached, will raise IndexError
                    print "2T, IndexError, debug: %3i %3i %3i, %4i,  %6i " % (row, column, asicOffset, lookupTableAsicDistance, rawDataOffset)
                    break
                except Exception as e:
                    print "Error while extracting image: ", e, "\nExiting.."
                    exit()

        if bDebug:
            print "\nNewFunc: %s. self.imageArray contents:" % bNewRetrieveFunc
            for idx in range(len(self.imageArray)):
                if idx > 1024:
                    continue
                if (idx % 32) == 0:
                    print "\n%4i:" % idx,
                print " %4i" % self.imageArray[idx],
            sys.exit()

        # Check whether this is the last image in the image data..
        #    NOTE: the 8192 pixels come from a region spanning 65,536 pixel in the quadrant data
        try:
            self._16BitWordArray[dataBeginning + 65536]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            pass    # Last Image detected in this train
        return bNextImageAvailable

    def retrieveFirstImage(self, dataBeginning):
        """ Faster implementation by adopting super module algorithm
            Extracts one image beginning at argument dataBeginning in the member array 
            self._16BitWordArray array. Returns boolean bImageAvailable indicating whether
            the current image is the last image in the data
        """
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False

        numCols = 16
        numRows = 8
        numAsics = numCols * numRows
        numColsPerAsic = 16
        numRowsPerAsic = 32

        numPixelsPerAsic = numColsPerAsic * numRowsPerAsic
        numPixels = numAsics * numPixelsPerAsic

        # Create linear array for unpacked pixel data
        self.imageLpdFullArray = np.zeros(numPixels, dtype=np.uint16)
        self.imageLpdFullArray = np.reshape(self.imageLpdFullArray, (numRows * numRowsPerAsic, numCols * numColsPerAsic))

        rawOffset = dataBeginning

        try:
            for asicRow in xrange(numRowsPerAsic):
                for asicCol in xrange(numColsPerAsic):
                    
                    self.imageLpdFullArray[asicRow::numRowsPerAsic, asicCol::numColsPerAsic] = self._16BitWordArray[rawOffset:(rawOffset + numAsics)].reshape(8,16)
                    rawOffset += numAsics

        except IndexError:
            print "Image Processing Error @ %6i %6i %6i %6i %6i %6i " % ( asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics )
            sys.exit()
        except Exception as e:
            print "Error while extracting image: ", e, "\nExiting.."
            print "Debug info: %6i %6i %6i %6i %6i %6i " % ( asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics )
            sys.exit()

        # TODO: Don't swapping 1st row with last row, second row with second last row, etc for Two Tile System
        # TODO: BUT, must swap rows for Super Module !
#        self.imageLpdFullArray[:,:] = self.imageLpdFullArray[::-1,:]

        # Create array for 2 Tile data; reshape into two dimensional array
        self.imageArray = np.zeros(32*256, dtype=np.uint16)
        self.imageArray = self.imageArray.reshape(32, 256)

        # Copy the two Tiles that exists in the two tile system
        try:
            # LHS Tile located in the second ASIC row, second ASIC column
            self.imageArray[0:32, 0:128]   = self.imageLpdFullArray[32:32+32, 256-1:128-1:-1]
            # RHS Tile located in the seventh ASIC row, second ASIC column
            self.imageArray[0:32, 128:256] = self.imageLpdFullArray[192:192+32, 256-1:128-1:-1]
        except Exception as e:
            print "Error accessing 2 Tile data: ", e
            print "dataBeginning: ", dataBeginning
            sys.exit()

        # Last image in the data?
        try:
            self._16BitWordArray[dataBeginning + self.imageSize]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            pass   # Last Image in this train detected
        return bNextImageAvailable

if __name__ == "__main__":

    # Check command line for host and port info    
    if len(sys.argv) == 3:
        femHost = sys.argv[1]
        femPort = int(sys.argv[2])
    else:
        # Nothing provided from command line; Use defaults
        femHost = None
        femPort = None        

    app = QtGui.QApplication(sys.argv)
    widget = BlitQT()
    widget.show()
    
    sys.exit(app.exec_())

