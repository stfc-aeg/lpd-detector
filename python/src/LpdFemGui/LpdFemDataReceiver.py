'''
Created on Apr 19, 2013

@author: tcn45
'''

from LpdDataContainers import *

import os, sys, time, socket
import numpy as np
from PyQt4 import QtCore

import h5py

#Display received data in plots
bDisplayPlotData = True

# Debugging enabled if set above 0
bDebug = 0
        
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
            print "LdpFemDataReceiver got exception during initialisation: %s" % e
        
    def injectTimestampData(self, evrData):

        self.frameProcessor.evrData = evrData

    def awaitCompletion(self):

            print "Waiting for frame processing to complete"
            while self.frameProcessor.framesHandled < self.numFrames and self.appMain.abortRun == False:
                time.sleep(0.1)
            
            if self.appMain.abortRun:
                print "Run aborted by user"
            
            print "Frame processor handled all frames, terminating data receiver threads"
            self.frameProcessorThread.quit()
            self.udpReceiverThread.quit()
            self.dataMonitorThread.quit()
            
            self.frameProcessorThread.wait()
            self.udpReceiverThread.wait()
            self.dataMonitorThread.wait()
            
            try:            
                print "Average frame UDP receive time : %f secs" % (self.udpReceiver.totalReceiveTime / self.udpReceiver.frameCount)
                print "Average frame processing time  : %f secs" % (self.frameProcessor.totalProcessingTime / self.frameProcessor.framesHandled)
            except Exception as e:
                print >> sys.stderr, "Got exception", e
                
            self.frameProcessor.cleanUp()
        
    def abortReceived(self):
        
        self.abortRunFlag = True
        
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

        print "UDP Receiver thread listening on address %s port %s" % (listenAddr, listenPort)


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
            offset = 0
            # TODO: Extract train number (the first four bytes)
            frame_number = 0

            # Extract packet number (the following four bytes)
            packet_number = ord(data[offset-4]) 

            trailer_info = ord(data[-1])

            # Extract Start Of Frame, End of Frame
            frm_sof = (trailer_info & 0x80) >> 7
            frm_eof = (trailer_info & 0x40) >> 6
            
            # frame_number = train number relative to execution of this software
            #lpdFrame.frameNumber = frame_number
            
            if self.first_frm_num == -1:
                self.first_frm_num = frame_number
                
            frame_number = frame_number - self.first_frm_num
            
            # Compare this packet number against the previous packet number
            if packet_number != (self.packetNumber +1):
                # packet numbering not consecutive
                if packet_number > self.packetNumber:
                    # this packet lost between this packet and the last packet received
                    print "Warning: Previous packet number: %3i versus this packet number: %3i" % (self.packetNumber, packet_number)

            # Update current packet number
            self.packetNumber = packet_number

            # Timestamp start of frame (when we received first data of train)
            if frm_sof == 1:

                lpdFrame.timeStampSof = time.time()
        
                # It's the start of a new train, clear any data left from previous train..
                lpdFrame.rawImageData = ""                

            if frm_eof == 1:
                lpdFrame.timeStampEof = time.time()
            
            # Append current packet data onto raw image omitting trailer info
            lpdFrame.rawImageData += data[0:-8]
            
            return frm_eof
        except Exception as e:
            print "processRxData() error: ", e
            return -1
        

class FrameProcessor(QtCore.QObject):

    def __init__(self, numFrames, cachedParams, liveViewSignal):

        QtCore.QObject.__init__(self)
        
        self.numFrames = numFrames
        self.evrData = None
        
        self.runNumber = cachedParams['runNumber']
        self.fileWriteEnable = cachedParams['fileWriteEnable']
        self.dataFilePath = cachedParams['dataFilePath']
        self.liveViewEnable = cachedParams['liveViewEnable']
        self.liveViewDivisor = cachedParams['liveViewDivisor']
        self.liveViewOffset  = cachedParams['liveViewOffset']

        self.liveViewSignal = liveViewSignal

        # Run start time
        self.tstart = time.time()

        # Initialise counters
        self.framesHandled = 0
        self.imagesWritten = 0
        self.dataBytesReceived = 0
        self.totalProcessingTime = 0.0

        # Define plotted image dimensions: 
        self.nrows = 32*8   # 32 rows * 8 ASICs = 256 
        self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        self.imageSize = self.nrows * self.ncols

        # Create an array to contain 65536 elements (32 x 8 x 16 x 16 = super module image)
        self.imageArray = np.zeros(self.imageSize, dtype=np.uint16)
        
        # Create HDF file if requested
        if self.fileWriteEnable:            
            self.createDataFile(cachedParams)           
        
   
    def createDataFile(self, cachedParams):
        '''
        Creates and HDF5 data file and internal structure, sets up metadata in file
        '''

        fileName = "{:s}/lpdData-{:05d}.hdf5".format(self.dataFilePath, self.runNumber)

        print "Creating HDF5 data file %s" % fileName
        try:
            self.hdfFile = h5py.File(fileName, 'w')
        except IOError as e:
            print "Failed to open HDF file with error: %s" % e
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

        # Build metadata attributes from cached parameters
        for param, val in cachedParams.iteritems():
            self.metaGroup.attrs[param] = val

        # Write the XML configuration files into the metadata group        
        self.xmlDs = {}
        str_type = h5py.new_vlen(str)
        for paramFile in ('readoutParamFile', 'fastParamFile', 'slowParamFile'):
            self.xmlDs['paramFile'] = self.metaGroup.create_dataset(paramFile, shape=(1,), dtype=str_type)
            try:
                with open(cachedParams[paramFile], 'r') as xmlFile:
                    self.xmlDs['paramFile'][:] = xmlFile.read()
                    
            except IOError as e:
                print "Failed to read %s XML file %s : %s " (paramFile, cachedParams[paramFile], e)
                raise(e)
            except Exception as e:
                print "Got exception trying to create metadata for %s XML file %s : %s " % (paramFile, cachedParams[paramFile], e)
                raise(e)
                

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

            imageOffset = self.imageSize * currentImage

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
                print "Injecting EVR timestamp data into HDF file structure"
                evrGroup          = self.lpdGroup.create_group('evr')
                self.evrEvent     = evrGroup.create_dataset('event', (len(self.evrData.event),), 'uint32')
                self.evrFiducial  = evrGroup.create_dataset('fiducial', (len(self.evrData.fiducial),), 'uint32')
                self.evrTimestamp = evrGroup.create_dataset('timeStamp', (len(self.evrData.timestamp),), 'float64')

                self.evrEvent[...] = np.array(self.evrData.event)
                self.evrFiducial[...] = np.array(self.evrData.fiducial)
                self.evrTimestamp[...] = np.array(self.evrData.timestamp)
            else:
                print "No EVR timestamp data received during run"

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

        numAsicCols = 16
        numAsicRows = 8
        numAsics = numAsicCols * numAsicRows
        numColsPerAsic = 16
        numRowsPerAsic = 32

        numPixelsPerAsic = numColsPerAsic * numRowsPerAsic
        numPixels = numAsics * numPixelsPerAsic

        # Create linear array for unpacked pixel data
        self.imageArray = np.zeros(numPixels, dtype=np.uint16)
        self.imageArray = np.reshape(self.imageArray, (numAsicRows * numRowsPerAsic, numAsicCols * numColsPerAsic))

        rawOffset = imageOffset

        try:
            for asicRow in xrange(numRowsPerAsic):
                for asicCol in xrange(numColsPerAsic):
                    
                    self.imageArray[asicRow::numRowsPerAsic, asicCol::numColsPerAsic] = self.pixelData[rawOffset:(rawOffset + numAsics)].reshape(8,16)
                    rawOffset += numAsics
        
        except IndexError:
            print "Image Processing Error @ %6i %6i %6i %6i %6i %6i " % ( asicRow, numRowsPerAsic, asicCol, numColsPerAsic, rawOffset, numAsics )
        except Exception as e:
            print "Error while extracting image: ", e

        # Image now upside down, reverse the order
        self.imageArray[:,:] = self.imageArray[::-1,:]

        # Last image in the data?
        try:
            self.pixelData[imageOffset + self.imageSize]
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
        
    def monitorLoop(self):
        
        try:
            while self.frameProcessor.framesHandled < self.numFrames:
                
                runStatus = LpdRunStatusContainer(self.udpReceiver.frameCount, self.frameProcessor.framesHandled, 
                                                self.frameProcessor.imagesWritten, self.frameProcessor.dataBytesReceived)
                self.updateSignal.emit(runStatus)
                time.sleep(0.5)

            runStatus = LpdRunStatusContainer(self.udpReceiver.frameCount, self.frameProcessor.framesHandled, 
                                            self.frameProcessor.imagesWritten, self.frameProcessor.dataBytesReceived)
            self.updateSignal.emit(runStatus)
            
        except Exception as e:
            print >> sys.stderr, "Got exception in data monitor loop:", e
