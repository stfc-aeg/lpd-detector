
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
#bHDF5 = False

from networkConfiguration import *

from PyQt4 import QtCore, QtGui

# Enable or disable time stamping
bTimeStamp = True


# Enable or disable debugging
bDebug = False

# Define variables used as arguments by
# Subplot function call: subplot(plotRows, plotCols, plotMaxPlots)
#    where max number of plotMaxPlots = plotRows * plotCols
plotRows = 2
plotCols = 2
plotMaxPlots = plotRows * plotCols

class dataLocker(object):
    '''
        dataLocker - data container class to contain UDP payload and meta data
        (such as timestamp, packet, etc)
    '''
    def __init__(self):
        # Create a string to contain payload of all UDP packets
        self.rawImageData = ""
        self.frameNumber = -1
        self.timeStampSof = 0.0
        self.packetNumber = -1
        

class RxThread(QtCore.QThread):
    
    def __init__(self, rxSignal, femHost, femPort):

        ###############################################
        #            MIGRATED VARIABLES               #
        ###############################################
        # Initialising variables used by processRxData..
        self.first_frm_num = -1
        self.j = 0
        # Create object to contain UDP payload, timestamps, etc
        self.dataObject = dataLocker()
        # Create a list to contain payload of all UDP packets
#        self.dataObject.rawImageData = ""
        # Track packet number
#        self.dataObject.packetNumber = -1

        ###############################################
        QtCore.QThread.__init__(self)
        self.rxSignal = rxSignal

        print "Listening to host: %s port: %s.." % (femHost, femPort)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((femHost, femPort))

    def __del__(self):
        self.wait()
        
    def run(self):

        try:
            while 1:    
                stream = self.sock.recv(9000)
#                print ".",
                foundEof  = self.processRxData(stream)
                if foundEof:
                    # Complete frame received, transmit frame along with meta data saved in dataLocker object
                    self.rxSignal.emit(self.dataObject)

        except Exception as e:
            print "processRxData() failed: ", e, "\nExiting.."
            sys.exit()

    def processRxData(self, data):
        """ Process (chunks of) UDP data into packets of a frame 
            [Code inherited from Rob - See: udp_rx_ll_mon_header_2_CA.py]
        """
#        if bTimeStamp:
#            t1 = time.time()

        # Save the read train number as it'll be modified to be RELATIVE before we reach the end of this function.. 
        rawFrameNumber = -1

        ''' DEBUGGING INFORMATION '''
#        if ( ( ord(data[-1]) & 0x80) >> 7 ) == 1:
#            print "The last eight bytes of each packet:"
#            print "-- -- -- -- -- -- -- -- -- -- -- --"
#            print "  -8, -7, -6, -5, -4, -3, -2, -1"
#        sDebug = ""
#        for i in range(8, 0, -1):
#            sDebug += "%4X" % ord( data[-i] )
#        print sDebug
        

        try:
            offset = 0
            # Extract train number (the first four bytes)
#            frame_number = (ord(data[offset+3]) << 24) + (ord(data[offset+2]) << 16) + (ord(data[offset+1]) << 8) + ord(data[offset+0])
            frame_number = 0
            # Extract packet number (the following four bytes)
            packet_number = ord(data[offset-4]) #(ord(data[offset+7]) << 24) + (ord(data[offset+6]) << 16) + (ord(data[offset+5]) << 8) + ord(data[offset+4])
#            packet_number = 0
            trailer_info = ord(data[-1])
#            print "trailer_info: ", trailer_info
            # Extract Start Of Frame, End of Frame
            frm_sof = (trailer_info & 0x80) >> 7
            frm_eof = (trailer_info & 0x40) >> 6
#            packet_number = packet_number & 0x3FFFFFFF
            
            if bDebug:
                print "sof/eof = %4X, %4X" % (frm_sof, frm_eof),
            # frame_number = train number relative to execution of this software
            self.dataObject.frameNumber = frame_number
            
            if self.first_frm_num == -1:
                self.first_frm_num = frame_number
                
            frame_number = frame_number - self.first_frm_num
            
            # Compare this packet number against the previous packet number
            if packet_number != (self.dataObject.packetNumber +1):
                # packet numbering not consecutive
                if packet_number > self.dataObject.packetNumber:
                    # this packet lost between this packet and the last packet received
                    print "Warning: Previous packet number: %3i versus this packet number: %3i" % (self.dataObject.packetNumber, packet_number)

            # Update current packet number
            self.dataObject.packetNumber = packet_number

            # Timestamp start of frame (when we received first data of train)
            if bTimeStamp:
                if frm_sof == 1:
                    # It's the start of a new train, clear any data left from previous train..
                    self.dataObject.rawImageData = ""
                    self.dataObject.timeStampSof = time.time()

            if frm_eof == 1:
                self.j=self.j+1

                if bTimeStamp:
                    self.timeStampEof = time.time()
                    print "UDP data receive time:               %.9f" % (self.timeStampEof - self.dataObject.timeStampSof)
            else:
                pass
            
            # Not yet end of file: copy current packet contents onto (previous) packet contents
            # Last 8 bytes are train number and packet number - omitting those..
            # both are of type string..
            self.dataObject.rawImageData += data[0:-8]
            # Return train number and end of train
            #return rawFrameNumber, frm_eof
            return frm_eof
        except Exception as e:
            print "processRxData() error: ", e
            return -1, -1


class BlitQT(FigureCanvas):

    ''' Change font size '''
    matplotlib.rcParams.update({'font.size': 8})
    
    dataRxSignal = QtCore.pyqtSignal(object)

    def __init__(self, femHost=None, femPort=None):
        FigureCanvas.__init__(self, Figure())

        # Dummy train counter
        self.trainNumber = 0

        # Define plotted image dimensions: 
        self.nrows = 32*8   # 32 rows * 8 ASICs = 256 
        self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        self.imageSize = self.nrows * self.ncols

        # Create an array to contain 65536 elements (32 x 8 x 16 x 16 = super module image)
        self.imageArray = np.zeros(self.imageSize, dtype=np.uint16)

#        # Initialising variables used by processRxData..
#        self.first_frm_num = -1
#        self.j = 0

#        # Create a list to contain payload of all UDP packets
#        self.rawImageData = ""

#        # DEBUG VARIABLES
#        self.deltaTime  = 0
#        self.deltaCount = 0

        # Generate list of xticks, yticks to label the x, y axis
        xlist = []
        for i in range(16, 256, 16):
            xlist.append(i)
            
        ylist = []
        for i in range(32, 256, 32):
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
            
            # Add vertical lines to differentiate between two tiles
            self.ax[idx].vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
            
            for i in range(32, self.nrows, 32):
                self.ax[idx].hlines(i-0.5, 0, self.nrows-1, color='y', linestyles='solid')
            
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


    def handleDataRx(self, dataRx):

        # End Of File found, self.rawImageData now contain every pixel of every ASIC (of the complete Quadrant!)
        if bTimeStamp:
            timeX1 = time.time()
        
        print "Raw Image Data Received:     ", len(dataRx.rawImageData), "(bytes)"

        ''' More information on numpy & Big/Little-endian:    http://docs.scipy.org/doc/numpy/user/basics.byteswapping.html '''
        # Create 16 bit, Little-Endian, integer type using numpy
        _16BitLittleEndianType = np.dtype('<i2')

        # Simultaneously extract 32 bit words and swap the byte order
        #     eg: ABCD => DCBA
        self._16BitWordArray = np.fromstring(dataRx.rawImageData, dtype=_16BitLittleEndianType)
    
        if bDebug:
            print "Extracted 16 bit words: ", len(self._16BitWordArray), ". Array contents:"
            self.display16BitArrayInHex()
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

        if bDebug:
            if bTimeStamp:
                time2 = time.time()
            #TODO: Checking the Gain bits slows down displaying the read out data..
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
        
        # Create hdf file - if HDF5 Library present
        if bHDF5:
            dateString = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            fileName = "/tmp/lpdSuperModule-%s.hdf5" % dateString
    
            hdfFile = h5py.File(fileName, 'w')
            ds = hdfFile.create_dataset('ds', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                            maxshape=(None,self.nrows, self.ncols))

        # Define variables that increase with each loop iteration
        currentPlot = 0
        bNextImageAvailable = True
        
#            if bTimeStamp:
#                print "self.timeStampGainCounter:  ", self.timeStampGainCounter

        # Loop over the specified number of plots
        while bNextImageAvailable and currentPlot < plotMaxPlots:

            if bTimeStamp:
                timeD1 = time.time()

            dataBeginning = self.imageSize*currentPlot

            # Get the first image of the image
            bNextImageAvailable = self.retrieveFirstSuperModuleImageFromAsicData(dataBeginning)

            # The first image, imageArray, has now been stripped from the image
            # Reshape image into 256 x 256 pixel array
            try:
                self.data = self.imageArray.reshape(self.nrows, self.ncols)
            except Exception as e:
                print "handleDataRx() failed to reshape imageArray: ", e, "\nExiting.."
                print "len(self.data),  self.nrows, self.ncols = ", len(self.data),  self.nrows, self.ncols
                exit()
            
            # Mask out gain bits from data
            self.data = self.data & 0xfff
            
            # Display debug information..
#                print "Train %i Image %i" % (frameNumber, currentPlot), " data left: ", len( self._16BitWordArray[dataBeginning:] )
#                # Set title as train number, current image number
#                self.ax[currentPlot].set_title("Train %i Image %i" % (frameNumber, currentPlot))
            print "Train %i Image %i" % (self.trainNumber, currentPlot), " data left: %8i" % len( self._16BitWordArray[dataBeginning:] ),
#                if bTimeStamp:
#                    print ".retrieve..(): ", self.timeStampRetrieveFunc
#                else:
#                    print ""

            self.ax[currentPlot].set_title("Train %i Image %i" % (self.trainNumber, currentPlot))
            
            # Load image into figure
            self.img[currentPlot].set_data(self.data)

            self.ax[currentPlot].draw_artist(self.img[currentPlot])
            # Draw new plot
            self.blit(self.ax[currentPlot].bbox)

            # Clear data before next iteration (image already rendered)
            self.data.fill(0)

            # Write image to file - if HDF5 Library present
            if bHDF5:
                ds.resize((currentPlot+1, self.nrows, self.ncols))
                ds[currentPlot,...] = self.data

            # Increment currentPlot
            currentPlot += 1
            if bTimeStamp:
                time3 = time.time()
                print "%.9f" %(time3 - timeD1)
        else:
            # Finished
#            print "\nFinished drawing subplots"
            # Close file if HDF5 Library present
            if bHDF5:
                hdfFile.close()

            # Dummy counter
            self.trainNumber += 1

        # 'Reset' rawImageData variable
        dataRx.rawImageData = dataRx.rawImageData[0:0]
        if bTimeStamp:
            timeX2 = time.time()
            print "Total time = ",(timeX2 - timeX1)

        print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
  
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
        data_len = len(self._16BitWordArray)
        
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


    def retrieveFirstSuperModuleImageFromAsicData(self, dataBeginning):
        """ Extracts one image beginning at argument dataBeginning in the member array 
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
        self.imageArray = np.zeros(numPixels, dtype=np.uint16)
        self.imageArray = np.reshape(self.imageArray, (numRows * numRowsPerAsic, numCols * numColsPerAsic))

        rawOffset = 0

        if bTimeStamp:
            t1 = time.time()
        try:
            for asicRow in xrange(numRowsPerAsic):
                for asicCol in xrange(numColsPerAsic):
                    
                    self.imageArray[asicRow::numRowsPerAsic, asicCol::numColsPerAsic] = self._16BitWordArray[rawOffset:(rawOffset + numAsics)].reshape(8,16)
                    rawOffset += numAsics
        
        except IndexError:
            print "Image Processing Error @ %6i %6i %6i %6i %6i %6i " % ( asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics )
            sys.exit()
        except Exception as e:
            print "Error while extracting image: ", e, "\nExiting.."
            sys.exit()

        # Image now upside down, reverse the order
        self.imageArray[:,:] = self.imageArray[::-1,:]

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
    widget = BlitQT(femHost, femPort)
    widget.show()
    
    sys.exit(app.exec_())
