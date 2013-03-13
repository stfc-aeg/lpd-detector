
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
bDebug = False

# Define variables used as arguments by
# Subplot function call: subplot(plotRows, plotCols, plotMaxPlots)
#    where max number of plotMaxPlots = plotRows * plotCols
plotRows = 2
plotCols = 2
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
        
        # Track packet number
        self.packetNumber = -1

        # Define plotted image dimensions: 
        self.nrows = 32*8   # 32 rows * 8 ASICs = 256 
        self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        self.imageSize = self.nrows * self.ncols

        # Create an array to contain 65536 elements (32 x 8 x 16 x 16 = super module image)
        self.imageArray = np.zeros(self.imageSize, dtype=np.uint16)

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
            self.ax[idx].set_title("Train %i" % idx)
                            
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
            
            # Create 32 bit, Little-Endian, integer type using numpy
            _32BitLittleEndianType = np.dtype('<i4')
            # Simultaneously extract 32 bit words and swap the byte order
            #     eg: ABCD => DCBA
            _32BitWordArray = np.fromstring(self.rawImageData, dtype=_32BitLittleEndianType)
            
            if bDebug:
                print "Extracted number of 32 bit words: ", len(_32BitWordArray)
                # Display array content 32 bit integers
                print "Array contents structured into 32 bit elements [byte swapped!]:"
                self.display32BitArrayInHex(_32BitWordArray)
                print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

            # Calculate length of 32 bit array
            _32BitArrayLen = len(_32BitWordArray)

            # Create empty array to store 16 bit elements (eg 32 Bit array * 2)
            #     Each 32-bit word contain 2 pixels
            _16BitWordArray = np.zeros(_32BitArrayLen*2, dtype='i2')
            
            
            # Split each 4 Byte element into 2 adjecent, 2 Byte elements
            for rawIdx in range(_32BitArrayLen):
                # Reverted back to NOT swapping ASIC pairs
                _16BitWordArray[rawIdx*2] = _32BitWordArray[rawIdx] >> 16
                _16BitWordArray[rawIdx*2 + 1]     = _32BitWordArray[rawIdx] & 0xFFFF

            # Check the Gain bits (Bits 12-13);
            # [0] = x100, [1] = x10, [2] = x1, [3] = invalid
            gainCounter = [0, 0, 0, 0]

            for idx in range( len(_16BitWordArray) ):

                # Check bits 12-13: 
                gainBits = _16BitWordArray[idx] & 0x3000
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
            del gainCounter
            
            
            if bDebug:
                print "Number of 16 Bit Word: ", len(_16BitWordArray)
                # Display array contenting 16 bit elements:
                print "Array contents re-structured into 16 bit elements:"
                self.display16BitArrayInHex(_16BitWordArray)
                print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
            
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
            
            # Loop over the specified number of plots
            while bNextImageAvailable and currentPlot < plotMaxPlots:
                
                dataBeginning = self.imageSize*currentPlot
                
                # Get the first image of the image
                bNextImageAvailable = self.retrieveFirstSuperModuleImageFromAsicData(_16BitWordArray[dataBeginning:])
                
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
                print "Train %i Image %i" % (frameNumber, currentPlot), " data left: ", len( _16BitWordArray[dataBeginning:] )
                
                # Set title as train number, current image number
                self.ax[currentPlot].set_title("Train %i Image %i" % (frameNumber, currentPlot))
                
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

            else:
                # Finished
                print "Finished drawing subplots"
                # Close file if HDF5 Library present
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
        except Exception as e:
            print "display32BitArrayInHex() error: ", e
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
        except Exception as e:
            print "display16BitArrayInHex() error: ", e
            exit(0)

# ~~~~~~~~~~~~ #


    def retrieveFirstSuperModuleImageFromAsicData(self, sixteenBitArray):
        """ The sixteenBitArray array argument containing all
            the ASIC data (full supermodule), and returns,    
            [AS OF  February 2013]: 
                * boolean to signal whether this is the last image in the data
                * the first image ( (32 x 8) * (16 x 16) pixels) of an image found in the data,
            in the form of the 16 ASICs organised into a 256 x 256 pixel image 
        """
        
        # Distance between two consecutive pixels within the same ASIC in the quadrant detector
        pixelDistance = 128
        
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        
        # Counter variables
        imageIndex = 0
        rawCounter = 0

        # Go from ASIC 1-128
        lookupTableAsicDistance = 0

        bDebug = False
        debugCount = 0
        
        # Iterate over 32 rows (within an ASIC)
        for ROW in range(31, -1, -1):

            # Iterate over 16 columns of ASIC tiles
            for asicColumn in range(16):
                
                # Iterate over the 8 rows of ASIC tiles
                for asicRow in range(7, -1, -1):

                    try:
                        # Iterate over 16 columns (within an ASIC)
                        for COLUMN in range(16):

                            imageIndex = 0 + (16* COLUMN) + (8192*asicRow) + asicColumn + (256*ROW)
                            rawDataOffset = lookupTableAsicDistance + (pixelDistance*rawCounter)
                            
                            if bDebug:
                                if rawDataOffset < 768:
#                                    print "%4i" % rawDataOffset,
                                    print "%6i" % imageIndex,
                            
                            self.imageArray[ imageIndex ] = sixteenBitArray[rawDataOffset]
                            
#                            # Print contents of one ASIC
#                            if lookupTableAsicDistance == 1:
#                                if debugCount % 16 == 0:
#                                    print "\n%4i:" % debugCount,
#                                print "%4i" % sixteenBitArray[rawDataOffset],
#                                debugCount += 1

                            # Increment lookupTableAsicDistance or zero it if we reached last ASIC
                            if lookupTableAsicDistance == 128-1:
                                lookupTableAsicDistance = 0
                                # Increment counter for rawDataOffset for every supermodule worth of (128) ASICs 
                                rawCounter += 1
                            else:
                                lookupTableAsicDistance += 1

                        if bDebug:
                            if rawDataOffset < 768:
                                print ""

                    except IndexError:
                        # If end of array reached, will raise IndexError
                        print "SMod-IdxError, debug: %3i %3i %3i %3i, %4i,  %6i "  % (asicRow, asicColumn, ROW, COLUMN, lookupTableAsicDistance, rawDataOffset)
                        break
                    except Exception as e:
                        print "retrieveFirstSuperModuleImageFromAsicData(), look up table execution failed: ", e, "\nExiting.."
                        exit()

        # Check whether this is the last image in the image data..
        try:
            sixteenBitArray[self.imageSize]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            pass   # Last Image detected
        return bNextImageAvailable


    def processRxData(self, data):
        """ Process (chunks of) UDP data into packets of a frame 
            [Code inherited from Rob - See: udp_rx_ll_mon_header_2_CA.py]
        """
                
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
            
#            print "sof/eof = %4X, %4X" % (frm_sof, frm_eof),
            # rawFrameNumber = train number read from packet
            # frame_number = train number relative to execution of this software
            rawFrameNumber = frame_number
            
            if self.first_frm_num == -1:
                self.first_frm_num = frame_number
                
            frame_number = frame_number - self.first_frm_num
            
            # Compare this packet number against the previous packet number
            if packet_number != (self.packetNumber +1):
                # packet numbering not consecutive
                print "Warning: Previous packet number: %3i versus this packet number: %3i" % (self.packetNumber, packet_number)

            # Update current packet number
            self.packetNumber = packet_number
                        
            if frm_eof == 1:
                self.j=self.j+1
            else:
                pass
            
            # Not yet end of file: copy current packet contents onto (previous) packet contents
            # Last 8 bytes are train number and packet number - omitting those..
            # both are of type string..
            self.rawImageData = self.rawImageData + data[0:-8]

            # Return train number and end of train
            return rawFrameNumber, frm_eof
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
