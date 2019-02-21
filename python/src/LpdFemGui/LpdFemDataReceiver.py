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
    
    def __init__(self, live_view_signal, run_status_signal, listen_addr, listen_port, num_frames, cached_params, app_main):
        
        try:
                
            self.num_frames = num_frames
            self.app_main = app_main

            # Create UDP recevier, frame processor and data monitor objects
            self.udp_receiver = UdpReceiver(listen_addr, listen_port, num_frames)
            self.frame_processor = FrameProcessor(num_frames, cached_params, live_view_signal)
            self.data_monitor = DataMonitor(self.udp_receiver, self.frame_processor, run_status_signal, num_frames)
            
            # Create threads to run them in
            self.udp_receiver_thread = QtCore.QThread() 
            self.frame_processor_thread = QtCore.QThread()
            self.data_monitor_thread = QtCore.QThread()
            
            # Move objects into threads
            self.udp_receiver.moveToThread(self.udp_receiver_thread)
            self.frame_processor.moveToThread(self.frame_processor_thread)
            self.data_monitor.moveToThread(self.data_monitor_thread)
            
            # Connect thread start signal of UDP receiver to receive loop function
            self.udp_receiver_thread.started.connect(self.udp_receiver.receiveLoop)
            
            # Connect data RX signal from UDP receiver to handleDataRx slot in frame processor
            self.udp_receiver.connect(self.udp_receiver, QtCore.SIGNAL("dataRxSignal"), self.frame_processor.processFrame)
                        
            # Connect monitor loop start singal to monitor loop function
            self.data_monitor_thread.started.connect(self.data_monitor.monitorLoop)
            
            # Start data monitor up
            self.data_monitor_thread.start()
            
            # Start the frame processor thread up
            self.frame_processor_thread.start()

            # Start the UDP receiver thread up            
            self.udp_receiver_thread.start()
            
        except Exception as e:
            print("LdpFemDataReceiver got exception during initialisation: %s" % e)
        
    def injectTimestampData(self, evrData):

        self.frame_processor.evr_data = evrData

    def awaitCompletion(self):

            print("Waiting for frame processing to complete")
            while self.frame_processor.frames_handled < self.num_frames and self.app_main.abort_run == False:
                time.sleep(0.1)
            
            if self.app_main.abort_run:
                print("Run aborted by user")
                self.udp_receiver.abort_run()
                self.data_monitor.abort_run()
            else:
                print("Frame processor handled all frames, terminating data receiver threads")
                
            self.frame_processor_thread.quit()
            self.udp_receiver_thread.quit()
            self.data_monitor_thread.quit()
            
            self.frame_processor_thread.wait()
            self.udp_receiver_thread.wait()
            self.data_monitor_thread.wait()
            
            try:
                if self.udp_receiver.frame_count > 0:            
                    print("Average frame UDP receive time : %f secs" % (self.udp_receiver.total_receive_time / self.udp_receiver.frame_count))
                if self.frame_processor.frames_handled > 0:
                    print("Average frame processing time  : %f secs" % (self.frame_processor.total_processing_time / self.frame_processor.frames_handled))
            except Exception as e:
                print("Got exception%s" % e, file=sys.stderr)
                
            self.frame_processor.cleanUp()

    def last_data_file(self):
        
        return self.frame_processor.file_name
    
#    def abortReceived(self):
#        
#        self.abortRunFlag = True
        
class UdpReceiver(QtCore.QObject):
        
    def __init__(self, listen_addr, listen_port, num_frames):

        super(UdpReceiver, self).__init__()
        
        # Initialise variables used by processRxData
        self.first_frm_num = -1       
        self.packet_number = -1
        self.frame_count = 0
        self.num_frames = num_frames
        self.total_receive_time = 0.0
        self.abort = False
        
        # Bind to UDP receive socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((listen_addr, listen_port))

        # Set socket timeout to allow receiver loop to tick and remain responsive to aborts
        self.sock.settimeout(0.5)
        
        print("UDP Receiver thread listening on address %s port %s" % (listen_addr, listen_port))

    def abort_run(self):
        self.abort = True
        
    def receiveLoop(self):
                    
        try:
            while self.frame_count < self.num_frames and self.abort == False:
                
                found_eof = 0
                lpd_frame = LpdFrameContainer(self.frame_count)
                
                while found_eof == 0 and self.abort == False:
                    try:
                        stream = self.sock.recv(9000)
                        found_eof  = self.processRxData(lpd_frame, stream)
                        if found_eof:
                            # Complete frame received, transmit frame along with meta data saved in LpdFrameContainer object
                            #print >> sys.stderr, "Frame %d receive complete" % lpd_frame.frameNumber
                            self.emit(QtCore.SIGNAL("dataRxSignal"), lpd_frame)
                            self.frame_count += 1
                            self.total_receive_time += (lpd_frame.timeStampEof - lpd_frame.timeStampSof)
                    except socket.timeout:
                        pass
                    
        except Exception as e:
            print("UDP receiver event loop got an exception: %s" % e)
            raise(e)
            
        #print >> sys.stderr, "Receiver thread completed"

    def processRxData(self, lpd_frame, data):
        ''' 
        Processes received data packets, decoding the Train Transfer Protocol information
        to construct completed frames (trains) 
        '''

        try:
            # Extract Trailer information
            trailer_info = np.zeros(2, dtype=np.uint32)
            trailer_info = np.fromstring(data[-8:], dtype=np.uint32)
            
            # Extract train/frame number (the second last 32 bit word from the raw data)
            frame_number = trailer_info[0]
            # Extract packet number (last 32 bit word)
            packet_number = trailer_info[1] & 0x3FFFFFFF
            
            # Extract Start Of Frame, End of Frame
            sof = (trailer_info[1] >> (31)) & 0x1
            eof = (trailer_info[1] >> (30)) & 0x1

            if self.first_frm_num == -1:
                self.first_frm_num = frame_number
                
            frame_number = frame_number - self.first_frm_num
            
            # Compare this packet number against the previous packet number
            if packet_number != (self.packet_number +1):
                # packet numbering not consecutive
                if packet_number > self.packet_number:
                    # this packet lost between this packet and the last packet received
                    print("Warning: Previous packet number: %3i versus this packet number: %3i" % (self.packet_number, packet_number))

            # Update current packet number
            self.packet_number = packet_number

            # Timestamp start of frame (when we received first data of train)
            if sof == 1:

                lpd_frame.timeStampSof = time.time()
        
                # It's the start of a new train, clear any data left from previous train..
                lpd_frame.rawImageData = b'' if is_python3 else ''

            if eof == 1:
                lpd_frame.timeStampEof = time.time()
            
            # Append current packet data onto raw image omitting trailer info
            lpd_frame.rawImageData += data[0:-8]
            
            return eof
        except Exception as e:
            print("processRxData() error: %s" % e)
            return -1
        

class FrameProcessor(QtCore.QObject):

    def __init__(self, num_frames, cached_params, live_view_signal):

        QtCore.QObject.__init__(self)
        
        self.num_frames = num_frames
        self.evr_data = None
        
        self.runNumber       = cached_params['runNumber']
        self.fileWriteEnable = cached_params['fileWriteEnable']
        self.dataFilePath    = cached_params['dataFilePath']
        self.liveViewEnable  = cached_params['liveViewEnable']
        self.liveViewDivisor = cached_params['liveViewDivisor']
        self.liveViewOffset  = cached_params['liveViewOffset']
        self.asicModuleType  = cached_params['asicModuleType']
        self.headersVersion  = cached_params['headersVersion']
        self.liveViewSignal  = live_view_signal
        
        self.file_name = None
        
        # Run start time
        self.tstart = time.time()

        # Initialise counters
        self.frames_handled = 0
        self.images_written = 0
        self.data_bytes_received = 0
        self.total_processing_time = 0.0

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
        self.image_module_size = self.nrows * self.ncols
        self.image_full_lpd_size = 256 * 256

        # Create an image array to contain the elements of the module type 
        # Super Module = (32 x 8 x 16 x 16) = 65536 elements
        # 2Tile System = (32 * 16 * 16)     = 8192 elements
        self.image_array = np.zeros(self.image_module_size, dtype=np.uint16)
        
        # Create HDF file if requested
        if self.fileWriteEnable:            
            self.createDataFile(cached_params)           
        
   
    def createDataFile(self, cached_params):
        '''
        Creates and HDF5 data file and internal structure, sets up metadata in file
        '''

        self.file_name = "{:s}/lpdData-{:05d}.hdf5".format(self.dataFilePath, self.runNumber)
        
        print("Creating HDF5 data file %s" % self.file_name)
        try:
            self.hdf_file = h5py.File(self.file_name, 'w')
            # File closed in cleanUp()
        except IOError as e:
            print("Failed to open HDF file with error: %s" % e)
            raise(e)
        
        # Create group structure
        self.lpd_group = self.hdf_file.create_group('lpd')
        self.meta_group = self.lpd_group.create_group('metadata')
        self.data_group = self.lpd_group.create_group('data')
        
        # Create data group entries    
        self.image_ds = self.data_group.create_dataset('image', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                        maxshape=(None,self.nrows, self.ncols))
        self.time_stamp_ds   = self.data_group.create_dataset('timeStamp',   (1,), 'float64', maxshape=(None,))
        self.train_number_ds = self.data_group.create_dataset('trainNumber', (1,), 'uint32', maxshape=(None,))
        self.image_number_ds = self.data_group.create_dataset('imageNumber', (1,), 'uint32', maxshape=(None,))

        # Add metadata to metadata group
        self.metadata_handler = MetadataWriter(cached_params)
        self.metadata_handler.write_metadata(self.meta_group)
     
    def processFrame(self, lpd_frame):
        
        #print >> sys.stderr, "Frame processor thread receiver frame number", lpd_frame.frameNumber, 'raw data length', len(lpd_frame.rawImageData)

        self.data_bytes_received += len(lpd_frame.rawImageData)
        
        # Capture time of starting processing
        start_time = time.time()
          
        # Simultaneously extract 16 bit pixel data from raw 32 bit words and swap the byte order
        #     eg: ABCD => DCBA
        self.pixel_data = np.fromstring(lpd_frame.rawImageData, dtype=np.dtype('<i2'))
            
        # Define variables that increase with each loop iteration
        current_image = 0
        b_next_image_available = True
        # Assume at least one image in train to begin with
        plot_max_plots = 1

        # Loop over the specified number of plots
        while b_next_image_available and current_image < plot_max_plots:

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
            LPD_DETECTOR_DEPENDENT_SIZE = 13 * 32 # fixed with trigger information from C&C module
            LPD_TRAILER_SIZE = 32 # includes crc

            LPD_FORMATTING_SIZE = LPD_HEADER_SIZE + LPD_IMAGE_DESCRIPTOR_SIZE + LPD_DETECTOR_DEPENDENT_SIZE + LPD_TRAILER_SIZE

            if self.headersVersion == 0:           
                image_offset = self.image_full_lpd_size * current_image
                # Change maximum plots to be 512 (effectively size of incoming image data) for old header format
                #plot_max_plots = 511  # (0-511 = 512 plots)
            else:
                # Differentiate between XFEL format revisions
                if self.headersVersion == 2 or self.headersVersion == 3:
                    LPD_HEADER_SIZE = 64
                
                image_offset = (self.image_full_lpd_size) * current_image + int(LPD_HEADER_SIZE/2) # Prevent Python3 creating float type
                
                # Print XFEL header information
                if current_image == 0:

                    if self.headersVersion == 3:
                        
    # Corrections to match f/w from vers $0298 which made all 64b fields Little Endian    John C Oct 2015
    # previous code also had wrong offsets 
    
                        magic_msb = self.pixel_data[2+0] + (self.pixel_data[3+0] << 16)  
                        #print("MAGIC Word Msw = $%08x " % magic_msb)
                        
                        train_lsb = self.pixel_data[0+8] + (self.pixel_data[1+8] << 16)
                        train_msb = self.pixel_data[2+8] + (self.pixel_data[3+8] << 16)
                        train_id  = (train_msb << 32) + train_lsb

                        data_lsb = self.pixel_data[0+12] + (self.pixel_data[1+12] << 16)
                        data_msb = self.pixel_data[2+12] + (self.pixel_data[3+12] << 16)
                        data_id  = (data_msb << 32) + data_lsb

                        link_lsb = self.pixel_data[0+16] + (self.pixel_data[1+16] << 16)
                        link_msb = self.pixel_data[2+16] + (self.pixel_data[3+16] << 16)
                        link_id  = (link_msb << 32) + link_lsb

                        img_count_id_lsb = self.pixel_data[0+20] + (self.pixel_data[1+20] << 16)
                        img_count_id_msb = self.pixel_data[2+20] + (self.pixel_data[3+20] << 16)
                        img_count_id  = (img_count_id_msb << 32) + img_count_id_lsb

                    else:
                    
                        # corrected offsets 
    
                        magic_msb = self.pixel_data[0+0] + (self.pixel_data[1+0] << 16)  
                        #print("MAGIC Word Msw = $%08x " % magic_msb)
                        
                        train_lsb = self.pixel_data[2+8] + (self.pixel_data[3+8] << 8)
                        train_msb = self.pixel_data[0+8] + (self.pixel_data[1+8] << 8)
                        train_id  = (train_msb << 16) + train_lsb
    
                        data_lsb = self.pixel_data[2+12] + (self.pixel_data[3+12] << 8)
                        data_msb = self.pixel_data[0+12] + (self.pixel_data[1+12] << 8)
                        data_id  = (data_msb << 16) + data_lsb
    
                        link_lsb = self.pixel_data[2+16] + (self.pixel_data[3+16] << 8)
                        link_msb = self.pixel_data[0+16] + (self.pixel_data[1+16] << 8)
                        link_id  = (link_msb << 16) + link_lsb
    
                        img_count_id  = self.pixel_data[22] #[13] # Previous XFEL header version or older??

                    # Overwrite maximum plots with image number extracted from XFEL header
                    plot_max_plots = img_count_id

                    #print("trainID: {0:>3} dataID: 0x{1:X} link_id: 0x{2:X} imageCount: 0x{3:X} ({4:})".format(train_id, data_id, link_id, img_count_id, img_count_id))

#################################################################

            # Get the first image of the image
            b_next_image_available = self.unpackImage(image_offset)
            
            # Write image to file if selected
            if self.fileWriteEnable:
                self.image_ds.resize((self.images_written+1, self.nrows, self.ncols))
                self.image_ds[self.images_written,...] = self.image_array
                
                self.time_stamp_ds.resize((self.images_written+1, ))
                self.time_stamp_ds[self.images_written] = lpd_frame.timeStampSof
                
                self.train_number_ds.resize((self.images_written+1, ))
                self.train_number_ds[self.images_written] = lpd_frame.frameNumber
                
                self.image_number_ds.resize((self.images_written+1, ))
                self.image_number_ds[self.images_written] = current_image

            # Signal live view update at appropriate rate if enabled
            if self.liveViewEnable:
                if (self.images_written - self.liveViewOffset) % self.liveViewDivisor == 0:
                    lpd_image = LpdImageContainer(self.runNumber, lpd_frame.frameNumber, current_image)
                    lpd_image.image_array = self.image_array.copy()
                    self.liveViewSignal.emit(lpd_image)
                    
            # Clear data before next iteration (but after data written to file)
            self.image_array.fill(0)
            
            # Increment current image
            current_image += 1
            self.images_written += 1
            
        # 'Reset' rawImageData variable - WHY??
        lpd_frame.rawImageData = lpd_frame.rawImageData[0:0]

        end_time = time.time()
        self.total_processing_time += (end_time - start_time)
        #print "Total frame processing time = %f secs" % (end_time - start_time)

        self.frames_handled += 1
        #if self.frames_handled >= self.num_frames:
        #    print >> sys.stderr, "Frame processor thread processed all frames, quitting"
        

    def cleanUp(self):
        
        # If timestamp data has been injected, add to the HDF file structure
        if self.evr_data != None:
            if len(self.evr_data.event) > 0:
                print("Injecting EVR timestamp data into HDF file structure")
                evr_group          = self.lpd_group.create_group('evr')
                self.evr_event     = evr_group.create_dataset('event', (len(self.evr_data.event),), 'uint32')
                self.evr_fiducial  = evr_group.create_dataset('fiducial', (len(self.evr_data.fiducial),), 'uint32')
                self.evr_timestamp = evr_group.create_dataset('timeStamp', (len(self.evr_data.timestamp),), 'float64')

                self.evr_event[...] = np.array(self.evr_data.event)
                self.evr_fiducial[...] = np.array(self.evr_data.fiducial)
                self.evr_timestamp[...] = np.array(self.evr_data.timestamp)
            else:
                print("No EVR timestamp data received during run")

        # Close file if enabled
        if self.fileWriteEnable:
            self.hdf_file.close()

    
    def unpackImage(self, image_offset):
        """ Extracts one image beginning at argument image_offset in the member array 
            self.pixel_data array. Returns boolean bImageAvailable indicating whether
            the current image is the last image in the data
        """
        # Boolean variable to track whether there is a image after this one in the data
        b_next_image_available = False
        
        # Check Asic Module type to determine how to process data
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA:
            # Raw data - no not re-order
            self.image_array = self.pixel_data[image_offset:image_offset + self.image_full_lpd_size].reshape(256, 256)
        else:
            # Not raw data, proceed to reorder data
            num_asic_cols = 16
            num_asic_rows = 8
            num_asics = num_asic_cols * num_asic_rows
            num_cols_per_asic = 16
            num_rows_per_asic = 32
    
            num_pixels_per_asic = num_cols_per_asic * num_rows_per_asic
            num_pixels = num_asics * num_pixels_per_asic
    
            # Create linear array for unpacked pixel data
            self.image_lpd_full_array = np.zeros(num_pixels, dtype=np.uint16)
            self.image_lpd_full_array = np.reshape(self.image_lpd_full_array, (num_asic_rows * num_rows_per_asic, num_asic_cols * num_cols_per_asic))
    
            raw_offset = image_offset
    
            try:
                for asic_row in range(num_rows_per_asic):
                    for asic_col in range(num_cols_per_asic):
                        
                        self.image_lpd_full_array[asic_row::num_rows_per_asic, asic_col::num_cols_per_asic] = self.pixel_data[raw_offset:(raw_offset + num_asics)].reshape(8,16)
                        raw_offset += num_asics
            
            except IndexError:
                print("Image Processing Error @ %6i %6i %6i %6i %6i %6i " % (asic_row, num_rows_per_asic, asic_col, num_cols_per_asic, raw_offset, num_asics))
            except Exception as e:
                print("Error extracting image at %i Bytes, need %i but only %i Bytes available" % (image_offset, self.image_full_lpd_size, self.pixel_data.shape[0] - image_offset))
                print("(Error: %s)" % e)

            # Module specific data processing
            if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
                
                # Super Module - Image now upside down, reverse the order
                self.image_lpd_full_array[:,:] = self.image_lpd_full_array[::-1,:]
                self.image_array = self.image_lpd_full_array.copy()
            elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
                
                #Two Tile
                # Create array for 2 Tile data; reshape into two dimensional array
                self.image_array = np.zeros(self.image_module_size, dtype=np.uint16)
                self.image_array = self.image_array.reshape(32, 256)
        
                # Copy the two Tiles that exists in the two tile system
                try:
                    # LHS Tile located in the second ASIC row, second ASIC column
                    self.image_array[0:32, 0:128]   = self.image_lpd_full_array[32:32+32, 256-1:128-1:-1]
                    # RHS Tile located in the seventh ASIC row, second ASIC column
                    self.image_array[0:32, 128:256] = self.image_lpd_full_array[192:192+32, 256-1:128-1:-1]
                except Exception as e:
                    print("Error accessing 2 Tile data: %s" % e)
                    print("image_offset: ", image_offset)
                    sys.exit()

        # Last image in the data?
        try:
            # Increment image_offset to start of next image
            image_offset += self.image_full_lpd_size
            self.pixel_data[image_offset + self.image_full_lpd_size]
            # Will only get here if there is a next image available..
            b_next_image_available = True
        except IndexError:
            pass   # Last Image in this train detected
        return b_next_image_available
        
        

class DataMonitor(QtCore.QObject):
    
    def __init__(self, udp_receiver, frame_processor, update_signal, num_frames):
        
        QtCore.QObject.__init__(self)
        
        self.udp_receiver = udp_receiver
        self.frame_processor = frame_processor
        self.update_signal = update_signal
        self.num_frames = num_frames
        self.abort = False
        
    def abort_run(self):
        self.abort = True
        
    def monitorLoop(self):
        
        try:
            while self.frame_processor.frames_handled < self.num_frames and self.abort == False:
                
                run_status = LpdRunStatusContainer(self.udp_receiver.frame_count, self.frame_processor.frames_handled, 
                                                self.frame_processor.images_written, self.frame_processor.data_bytes_received)
                self.update_signal.emit(run_status)
                time.sleep(0.5)

            run_status = LpdRunStatusContainer(self.udp_receiver.frame_count, self.frame_processor.frames_handled, 
                                            self.frame_processor.images_written, self.frame_processor.data_bytes_received)
            self.update_signal.emit(run_status)
            
        except Exception as e:
            print("Got exception in data monitor loop:%s" % e, file=sys.stderr)
