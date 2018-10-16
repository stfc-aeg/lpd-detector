'''
Created on Apr 19, 2013

@author: tcn45
'''
from __future__ import print_function

from LpdDataContainers import *
from LpdFemClient.LpdFemClient import LpdFemClient
from LpdFemMetadataWriter import *

import os, sys, time, socket
import numpy as np
from PyQt4 import QtCore

import h5py

# Test if running python 3
is_python3 = sys.version_info > (3,)

#Display received data in plots
bDisplayPlotData = True

class LpdFemDataReceiver():
    
    def __init__(self, liveViewSignal, runStatusSignal, listenAddr, listenPort, numFrames, cachedParams, appMain):
        
        try:
                
            self.numFrames = numFrames
            self.appMain = appMain

            # Create UDP recevier, frame processor and data monitor objects
            self.udpReceiver = UdpReceiver(listenAddr, listenPort, numFrames)
            self.frameProcessor = FrameProcessor(numFrames, cachedParams, liveViewSignal)
            self.dataMonitor = DataMonitor(self.udpReceiver, self.frameProcessor, runStatusSignal, numFrames)
            
            # Create threads to run them in
            self.udpReceiverThread = QtCore.QThread() 
            self.frameProcessorThread = QtCore.QThread()
            self.dataMonitorThread = QtCore.QThread()
            
            # Move objects into threads
            self.udpReceiver.moveToThread(self.udpReceiverThread)
            self.frameProcessor.moveToThread(self.frameProcessorThread)
            self.dataMonitor.moveToThread(self.dataMonitorThread)
            
            # Connect thread start signal of UDP receiver to receive loop function
            self.udpReceiverThread.started.connect(self.udpReceiver.receiveLoop)
            
            # Connect data RX signal from UDP receiver to handleDataRx slot in frame processor
            self.udpReceiver.connect(self.udpReceiver, QtCore.SIGNAL("dataRxSignal"), self.frameProcessor.processFrame)
                        
            # Connect monitor loop start singal to monitor loop function
            self.dataMonitorThread.started.connect(self.dataMonitor.monitorLoop)
            
            # Start data monitor up
            self.dataMonitorThread.start()
            
            # Start the frame processor thread up
            self.frameProcessorThread.start()

            # Start the UDP receiver thread up            
            self.udpReceiverThread.start()
            
        except Exception as e:
            print("LdpFemDataReceiver got exception during initialisation: %s" % e)
        
    def injectTimestampData(self, evrData):

        self.frameProcessor.evrData = evrData

    def awaitCompletion(self):

            print("Waiting for frame processing to complete")
            while self.frameProcessor.framesHandled < self.numFrames and self.appMain.abortRun == False:
                time.sleep(0.1)
            
            if self.appMain.abortRun:
                print("Run aborted by user")
                self.udpReceiver.abortRun()
                self.dataMonitor.abortRun()
            else:
                print("Frame processor handled all frames, terminating data receiver threads")
                
            self.frameProcessorThread.quit()
            self.udpReceiverThread.quit()
            self.dataMonitorThread.quit()
            
            self.frameProcessorThread.wait()
            self.udpReceiverThread.wait()
            self.dataMonitorThread.wait()
            
            try:
                if self.udpReceiver.frameCount > 0:            
                    print("Average frame UDP receive time : %f secs" % (self.udpReceiver.totalReceiveTime / self.udpReceiver.frameCount))
                if self.frameProcessor.framesHandled > 0:
                    print("Average frame processing time  : %f secs" % (self.frameProcessor.totalProcessingTime / self.frameProcessor.framesHandled))
            except Exception as e:
                print("Got exception%s" % e, file=sys.stderr)
                
            self.frameProcessor.cleanUp()

    def lastDataFile(self):
        
        return self.frameProcessor.fileName
    
#    def abortReceived(self):
#        
#        self.abortRunFlag = True
        
class UdpReceiver(QtCore.QObject):
        
    def __init__(self, listenAddr, listenPort, numFrames):

        super(UdpReceiver, self).__init__()
        
        # Initialise variables used by processRxData
        self.first_frm_num = -1       
        self.packetNumber = -1
        self.frameCount = 0
        self.numFrames = numFrames
        self.totalReceiveTime = 0.0
        self.abort = False
        
        # Bind to UDP receive socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((listenAddr, listenPort))

        # Set socket timeout to allow receiver loop to tick and remain responsive to aborts
        self.sock.settimeout(0.5)
        
        print("UDP Receiver thread listening on address %s port %s" % (listenAddr, listenPort))

    def abortRun(self):
        self.abort = True
        
    def receiveLoop(self):
                    
        try:
            while self.frameCount < self.numFrames and self.abort == False:
                
                foundEof = 0
                lpdFrame = LpdFrameContainer(self.frameCount)
                
                while foundEof == 0 and self.abort == False:
                    try:
                        stream = self.sock.recv(9000)
                        foundEof  = self.processRxData(lpdFrame, stream)
                        if foundEof:
                            # Complete frame received, transmit frame along with meta data saved in LpdFrameContainer object
                            #print >> sys.stderr, "Frame %d receive complete" % lpdFrame.frameNumber
                            self.emit(QtCore.SIGNAL("dataRxSignal"), lpdFrame)
                            self.frameCount += 1
                            self.totalReceiveTime += (lpdFrame.timeStampEof - lpdFrame.timeStampSof)
                    except socket.timeout:
                        pass
                    
        except Exception as e:
            print("UDP receiver event loop got an exception: %s" % e)
            raise(e)
            
        #print >> sys.stderr, "Receiver thread completed"

    def processRxData(self, lpdFrame, data):
        ''' 
        Processes received data packets, decoding the Train Transfer Protocol information
        to construct completed frames (trains) 
        '''

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

            if self.first_frm_num == -1:
                self.first_frm_num = frameNumber
                
            frameNumber = frameNumber - self.first_frm_num
            
            # Compare this packet number against the previous packet number
            if packetNumber != (self.packetNumber +1):
                # packet numbering not consecutive
                if packetNumber > self.packetNumber:
                    # this packet lost between this packet and the last packet received
                    print("Warning: Previous packet number: %3i versus this packet number: %3i" % (self.packetNumber, packetNumber))

            # Update current packet number
            self.packetNumber = packetNumber

            # Timestamp start of frame (when we received first data of train)
            if sof == 1:

                lpdFrame.timeStampSof = time.time()
        
                # It's the start of a new train, clear any data left from previous train..
                lpdFrame.rawImageData = b'' if is_python3 else ''

            if eof == 1:
                lpdFrame.timeStampEof = time.time()
            
            # Append current packet data onto raw image omitting trailer info
            lpdFrame.rawImageData += data[0:-8]
            
            return eof
        except Exception as e:
            print("processRxData() error: %s" % e)
            return -1
        

class FrameProcessor(QtCore.QObject):

    def __init__(self, numFrames, cachedParams, liveViewSignal):

        QtCore.QObject.__init__(self)
        
        self.numFrames = numFrames
        self.evrData = None
        
        self.runNumber       = cachedParams['runNumber']
        self.fileWriteEnable = cachedParams['fileWriteEnable']
        self.dataFilePath    = cachedParams['dataFilePath']
        self.liveViewEnable  = cachedParams['liveViewEnable']
        self.liveViewDivisor = cachedParams['liveViewDivisor']
        self.liveViewOffset  = cachedParams['liveViewOffset']
        self.asicModuleType  = cachedParams['asicModuleType']
        self.headersVersion  = cachedParams['headersVersion']
        self.liveViewSignal  = liveViewSignal
        
        self.fileName = None
        
        # Run start time
        self.tstart = time.time()

        # Initialise counters
        self.framesHandled = 0
        self.imagesWritten = 0
        self.dataBytesReceived = 0
        self.totalProcessingTime = 0.0

        # Define plotted image dimensions: 
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
            self.nrows = 256
            self.ncols = 256
        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
            self.nrows = 32
            self.ncols = 256
        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA:
            self.nrows = 256 
            self.ncols = 256
        else:
            print("Error: Unsupported asicModuleType selected: %r" % self.asicModuleType, file=sys.stderr)
            
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

        self.fileName = "{:s}/lpdData-{:05d}.hdf5".format(self.dataFilePath, self.runNumber)
        
        print("Creating HDF5 data file %s" % self.fileName)
        try:
            self.hdfFile = h5py.File(self.fileName, 'w')
        except IOError as e:
            print("Failed to open HDF file with error: %s" % e)
            raise(e)
        
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

        # Add metadata to metadata group
        self.metadataHandler = MetadataWriter(cachedParams)
        self.metaGroup.write_metadata(self.metaGroup)
     
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
        # Assume at least one image in train to begin with
        plotMaxPlots = 1

        # Loop over the specified number of plots
        while bNextImageAvailable and currentImage < plotMaxPlots:

#################################################################
# For readout with LPD Data Formatting ; 
# lpd headers and trailers in the data payload
# lpd header ; image data ; image descriptors ; lpd detector dependent ; lpd trailer ; 
            # following sizes in BYTES
            LPD_HEADER_SIZE = 32  # includes train id
            # Image Descriptors are fixed with 512 entries each of 4 blocks of descriptors:
            # 1) storageCellNumber (2 bytes)
            # 2) bunchNumber (8 bytes)
            # 3) status (2 bytes)
            # 4) length (4 bytes)
            LPD_IMAGE_DESCRIPTOR_SIZE = 0  # 8192
            LPD_DETECTOR_DEPENDENT_SIZE = (13*32); # fixed with trigger information from C&C module
            LPD_TRAILER_SIZE = 32 # includes crc

            LPD_FORMATTING_SIZE = LPD_HEADER_SIZE + LPD_IMAGE_DESCRIPTOR_SIZE + LPD_DETECTOR_DEPENDENT_SIZE + LPD_TRAILER_SIZE

            if self.headersVersion == 0:           
                imageOffset = self.imageFullLpdSize*currentImage
                # Change maximum plots to be 512 (effectively size of incoming image data) for old header format
                #plotMaxPlots = 511  # (0-511 = 512 plots)
            else:
                # Differentiate between XFEL format revisions
                if self.headersVersion == 2 or self.headersVersion == 3:
                    LPD_HEADER_SIZE = 64
                
                imageOffset = (self.imageFullLpdSize)*currentImage + int(LPD_HEADER_SIZE/2) # Prevent Python3 creating float type
                
                # Print XFEL header information
                if currentImage == 0:

                    if self.headersVersion == 3:
                        
    # Corrections to match f/w from vers $0298 which made all 64b fields Little Endian    John C Oct 2015
    # previous code also had wrong offsets 
    
                        magicMsb = self.pixelData[2+0] + (self.pixelData[3+0] << 16)  
                        #print("MAGIC Word Msw = $%08x " % magicMsb)
                        
                        trainLsb = self.pixelData[0+8] + (self.pixelData[1+8] << 16)
                        trainMsb = self.pixelData[2+8] + (self.pixelData[3+8] << 16)
                        trainId  = (trainMsb << 32) + trainLsb

                        dataLsb = self.pixelData[0+12] + (self.pixelData[1+12] << 16)
                        dataMsb = self.pixelData[2+12] + (self.pixelData[3+12] << 16)
                        dataId  = (dataMsb << 32) + dataLsb

                        linkLsb = self.pixelData[0+16] + (self.pixelData[1+16] << 16)
                        linkMsb = self.pixelData[2+16] + (self.pixelData[3+16] << 16)
                        linkId  = (linkMsb << 32) + linkLsb

                        imgCountIdLsb = self.pixelData[0+20] + (self.pixelData[1+20] << 16)
                        imgCountIdMsb = self.pixelData[2+20] + (self.pixelData[3+20] << 16)
                        imgCountId  = (imgCountIdMsb << 32) + imgCountIdLsb

                    else:
                    
                        # corrected offsets 
    
                        magicMsb = self.pixelData[0+0] + (self.pixelData[1+0] << 16)  
                        #print("MAGIC Word Msw = $%08x " % magicMsb)
                        
                        trainLsb = self.pixelData[2+8] + (self.pixelData[3+8] << 8)
                        trainMsb = self.pixelData[0+8] + (self.pixelData[1+8] << 8)
                        trainId  = (trainMsb << 16) + trainLsb
    
                        dataLsb = self.pixelData[2+12] + (self.pixelData[3+12] << 8)
                        dataMsb = self.pixelData[0+12] + (self.pixelData[1+12] << 8)
                        dataId  = (dataMsb << 16) + dataLsb
    
                        linkLsb = self.pixelData[2+16] + (self.pixelData[3+16] << 8)
                        linkMsb = self.pixelData[0+16] + (self.pixelData[1+16] << 8)
                        linkId  = (linkMsb << 16) + linkLsb
    
                        imgCountId  = self.pixelData[22] #[13] # Previous XFEL header version or older??

                    # Overwrite maximum plots with image number extracted from XFEL header
                    plotMaxPlots = imgCountId

                    #print("trainID: {0:>3} dataID: 0x{1:X} linkId: 0x{2:X} imageCount: 0x{3:X} ({4:})".format(trainId, dataId, linkId, imgCountId, imgCountId))

#################################################################

            # Get the first image of the image
            bNextImageAvailable = self.unpackImage(imageOffset)
            
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

            # Signal live view update at appropriate rate if enabled
            if self.liveViewEnable:
                if (self.imagesWritten - self.liveViewOffset) % self.liveViewDivisor == 0:
                    lpdImage = LpdImageContainer(self.runNumber, lpdFrame.frameNumber, currentImage)
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
        

    def cleanUp(self):
        
        # If timestamp data has been injected, add to the HDF file structure
        if self.evrData != None:
            if len(self.evrData.event) > 0:
                print("Injecting EVR timestamp data into HDF file structure")
                evrGroup          = self.lpdGroup.create_group('evr')
                self.evrEvent     = evrGroup.create_dataset('event', (len(self.evrData.event),), 'uint32')
                self.evrFiducial  = evrGroup.create_dataset('fiducial', (len(self.evrData.fiducial),), 'uint32')
                self.evrTimestamp = evrGroup.create_dataset('timeStamp', (len(self.evrData.timestamp),), 'float64')

                self.evrEvent[...] = np.array(self.evrData.event)
                self.evrFiducial[...] = np.array(self.evrData.fiducial)
                self.evrTimestamp[...] = np.array(self.evrData.timestamp)
            else:
                print("No EVR timestamp data received during run")

        # Close file if enabled
        if self.fileWriteEnable:
            self.hdfFile.close()

    
    def unpackImage(self, imageOffset):
        """ Extracts one image beginning at argument imageOffset in the member array 
            self.pixelData array. Returns boolean bImageAvailable indicating whether
            the current image is the last image in the data
        """
        # Boolean variable to track whether there is a image after this one in the data
        bNextImageAvailable = False
        
        # Check Asic Module type to determine how to process data
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA:
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
                for asicRow in range(numRowsPerAsic):
                    for asicCol in range(numColsPerAsic):
                        
                        self.imageLpdFullArray[asicRow::numRowsPerAsic, asicCol::numColsPerAsic] = self.pixelData[rawOffset:(rawOffset + numAsics)].reshape(8,16)
                        rawOffset += numAsics
            
            except IndexError:
                print("Image Processing Error @ %6i %6i %6i %6i %6i %6i " % (asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics))
            except Exception as e:
                print("Error extracting image at %i Bytes, need %i but only %i Bytes available" % (imageOffset, self.imageFullLpdSize, self.pixelData.shape[0] - imageOffset))
                print("(Error: %s)" % e)

            # Module specific data processing
            if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
                
                # Super Module - Image now upside down, reverse the order
                self.imageLpdFullArray[:,:] = self.imageLpdFullArray[::-1,:]
                self.imageArray = self.imageLpdFullArray.copy()
            elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
                
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
                    print("Error accessing 2 Tile data: %s" % e)
                    print("imageOffset: ", imageOffset)
                    sys.exit()

        # Last image in the data?
        try:
            # Increment imageOffset to start of next image
            imageOffset += self.imageFullLpdSize
            self.pixelData[imageOffset + self.imageFullLpdSize]
            # Will only get here if there is a next image available..
            bNextImageAvailable = True
        except IndexError:
            pass   # Last Image in this train detected
        return bNextImageAvailable
        
        

class DataMonitor(QtCore.QObject):
    
    def __init__(self, udpReceiver, frameProcessor, updateSignal, numFrames):
        
        QtCore.QObject.__init__(self)
        
        self.udpReceiver = udpReceiver
        self.frameProcessor = frameProcessor
        self.updateSignal = updateSignal
        self.numFrames = numFrames
        self.abort = False
        
    def abortRun(self):
        self.abort = True
        
    def monitorLoop(self):
        
        try:
            while self.frameProcessor.framesHandled < self.numFrames and self.abort == False:
                
                runStatus = LpdRunStatusContainer(self.udpReceiver.frameCount, self.frameProcessor.framesHandled, 
                                                self.frameProcessor.imagesWritten, self.frameProcessor.dataBytesReceived)
                self.updateSignal.emit(runStatus)
                time.sleep(0.5)

            runStatus = LpdRunStatusContainer(self.udpReceiver.frameCount, self.frameProcessor.framesHandled, 
                                            self.frameProcessor.imagesWritten, self.frameProcessor.dataBytesReceived)
            self.updateSignal.emit(runStatus)
            
        except Exception as e:
            print("Got exception in data monitor loop:%s" % e, file=sys.stderr)
