
# X10G Development code
# Receive and display 10G image data
# Hacked together by Christian Angelsen 18-06-2012


# For detailed comments on animation and the techniqes used here, see
# the wiki entry http://www.scipy.org/Cookbook/Matplotlib/Animations

from LpdFemClient.LpdFemClient import LpdFemClient

import sys, time, datetime, argparse, socket, os
from datetime import datetime

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib

# Import HDF5 Library; Disable its use if library not installed on PC
try:
    import h5py
except:
    print "No HDF5 Library detected - Disabling file writing"
    bNoHdf5Library = True
else:
    print "HDF5 Library present."
    bNoHdf5Library = False

from PyQt4 import QtCore, QtGui


class LpdFrameObject(object):
    '''
        LpdFrameObject - data container class to contain UDP payload and meta data
        (such as timestamps)
    '''
    def __init__(self, frameNumber):
        # Create a string to contain payload of all UDP packets
        self.rawImageData = ""
        self.frameNumber = frameNumber
        self.timeStampSof = 0.0
        self.timeStampEof = 0.0
        self.processingTime = 0.0

class ReceiveThread(QtCore.QThread):
    
    def __init__(self, rxSignal, femHost='10.0.0.1', femPort=61649):
        
        # Initialising variable used by processData
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
                lpdFrame = LpdFrameObject(frameCount)
                while foundEof == 0:
                    stream = self.sock.recv(9000)
                    foundEof  = self.processData(lpdFrame, stream)
                    if foundEof:
                        # Complete frame received, transmit frame along with meta data saved in LpdFrameObject object
                        self.rxSignal.emit(lpdFrame)
                        # Increment frame counter
                        frameCount += 1
                        
        except Exception as e:
            print "processData() failed: ", e, "\nExiting.."
            sys.exit()

    def processData(self, lpdFrame, data):
        """ 
        Processes received data packets, decoding the Train Transfer Protocol information
        to construct completed frames (trains) 
        """
        
        try:
            # Time processing
            processingStart = time.time()
            
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

            # Debug - Display XFEL Header (64 bytes)
            if debugLevel  > 1:
                if sof == 1:
                    print "processData() XFEL Header:"
                    initialData = np.zeros(64, dtype=np.uint32)
                    initialData = np.fromstring(data[:64], dtype=np.uint32)
                    for index in range(len(initialData)):
                        if (index!= 0) and (index % 16 == 0):
                            print ""
                        print "%X "  % initialData[index],
                    print ""
                    
            if debugLevel > 1:
                if sof == 1:
                    print "-=-=-=-=- FrameNumber PacketNumber"
                if (trailerInfo[1] < 3) or (eof == 1):
                    print "trailerInfo: %8X %8X sof: %d eof: %d" % (trailerInfo[0], trailerInfo[1], sof, eof)
                if (trailerInfo[1] == 7):
                    print "[...]"
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
                    #raise Exception

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
            
            lpdFrame.processingTime += time.time() - processingStart
            return eof
        except Exception as e:
            print "processData() error: ", e
            raise e

class ImageDisplay(FigureCanvas):

    ''' Change font size '''
    matplotlib.rcParams.update({'font.size': 8})
    
    dataRxSignal = QtCore.pyqtSignal(object)

    #def __init__(self, femHost, femPort, asicModuleType):
    def __init__(self, femhost, femport, asicmodule, canvasrows, canvascols, colorbar, debuglevel, timeinfo, writedata, lpdheadertrailer, subtractPedestals):
        
        self.host           = femhost
        self.port           = femport
        self.asicModuleType = asicmodule
        self.plotRows       = canvasrows
        self.plotCols       = canvascols
        self.bColorbarVisible = False if colorbar == 0 else True
        self.debugLevel     = debuglevel
        self.bTimeStamp     = False if timeinfo == 0 else True
        self.bHDF5          = False if writedata == 0 else True
        self.lpdheadertrailer = lpdheadertrailer
        self.subtractPedestals = subtractPedestals
        # Remember number of plots in figure in case future train contain too many images
        self.plotsInFigure = canvasrows * canvascols

        self.moduleString = {0 : "SuperModule", 1 : "Asic", 2 : "TwoTile", 3 : "Fem", 4 : "RawData"}
        
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
            asicTilesPerColumn = 8
            (xStart, xStop, xStep)  = (16, 256, 16)
            (yStart, yStop, yStep)  = (32, 256, 32)

        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
            asicTilesPerColumn = 1
            (xStart, xStop, xStep)  = (16, 256, 16)
            (yStart, yStop, yStep)  = (8, 32, 8)

        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA:
            asicTilesPerColumn = 8
            (xStart, xStop, xStep)  = (16, 256, 16)
            (yStart, yStop, yStep)  = (32, 256, 32)

        else:
            print "Error: Selected ASIC module (type = %r) not supported." %  self.asicModuleType
            sys.exit()
            
        print "Initialising.. "
        
        # Dummy train counter
        self.trainNumber = 0
        
        # Count number of iterations across multiple trains (ie number images across multiple trains)
        self.imageCounter   = 0
        # iterateOffset tracks how many images have been written to previous file(s) and offsets .resize() calls to prevent
        #    accummulating rows of 0 in hdf5 files.
        self.iterateOffset      = 0

        # Define plotted image dimensions:
        self.nrows = 32 * asicTilesPerColumn    # 32 rows [2-Tile]; * 8 ASICs = 256 [Super Module] 
        self.ncols = 256                        # 256 columns [2-Tile, Super Module]
        
        # superModuleImageSize [65536] used by all module types
        self.superModuleImageSize = 256*256
        # moduleImageSize differs according to self.asicModuleType
        self.moduleImageSize = self.nrows * self.ncols

        # Create an array to contain module's elements
        self.imageArray = np.zeros(self.moduleImageSize, dtype=np.uint16)
        
        # Create hdf file - if HDF5 Library present
        if self.bHDF5:
            dateString = datetime.now().strftime("%Y%m%d-%H%M%S")
            fileName = "/tmp/lpd%s-%s.hdf5" % ( self.moduleString[self.asicModuleType], dateString)

            self.hdfFile = h5py.File(fileName, 'w')
            # Create group structure
            self.lpdGroup = self.hdfFile.create_group('lpd')
            self.metaGroup = self.lpdGroup.create_group('metadata')
            self.dataGroup = self.lpdGroup.create_group('data')
            
            # Create data group entries    
            self.imageDs = self.dataGroup.create_dataset('image', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                            maxshape=(None,self.nrows, self.ncols))
            self.timeStampDs   = self.dataGroup.create_dataset('timeStamp',   (1,), 'float64', maxshape=(None,))
            self.trainNumberDs = self.dataGroup.create_dataset('trainNumber', (1,), 'uint32', maxshape=(None,))
            self.imageNumberDs = self.dataGroup.create_dataset('imageNumber', (1,), 'uint32', maxshape=(None,))

        FigureCanvas.__init__(self, Figure())
    
        (xlist, ylist) = ([], [])
        if self.bColorbarVisible:
            # Generate list of xticks to label the x axis
            for i in range(xStart, xStop, xStep):
                xlist.append(i)
            
            # Generate yticks if super module or raw data selected
            for i in range(yStart, yStop, yStep):
                ylist.append(i)

        print "Preparing graphics.."
        
        # Create a list for axes object and one for image objects, to store that info for each image
        self.ax = []
        self.img = []
        
        
        # Because subplotting has been selected, need a list of axes to cover multiple subplots
        for idx in range(self.plotsInFigure):

            axesObject =  self.figure.add_subplot(self.plotRows, self.plotCols, idx+1)
            self.ax.extend([axesObject])
            
            self.ax[idx].set_xticks(xlist)
            self.ax[idx].set_yticks(ylist)
            
            # Rotate X axis text by 45
            self.ax[idx].set_xticklabels(xlist, rotation=45)
            
            # Set the title of each plot temporarily
            self.ax[idx].set_title("Image %i" % idx)
                            
            self.cnt = 0
            self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)

            imgObject = self.ax[idx].imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')
            self.img.extend([imgObject])

            if self.bColorbarVisible:
                # http://stackoverflow.com/questions/2539331/how-do-i-set-a-matplotlib-colorbar-extents
                axc, kw = matplotlib.colorbar.make_axes(self.ax[idx])
                cb = matplotlib.colorbar.Colorbar(axc, self.img[idx])
                # Modify the ticks on colour bar
                cTicks = [0, 511, 1023, 1535, 2047, 2559, 3071, 3583, 4095]
                cb.set_ticks(ticks=cTicks, update_ticks=True)

                # Set the colour bar
                self.img[idx].colorbar = cb

                # Add vertical lines to differentiate between the ASICs
                for i in range(16, self.ncols, 16):
                    self.ax[idx].vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
                
                # Add vertical lines to differentiate between two tiles
                self.ax[idx].vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
                
                # Add horizontal lines only if super module or raw data selected
                if (self.asicModuleType == 0) or (self.asicModuleType == 4):
                    for i in range(32, self.nrows, 32):
                        self.ax[idx].hlines(i-0.5, 0, self.nrows-1, color='y', linestyles='solid')
            
            self.draw()

        self.dataRxSignal.connect(self.handleFrame)
                
        self.tstart = time.time()

        self.rxThread = ReceiveThread(self.dataRxSignal, femHost, femPort)
        self.rxThread.start()


    def handleFrame(self, lpdFrame):

        # End Of File found, self.rawImageData now contain every pixel of every ASIC (of the complete Quadrant!)
        if self.bTimeStamp:
            timeX1 = time.time()
        
        print "Raw Image Data Received: %16i ($%08x)" %(len(lpdFrame.rawImageData), len(lpdFrame.rawImageData)), "(bytes, @%s)" % str( datetime.now())[11:-4],
        if self.bTimeStamp:
            print "Rx time: ", lpdFrame.processingTime
        else:
            print ""

        ''' More information on numpy & Big/Little-endian:    http://docs.scipy.org/doc/numpy/user/basics.byteswapping.html '''
        # Create 16 bit, Little-Endian, integer type using numpy
        pixelDataType = np.dtype('<i2')

        # Simultaneously extract 16 bit words and swap the byte order
        #     eg: ABCD => DCBA
        self.pixelDataArray = np.fromstring(lpdFrame.rawImageData, dtype=pixelDataType)
    
        if (self.debugLevel > 2) and (self.debugLevel < 8):
            print "Extracted 16 bit words: ", len(self.pixelDataArray), ". Array contents:"
            self.display16BitArrayInHex()
            print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

        if self.debugLevel > 7:
            if self.bTimeStamp:
                time2 = time.time()
            # Check the Gain bits (Bits 12-13);
            # [0] = x100, [1] = x10, [2] = x1, [3] = invalid
            gainCounter = [0, 0, 0, 0]

            for idx in range( len(self.pixelDataArray) ):

                # Check bits 12-13: 
                gainBits = self.pixelDataArray[idx] & 0x3000
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
            if self.bTimeStamp:
                time1 = time.time()
                self.timeStampGainCounter = time1 - time2

            print "\nGain:      x100       x10        x1  (invalid)"
            print "      %9i %9i %9i %9i" % (gainCounter[0], gainCounter[1], gainCounter[2], gainCounter[3])

        # Define variables that increase with each loop iteration
        currentPlot = 0
        bNextImageAvailable = True
        
        # Track how many plots in figure, as subsequent trains may contain more/less images
        plotMaxPlots = self.plotsInFigure
        
        # Loop over the specified number of plots
        while bNextImageAvailable and currentPlot < plotMaxPlots:

            if self.bTimeStamp:
                timeD1 = time.time()
            
#################################################################
# For readout with LPD Data Formatting ; 
# lpd headers and trailers in the data payload
# lpd header ; image data ; image descriptors ; lpd detector dependent ; lpd trailer ; 
            # following sizes in BYTES
            LPD_HEADER_SIZE = 32; # includes train id
            # Image Descriptors are fixed with 512 entries each of 4 blocks of descriptors:
            # 1) storageCellNumber (2 bytes)
            # 2) bunchNumber (8 bytes)
            # 3) status (2 bytes)
            # 4) length (4 bytes)
            LPD_IMAGE_DESCRIPTOR_SIZE = 0;  # 8192
            LPD_DETECTOR_DEPENDENT_SIZE = (13*32); # fixed with trigger information from C&C module
            LPD_TRAILER_SIZE = 32; # includes crc

            LPD_FORMATTING_SIZE = LPD_HEADER_SIZE + LPD_IMAGE_DESCRIPTOR_SIZE + LPD_DETECTOR_DEPENDENT_SIZE + LPD_TRAILER_SIZE

            if self.lpdheadertrailer == 0:           
                dataBeginning = self.superModuleImageSize*currentPlot
                # Change maximum plots to be 512 (effectively size of incoming image data) for old header format
                #plotMaxPlots = 511  # (0-511 = 512 plots)
            else:
                # Differentiate between XFEL format revisions
                if self.lpdheadertrailer == 2 or self.lpdheadertrailer == 3:
                    LPD_HEADER_SIZE = 64

                dataBeginning = (self.superModuleImageSize)*currentPlot + LPD_HEADER_SIZE/2
                
                # Print XFEL header information
                if currentPlot == 0:

                    if self.lpdheadertrailer == 3:

    # Corrections to match f/w from vers $0298 which made all 64b fields Little Endian    John C Oct 2015
    # previous code also had wrong offsets 
    
                        magicMsb = self.pixelDataArray[2+0] + (self.pixelDataArray[3+0] << 16)  
                        print "MAGIC Word Msw = $%08x " %(magicMsb)
                        
                        trainLsb = self.pixelDataArray[0+8] + (self.pixelDataArray[1+8] << 16)
                        trainMsb = self.pixelDataArray[2+8] + (self.pixelDataArray[3+8] << 16)
                        trainId  = (trainMsb << 32) + trainLsb
    
                        dataLsb = self.pixelDataArray[0+12] + (self.pixelDataArray[1+12] << 16)
                        dataMsb = self.pixelDataArray[2+12] + (self.pixelDataArray[3+12] << 16)
                        dataId  = (dataMsb << 32) + dataLsb
    
                        linkLsb = self.pixelDataArray[0+16] + (self.pixelDataArray[1+16] << 16)
                        linkMsb = self.pixelDataArray[2+16] + (self.pixelDataArray[3+16] << 16)
                        linkId  = (linkMsb << 32) + linkLsb
    
                        imgCountIdLsb = self.pixelDataArray[0+20] + (self.pixelDataArray[1+20] << 16)
                        imgCountIdMsb = self.pixelDataArray[2+20] + (self.pixelDataArray[3+20] << 16)
                        imgCountId  = (imgCountIdMsb << 32) + imgCountIdLsb
                    
                    else:
                    
                        # corrected offsets 
    
                        magicMsb = self.pixelDataArray[0+0] + (self.pixelDataArray[1+0] << 16)  
                        print "MAGIC Word Msw = $%08x " %(magicMsb)
                        
                        trainLsb = self.pixelDataArray[2+8] + (self.pixelDataArray[3+8] << 8)
                        trainMsb = self.pixelDataArray[0+8] + (self.pixelDataArray[1+8] << 8)
                        trainId  = (trainMsb << 16) + trainLsb
    
                        dataLsb = self.pixelDataArray[2+12] + (self.pixelDataArray[3+12] << 8)
                        dataMsb = self.pixelDataArray[0+12] + (self.pixelDataArray[1+12] << 8)
                        dataId  = (dataMsb << 16) + dataLsb
    
                        linkLsb = self.pixelDataArray[2+16] + (self.pixelDataArray[3+16] << 8)
                        linkMsb = self.pixelDataArray[0+16] + (self.pixelDataArray[1+16] << 8)
                        linkId  = (linkMsb << 16) + linkLsb
    
                        imgCountId  = self.pixelDataArray[22] #[13] # Previous XFEL header version or older??

                    # Overwrite maximum plots with image number extracted from XFEL header
                    plotMaxPlots = imgCountId

                    print "trainID: {0:>3} dataID: 0x{1:X} linkId: 0x{2:X} imageCount: 0x{3:X} ({4:})".format(trainId, dataId, linkId, imgCountId, imgCountId)

                    if self.debugLevel > 0:
                        print "_______________________________________________________________________________________________"
                        print " * plot: %d dataBegin: %7d (0x%X) of %d S-ModSize: %d (0x%X) LPD hdr offset = %d." % \
                        (currentPlot, dataBeginning, dataBeginning, len(self.pixelDataArray), self.superModuleImageSize, self.superModuleImageSize, (LPD_HEADER_SIZE/2))
                        for index in range(32):
                            if (index!= 0) and (index % 16 == 0):
                                print ""
                            print "%4X " % self.pixelDataArray[index],
                        print ""

#################################################################

            # Get the first image of the train
            bNextImageAvailable = self.retrieveImage(dataBeginning)
            
            # The first image, imageArray, has now been stripped from the image
            # Reshape image into pixel array according to module geometry
            try:
                self.data = self.imageArray.reshape(self.nrows, self.ncols)
            except Exception as e:
                print "handleFrame() failed to reshape imageArray: ", e, "\nExiting.."
                print "len(self.data),  self.nrows, self.ncols = ", len(self.data),  self.nrows, self.ncols
                exit()
            
                           
            # Mask out gain bits from data
            self.data = self.data & 0xfff
            
            
            # jac ; dec 2015
            #subtractPedestals = 0;
            
            if self.subtractPedestals == 1:
                
                #print "\nBefore test print 0"
                #print self.data[0]
                                
            
                # calculate simple pedestal summing central row of each asic
                pix_row = 16    # pick central row 
                ncol_per_asic = 16
                nrow_per_asic = 32
                nasics = 8
                sum = 0
                ped_factor = 1
                ped = [0,0,0,0,0,0,0,0]
                ped_width = 200  # spread of pedestals
                
                for asicNr in range (nasics):                
                    sum = 0
                    for col in range (ncol_per_asic):
                        sum += self.data[28, asicNr*ncol_per_asic + col]                    
                        sum += self.data[29, asicNr*ncol_per_asic + col]                   
                        sum += self.data[30, asicNr*ncol_per_asic + col]                   
                        sum += self.data[31, asicNr*ncol_per_asic + col]
                    ped[asicNr] = sum / (ncol_per_asic*4) / ped_factor
                    print "asicNr = %d ; sum = %d ; ped = %d" %(asicNr, sum, ped[asicNr]*ped_factor)
    
                for asicNr in range (nasics):                
                    for col in range (ncol_per_asic):                
                        for row in range (nrow_per_asic):
                            self.data[row, asicNr*ncol_per_asic + col] -= ped[asicNr]
                            if self.data[row, asicNr*ncol_per_asic + col] > (65536 - ped_width):
                                self.data[row, asicNr*ncol_per_asic + col] = 0
    
                #print "\nAfter test print 0"
                #print self.data[0]

            self.ax[currentPlot % self.plotsInFigure].set_title("Train %i Image %i" % (self.trainNumber, currentPlot))
            
            # Load image into figure
            self.img[currentPlot % self.plotsInFigure].set_data(self.data)

            self.ax[currentPlot % self.plotsInFigure].draw_artist(self.img[currentPlot % self.plotsInFigure])
            self.blit(self.ax[currentPlot % self.plotsInFigure].bbox)

            # Write image to file - if HDF5 Library present
            if self.bHDF5:

                # index within the opened file
                fileIndex = self.imageCounter % numberPlotsPerFile

                # Check if file opened
                try:
                    self.hdfFile.filename
                except ValueError:
                    # Create new file
                    dateString = datetime.now().strftime("%Y%m%d-%H%M%S")
                    fileName = "/tmp/lpd%s-%s.hdf5" % ( self.moduleString[self.asicModuleType], dateString)
                    
                    # Check if file already exists
                    if os.path.isfile(fileName):
                        # Don't overwrite existing file
                        fileName = fileName[:-5] + '_' + str(self.imageCounter) + fileName[-5:]
                        if self.debugLevel > 0:
                            print "\nNew use filename:  '" + fileName + "'"

                    self.hdfFile = h5py.File(fileName, 'w')
                    # Recreate datasets
                    self.lpdGroup = self.hdfFile.create_group('lpd')
                    self.metaGroup = self.lpdGroup.create_group('metadata')
                    self.dataGroup = self.lpdGroup.create_group('data')
                    
                    # Create data group entries    
                    self.imageDs = self.dataGroup.create_dataset('image', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                                    maxshape=(None,self.nrows, self.ncols))
                    self.timeStampDs   = self.dataGroup.create_dataset('timeStamp',   (1,), 'float64', maxshape=(None,))
                    self.trainNumberDs = self.dataGroup.create_dataset('trainNumber', (1,), 'uint32', maxshape=(None,))
                    self.imageNumberDs = self.dataGroup.create_dataset('imageNumber', (1,), 'uint32', maxshape=(None,))


                # Write data and info to file                    
                self.imageDs.resize((fileIndex+1, self.nrows, self.ncols))
                self.imageDs[fileIndex,...] = self.data
                
                self.timeStampDs.resize((fileIndex+1, ))
                self.timeStampDs[fileIndex] = lpdFrame.timeStampSof
                
                self.trainNumberDs.resize((fileIndex+1, ))
                self.trainNumberDs[fileIndex] = self.trainNumber
                
                self.imageNumberDs.resize((fileIndex+1, ))
                self.imageNumberDs[fileIndex] = currentPlot

                # Close file if specified number of images written
                if fileIndex == (numberPlotsPerFile-1):
                    # Add numTrains to file before closing
                    self.metaGroup.attrs['numTrains'] = numberPlotsPerFile
                    # Close old file
                    self.hdfFile.flush()
                    self.hdfFile.close()
                    
                # Increment image number counter
                self.imageCounter += 1
                
            # Clear data before next iteration (but after data written to file)
            self.data.fill(0)

            if self.bTimeStamp:
                timeD2 = time.time()
                print "plot %i took   %.9f seconds to process." % (currentPlot, timeD2 - timeD1)
            
            # Increment currentPlot
            currentPlot += 1
        else:
            # Finished drawing subplots

            # Dummy counter
            self.trainNumber += 1

        # 'Reset' rawImageData variable
        lpdFrame.rawImageData = lpdFrame.rawImageData[0:0]
        if self.bTimeStamp:
            timeX2 = time.time()
            print "Data ordering & displaying time = ",(timeX2 - timeX1)

        print " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        
        if self.cnt == 0:
            self.draw()
        else:
            self.cnt += 1

    def __del__(self):
        # Close file if HDF5 Library present
        if self.bHDF5:
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
        if self.debugLevel > 6:
            data_len = len(self.pixelDataArray)
        elif self.debugLevel > 5:
            data_len = len(self.pixelDataArray) / 2
        elif self.debugLevel > 4:
            data_len = len(self.pixelDataArray) / 4
        elif self.debugLevel > 3:
            data_len = len(self.pixelDataArray) / 8
        elif self.debugLevel > 2:
            data_len = 160
        
        currentArrayElement = ""
        try:
            # Convert each 2 byte into 16 bit data and print that
            for idx in range(data_len):
                
                if (idx %16 == 0):
                    print "%6d : " % idx,
                    
                currentArrayElement =  currentArrayElement + "   %04X " % self.pixelDataArray[idx]
                
                if (idx % 16 == 15):
                    print currentArrayElement
                    currentArrayElement = ""
                
            print "Number of 16 bit words: ", data_len
        except Exception as e:
            print "display16BitArrayInHex() error: ", e
            exit(0)


    def retrieveImage(self, dataBeginning):
        """ Extracts one image beginning at argument dataBeginning in the member array 
            self.pixelDataArray array. Returns boolean bImageAvailable indicating whether
            the current image is the last image in the data
        """

        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        
        #DEBUG
#        f = open("LpdReceiver_debugged_%s.txt" % str(dataBeginning), 'w')
        # Check Asic Module type to determine how to process data
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA:
            # Raw data - no not re-order
            self.imageArray = self.pixelDataArray[dataBeginning:dataBeginning + self.superModuleImageSize].reshape(256, 256)
        else:
            # Not raw data, proceed to reorder data
            numAsicCols = 16
            numAsicRows = 8
            numAsics = numAsicCols * numAsicRows
            numColsPerAsic = 16
            numRowsPerAsic = 32
    
            numPixelsPerAsic = numColsPerAsic * numRowsPerAsic
            numPixels = numAsics * numPixelsPerAsic
    
            # Create linear array for unpacked pixel data
            self.imageLpdFullArray = np.zeros(numPixels, dtype=np.uint16)
            self.imageLpdFullArray = np.reshape(self.imageLpdFullArray, (numAsicRows * numRowsPerAsic, numAsicCols * numColsPerAsic))
    
            rawOffset = dataBeginning
    
            try:
                for asicRow in xrange(numRowsPerAsic):
                    for asicCol in xrange(numColsPerAsic):
                        
                        #DEBUGGING
#                        print >> sys.stderr, "{0:>9} [{1:>2}::{2:>2}, {3:>2}::{4:>2}] = {5:>9} [{6:>7}:({7:>7})]".format( self.imageLpdFullArray.shape, asicRow, numRowsPerAsic, asicCol, numColsPerAsic, 
#                                                              self.pixelDataArray.shape, rawOffset, (rawOffset + numAsics) )
#                        f.write( "{0:>9} [{1:>2}::{2:>2}, {3:>2}::{4:>2}] = {5:>9} [{6:>7}:({7:>7})]".format( self.imageLpdFullArray.shape, asicRow, numRowsPerAsic, asicCol, numColsPerAsic, 
#                                                              self.pixelDataArray.shape, rawOffset, (rawOffset + numAsics) )  + '\n')
                        self.imageLpdFullArray[asicRow::numRowsPerAsic, asicCol::numColsPerAsic] = self.pixelDataArray[rawOffset:(rawOffset + numAsics)].reshape(8,16)
                        rawOffset += numAsics
            
            except IndexError:
                print "Image Processing Error @ %6i %6i %6i %6i %6i %6i " % ( asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics )
            except Exception as e:
                print "Error extracting image at %i Bytes, need %i but only %i Bytes available" % (dataBeginning, self.superModuleImageSize, self.pixelDataArray.shape[0] - dataBeginning)
                print "(Error: %s)" % e
    
            # Module specific data processing
            if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
                
                # Super Module - Image now upside down, reverse the order
#                self.imageLpdFullArray[:,:] = self.imageLpdFullArray[::-1,:]
                self.imageLpdFullArray[:,:] = self.imageLpdFullArray[:,::-1]
                self.imageArray = self.imageLpdFullArray.copy()
                
            elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
                
                #Two Tile
                # Create array for 2 Tile data; reshape into two dimensional array
                self.imageArray = np.zeros(self.moduleImageSize, dtype=np.uint16)
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
#             print >> sys.stderr, "pixelDataArray: {0:>9} dataBeginning: {1:>9}  imageSize: {2:>9} data+image: {3:>9}".format( \
#                                                 self.pixelDataArray.shape, dataBeginning, self.superModuleImageSize, dataBeginning + self.superModuleImageSize)
            # Increment dataBeginning to start of next image
            dataBeginning += self.superModuleImageSize
            self.pixelDataArray[dataBeginning + self.superModuleImageSize]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            pass   # Last Image in this train detected
        return bNextImageAvailable

if __name__ == "__main__":

    # Define default values
    asicModule          = 0
    femHost             = '10.0.0.1'
    femPort             = 61649
    bTimeStamp          = False
    bColorbarVisible    = True
    bHDF5               = False
    debugLevel          = 0
    plotRows            = 2
    plotCols            = 2
    numberPlotsPerFile  = 1
    lpdheadertrailer    = 0
    subtract_pedestals  = 0

    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="LpdReceiver.py - Receive data from an LPD detector. ",
                                     epilog="Default: femhost=10.0.0.1, femport=61649 and asicModule=0, all other flags' default values denoted by 'D: x'.")

    parser.add_argument("--femhost",        help="Set fem host IP (e.g 10.0.0.1)",                                      type=str, default=femHost)
    parser.add_argument("--femport",        help="Set fem port (eg 61649)",                                             type=int, default=femPort)
    parser.add_argument("--asicmodule",     help="Set ASIC Module (0=Supermodule, 2=2-Tile, 4=Raw data; D: 0)",         type=int, choices=[0, 2, 4], default=asicModule)
    parser.add_argument("--canvasrows",     help="Set rows of plots (D: 2)",                                            type=int, default=plotRows)
    parser.add_argument("--canvascols",     help="Set columns of plots (D: 2)",                                         type=int, default=plotCols)
    parser.add_argument("--colorbar",       help="Enable colorbar (0=Disable, 1=Enable; D: 1)",                         type=int, default=1)
    parser.add_argument("--debuglevel",     help="Enable debug level (0=Disable, 1-8=level; D: 0)",                     type=int, choices=range(9), default=0)
    parser.add_argument("--timeinfo",       help="Display timing info (0=Disable, 1=Enable; D: 0)",                     type=int, choices=[0, 1], default=0)
    parser.add_argument("--writedata",      help="Write data to hdf5 file (0=Disable, 0> = number images/file; D: 0)",  type=int, default=0)
    parser.add_argument("--lpdheadertrailer",help="Process LPD Data with headers & trailers (0=None, 1=32 byte header, 2=64 byte hdr, 3=64b fields little-endian (f/w vers $0298); D: 0)",type=int, default=0)
    parser.add_argument("--subtractPedestals",       help="Subtract pedestals (0=Disable, 1=Enable; D: 0)",      type=int, choices=[0, 1], default=0)   
    args = parser.parse_args()

    asicModule  = args.asicmodule
    femHost     = args.femhost
    femPort     = args.femport

    if args.timeinfo:
        bTimeStamp = True
        
    # Only allow file write if HDF5 library installed
    if bNoHdf5Library:
        bHDF5 = False
    else:
        if args.writedata == 0:
            bHDF5 = False
        else:
            bHDF5 = True
            numberPlotsPerFile = args.writedata

    debugLevel = args.debuglevel
    plotRows = args.canvasrows
    plotCols = args.canvascols
        
    if args.colorbar == 0:
        bColorbarVisible = False

#    if args.lpdheadertrailer == 1:
#        lpdheadertrailer = True

#    # Calculate number of plots to draw
#    plotMaxPlots = plotRows * plotCols

    if debugLevel > 0:
        print "module: ", asicModule
        print "host: ", femHost
        print "port: ", femPort
        print "time: ", bTimeStamp
        print "color: ", bColorbarVisible
        print "file: ", bHDF5
        print "debugLevel(%i)" % debugLevel
        print "plotCols(%i)" % args.canvascols
        print "plotRows(%i)" % args.canvasrows
        print "subtractPedestals: ", subtractPedestals
    #print vars(args), "\n\n"
    app = QtGui.QApplication(sys.argv)
    widget = ImageDisplay(**vars(args)) #femHost, femPort, asicModule)
    widget.setWindowTitle('LpdReceiver - %s:%s' % (femHost, femPort) )
    widget.show()
    
    sys.exit(app.exec_())
