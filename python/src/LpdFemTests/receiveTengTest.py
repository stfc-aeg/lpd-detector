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

from PyQt4 import QtCore, QtGui


nrows = 32
ncols = 256     # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors in 2-Tile System: 16 x 16 = 256 columns

# processRxData function constants..
frm_buf_lim = 100     # Number of frames
data_buf_lim = 100   # Number of packets in each frame

# Variable used to enable/test subplotting
global_bSubPlotting = True
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
    
    def __init__(self, rxSignal):
        
        QtCore.QThread.__init__(self)
        self.rxSignal = rxSignal
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('192.168.7.1', 61649))

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

        # Initialising variables used by processRxData..
        # ---------------------------------------------- #
        
        frm_buf_num = frm_buf_lim*4
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
                self.data = np.empty((nrows, ncols), dtype=np.uint16)        
                
                imgObject = self.ax[idx].imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')
                self.img.extend([imgObject])

                # http://stackoverflow.com/questions/2539331/how-do-i-set-a-matplotlib-colorbar-extents
                axc, kw = matplotlib.colorbar.make_axes(self.ax[idx])
                cb = matplotlib.colorbar.Colorbar(axc, self.img[idx])

                # Set the colour bar
                self.img[idx].colorbar = cb

                # Add vertical lines to differentiate between the ASICs
                for i in range(16, ncols, 16):
                    self.ax[idx].vlines(i-0.5, 0, nrows-1, color='b', linestyles='solid')
                
                # Add vertical lines to differentiate between the two tiles
                self.ax[idx].vlines(128-0.5, 0, nrows-1, color='r', linestyle='solid')
                
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
    
            self.data = np.empty((nrows, ncols), dtype=np.uint16)        
            
            self.img = self.ax.imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')
    
            # http://stackoverflow.com/questions/2539331/how-do-i-set-a-matplotlib-colorbar-extents
            axc, kw = matplotlib.colorbar.make_axes(self.ax)
            cb = matplotlib.colorbar.Colorbar(axc, self.img)

            # Set the colour bar
            self.img.colorbar = cb
    
            # Add vertical lines to differentiate between the ASICs
            for i in range(16, ncols, 16):
                self.ax.vlines(i-0.5, 0, nrows-1, color='b', linestyles='solid')
            
            # Add vertical lines to differentiate between the two tiles
            self.ax.vlines(128-0.5, 0, nrows-1, color='r', linestyle='solid')
            
            self.draw()

        self.dataRxSignal.connect(self.handleDataRx)
                
        self.tstart = time.time()
        self.rxThread = RxThread(self.dataRxSignal)
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

        # Only process image data when End Of File encountered..
        if foundEof:
            
            # End Of File found, self.rawImageData now contain every pixel of every ASIC (of the complete Quadrant!)
            
            print ""

            ''' More information on numpy & Big/Little-endian:    http://docs.scipy.org/doc/numpy/user/basics.byteswapping.html '''
            
            # Create 32 bit, Little-Endian, integer type using numpy
            _32BitLittleEndianType = np.dtype('<i4')
            # Simultaneously extract 32 bit words and swap the byte order
            #     eg: ABCD => DCBA
            _32BitWordArray = np.fromstring(self.rawImageData, dtype=_32BitLittleEndianType)
            
            """ DEBUG INFO: """
            # Display array content 32 bit integers
            print "Array contents structured into 32 bit elements [byte swapped!]:"
            self.display32BitArrayInHex(_32BitWordArray)
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

            # Calculate length of 32 bit array
            _32BitArrayLen = len(_32BitWordArray)

            # Create empty array to store 16 bit elements (eg 32Bit array * 2)
            #     Each 32-bit word contain 2 pixels
            _16BitWordArray = np.empty(_32BitArrayLen*2, dtype='i2')
            
            # Split each 4 Byte element into 2 adjecent, 2 Byte elements
            for rawIdx in range(_32BitArrayLen):
                _16BitWordArray[rawIdx*2]     = _32BitWordArray[rawIdx] >> 16
                _16BitWordArray[rawIdx*2 + 1] = _32BitWordArray[rawIdx] & 0xFFFF
                # Check whether gain bits are set
                if (_16BitWordArray[rawIdx*2] & 0xF000) > 0:
                    print " !",
                if (_16BitWordArray[rawIdx*2+1] & 0xF000) > 0:
                    print "| ",
                    
            print ""
                

            """ DEBUG INFO: """ 
            # Display array contenting 16 bit elements:
            print "Array contents re-structured into 16 bit elements:"
            self.display16BitArrayInHex(_16BitWordArray)
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
            
            # Extract the 16 ASICs image data from the full Quadrant data
            completeDataArray = self.convertAsicDataIntoImage(_16BitWordArray)
            
            # Plot multiple images if subplot enabled according to line 35
            if global_bSubPlotting:
                # Define variables that increase with each while loop iteration
                currentPlot = 0
                bNextImageAvailable = True
                
                # Loop over the specified number of plots
                while bNextImageAvailable and currentPlot < plotMaxPlots:
                    
                    # Get the first image of the image
                    bNextImageAvailable, imageArray = self.retrieveFirstImageFromAsicData(_16BitWordArray)
                    
                    # The first image, imageArray, has now been stripped from the image
                    # Reshape image into 32 x 256 pixel array
                    try:
                        self.data = imageArray.reshape(nrows, ncols)
                    except Exception as errStr:
                        print "handleDataRx() failed to reshape imageArray: ", errStr, "\nExiting.."
                        exit()
                        
                    # Display debug information..
                    print "currentPlot: ", currentPlot, " data left: ", len(_16BitWordArray), " image data: \n", self.data
                    
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

            
            bDebug = False
            
            if bDebug:            
                """ DEBUG INFO - PRINT IMAGE ADC VALUES TO FILE """
                print "Writing ADC values to file.."
                try:
                    OutputFile = open('/u/ckd27546/workspace/lpd/src/AdjustedDodgyAsicsReadout.txt', 'w+')
                except Exception as errStr:
                    print "Error opening file: ", errStr
                
                try:
                    for row in range( 32 ):
                        for asic in range(16):
                            for column in range(16):
                                pxlVal = completeDataArray[ column + (asic * 16) + (row * 256) ]
                                # Check if this is the second, fourth, sixth or eighth ASIC
                                if (asic == 1) or (asic == 3) or (asic == 5) or (asic == 7):
                                    # This is one of the dodgy ASICs
                                    if pxlVal > 2048:
    #                                    print ".",
                                        pxlVal -= 2048
                                    # Bit shift by one; whether 12 bit set or not
                                    pxlVal = pxlVal << 1
                                OutputFile.write("%i, " % pxlVal)
                                # Update Dodgy asics' values
                                completeDataArray[ column + (asic * 16) + (row * 256) ] = pxlVal
                except Exception as errStr:
                    print "Error writing ADC values to file: ", errStr
                else:
                    print "Finished writing to file"
    
                try:
                    OutputFile.close()
                except Exception as errStr:
                    print "Error closing file: ", errStr
            else:
                print "(Not modifying data..)"


            """ NOTE THAT THIS IS THE REAL MCCOY; DO NOT REMOVE IF ELIMINATING SUBPLOT FROM CODE
            !!!!!
            """
            if global_bSubPlotting is False:
                print "Reshaping completeDataArray from 1x8192 array into 32*256 array.."
                
                try:
                    self.data = completeDataArray.reshape(nrows, ncols)
                except Exception as errStr:
                    print "completeDataArray.reshape() failed! Exiting.."
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
        
        data_len = 160
        
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


#    def read16AsicData(self, sixteenBitArray):
#        """ read16AsicData() accepts sixteenBitArray array argument containing all
#            the ASIC data, and returns a LIST (!!) containing the data from the 16 ASICs
#            mounting in the two tile system """
#        
#        # 
#        twoTileAsicList = []
#        
#        # Distance [2 indices * 64 words] between any two consecutive pixels in the same ASIC
#        pixelDistance = 128
#        # Iterate over 512 pixels in one image
#        # Pixel = [0, 1, 2, 3, ..., 511]
#        try:
#            # Debug information for ASIC97
#            print "read16AsicData(), ASIC97 contains:"
#            
#            for pixel in range(512):
#                
#                # ASIC 97 located in word 27        [(27-1) * 2 = 52]
#                # ASIC 98 located in word 27 + 1    [ASIC97 + 1 = 53]
#                # ASIC 99 located in word 28 + 2    [ASIC97 + 2 = 54]
#                # ASIC100 located in word 28 + 3    [ASIC97 + 3 = 55]
#                ASIC97 = sixteenBitArray[pixel*pixelDistance + 52]
#                ASIC98 = sixteenBitArray[pixel*pixelDistance + 53]
#                ASIC99 = sixteenBitArray[pixel*pixelDistance + 54]
#                ASIC100 = sixteenBitArray[pixel*pixelDistance + 55]
#                
#                # ASIC 101 located in word 19                  [(19-1) * 2 =  36]
#                # ASIC 102 located in word 19 + 1              [ASIC101 + 1 = 37]
#                # ASIC 103 located in word 20                  [ASIC101 + 2 = 38]
#                # ASIC 104 located in word 20 + 3              [ASIC101 + 3 = 39]
#                ASIC101 = sixteenBitArray[pixel*pixelDistance + 36]
#                ASIC102 = sixteenBitArray[pixel*pixelDistance + 37]
#                ASIC103 = sixteenBitArray[pixel*pixelDistance + 38]
#                ASIC104 = sixteenBitArray[pixel*pixelDistance + 39]
#    
#                # ASIC 17 located in word 47                  [(47-1) * 2 = 92]
#                # ASIC 18 located in word 47 + 1              [ASIC17 + 1 = 93]
#                # ASIC 19 located in word 48 + 2              [ASIC17 * 2 = 94]
#                # ASIC 20 located in word 48 +                [ASIC17 + 3 = 95]
#                ASIC17 = sixteenBitArray[pixel*pixelDistance + 92]
#                ASIC18 = sixteenBitArray[pixel*pixelDistance + 93]
#                ASIC19 = sixteenBitArray[pixel*pixelDistance + 94]
#                ASIC20 = sixteenBitArray[pixel*pixelDistance + 95]
#                
#                # ASIC 21 located in word 39                  [(39-1) * 2 = 76]
#                # ASIC 22 located in word 39 + 1 [ASIC21 + 1 = 77]
#                # ASIC 23 located in word 40                  [ASIC21 + 2 = 78]
#                # ASIC 24 located in word 40 + 3 [ASIC21 + 3 = 79]
#                ASIC21 = sixteenBitArray[pixel*pixelDistance + 76]
#                ASIC22 = sixteenBitArray[pixel*pixelDistance + 77]
#                ASIC23 = sixteenBitArray[pixel*pixelDistance + 78]
#                ASIC24 = sixteenBitArray[pixel*pixelDistance + 79]
#                
#                # Append each of the 16 ASIC values to the list
#                twoTileAsicList.append(ASIC97)
#                twoTileAsicList.append(ASIC98)
#                twoTileAsicList.append(ASIC99) 
#                twoTileAsicList.append(ASIC100) 
#                twoTileAsicList.append(ASIC101) 
#                twoTileAsicList.append(ASIC102) 
#                twoTileAsicList.append(ASIC103) 
#                twoTileAsicList.append(ASIC104) 
#                twoTileAsicList.append(ASIC17) 
#                twoTileAsicList.append(ASIC18) 
#                twoTileAsicList.append(ASIC19) 
#                twoTileAsicList.append(ASIC20) 
#                twoTileAsicList.append(ASIC21) 
#                twoTileAsicList.append(ASIC22) 
#                twoTileAsicList.append(ASIC23) 
#                twoTileAsicList.append(ASIC24)
#                
#                # Debug information for ASIC97
#                print "%03X, " % ASIC97,
#                
#        except Exception as errStr:
#            print "read16AsicData() Error: ", errStr
#            exit()
#        
#        print ""
#        return twoTileAsicList

    def convertAsicDataIntoImage(self, sixteenBitArray):
        """ convertAsicDataIntoImage() sixteenBitArray array argument containing all
            the ASIC data, and returns a complete image consisting of the data from 
            the 16 ASICs organised into a 32 x 256 pixel image """
        # Create an array to contain 8192 elements (32 x 16 x 16)
        completeImageArray = np.empty(8192, dtype=np.uint16)
        
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        
#        print "convertAsicDataIntoImage(), algorithm picking out indices:"
        
        try:
#            # Debugging test..
#            for pxl in range(8192):
#                
#                if ( 256 <= pxl <= 511):
#                    completeImageArray[pxl] = 4095
#                elif ( 7936 <= pxl <= (7936+255) ):
#                    completeImageArray[pxl] = 4095
#                else:
#                    completeImageArray[pxl] = 295
            
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
                        print "convertAsicDataIntoImage(), look up table execution failed: ", errStr, "\nExiting.."
                        exit()                    

        except Exception as errStr:
            print "convertAsicDataIntoImage() Error: ", errStr, "\nExiting.."
            exit()
        
        return completeImageArray

# ~~~~~~~~~~~~ #
    def retrieveFirstImageFromAsicData(self, sixteenBitArray):
        """ retrieveFirstImageFromAsicData() takes the sixteenBitArray array argument containing all
            the ASIC data (full supermodule), and returns,
                * boolean to signal whether this is the last image in the data
                * the first image (32 x 16 x 16 pixels) of an image found in the data,
            in the form of the 16 ASICs organised into a 32 x 256 pixel image 
        """
        # Create an array to contain 8192 elements (32 x 16 x 16)
        imageImageArray = np.empty(8192, dtype=np.uint16)
        
        
        """ Debug information.. """
#        print "retrieveFirstImageFromAsicData() len(sixteenBitArray) ", len(sixteenBitArray)
        
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
                    print "retrieveFirstImageFromAsicData(), look up table execution failed: ", errStr, "\nExiting.."
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

# ~~~~~~~~~~~~ #

    def processRxData(self, data):
        """ Process (chunks of) UDP data into packets of a frame 
            [Code inherited from Rob - See: udp_rx_ll_mon_header_2_CA.py]
        """
                
        # save the read frame number as it'll be modified to be RELATIVE before we reach the end of this function.. 
        rawFrameNumber = -1

        data_len = len(data)

        try:
            offset = 0
            # Extract frame number (the first four bytes)
            frame_number = (ord(data[offset+3]) << 24) + (ord(data[offset+2]) << 16) + (ord(data[offset+1]) << 8) + ord(data[offset+0])
            # Extract packet number (the following four bytes)
            packet_number = (ord(data[offset+7]) << 24) + (ord(data[offset+6]) << 16) + (ord(data[offset+5]) << 8) + ord(data[offset+4])
            # Extract Start Of Frame, End of Frame
            frm_sof = (packet_number & 0x80000000) >> 31
            frm_eof = (packet_number & 0x40000000) >> 30
            packet_number = packet_number & 0x3FFFFFFF
    
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
                sys.exit()
            
            if frm_eof == 1:
                self.j=self.j+1
            else:
                pass

            # Not yet end of file: copy current packet contents onto (previous) packet contents
            # First 8 bytes are frame number and packet number - omitting those..
            # both are of type string..
            self.rawImageData = self.rawImageData + data[8:]

            try:
                #Add packet number to frame packet list
                #print "1", frame_number, packet_number
                self.packet_number_list[frame_number][packet_number] = self.packet_number_list[frame_number][packet_number] + 1
                #print "2", frame_number, packet_number
                #debug
            except Exception as errStr:
                print "self.packet_number_list error: ", errStr, "\nExiting.."
                sys.exit()


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
            
#            # start frm num prev at first frm num
#            if self.frm_num_prv == -1:
#                self.frm_num_prv = frame_number

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

