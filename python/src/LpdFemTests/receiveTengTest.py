# X10G Development code
# Receive and display 10G image data
# Hacked together by Christian Angelsen 18-06-2012


# For detailed comments on animation and the techniqes used here, see
# the wiki entry http://www.scipy.org/Cookbook/Matplotlib/Animations

import os
import sys
import time
import socket

#import matplotlib
#matplotlib.use('Qt4Agg')
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.cm as cm
import matplotlib.pyplot
import matplotlib

from machineConfiguration import *

from PyQt4 import QtCore, QtGui

#
#self.nrows = 32
#self.ncols = 256     # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors in 2-Tile System: 16 x 16 = 256 columns

# processRxData function constants..
frm_buf_lim = 100     # Number of frames
data_buf_lim = 100   # Number of packets in each frame

# Variable used to enable/test subplotting
global_bSubPlotting = False

# Enable or disable debugging
bDebug = True

# Define variables used as arguments by
# Subplot function call: subplot(plotRows, plotCols, plotMaxPlots)
#    where max number of plotMaxPlots = plotRows * plotCols
plotRows = 2
plotCols = 1
plotMaxPlots = plotRows * plotCols


NX = 100
NY = 100
ITERS = 1000

class RxThread(QtCore.QThread):
    
    def __init__(self, rxSignal, pcAddressConfig):
        
        QtCore.QThread.__init__(self)
        self.rxSignal = rxSignal

        # Instantiate objects of machineConfiguration to obtain network information regarding the current machine
        #    (to enable this code to the run unmodified on different systems and PCs)
        self.myAddressConfig = pcAddressConfig
        femHost = self.myAddressConfig.get10gDestinationIpAddress(0) # 0 =  x10g_0, 1 = x10g_1
        if femHost is None:
            print "Error selecting interface, only 0 or 1 valid!\n\nExiting.."
            print "(femHost = %s)" % femHost
            sys.exit()
        
        print "Connecting to host: %s.." % (femHost)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#        self.sock.bind(('192.168.7.1', 61649))
        self.sock.bind((femHost, 61649))

    def __del__(self):
        self.wait()
        
    def run(self):
        
        while 1:    
            stream = self.sock.recv(9000)
            print ".",
            self.rxSignal.emit(stream)
    
    
class BlitQT(FigureCanvas):

    ''' Change font size '''
    matplotlib.rcParams.update({'font.size': 8})
    
    dataRxSignal = QtCore.pyqtSignal(object)

    def __init__(self):
        FigureCanvas.__init__(self, Figure())


        self.nrows = 32
        self.ncols = 128    # 256     # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors in 2-Tile System: 16 x 16 = 256 columns
#        self.numAsics = 8
        print "Note: self.ncols = ", self.ncols


        # Initialising variables used by processRxData..
        # ---------------------------------------------- #
        
        frm_buf_num = 100*4 # frm_buf_lim*4
        data_buf_num = data_buf_lim+10
        
        #frame Info arrays
        self.packet_count    = [0] * frm_buf_num
        self.frame_count  = 0

        # frame_length is frame length less header info
        self.frame_length = [0] * frm_buf_num
        
        
        self.packet_number_list     = [ [0] * data_buf_num ] * frm_buf_num
        self.frame_number_list     = [0] * frm_buf_num
        self.frame_number_index_list =  [0] * frm_buf_num
        
        self.first_frm_num = -1

        self.j = 0
        
        # ---------------------------------------------- #
        
        # Create a list (array?) to contain payload from all UDP packets
        self.rawImageData = ""


        # Generate list of xticks, yticks to label the x, y axis
        xlist = []
        for i in range(16, 256, 16):
            xlist.append(i)
            
        ylist = []
        for i in range(8, 32, 8):
            ylist.append(i)

        if global_bSubPlotting:
            
            print "SubPlotting selected; Preparing graphics.."
            
            # Create a list for axis object and image object, to contain one instance for each image
            self.ax = []
            self.img = []
            
            # Because subplotting has been selected, need a list of axis to cover multiple subplots
            for idx in range(plotMaxPlots):

                axesObject =  self.figure.add_subplot(plotRows, plotCols, idx+1)
                self.ax.extend([axesObject])
                
                self.ax[idx].set_xticks(xlist)
                self.ax[idx].set_yticks(ylist)
                
                # Set the title of each plot temporarily
                self.ax[idx].set_title("Frame %i" % idx)
                
                # Stuff copied from else statement..
                
                self.cnt = 0
                self.data = np.empty((self.nrows, self.ncols), dtype=np.uint16)        
                
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
                self.ax[idx].vlines(128-0.5, 0, self.nrows-1, color='r', linestyle='solid')
                
                self.draw()
        else:
            ''' Ordinary readout, only plot the first image from the image '''
            self.ax = self.figure.add_subplot(1, 1, 1)  #111)

            self.ax.set_xticks(xlist)
            self.ax.set_yticks(ylist)
    
            self.draw()
    
            self.old_size = self.ax.bbox.width, self.ax.bbox.height
            self.ax_background = self.copy_from_bbox(self.ax.bbox)
            self.cnt = 0
    
            self.data = np.empty((self.nrows, self.ncols), dtype=np.uint16)
#            print "__init__() just created: len(self.data) = %i,  self.nrows = %i, self.ncols = %i" % (len(self.data),  self.nrows, self.ncols)

            self.img = self.ax.imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')
    
            # http://stackoverflow.com/questions/2539331/how-do-i-set-a-matplotlib-colorbar-extents
            axc, kw = matplotlib.colorbar.make_axes(self.ax)
            cb = matplotlib.colorbar.Colorbar(axc, self.img)

            # Set the colour bar
            self.img.colorbar = cb
    
            # Add vertical lines to differentiate between the ASICs
            for i in range(16, self.ncols, 16):
                self.ax.vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
            
            # Add vertical lines to differentiate between the two tiles
            self.ax.vlines(128-0.5, 0, self.nrows-1, color='r', linestyle='solid')
            
            self.draw()

        self.dataRxSignal.connect(self.handleDataRx)
                
        self.tstart = time.time()
        
        
        # Instantiate objects of machineConfiguration to obtain network information regarding the current machine
        #    (to enable this code to the run unmodified on different systems and PCs)
        self.myAddressConfig = machineConfiguration()
        femHost = self.myAddressConfig.get10gDestinationIpAddress(0) # 0 =  x10g_0, 1 = x10g_1
        if femHost is None:
            print "Error selecting10 interface, only 0 or 1 valid!\n\nExiting.."
            print "(femHost = %s)" % femHost
            sys.exit()
        
        
        self.rxThread = RxThread(self.dataRxSignal, self.myAddressConfig)
        self.rxThread.start()


    def handleDataRx(self, data):

        if global_bSubPlotting:
            pass
            # Don't do restore_region() at the moment if subplotting..
        else:
            current_size = self.ax.bbox.width, self.ax.bbox.height
            if self.old_size != current_size:
                self.old_size = current_size

                self.draw()
                self.ax_background = self.copy_from_bbox(self.ax.bbox)
    
            self.restore_region(self.ax_background)

        # process UDP data in data variable
        try:
            frameNumber, foundEof  = self.processRxData(data)
        except Exception as errStr:
            print "processRxData() failed: ", errStr, "\nExiting.."
            sys.exit()
#        print "frameNumber, foundEof = ", frameNumber, foundEof
        
        # Only process image data when End Of File encountered..
        if foundEof:
            
            
            print "\nrawImageData length = ", len(self.rawImageData), " (bytes)"
#            print "RAW IMAGE CONTENT: "
#            for i in range(640):
#                if i % 16 == 0:
#                    print "\n%3X: " % i,                
#                print "%3X" % ord(self.rawImageData[i]),
#            print ""
#            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

            
            # End Of File found, self.rawImageData now contain every pixel of every ASIC (of the complete Quadrant!)
            
#            print ""

            ''' More information on numpy & Big/Little-endian:    http://docs.scipy.org/doc/numpy/user/basics.byteswapping.html '''
            
            # Create 32 bit, Little-Endian, integer type using numpy
            _32BitLittleEndianType = np.dtype('<i4')
            # Simultaneously extract 32 bit words and swap the byte order
            #     eg: ABCD => DCBA
            _32BitWordArray = np.fromstring(self.rawImageData, dtype=_32BitLittleEndianType)
            
            """ DEBUG INFO: """
#            print "Extracted number of 32 bit words: ", len(_32BitWordArray)
#            # Display array content 32 bit integers
#            print "Array contents structured into 32 bit elements [byte swapped!]:"
#            self.display32BitArrayInHex(_32BitWordArray)
#            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

            # Calculate length of 32 bit array
            _32BitArrayLen = len(_32BitWordArray)

            # Create empty array to store 16 bit elements (eg 32Bit array * 2)
            #     Each 32-bit word contain 2 pixels
            _16BitWordArray = np.empty(_32BitArrayLen*2, dtype='i2')
            
            # Split each 4 Byte element into 2 adjecent, 2 Byte elements
            for rawIdx in range(_32BitArrayLen):
#                _16BitWordArray[rawIdx*2]     = _32BitWordArray[rawIdx] >> 16
#                _16BitWordArray[rawIdx*2 + 1] = _32BitWordArray[rawIdx] & 0xFFFF
                _16BitWordArray[rawIdx*2 + 1] = _32BitWordArray[rawIdx] >> 16
                _16BitWordArray[rawIdx*2]     = _32BitWordArray[rawIdx] & 0xFFFF

                # Check whether gain bits are set
                if (_16BitWordArray[rawIdx*2] & 0xF000) > 0:
                    print " !",
                if (_16BitWordArray[rawIdx*2+1] & 0xF000) > 0:
                    print "| ",
                    
#            print ""
                

            """ DEBUG INFO: """ 
#            print "Number of 16 Bit Word: ", len(_16BitWordArray)
#            # Display array contenting 16 bit elements:
#            print "Array contents re-structured into 16 bit elements:"
#            self.display16BitArrayInHex(_16BitWordArray)
#            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
            
            # Extract the 16 ASICs image data from the full Quadrant data
#            completeDataArray = self.convertAsicDataIntoTwoTileImage(_16BitWordArray)
#            print "------------------ Before: ------------------"
#            for i in range(640):
#                if i % 16 == 0:
#                    print "\n%3X: " % i,
#                print "%3X" % _16BitWordArray[i],
#            print ""
            
            completeDataArray = self.convertAsicDataIntoSuperModuleImage(_16BitWordArray)

#            print "------------------ After: ------------------"
            print "---------- Image Data ----------"
            for i in range(80):
                if i % 16 == 0:
                    print "\n%3X: " % i,
                print "%3X" % completeDataArray[i],
            print ""
            
            # Plot multiple images if subplot enabled according to line 35
            if global_bSubPlotting:
                # Define variables that increase with each while loop iteration
                currentPlot = 0
                bNextImageAvailable = True
                
                # Loop over the specified number of plots
                while bNextImageAvailable and currentPlot < plotMaxPlots:
                    
                    # Get the first image of the image
#                    bNextImageAvailable, imageArray = self.retrieveFirstTwoTileImageFromAsicData(_16BitWordArray)
                    bNextImageAvailable, imageArray = self.retrieveFirstSuperModuleImageFromAsicData(_16BitWordArray)
                    
                    
                    # The first image, imageArray, has now been stripped from the image
                    # Reshape image into 32 x 256 pixel array
                    try:
                        self.data = imageArray.reshape(self.nrows, self.ncols)
                    except Exception as errStr:
                        print "handleDataRx() failed to reshape imageArray: ", errStr, "\nExiting.."
                        print "len(self.data),  self.nrows, self.ncols = ", len(self.data),  self.nrows, self.ncols
                        exit()
                        
                    # Display debug information..
#                    print "Frame %i Image %i" % (frameNumber, currentPlot), " data left: ", len(_16BitWordArray), " image data: \n", self.data
                    
                    # Set title as frame number, current image number
                    self.ax[currentPlot].set_title("Frame %i Image %i" % (frameNumber, currentPlot))
                    
                    # Load image into figure
                    self.img[currentPlot].set_data(self.data)

                    self.ax[currentPlot].draw_artist(self.img[currentPlot])
                    self.blit(self.ax[currentPlot].bbox)
                                        
                    # Increment currentPlot
                    currentPlot += 1

                    """ Remove this image from image array before next iteration
                        NOTE: _16BitWordArray contains full quadrant data, therefore while one image is 8192 pixels, 
                                it represents a region of 65,536 pixels within the full quadrant data !
                    """
                    _16BitWordArray = _16BitWordArray[65536:]
                else:
                    # Finished
                    print "Finished drawing subplots"
                    print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

            
            bDebug = False
            
            if bDebug:
                filename = '/u/ckd27546/AsicsReadout.txt'
                """ DEBUG INFO - PRINT IMAGE ADC VALUES TO FILE """
                print "Writing ADC values to file '%s'" % filename
                try:
                    OutputFile = open(filename, 'w+')
                except Exception as errStr:
                    print "Error opening file: ", errStr
                
                try:
                    for pxl in range(self.ncols*self.nrows):
                        OutputFile.write("%i, " % completeDataArray[pxl])
                except Exception as errStr:
                    print "Error writing ADC values to file: ", errStr
                else:
                    print "Finished writing to file"
    
                try:
                    OutputFile.close()
                except Exception as errStr:
                    print "Error closing file '%' because: %s" % (filename, errStr)


            """ NOTE THAT THIS IS THE REAL MCCOY; DO NOT REMOVE IF ELIMINATING SUBPLOT FROM CODE
            !!!!!
            """
            if global_bSubPlotting is False:
                print "Reshaping completeDataArray to fit plot.."
                
                try:
                    self.data = completeDataArray.reshape(self.nrows, self.ncols)
                except Exception as errStr:
                    print "completeDataArray.reshape() failed: %s \nExiting.." % errStr
                    print "len(self.data),  self.nrows, self.ncols = ", len(self.data),  self.nrows, self.ncols
                    exit()

                # Set title to current frame number
                self.ax.set_title("Frame %i" % frameNumber)
                
                # Load image into figure
                self.img.set_data(self.data)
                
                self.ax.draw_artist(self.img)
                self.blit(self.ax.bbox)

#            """ Debug Testing: saving the image.. """
#            # Only saves the 32 x 256 image, nothing else:
#            try:
#                matplotlib.pyplot.imsave("ImageFrame_%03i.png" % frameNumber, self.data)
#            except Exception as errStr:
#                print "Failed to use .imsave() because: ", errStr, "\nExiting.."
#                exit()

            # 'Reset' rawImageData variable
            self.rawImageData = self.rawImageData[0:0]
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        else:
            # Didn't find End Of File within this packet, check next packet..
            pass
  
        if self.cnt == 0:
            # TODO: this shouldn't be necessary, but if it is excluded the
            # canvas outside the axes is not initially painted.
            self.draw()
        else:
            self.cnt += 1

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
#        Restructured functions to operate on numpy arrays
#
#  -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    def display32BitArrayInHex(self, dataArray):
        """ display32BitArrayInHex takes dataArray argument containing array of raw data
            AFTER it's been byte swapped and then displays each 16 bit ADC value (each index/byte) 
            .. Unless data_len hardcoded to 160..
        """
        
        data_len = len(dataArray)
        
        data_len = 160*5
        
        currentArrayElement = ""
        try:
            # Convert each 2 byte into 16 bit data and print that
            for idx in range(data_len/2):
                
                if (idx %8 == 0):
                    print "%6d : " % idx,
                    
                currentArrayElement =  currentArrayElement + "       %08X " % dataArray[idx]
                
                if (idx % 8 == 7):
                    print currentArrayElement
                    currentArrayElement = ""
                
            print "Number of 16 bit words: ", data_len/2
        except Exception as errStr:
            print "display32BitArrayInHex() error: ", errStr
            exit(0)

    def display16BitArrayInHex(self, dataArray):
        """ display16BitArrayInHex takes dataArray argument containing array of raw data
            AFTER it's been byte swapped and then displays each 16 bit ADC value (each index/byte)
            .. Unless data_len hardcoded to 160..
        """
        data_len = len(dataArray)
        
        data_len = 160
        
        currentArrayElement = ""
        try:
            # Convert each 2 byte into 16 bit data and print that
            for idx in range(data_len):
                
                if (idx %16 == 0):
                    print "%6d : " % idx,
                    
                currentArrayElement =  currentArrayElement + "   %04X " % dataArray[idx]
                
                if (idx % 16 == 15):
                    print currentArrayElement
                    currentArrayElement = ""
                
            print "Number of 16 bit words: ", data_len
        except Exception as errStr:
            print "display16BitArrayInHex() error: ", errStr
            exit(0)


    def convertAsicDataIntoTwoTileImage(self, sixteenBitArray):
        """ convertAsicDataIntoTwoTileImage() sixteenBitArray array argument containing all
            the ASIC data, and returns a complete image consisting of the data from 
            the 16 ASICs organised into a 32 x 256 pixel image """
        # Create an array to contain 8192 elements (32 x 16 x 16)
        completeImageArray = np.empty(8192, dtype=np.uint16)
        
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        
#        print "convertAsicDataIntoTwoTileImage(), algorithm picking out indices:"
        
        try:
            
            # Define variables used by nested loops..
            # Distance between adjacent columns and rows, respectively
            column_width = pixelDistance
            row_length = 16 * pixelDistance

            # Distance within the 64 word table that defines order of ASIC read out
            # Each word represents two array elements; Word 1 = 97, 98; Word 2 = 99, 100; etc
            lookupTableAsicDistance = 0
            
            #Iterate over 32 rows
            for row in range(32):
                
                # Iterate over 16 columns
                for column in range(16):

                    lookupTableAsicDistance = 52
                    try:
                        
                        # Iterate over the 16 ASICs
                        for asicOffset in range(16):
                            
                            rawDataOffset = (column * column_width) + (row * row_length) + lookupTableAsicDistance
                            
                            completeImageArray[ (15 - column) + (16 * asicOffset) + (256 * row)] = sixteenBitArray[rawDataOffset]

#                            # DEBUG - mark every read pixel value in raw data
#                            sixteenBitArray[rawDataOffset] = 4095
#                            print "%1X:%1X:%5i   " % (column, asicOffset, rawDataOffset),
                            
                            # Need to update lookupTableAsicDistance manually for ASIC 101, 17 and 21..
                            if asicOffset is 3:
                                # ASIC101 is next
                                lookupTableAsicDistance = 36
                            elif asicOffset is 7:
                                # ASIC17 is next
                                lookupTableAsicDistance = 92
                            elif asicOffset is 11:
                                # ASIC21 is next
                                lookupTableAsicDistance = 76
                            else:
                                lookupTableAsicDistance += 1
                                
#                            # DEBUG - add new line
#                            if asicOffset == 15:
#                                print "."
                            
                    except Exception as errStr:
                        print "convertAsicDataIntoTwoTileImage(), look up table execution failed: ", errStr, "\nExiting.."
                        exit()                    

        except Exception as errStr:
            print "convertAsicDataIntoTwoTileImage() Error: ", errStr, "\nExiting.."
            exit()
        
        return completeImageArray

    def convertAsicDataIntoSuperModuleImage(self, sixteenBitArray):
        """ Argument sixteenBitArray array contains all data from the complete super module.
            From the 65,536 pixels, the function picks out and returns 512 pixels times the number of ASIC
            [AS OF 10/12/2012] ->
                8 ASICs organised into a 32 x 128 pixel image; 4096 pixels """
        # Create an array to contain 4096 elements (32 x 16 x 8)
        completeImageArray = np.empty(4096, dtype=np.uint16)
        
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        
        bDebug = False
        if bDebug:
            print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
            print "convertAsicDataIntoSuperModuleImage(), algorithm picking out indices:"
            print "sixteenBitArray[rawDataOffset] => imageIndex"
            rawInfo = ""
            imageInfo = ""
            
        try:
            # Counter variables
            imageIndex = 0
            rawCounter = 0

            # Distance within the 64 word table that defines order of ASIC read out
            # Each word represents two array elements; Word 1 = 97, 98; Word 2 = 99, 100; etc
            lookupTableAsicDistance = 0
            
            #Iterate over 32 rows
            for row in range(32):
                
                # Iterate over 16 columns
                for column in range(16):

                    # Go in reverse order from ASIC 112-105
                    lookupTableAsicDistance = 112-1

                    try:
                        # Iterate over the number of ASICs
                        for asicOffset in range(8):
                            
                            imageIndex = 15 + (16 * asicOffset) - column + (self.ncols * row)
                            rawDataOffset = lookupTableAsicDistance + 128 * rawCounter
                            
                            completeImageArray[ imageIndex ] = sixteenBitArray[rawDataOffset]

#                            # DEBUG - mark every read pixel value in raw data
#                            sixteenBitArray[rawDataOffset] = 2500   #4095

                            if bDebug:
                                rawInfo += "%6i" % sixteenBitArray[rawDataOffset]
                                imageInfo += "%5i" % imageIndex

                            # Decrement lookupTableAsicDistance since ASIC are located in one row
                            lookupTableAsicDistance -= 1

                            # Increment counter for imageIndex for every ASIC and every pixel
                            imageIndex += 1
                        
                        # Increment counter for rawDataOffset for every tile of 8 ASICs 
                        rawCounter += 1
                        
                        if bDebug:
                            if row < 2:
                                print rawInfo, " => ", imageInfo
                            rawInfo = ""
                            imageInfo = ""

                    except Exception as errStr:
                        print "convertAsicDataIntoSuperModuleImage(), look up table execution failed: ", errStr, "\nExiting.."
                        exit()                    

        except Exception as errStr:
            print "convertAsicDataIntoSuperModuleImage() Error: ", errStr, "\nExiting.."
            exit()
        
        return completeImageArray

# ~~~~~~~~~~~~ #

    def retrieveFirstTwoTileImageFromAsicData(self, sixteenBitArray):
        """ retrieveFirstTwoTileImageFromAsicData() takes the sixteenBitArray array argument containing all
            the ASIC data (full supermodule), and returns,
                * boolean to signal whether this is the last image in the data
                * the first image (32 x 16 x 16 pixels) of an image found in the data,
            in the form of the 16 ASICs organised into a 32 x 256 pixel image 
        """
        # Create an array to contain 8192 elements (32 x 16 x 16)
        imageImageArray = np.empty(8192, dtype=np.uint16)
        
        
        """ Debug information.. """
#        print "retrieveFirstTwoTileImageFromAsicData() len(sixteenBitArray) ", len(sixteenBitArray)
        
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        
        # Define variables used by nested loops..
        # Distance between adjacent columns and rows, respectively
        column_width = pixelDistance
        row_length = 16 * pixelDistance

        # Distance within the 64 word table that defines order of ASIC read out
        # Each word represents two array elements; Word 1 = 97, 98; Word 2 = 99, 100; etc
        lookupTableAsicDistance = 0
        
        #Iterate over 32 rows
        for row in range(32):
            
            # Iterate over 16 columns
            for column in range(16):

                lookupTableAsicDistance = 52
                try:
                    
                    # Iterate over the 16 ASICs
                    for asicOffset in range(16):
                        
                        rawDataOffset = (column * column_width) + (row * row_length) + lookupTableAsicDistance
                        
                        imageImageArray[ (15 - column) + (16 * asicOffset) + (256 * row)] = sixteenBitArray[rawDataOffset]
                        
                        # Need to update lookupTableAsicDistance manually for ASIC 101, 17 and 21..
                        if asicOffset is 3:
                            # ASIC101 is next
                            lookupTableAsicDistance = 36
                        elif asicOffset is 7:
                            # ASIC17 is next
                            lookupTableAsicDistance = 92
                        elif asicOffset is 11:
                            # ASIC21 is next
                            lookupTableAsicDistance = 76
                        else:
                            lookupTableAsicDistance += 1
                        
                except IndexError:
                    # If end of array reached, will raise IndexError
                    print "IndexError, loop counters: (", row, column, asicOffset, "). lookupTableAsi..: ", lookupTableAsicDistance, " rawDataOffset: ", rawDataOffset, " Breaking out of loop.."
                    break
                except Exception as errStr:
                    print "retrieveFirstTwoTileImageFromAsicData(), look up table execution failed: ", errStr, "\nExiting.."
                    exit()

        # Check whether this is the last image in the image data..
        #    NOTE: the 8192 pixels come from a region spanning 65,536 pixel in the quadrant data
        try:
            sixteenBitArray[65536]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            print "Last Image detected"

        return bNextImageAvailable, imageImageArray


    def retrieveFirstSuperModuleImageFromAsicData(self, sixteenBitArray):
        """ retrieveFirstSuperModuleImageFromAsicData() takes the sixteenBitArray array argument containing all
            the ASIC data (full supermodule), and returns,    [AS OF 10/12/2012] 
                * boolean to signal whether this is the last image in the data
                * the first image (32 x 16 x 8 pixels) of an image found in the data,
            in the form of the 8 ASICs organised into a 32 x 128 pixel image 
        """
        # Create an array to contain 4096 elements (32 x 16 x 8)
        imageImageArray = np.empty(4096, dtype=np.uint16)
        
        print "-- -- -- -- -- -- -- -- -- IT REALLY IS THIS FUNCTION -- -- -- -- -- -- -- -- --"
        """ Debug information.. """
#        print "retrieveFirstSuperModuleImageFromAsicData() len(sixteenBitArray) ", len(sixteenBitArray)
        
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        
        # Define variables used by nested loops..
        # Distance between adjacent columns and rows, respectively
#        column_width = pixelDistance
#        row_length = 16 * pixelDistance
        imageIndex = 0
        rawCounter = 0

        # Distance within the 64 word table that defines order of ASIC read out
        # Each word represents two array elements; Word 1 = 97, 98; Word 2 = 99, 100; etc
        lookupTableAsicDistance = 0
        
        #Iterate over 32 rows
        for row in range(32):
            
            # Iterate over 16 columns
            for column in range(16):

                lookupTableAsicDistance = 105-1   #52
                try:
                    
                    # Iterate over the 8 ASICs
                    for asicOffset in range(8):

#                        rawDataOffset = (column * column_width) + (row * row_length) + lookupTableAsicDistance
#                        imageImageArray[ (15 - column) + (8 * asicOffset) + (self.ncols * row)] = sixteenBitArray[rawDataOffset]
                        rawDataOffset = lookupTableAsicDistance + pixelDistance * rawCounter
                        imageImageArray[ imageIndex ] = sixteenBitArray[rawDataOffset]

                        # Increment lookupTableAsicDistance since ASIC are located in one row
                        lookupTableAsicDistance += 1

                        # Increment counter for imageIndex for every ASIC and every pixel
                        imageIndex += 1

                    # Increment counter for rawDataOffset for every tile of 8 ASICs 
                    rawCounter += 1

                except IndexError:
                    # If end of array reached, will raise IndexError
#                    print "SM-IndexError, loop counters: (", row, column, asicOffset, "). lookupTableAsi..: ", lookupTableAsicDistance, " rawDataOffset: ", rawDataOffset, " Breaking out of loop.."
                    break
                except Exception as errStr:
                    print "retrieveFirstSuperModuleImageFromAsicData(), look up table execution failed: ", errStr, "\nExiting.."
                    exit()                    

        # Check whether this is the last image in the image data..
        #    NOTE: the 4096 pixels come from a region spanning 65,536 pixel in the quadrant data
        try:
            sixteenBitArray[65536]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            print "Last Image detected"

        return bNextImageAvailable, imageImageArray

# ~~~~~~~~~~~~ #

    def processRxData(self, data):
        """ Process (chunks of) UDP data into packets of a frame 
            [Code inherited from Rob - See: udp_rx_ll_mon_header_2_CA.py]
        """
                
        # save the read frame number as it'll be modified to be RELATIVE before we reach the end of this function.. 
        rawFrameNumber = -1

        data_len = len(data)

        ''' DEBUGGING INFORMATION '''
#        if ( ( ord(data[-1]) & 0x80) >> 7 ) == 1:
#            print "The last eight bytes of each packet:"
#            print "-- -- -- -- -- -- -- -- -- -- -- --"
#            print "  -8, -7, -6, -5, -4, -3, -2, -1"
#        sDebug = ""
#        for i in range(8, 0, -1):
##        for i in range(18, 0, -1):
#            sDebug += "%4X" % ord( data[-i] )
#        print sDebug
        
        try:
            offset = 0
            # Extract frame number (the first four bytes)
            frame_number = (ord(data[offset+3]) << 24) + (ord(data[offset+2]) << 16) + (ord(data[offset+1]) << 8) + ord(data[offset+0])
            # Extract packet number (the following four bytes)
            packet_number = ord(data[offset-4]) #(ord(data[offset+7]) << 24) + (ord(data[offset+6]) << 16) + (ord(data[offset+5]) << 8) + ord(data[offset+4])
            header_info = ord(data[-1])
#            print "header_info: ", header_info
            # Extract Start Of Frame, End of Frame
#            frm_sof = (packet_number & 0x80000000) >> 31
#            frm_eof = (packet_number & 0x40000000) >> 30
            frm_sof = (header_info & 0x80) >> 7
            frm_eof = (header_info & 0x40) >> 6
#            packet_number = packet_number & 0x3FFFFFFF
            
#            print "sof/eof = %4X, %4X" % (frm_sof, frm_eof),
            # rawFrameNumber = frame number read from packet
            # frame_number = frame number relative to execution of this software
            rawFrameNumber = frame_number
            
            if self.first_frm_num == -1:
                self.first_frm_num = frame_number
                
            frame_number = frame_number - self.first_frm_num
            
            try:
                #Add frame number to index list
                if self.frame_number_list[frame_number] == 0:
                    self.frame_number_index_list[self.j] = frame_number
            except Exception as errStr:
                print "self.frame_number_index_list error: ", errStr, "\nExiting.."
#                print "frame_number = ", frame_number, " self.j = ", self.j
                sys.exit()
            
            if frm_eof == 1:
                self.j=self.j+1
            else:
                pass
            
            
            # Not yet end of file: copy current packet contents onto (previous) packet contents
            # First 8 bytes are frame number and packet number - omitting those..
            # both are of type string..
#            self.rawImageData = self.rawImageData + data[8:]
            self.rawImageData = self.rawImageData + data[0:-8]

#            print "Before: [%3i][%3i] " % (frame_number, packet_number),
            try:
                #Add packet number to frame packet list
                #print "1", frame_number, packet_number
                self.packet_number_list[frame_number][packet_number] = self.packet_number_list[frame_number][packet_number] + 1
                #print "2", frame_number, packet_number
                #debug
            except Exception as errStr:
                print "frame_number, = ", frame_number, " packet_number = ", packet_number
                print "self.packet_number_list error: ", errStr, "\nExiting.."
                sys.exit()
#            print "After: [%3i][%3i] " % (frame_number, packet_number)

            try:
                #Add frame number to frm packet count list        
                self.frame_number_list[frame_number] = self.frame_number_list[frame_number] + 1
            except Exception as errStr:
                print "self.frame_number_list error: ", errStr, "\nExiting.."
                sys.exit()
                
            try:
                self.frame_length[frame_number] = self.frame_length[frame_number] + data_len - 8    # Remove 8 for the frame header
                self.packet_count[frame_number] = self.packet_count[frame_number]+1
            except Exception as errStr:
                print "frame_length or data_count error: ", errStr, "\nExiting.."
                sys.exit
            
            # Return frame number and end of frame
            return rawFrameNumber, frm_eof
        except Exception as errString:
            print "processRxData() error: ", errString
            return -1, -1

        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    widget = BlitQT()
    widget.show()
    
    sys.exit(app.exec_())

