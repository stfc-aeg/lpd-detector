
# X10G Development code
# Receive and display 10G image data
# Hacked together by Christian Angelsen 18-06-2012


# For detailed comments on animation and the techniqes used here, see
# the wiki entry http://www.scipy.org/Cookbook/Matplotlib/Animations

import os, sys, time, socket, datetime

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.cm as cm
import matplotlib.pyplot
import matplotlib

# Import HDF5 Library; Disable its use if library not installed on PC
try:
    import h5py
except:
    print "No HDF5 Library detected - Disabling file writing"
    bHDF5 = False
else:
    print "HDF5 Library present."
    bHDF5 = True

from networkConfiguration import *

from PyQt4 import QtCore, QtGui


# Enable or disable debugging
bDebug = 0

#bNewRetrieveFunc = True

# Define variables used as arguments by
# Subplot function call: subplot(plotRows, plotCols, plotMaxPlots)
#    where max number of plotMaxPlots = plotRows * plotCols
plotRows = 4
plotCols = 1
plotMaxPlots = plotRows * plotCols


class RxThread(QtCore.QThread):
    
    def __init__(self, rxSignal, femHost, femPort):
        
        QtCore.QThread.__init__(self)
        self.rxSignal = rxSignal

        print "Listening to host: %s port: %s.." % (femHost, femPort)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((femHost, femPort))

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

    def __init__(self, femHost=None, femPort=None):
        FigureCanvas.__init__(self, Figure())

        # Time code execution
        self.timeStart = []
        self.timeStop = []
        
        # Track packet number
        self.packetNumber = -1

        # Define plotted image dimensions: 
        self.nrows = 32
        self.ncols = 256     # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors in 2-Tile System: 16 x 16 = 256 columns
        self.imageSize = self.nrows * self.ncols

        # Create an array to contain 8192 elements (32 x 16 x 16)
        self.imageArray= np.zeros(self.imageSize, dtype=np.uint16)
        
        # Initialising variables used by processRxData..
        self.first_frm_num = -1
        self.j = 0
        
        # Create a list to contain payload of all UDP packets
        self.rawImageData = ""

        # Generate list of xticks, yticks to label the x, y axis
        xlist = []
        for i in range(16, 256, 16):
            xlist.append(i)
            
        ylist = []
        for i in range(8, 32, 8):
            ylist.append(i)
        
        print "Initialising; Preparing graphics.."
        
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
            

        self.dataRxSignal.connect(self.handleDataRx)
                
        self.tstart = time.time()

        # Was either femHost and femPort NOT provided to this class?
        if (femHost == None) or (femPort == None):
            # Either or both were not supplied from the command line; Use networkConfiguration class
            networkConfig = networkConfiguration()
            femHost = networkConfig.tenGig0DstIp
            femPort = int(networkConfig.tenGig0DstPrt)

        self.rxThread = RxThread(self.dataRxSignal, femHost, femPort)
        self.rxThread.start()


    def handleDataRx(self, data):

        # process UDP data in data variable
        try:
            frameNumber, foundEof  = self.processRxData(data)
        except Exception as e:
            print "processRxData() failed: ", e, "\nExiting.."
            sys.exit()
        
        # Only process image data when End Of File encountered
        if foundEof:
            
            print "\nRaw Image Data Received = ", len(self.rawImageData), " (bytes)"
            
            # End Of File found, self.rawImageData now contain every pixel of every ASIC (of the complete Quadrant!)
            # Reset packet number
            self.packetNumber= -1
            
            ''' More information on numpy & Big/Little-endian:    http://docs.scipy.org/doc/numpy/user/basics.byteswapping.html '''
            
            # Create 16 bit, Little-Endian, integer type using numpy
            _16BitLittleEndianType = np.dtype('<i2')
            # Simultaneously extract 16 bit words and swap the byte order
            #     eg: ABCD => DCBA
            self._16BitWordArray = np.fromstring(self.rawImageData, dtype=_16BitLittleEndianType)
            
            if bDebug > 5:
                print "Extracted 16 bit words: ", len(self._16BitWordArray), ". Array contents: "
                self.display16BitArrayInHex()
                print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

            if bDebug > 7:

                # Check the Gain bits (Bits 12-13);
                # [0] = x100, [1] = x10, [2] = x1, [3] = invalid
                gainCounter = [0, 0, 0, 0]
    
                for idx in range( len(self._16BitWordArray) ):
    
                    # Check bits 12-13: 
                    gainBits = self._16BitWordArray[idx] & 0x3000
                    if gainBits > 0:
                        # Gain isn't x100, determine its type
                        gain = gainBits >> 12
                        if gain == 1:
                            # x10
                            gainCounter[1] += 1
                        elif gain == 2:
                            # x1
                            gainCounter[2] += 1
                        else:
                            # Invalid gain setting detected
                            gainCounter[3] += 1
                    else:
                        # Gain is x100
                        gainCounter[0] += 1

                print "\nGain:      x100       x10        x1  (invalid)"
                print "      %9i %9i %9i %9i" % (gainCounter[0], gainCounter[1], gainCounter[2], gainCounter[3])

            # Create hdf file - if HDF5 Library present
            if bHDF5:
                dateString = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                fileName = "/tmp/lpdTwoTile-%s.hdf5" % dateString
        
                hdfFile = h5py.File(fileName, 'w')
                ds = hdfFile.create_dataset('ds', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                                maxshape=(None,self.nrows, self.ncols))

            # Define variables that increase with each loop iteration
            currentPlot = 0
            bNextImageAvailable = True
            
            # Loop over the specified number of plots
            while bNextImageAvailable and currentPlot < plotMaxPlots:
                
                dataBeginning = 65536*currentPlot

                t1 = time.time()
                self.timeStart.append(t1)

                # Get the first image of the train
                bNextImageAvailable = self.retrieveImage(dataBeginning)
                    
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
                
                # Display plot information
                print "Train %i Image %i" % (frameNumber, currentPlot), " data left: %9i" % len( self._16BitWordArray[dataBeginning:] )
                
                # Set title as train number, current image number
                self.ax[currentPlot].set_title("Train %i Image %i" % (frameNumber, currentPlot))
                
                # Load image into figure
                self.img[currentPlot].set_data(self.data)

                self.ax[currentPlot].draw_artist(self.img[currentPlot])
                self.blit(self.ax[currentPlot].bbox)

                # Write image to file - if HDF5 Library present
                if bHDF5:
                    ds.resize((currentPlot+1, self.nrows, self.ncols))
                    ds[currentPlot,...] = self.data

                # Increment currentPlot
                currentPlot += 1

            else:
                # Finished this train - work out timings..
                if len(self.timeStart) != len(self.timeStop):
                    print "Mismatch between timeStart %i and timeStop %i" % (len(self.timeStart), len(self.timeStop))
                else:
                    delta = 0
                    tSum = 0
                    for idx in range(len(self.timeStart)):
                        delta = self.timeStop[idx] - self.timeStart[idx]
                        tSum += delta
                    print "Average time executing fuction: ", (tSum / len(self.timeStop))

                # Finished - Close file if HDF5 Library present
                if bHDF5:
                    hdfFile.close()

            # 'Reset' rawImageData variable
            self.rawImageData = self.rawImageData[0:0]
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        else:
            # Didn't find End Of File within this packet, check next packet..
            pass
  
        if self.cnt == 0:
            self.draw()
        else:
            self.cnt += 1

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
#        Restructured functions to operate on numpy arrays
#
#  -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    def display16BitArrayInHex(self):
        """ display16BitArrayInHex displays each 16 bit ADC value (each index/byte)
            .. Unless data_len hardcoded to 160..
        """
        if bDebug > 8:
            data_len = len(self._16BitWordArray)
        elif bDebug > 7:
            data_len = len(self._16BitWordArray) / 2
        elif bDebug > 6:
            data_len = len(self._16BitWordArray) / 4
        elif bDebug > 5:
            data_len = 160
        
        currentArrayElement = ""
        try:
            # Convert each 2 byte into 16 bit data and print that
            for idx in range(data_len):
                
                if (idx %16 == 0):
                    print "%6d : " % idx,
                    
                currentArrayElement =  currentArrayElement + "   %04X " % self._16BitWordArray[idx]
                
                if (idx % 16 == 15):
                    print currentArrayElement
                    currentArrayElement = ""
                
            print "Number of 16 bit words: ", data_len
        except Exception as e:
            print "display16BitArrayInHex() error: ", e
            exit(0)
            
# ~~~~~~~~~~~~ #

    def retrieveImage(self, dataBeginning):
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

    def processRxData(self, data):
        """ 
        Processes received data packets, decoding the Train Transfer Protocol information
        to construct completed frames (trains) 
        """

        try:
            # Extract Trailer information
            trailerInfo = np.zeros(2, dtype=np.uint32)
            trailerInfo = np.fromstring(data[-8:], dtype=np.uint32)
            
            # Extract train/frame number (the second last 32 bit word from the raw data)
            frameNumber = trailerInfo[0]
            # Extract packet number (last 32 bit word)
            packetNumber = trailerInfo[1] & 0x3FFFFFFF

            # Extract Start Of Frame, End of Frame
            sof = (trailerInfo[1] >> (31)) & 0x1
            eof = (trailerInfo[1] >> (30)) & 0x1

            if bDebug > 0:
                if sof == 1:
                    print "-=-=-=-=- FrameNumber PacketNumber"
                print "trailerInfo: %8X %8X " % (trailerInfo[0], trailerInfo[1])
                if eof == 1:
                    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-" 
            
            if self.first_frm_num == -1:
                self.first_frm_num = frameNumber
                
            frameNumber = frameNumber - self.first_frm_num
            
            # Compare this packet number against the previous packet number
            if packetNumber != (self.packetNumber +1):
                
                # packet numbering not consecutive
                if packetNumber > self.packetNumber:
                    
                    # this packet lost between this packet and the last packet received
                    print "Warning: Previous packet number: %3i while current packet number: %3i" % (self.packetNumber, packetNumber)

            # Update current packet number
            self.packetNumber = packetNumber

            # Not yet end of file: copy current packet contents onto (previous) packet contents
            # Last 8 bytes are frame number and packet number - omit these
            self.rawImageData = self.rawImageData + data[0:-8]

            # Return train number and end of frame
            return frameNumber, eof
        except Exception as e:
            print "processRxData() error: ", e
            return -1, -1


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
    widget = BlitQT(femHost, femPort)
    widget.show()
    
    sys.exit(app.exec_())

