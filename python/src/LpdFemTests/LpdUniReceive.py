'''
Created on Jun 12, 2013

    Modelled upon LpdFemDataReceiver.py

@author: ckd27546
'''

from LpdFemGui.LpdDataContainers import *

import os, sys, time, socket
import numpy as np
from PyQt4 import QtCore

# Import HDF5 Library; Disable its use if library not installed on PC
try:
    import h5py
except:
    # "No HDF5 Library detected - Disabling file writing"
    bHDF5 = False
else:
    # "HDF5 Library present."
    bHDF5 = True

#Display received data in plots
bDisplayPlotData = True

# Debugging enabled if set above 0
bDebug = 0
        
class LpdFemDataReceiver(QtCore.QObject):

    def __init__(self, liveViewSignal, listenAddr, listenPort, numFrames, cachedParams, appMain):
        
        try:
            super(LpdFemDataReceiver, self).__init__()
                
            self.numFrames = numFrames
            self.appMain = appMain
            self.debugLevel = cachedParams['debugLevel']
            
            # Create UDP recevier, frame processor and data monitor objects
            self.udpReceiver = UdpReceiver(listenAddr, listenPort, numFrames)
            self.frameProcessor = FrameProcessor(numFrames, cachedParams, liveViewSignal)
            
            # Create threads to run them in
            self.udpReceiverThread = QtCore.QThread() 
            self.frameProcessorThread = QtCore.QThread()
            
            # Move objects into threads
            self.udpReceiver.moveToThread(self.udpReceiverThread)
            self.frameProcessor.moveToThread(self.frameProcessorThread)
            
            # Connect thread start signal of UDP receiver to receive loop function
            self.udpReceiverThread.started.connect(self.udpReceiver.receiveLoop)
            
            # Connect data RX signal from UDP receiver to handleDataRx slot in frame processor
            self.udpReceiver.connect(self.udpReceiver, QtCore.SIGNAL("dataRxSignal"), self.frameProcessor.processFrame)
            
            # Start the frame processor thread up
            self.frameProcessorThread.start()

            # Start the UDP receiver thread up            
            self.udpReceiverThread.start()
            
        except Exception as e:
            print "LpdFemDataReceiver got exception during initialisation: %s" % e
            raise(e)

    def awaitCompletion(self):

            if self.debugLevel > 0:
                print "Waiting for frame processing to complete"
            while self.frameProcessor.framesHandled < self.numFrames and self.appMain.abortRun == False:
                time.sleep(0.1)
            
            if self.appMain.abortRun:
                print "Run aborted by user"
            
            if self.debugLevel > 0:
                print "Frame processor handled all frames, terminating data receiver threads"

            #TODO: Close udpReceiver's socket? - Success
            self.udpReceiver.closeConnection()
            
            self.frameProcessorThread.quit()
            self.udpReceiverThread.quit()
            
            self.frameProcessorThread.wait()
            self.udpReceiverThread.wait()
            
            try:
                print "Average frame UDP receive time : %f secs" % (self.udpReceiver.totalReceiveTime / self.udpReceiver.frameCount)
                print "Average frame processing time  : %f secs" % (self.frameProcessor.totalProcessingTime / self.frameProcessor.framesHandled)
            except Exception as e:
                print >> sys.stderr, "Got exception", e
            if self.debugLevel > 0:
                print "awaitCompletion() finished"
        
class UdpReceiver(QtCore.QObject):
        
    def __init__(self, listenAddr, listenPort, numFrames):

        super(UdpReceiver, self).__init__()
        
        # Initialise variables used by processRxData
        self.first_frm_num = -1       
        self.packetNumber = -1
        self.frameCount = 0
        self.numFrames = numFrames
        self.totalReceiveTime = 0.0
        
        # Bind to UDP receive socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((listenAddr, listenPort))

        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        print "UDP Receiver thread listening on address %s port %s  (%i frames/file)" % (listenAddr, listenPort, numFrames)

    def closeConnection(self):

        self.sock.close()


    def receiveLoop(self):
                    
        try:
            while self.frameCount < self.numFrames:
                
                foundEof = 0
                lpdFrame = LpdFrameContainer(self.frameCount)
                
                while foundEof == 0:
                    stream = self.sock.recv(9000)
                    foundEof  = self.processRxData(lpdFrame, stream)
                    if foundEof:
                        # Complete frame received, transmit frame along with meta data saved in LpdFrameContainer object
                        #print >> sys.stderr, "Frame %d receive complete" % lpdFrame.frameNumber
                        self.emit(QtCore.SIGNAL("dataRxSignal"), lpdFrame)
                        self.frameCount += 1
                        self.totalReceiveTime += (lpdFrame.timeStampEof - lpdFrame.timeStampSof)
                        
        except Exception as e:
            print "UDP receiver event loop got an exception: %s" % e
            raise(e)
            
        #print >> sys.stderr, "Receiver thread completed"

    def processRxData(self, lpdFrame, data):
        ''' 
        Processes received data packets, decoding the Train Transfer Protocol information
        to construct completed frames (trains) 
        '''

        try:
            #Extract Trailer information
            trailerInfo = np.zeros(2, dtype=np.uint32)
            trailerInfo = np.fromstring(data[-8:], dtype=np.uint32)
            
            # Extract train/frame number (the second last 32 bit word from the raw data)
            frameNumber = trailerInfo[0]
            # Extract packet number (last 32 bit word)
            packetNumber = trailerInfo[1] & 0x3FFFFFFF

            # Extract Start Of Frame, End of Frame
            sof = (trailerInfo[1] >> (31)) & 0x1
            eof = (trailerInfo[1] >> (30)) & 0x1
            
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
        

class FrameProcessor(QtCore.QObject):

    AsicTypeSuperModule = 0
    AsicTypeSingleAsic  = 1
    AsicTypeTwoTile     = 2
    AsicTypeAloneFem    = 3
    AsicTypeRawData     = 4
    
    def __init__(self, numFrames, cachedParams, liveViewSignal):

        QtCore.QObject.__init__(self)
        
        self.numFrames = numFrames
        self.evrData = None
        
        #Only allow writing of HDF5 files if h5py library installed..
        if bHDF5:
            self.fileWriteEnable = cachedParams['fileWriteEnable']
        else:
            self.fileWriteEnable = False
        self.dataFilePath = cachedParams['dataFilePath']
        self.liveViewDivisor = cachedParams['liveViewDivisor']
        self.liveViewOffset  = cachedParams['liveViewOffset']
        #asicModuleType:     0: super module    1: single ASIC    (redundant?)    2: 2-tile module    3: stand-alone fem    (4: raw data ?)
        self.asicModuleType = cachedParams['asicModuleType']
        self.debugLevel = cachedParams['debugLevel']
        if self.debugLevel > 1:
            print "numFrames:       ", self.numFrames
            print "fileWrite:       ", self.fileWriteEnable
            print "dataFilePath:    ", self.dataFilePath
            print "liveViewDivisor: ", self.liveViewDivisor
            print "liveViewOffset:  ", self.liveViewOffset
            print "asicModuleType:  ", self.asicModuleType
            print "debugLevel:      ", self.debugLevel
        
        self.liveViewSignal = liveViewSignal

        # Run start time
        self.tstart = time.time()

        # Initialise counters
        self.framesHandled = 0
        self.imagesWritten = 0
        self.dataBytesReceived = 0
        self.totalProcessingTime = 0.0

        # Define plotted image dimensions: 
        if self.asicModuleType == FrameProcessor.AsicTypeSuperModule:
            self.nrows = 32*8   # 32 rows * 8 ASICs = 256 
            self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        elif self.asicModuleType == FrameProcessor.AsicTypeSingleAsic:
            self.nrows = 32     # 32 rows
            self.ncols = 16     # 16 columns
        elif self.asicModuleType == FrameProcessor.AsicTypeTwoTile:
            self.nrows = 32     # 32 rows
            self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        elif self.asicModuleType == FrameProcessor.AsicTypeAloneFem:
            self.nrows = 32     # 32 rows
            self.ncols = 128    # 16 columns/ASIC, 8 ASICs / sensor: 16 x 8 = 128 columns
        if self.asicModuleType == FrameProcessor.AsicTypeRawData:
            self.nrows = 256   # 32 rows * 8 ASICs = 256 
            self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
            

        # Define Module and Full Lpd size (Module differs if 2-tile, SuperMod, Fem, etc)
        self.imageModuleSize = self.nrows * self.ncols
        self.imageFullLpdSize = 256 * 256

        # Create an image array to contain the elements of the module type 
        # Super Module = (32 x 8 x 16 x 16) = 65536 elements
        # 2Tile System = (32 * 16 * 16)     = 8192 elements
        self.imageArray = np.zeros(self.imageModuleSize, dtype=np.uint16)
        
        # Create HDF file if requested
        if self.fileWriteEnable:            
            self.createDataFile(cachedParams)           
        
   
    def createDataFile(self, cachedParams):
        '''
        Creates and HDF5 data file and internal structure, sets up metadata in file
        '''

        fileName = self.dataFilePath

        try:
            self.hdfFile = h5py.File(fileName, 'w')
        except IOError as e:
            # Did it fail because file previous used?
            bFileOk = False
            sPart = 0
            while bFileOk != True:
                try:
                    fileName = self.dataFilePath[:-5] + str("_") + str(sPart) + self.dataFilePath[-5:]
                    self.hdfFile = h5py.File(fileName, 'w')
                except IOError as e:
                    # filename exists, increment and try again
                    sPart += 1
                except Exception as e:
                    print "Failed to open HDF file with error: %s" % e
                    raise(e)
                else:
                    bFileOk = True
            
        if self.debugLevel > 0:
            print "Created HDF5 data file %s" % fileName

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

        # Build metadata attributes from cached parameters
        for param, val in cachedParams.iteritems():
            self.metaGroup.attrs[param] = val

         
    def processFrame(self, lpdFrame):
        
        #print >> sys.stderr, "Frame processor thread receiver frame number", lpdFrame.frameNumber, 'raw data length', len(lpdFrame.rawImageData)

        self.dataBytesReceived += len(lpdFrame.rawImageData)
        
        # Capture time of starting processing
        startTime = time.time()
        
        # Simultaneously extract 16 bit pixel data from raw 32 bit words and swap the byte order
        #     eg: ABCD => DCBA
        self.pixelData = np.fromstring(lpdFrame.rawImageData, dtype=np.dtype('<i2'))
            
        # Define variables that increase with each loop iteration
        currentImage = 0
        bNextImageAvailable = True

        # Loop over the specified number of plots
        while bNextImageAvailable:

            imageOffset = self.imageFullLpdSize * currentImage

            # Get the first image of the image
            bNextImageAvailable = self.unpackImage(imageOffset)

            # Mask out gain bits from data
            # TODO REMOVE THIS
            #self.imageArray = self.imageArray & 0xfff
            
            # Write image to file if selected
            if self.fileWriteEnable:
                self.imageDs.resize((self.imagesWritten+1, self.nrows, self.ncols))
                self.imageDs[self.imagesWritten,...] = self.imageArray
                
                self.timeStampDs.resize((self.imagesWritten+1, ))
                self.timeStampDs[self.imagesWritten] = lpdFrame.timeStampSof
                
                self.trainNumberDs.resize((self.imagesWritten+1, ))
                self.trainNumberDs[self.imagesWritten] = lpdFrame.frameNumber
                
                self.imageNumberDs.resize((self.imagesWritten+1, ))
                self.imageNumberDs[self.imagesWritten] = currentImage

            # Send signal to update plotted graph at appropriate rate
            if (self.imagesWritten - self.liveViewOffset) % self.liveViewDivisor == 0:
                lpdImage = LpdImageContainer(0, lpdFrame.frameNumber, currentImage) # 0 = runNumber, not used
                lpdImage.imageArray = self.imageArray.copy()
                self.liveViewSignal.emit(lpdImage)
                    
            # Clear data before next iteration (but after data written to file)
            self.imageArray.fill(0)
            
            # Increment current image
            currentImage += 1
            self.imagesWritten += 1
            
        # 'Reset' rawImageData variable - WHY??
        lpdFrame.rawImageData = lpdFrame.rawImageData[0:0]

        endTime = time.time()
        self.totalProcessingTime += (endTime - startTime)
        #print "Total frame processing time = %f secs" % (endTime - startTime)

        self.framesHandled += 1
        #if self.framesHandled >= self.numFrames:
        #    print >> sys.stderr, "Frame processor thread processed all frames, quitting"
        

    def unpackImage(self, imageOffset):
        """ Extracts one image beginning at argument imageOffset in the member array 
            self.pixelData array. Returns boolean bImageAvailable indicating whether
            the current image is the last image in the data
        """
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        
        # Check Asic Module type to determine how to process data
        if self.asicModuleType == FrameProcessor.AsicTypeRawData:
            # Raw data - no not re-order
            self.imageArray = self.pixelData[imageOffset:imageOffset + self.imageFullLpdSize].reshape(256, 256)
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
    
            rawOffset = imageOffset
    
            try:
                for asicRow in xrange(numRowsPerAsic):
                    for asicCol in xrange(numColsPerAsic):
                        
                        self.imageLpdFullArray[asicRow::numRowsPerAsic, asicCol::numColsPerAsic] = self.pixelData[rawOffset:(rawOffset + numAsics)].reshape(8,16)
                        rawOffset += numAsics
            
            except IndexError:
                print "Image Processing Error @ %6i %6i %6i %6i %6i %6i " % ( asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics )
            except Exception as e:
                print "Error while extracting image: ", e, " -> imgOffset: ", imageOffset
    
            # Module specific data processing
            if self.asicModuleType == FrameProcessor.AsicTypeSuperModule:
                
                # Super Module - Image now upside down, reverse the order
                self.imageLpdFullArray[:,:] = self.imageLpdFullArray[::-1,:]
                self.imageArray = self.imageLpdFullArray.copy()
            elif self.asicModuleType == FrameProcessor.AsicTypeTwoTile:
                
                #Two Tile
                # Create array for 2 Tile data; reshape into two dimensional array
                self.imageArray = np.zeros(self.imageModuleSize, dtype=np.uint16)
                self.imageArray = self.imageArray.reshape(32, 256)
        
                # Copy the two Tiles that exists in the two tile system
                try:
                    # LHS Tile located in the second ASIC row, second ASIC column
                    self.imageArray[0:32, 0:128]   = self.imageLpdFullArray[32:32+32, 256-1:128-1:-1]
                    # RHS Tile located in the seventh ASIC row, second ASIC column
                    self.imageArray[0:32, 128:256] = self.imageLpdFullArray[192:192+32, 256-1:128-1:-1]
                except Exception as e:
                    print "Error accessing 2 Tile data: ", e
                    print "imageOffset: ", imageOffset
                    sys.exit()

        # Last image in the data?
        try:
            self.pixelData[imageOffset + self.imageFullLpdSize]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            pass   # Last Image in this train detected
        return bNextImageAvailable
        

