
# X10G Development code
# Receive and display 10G image data
# Hacked together by Christian Angelsen 18-06-2012


# For detailed comments on animation and the techniqes used here, see
# the wiki entry http://www.scipy.org/Cookbook/Matplotlib/Animations

import sys, time, datetime, argparse

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib

# Import HDF5 Library; Disable its use if library not installed on PC
try:
    import h5py
except:
    print "No HDF5 Library detected - Disabling file writing"
    bNoHdf5LibraryPresent = False
else:
    print "HDF5 Library present."
    bNoHdf5LibraryPresent = True

from networkConfiguration import *

from PyQt4 import QtCore, QtGui


class LpdImageObject(object):
    '''
        LpdImageObject - data container class to contain UDP payload and meta data
        (such as timestamp, packet, etc)
    '''
    def __init__(self, frameNumber):
        # Create a string to contain payload of all UDP packets
        self.rawImageData = ""
        self.frameNumber = frameNumber
        self.timeStampSof = 0.0

class RxThread(QtCore.QThread):
    
    def __init__(self, rxSignal, femHost, femPort):
        
        # Initialising variable used by processRxData
        self.first_frm_num = -1
        
        QtCore.QThread.__init__(self)
        self.rxSignal = rxSignal

        self.packetNumber = -1
        print "Listening to host: %s port: %s.." % (femHost, femPort)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((femHost, femPort))

    def __del__(self):
        self.wait()
        
    def run(self):

        frameCount = 0
        try:
            while 1:
                foundEof = 0
                lpdFrame = LpdImageObject(frameCount)
                while foundEof == 0:
                    stream = self.sock.recv(9000)
                    foundEof  = self.processRxData(lpdFrame, stream)
                    if foundEof:
                        # Complete frame received, transmit frame along with meta data saved in LpdImageObject object
                        self.rxSignal.emit(lpdFrame)
                        # Increment frame counter
                        frameCount += 1
                        
        except Exception as e:
            print "processRxData() failed: ", e, "\nExiting.."
            sys.exit()

    def processRxData(self, lpdFrame, data):
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

            if debugInfo > 1:
                if sof == 1:
                    print "-=-=-=-=- FrameNumber PacketNumber"
                print "trailerInfo: %8X %8X " % (trailerInfo[0], trailerInfo[1])
                if eof == 1:
                    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-" 
            
            #TODO: Restore this link if frame number coming from fem before absolute?          
            # frameNumber = train number relative to execution of this software
            #lpdFrame.frameNumber = frameNumber
            
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

            # Timestamp start of frame (when we received first data of train)
            if sof == 1:

                lpdFrame.timeStampSof = time.time()
                # It's the start of a new train, clear any data left from previous train..
                lpdFrame.rawImageData = ""                

            if eof == 1:
                lpdFrame.timeStampEof = time.time()
            
            # Append current packet data onto raw image omitting trailer info
            lpdFrame.rawImageData += data[0:-8]
            
            return eof
        except Exception as e:
            print "processRxData() error: ", e
            return -1

class BlitQT(FigureCanvas):

    ''' Change font size '''
    matplotlib.rcParams.update({'font.size': 8})
    
    dataRxSignal = QtCore.pyqtSignal(object)

    def __init__(self, femHost=None, femPort=None):

        print "Initialising.. "
        
        # Dummy train counter
        self.trainNumber = 0
        
        # Count number of iterations across multiple trains (ie number images across multiple trains)
        self.imageCounter   = 0
        # iterateOffset tracks how many images have been written to previous file(s) and offsets .resize() calls to prevent
        #    accummulating rows of 0 in hdf5 files.
        self.iterateOffset      = 0

        # Define plotted image dimensions: 
        self.nrows = 32
        self.ncols = 256     # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors in 2-Tile System: 16 x 16 = 256 columns
        self.imageSize = self.nrows * self.ncols

        # Create an array to contain 8192 elements (32 x 16 x 16)
        self.imageArray = np.zeros(self.imageSize, dtype=np.uint16)
        
        # Create hdf file - if HDF5 Library present
        if bHDF5:
            dateString = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            fileName = "/tmp/lpdSuperModule-%s.hdf5" % dateString

            self.hdfFile = h5py.File(fileName, 'w')
            self.imageDs = self.hdfFile.create_dataset('ds', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                            maxshape=(None,self.nrows, self.ncols))
            self.timeStampDs   = self.hdfFile.create_dataset('timeStamp',   (1,), 'f',      maxshape=(None,))
            self.trainNumberDs = self.hdfFile.create_dataset('trainNumber', (1,), 'uint32', maxshape=(None,))
            self.imageNumberDs = self.hdfFile.create_dataset('imageNumber', (1,), 'uint32', maxshape=(None,))

        FigureCanvas.__init__(self, Figure())
        
        # Only create plots if user selected data to be plotted..
        if bDisplayPlotData:

            # Generate list of xticks, yticks to label the x, y axis
            xlist = []
            for i in range(16, 256, 16):
                xlist.append(i)
                
            ylist = []
            for i in range(8, 32, 8):
                ylist.append(i)
            
            print "Preparing graphics.."
            
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

                if bColorbarVisible:
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

        # Was either femHost and femPort NOT provided by parser?
        if (femHost == None) or (femPort == None):
            # At least one not supplied by the command line; Use networkConfiguration class
            networkConfig = networkConfiguration()
            
            if femHost == None:
                femHost = networkConfig.tenGig0DstIp
            if femPort == None:
                femPort = int(networkConfig.tenGig0DstPrt)

        self.rxThread = RxThread(self.dataRxSignal, femHost, femPort)
        self.rxThread.start()


    def handleDataRx(self, dataRx):

        # End Of File found, self.rawImageData now contain every pixel of every ASIC (of the complete Quadrant!)
        if bTimeStamp:
            timeX1 = time.time()
        
        print "Raw Image Data Received:     ", len(dataRx.rawImageData), "(bytes)"

        ''' More information on numpy & Big/Little-endian:    http://docs.scipy.org/doc/numpy/user/basics.byteswapping.html '''
        # Create 16 bit, Little-Endian, integer type using numpy
        _16BitLittleEndianType = np.dtype('<i2')

        # Simultaneously extract 16 bit words and swap the byte order
        #     eg: ABCD => DCBA
        self._16BitWordArray = np.fromstring(dataRx.rawImageData, dtype=_16BitLittleEndianType)
    
        if (debugInfo > 2) and (debugInfo < 8):
            print "Extracted 16 bit words: ", len(self._16BitWordArray), ". Array contents:"
            self.display16BitArrayInHex()
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

        if debugInfo > 7:
            if bTimeStamp:
                time2 = time.time()
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
            if bTimeStamp:
                time1 = time.time()
                self.timeStampGainCounter = time1 - time2

            print "\nGain:      x100       x10        x1  (invalid)"
            print "      %9i %9i %9i %9i" % (gainCounter[0], gainCounter[1], gainCounter[2], gainCounter[3])

        # Define variables that increase with each loop iteration
        currentPlot = 0
        bNextImageAvailable = True

        # Count number of loops with respect to trains per hdf5 file if selected
        loopCounter = 0
        
        # Loop over the specified number of plots
        while bNextImageAvailable and currentPlot < plotMaxPlots:

            if bTimeStamp:
                timeD1 = time.time()
            
            dataBeginning = 65536*currentPlot

            # Get the first image of the train
            bNextImageAvailable = self.retrieveImage(dataBeginning)
            
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
            
            if bDisplayPlotData:
#                print "Train %i Image %i" % (frameNumber, currentPlot), " data left: ", len( self._16BitWordArray[dataBeginning:] )
#                # Set title as train number, current image number
#                self.ax[currentPlot].set_title("Train %i Image %i" % (frameNumber, currentPlot))
                print "Train %i Image %i" % (self.trainNumber, currentPlot), " data left: %10i" % len( self._16BitWordArray[dataBeginning:] ),
                if bTimeStamp is False:
                    print ""

                self.ax[currentPlot].set_title("Train %i Image %i" % (self.trainNumber, currentPlot))
                
                # Load image into figure
                self.img[currentPlot].set_data(self.data)
    
                self.ax[currentPlot].draw_artist(self.img[currentPlot])
                self.blit(self.ax[currentPlot].bbox)

            # Write image to file - if HDF5 Library present
            if bHDF5:
                self.imageDs.resize((loopCounter+1, self.nrows, self.ncols))
                self.imageDs[loopCounter,...] = self.data
                
                self.timeStampDs.resize((loopCounter+1, ))
                self.timeStampDs[loopCounter] = dataRx.timeStampSof
                
                self.trainNumberDs.resize((loopCounter+1, ))
                self.trainNumberDs[loopCounter] = self.trainNumber
                
                self.imageNumberDs.resize((loopCounter+1, ))
                self.imageNumberDs[loopCounter] = self.imageCounter

                # Check whether specified number of images written to file
                if (self.imageCounter % (numberPlotsPerFile+1)) == numberPlotsPerFile:
                    # Reset loop counter, determine new file name
                    loopCounter = 0
                    dateString = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    fileName = "/tmp/lpdSuperModule-%s.hdf5" % dateString
                    
                    if self.hdfFile.filename == fileName:
                        # Modify new name to avoid overwritten old..
                        fileName = fileName[:-5] + '_' + str(self.imageCounter) + fileName[-5:]
                        if debugInfo > 0:
                            print "\nPrevious filename: '" + self.hdfFile.filename + "'"
                            print "New use filename:  '" + fileName + "'"
                    
                    # Close old file
                    self.hdfFile.close()
                    self.hdfFile = h5py.File(fileName, 'w')
                    # Recreate datasets
                    self.imageDs = self.hdfFile.create_dataset('ds', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols),
                                                               maxshape=(None,self.nrows, self.ncols))
                    self.timeStampDs   = self.hdfFile.create_dataset('timeStamp',   (1,), 'f',      maxshape=(None,))
                    self.trainNumberDs = self.hdfFile.create_dataset('trainNumber', (1,), 'uint32', maxshape=(None,))
                    self.imageNumberDs = self.hdfFile.create_dataset('imageNumber', (1,), 'uint32', maxshape=(None,))
                else:
                    loopCounter += 1
                    
                # Increment image number counter
                self.imageCounter += 1
                
            # Clear data before next iteration (but after data written to file)
            self.data.fill(0)

            # Increment currentPlot
            currentPlot += 1
            if bTimeStamp:
                timeD2 = time.time()
                print "%.9f" %(timeD2 - timeD1)
        else:
            # Finished drawing subplots

            # Dummy counter
            self.trainNumber += 1

        # 'Reset' rawImageData variable
        dataRx.rawImageData = dataRx.rawImageData[0:0]
        if bTimeStamp:
            timeX2 = time.time()
            print "Total time = ",(timeX2 - timeX1)

        print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        
        if bDisplayPlotData:
            if self.cnt == 0:
                self.draw()
            else:
                self.cnt += 1

    def __del__(self):
        # Close file if HDF5 Library present
        if bHDF5:
            self.hdfFile.close()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
#        Restructured functions to operate on numpy arrays
#
#  -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    def display16BitArrayInHex(self):
        """ display16BitArrayInHex displays each 16 bit ADC value (each index/byte)
            .. Unless data_len hardcoded to 160..
        """
        if debugInfo > 6:
            data_len = len(self._16BitWordArray)
        elif debugInfo > 5:
            data_len = len(self._16BitWordArray) / 2
        elif debugInfo > 4:
            data_len = len(self._16BitWordArray) / 4
        elif debugInfo > 3:
            data_len = len(self._16BitWordArray) / 8
        elif debugInfo > 2:
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
            print "Debug info: %6i %6i %6i %6i %6i %6i " % (asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics)
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


if __name__ == "__main__":

    # Define default values
    femHost          = None
    femPort          = None
    bTimeStamp       = False
    bColorbarVisible = False
    bDisplayPlotData = False
    bHDF5            = False
    debugInfo        = 0
    plotRows         = 4
    plotCols         = 1
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="superModuleReceiveTest.py - Receive data from a Super Module. ",
                                     epilog="If no flags are specified, femhost and femport are set according to machineConfiguration.py, everything else's disabled.")

    parser.add_argument("--canvasrows",     help="Set rows of plots (eg 2 rows)",                               type=int, default=plotRows)
    parser.add_argument("--canvascols",     help="Set columns of plots (eg 2 columns)",                         type=int, default=plotCols)
    parser.add_argument("--colorbar",       help="Enable colorbar (0=disable, 1=enable)",                       type=int, default=bColorbarVisible)
    parser.add_argument("--debuginfo",      help="Enable debug info (0=disable, 1=enable)",                     type=int, choices=range(9), default=0)
    parser.add_argument("--femhost",        help="Set fem host IP (e.g 10.0.0.1)",                              type=str, default=femHost)
    parser.add_argument("--femport",        help="Set fem port (eg 61649)",                                     type=int, default=femPort)
    parser.add_argument("--plotdata",       help="Plot received data (0=disable, 1=enable)",                    type=int, choices=[0, 1], default=0)
    parser.add_argument("--timeinfo",       help="Display timing info (0=disable, 1=enable)",                   type=int, choices=[0, 1], default=0)
    parser.add_argument("--writedata",      help="Write data to hdf5 file (0=disable, 0> = number images/file)",type=int, default=0)
    args = parser.parse_args()

    # Temp debug info
    print "User selected: -->",
    # Copy value(s) for the provided arguments
    if args.femhost:
        femHost = args.femhost
        print "femhost",

    if args.femport:
        femPort = int(args.femport)
        print "femPort",

    if args.timeinfo:
        print "timeinfo",
        bTimeStamp = True
        
    if args.plotdata:
        print "plotdata",
        bDisplayPlotData = True
        
    if args.writedata:
        # Only allow file write if HDF5 library installed..
        if bNoHdf5LibraryPresent:
            print "writedata(%i)" % args.writedata,
            bHDF5 = True
            numberPlotsPerFile = args.writedata
        else:
            print "(no HDF5 lib)",
            bHDF5 = False
        
    if args.debuginfo:
        print "debuginfo(%i)" % args.debuginfo,
        debugInfo = args.debuginfo

    if args.canvasrows:
        print "plotRows(%i)" % args.canvasrows,
        plotRows = args.canvasrows
        
    if args.canvascols:
        print "plotCols(%i)" % args.canvascols,
        plotCols = args.canvascols
        
    if args.colorbar:
        print "colorbar"
        bColorbarVisible = True

    # Calculate number of plots to draw
    plotMaxPlots = plotRows * plotCols

    # Temp debug info
    print " <--"
    
    app = QtGui.QApplication(sys.argv)
    widget = BlitQT(femHost, femPort)
    widget.show()
    
    sys.exit(app.exec_())
