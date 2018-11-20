'''
Created on Apr 19, 2013

@author: tcn45
'''
from __future__ import print_function

from LpdDataContainers import *
from LpdFemClient.LpdFemClient import LpdFemClient
from LpdFemGui import *
from LpdFemMetadataWriter import *

import os, sys, time, socket, json, h5py, zmq
import numpy as np
from PyQt4 import QtCore

from subprocess import Popen, PIPE

from odin_data.ipc_channel import IpcChannel, IpcChannelException
from odin_data.ipc_message import IpcMessage, IpcMessageException

# Test if running python 3
is_python3 = sys.version_info > (3,)

#Display received data in plots
b_display_plot_data = True


class LpdFemOdinDataReceiver():
    """
    This object is used when the data is coming from ODIN (as opposed to internally). This object 
    is recycled throughout the lifecycle of the GUI session (everything in __init__() )
    """

    MESSAGE_ID_MAX = 2**32
    _msg_id = 0

    def __init__(self, run_status_signal, num_frames, app_main, live_view_signal):
        """ This is executed on the first run of each GUI session - this object is retained 
        throughout the lifecycle of the session.
        """

        try:
            self.run_status_signal = run_status_signal
            self.num_frames = num_frames
            self.app_main = app_main
            self.live_view_signal = live_view_signal

            print("Launching Frame Receiver and Frame Processor")
            # Getting location of FR & FP and paths of their config files
            fr_fp_location = self.app_main.getCachedParam("frameReceiverProcessorLocation")
            frame_receiver_config_path = self.app_main.getCachedParam("frameReceiverConfigFile")
            frame_processor_config_path = self.app_main.getCachedParam("frameProcessorConfigFile")

            # Using Subprocess to launch the frame receiver and frame processor
            start_frame_receiver = Popen(["./frameReceiver", "--debug", "2", "--logconfig", 
                                          frame_receiver_config_path], cwd=fr_fp_location)
            start_frame_processor = Popen(["./frameProcessor", "--logconfig", 
                                           frame_processor_config_path], cwd=fr_fp_location)

            # Create the appropriate IPC channels for receiver and proccessor
            print("Connecting to Frame Receiver's IPC Control Channel")
            self.fr_ctrl_channel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
            self.fr_ctrl_channel.connect(self.app_main.getCachedParam('odinFrCtrlChannel'))

            print("Connecting to Frame Proccessor's IPC Control Channel")
            self.fp_ctrl_channel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
            self.fp_ctrl_channel.connect(self.app_main.getCachedParam('odinFpCtrlChannel'))          
        except Exception as e:
            print("LdpFemOdinDataReceiver got exception during initialisation: %s" % e)
            
    def configure(self, num_frames, num_images):
        ''' Executed at the start of every run to do a number of things including creating and 
            starting the data monitor thread.
        '''
        try:
            self.num_frames = num_frames

            # Load Odin Data config
            print("Loading ODIN Data config from {}".format(self.app_main.getCachedParam('odinDataConfigFile')))
            with open(self.app_main.getCachedParam('odinDataConfigFile')) as configFile:
                self.odin_data_config = json.load(configFile)
                self.config_receiver = self.odin_data_config['receiver_default_config']
                self.config_processor = self.odin_data_config['processor_default_config']
                self.config_processor_plugins = self.odin_data_config['processor_plugins']
            
            # Set number of expected frames based on the master dataset (dataset containing the data, 
            # as defined in odin_data_lpd_config.json)
            self.config_processor['hdf']['frames'] = (self.num_frames * num_images)
            
            # Set path and filename of output file
            print("Setting Path & Filename of Output File")
            file_path = self.app_main.getCachedParam('dataFilePath')
            self.config_processor['hdf']['file']['path'] = file_path
            
            # Set file name based on current run number
            run_number = self.app_main.getCachedParam('runNumber')            
            file_name = "lpdData-{:05d}.hdf5".format(run_number)
            self.config_processor['hdf']['file']['name'] = file_name

            # Send Frame Receiver config
            print("Sending Frame Receiver Config")
            self.send_config_msg(self.fr_ctrl_channel, self.config_receiver)
            
            # Send Frame Receiver info to Frame Processor
            print("Sending Receiver connection info to Frame Processor")
            params = {'fr_setup' : self.config_processor['fr_setup']}
            self.send_config_msg(self.fp_ctrl_channel, params)
            
            # Sending Processor plugin configs
            if len(self.config_processor_plugins):
                print("Sending Processor plugin chain config to Frame Processor")
                for plugin in self.config_processor_plugins:
                    self.send_config_msg(self.fp_ctrl_channel, plugin)

            # Send Frame Processor config
            print("Sending Frame Processor Config")
            self.send_config_msg(self.fp_ctrl_channel, self.config_processor)

            print("Waiting for Receiver/Processor handshake to complete")
            # Around 8 seconds before timeout
            timeout_attempts = 40
            request_number = 0
            
            # Checking status of FR/FP handshake
            while True:
                reply = self.send_status_cmd(self.fp_ctrl_channel)
                if reply is not None:
                    shared_memory_buffer_status = reply.attrs['params']['shared_memory']['configured']
                    if shared_memory_buffer_status is True:
                        break
                    
                request_number += 1
                if(request_number > timeout_attempts):
                    break 
                time.sleep(0.2)
      
            # Create data monitor object and thread then move object into thread
            print("Creating Data Monitor Thread")
            self.data_monitor = OdinDataMonitor(self)
            self.data_monitor_thread = QtCore.QThread()
            self.data_monitor.moveToThread(self.data_monitor_thread)

            # Connect monitor loop start signal to monitor loop function
            print("Starting Data Monitor Thread")
            self.data_monitor_thread.started.connect(self.data_monitor.monitorLoop)
            self.data_monitor_thread.start()
            
            if self.app_main.getCachedParam("liveViewEnable"):
                # Create live view receiver object and thread, then move object into thread
                print("Creating Live View Receiver Thread")
                self.live_view_receiver = LiveViewReceiver(self, self.live_view_signal)
                self.live_view_receiver_thread = QtCore.QThread()
                self.live_view_receiver.moveToThread(self.live_view_receiver_thread)
                
                # Start the thread and connect start signal to receive_data()
                print("Starting Live View Receiver Thread")
                self.live_view_receiver_thread.started.connect(self.live_view_receiver.receive_data)
                self.live_view_receiver_thread.start()
            
        except Exception as e:
            print("LdpFemOdinDataReceiver got exception during configuration: %s" % e)

    def awaitCompletion(self):

            print("Waiting for frame processing to complete")
            while (self.data_monitor.running) and (self.app_main.abort_run == False):
                time.sleep(0.1)

            if self.app_main.abort_run:
                print("Run aborted by user")
                self.data_monitor.abort_run()
            else:
                print("Frame processor handled all frames, terminating data monitor thread")

            self.set_file_writing(False)

            # Get path of hdf file for the current run
            file_path = self.config_processor['hdf']['file']['path']
            file_name = self.config_processor['hdf']['file']['name']
            hdf_file_location = file_path + "/" + file_name + "_000001.h5"  # Remove hardcoded file ending when feature disabled
      
            # Open hdf file for metadata to be written to it      
            try:
                self.hdf_file = h5py.File(hdf_file_location, 'r+')
            except IOError as e:
                print("Failed to open HDF file with error: %s" % e)
                raise(e)
            
            # Create metadata group and add datasets to it
            metadata_group = self.hdf_file.create_group('metadata')
            self.metadata_handler = MetadataWriter(self.app_main.cached_params)
            self.metadata_handler.write_metadata(metadata_group)
            
            # Close hdf file
            self.hdf_file.close()
            
            self.data_monitor_thread.quit()
            self.data_monitor_thread.wait()

    def await_response(self, channel, timeout_ms=1000):
        reply = None
        pollevts = channel.poll(1000)
        if pollevts == IpcChannel.POLLIN:
            reply = IpcMessage(from_str=channel.recv())
        return reply

    def _next_msg_id(self):
        self._msg_id = (self._msg_id + 1) % self.MESSAGE_ID_MAX
        return self._msg_id

    def send_config_msg(self, channel, config):
        config_msg =  IpcMessage('cmd', 'configure', id=self._next_msg_id())
        config_msg.attrs['params'] = config
        channel.send(config_msg.encode())
        reply = self.await_response(channel)
  
    def send_status_cmd(self, channel):
        status_msg =  IpcMessage('cmd', 'status', id=self._next_msg_id())
        channel.send(status_msg.encode())
        reply = self.await_response(channel)
        return reply
    
    def do_shutdown_cmd(self, channel):
        ''' Sends a shutdown command to the channel that's passed
        '''
        shutdown_msg = IpcMessage('cmd', 'shutdown')
        channel.send(shutdown_msg.encode())
        self.await_response(channel)
        
    def shutdown_frame_receiver_processor(self):
        ''' Used when GUI is closed to stop FR & FP processes
        ''' 
        print("Shutting down frame receiver and frame processor")
        self.do_shutdown_cmd(self.fr_ctrl_channel)

        # Frame processor requires a shutdown config request to be sent
        self.send_config_msg(self.fp_ctrl_channel, {'shutdown': True})
        
    def set_file_writing(self, enable):
        ''' Enables or disables file writing (typically once a run has finished)
        '''
        self.config_processor['hdf']['frames'] = self.num_frames
        self.config_processor['hdf']['write'] = enable

        config_msg = IpcMessage('cmd', 'configure', id=self._next_msg_id())
        config_msg.attrs['params'] = {'hdf': self.config_processor['hdf']}
        
        print('Sending file writing {} command to frame processor'.format(
              'enable' if enable else 'disable'))

        self.fp_ctrl_channel.send(config_msg.encode())
        self.await_response(self.fp_ctrl_channel)


class OdinDataMonitor(QtCore.QObject):

    def __init__(self, parent):
        QtCore.QObject.__init__(self)

        self.parent = parent
        self.update_signal = parent.run_status_signal
        self.num_frames = parent.num_frames
        self.fr_ctrl_channel = parent.fr_ctrl_channel
        self.fp_ctrl_channel = parent.fp_ctrl_channel

        self.abort = False
        self.running = True

    def abort_run(self):
        self.abort = True
        self.running = False

    def monitorLoop(self):

        try:
            frames_received = -1
            frames_processed = -1
            data_recieved = -1
            images_written = -1

            frames_already_received = 0
            frames_already_processed = 0
            data_already_recieved = 0
            images_already_written = 0

            try:
                # Get values from previous runs in order to subtract them from current
                reply = self.parent.send_status_cmd(self.fr_ctrl_channel)

                if reply is not None:
                    frames_already_received = reply.attrs['params']['frames']['received']
            except Exception as e:
                print("Got exception requesting status from frame receiver: %s" % e, file=sys.stderr)

            try:
                # Get values from previous runs in order to subtract them from current
                reply = self.parent.send_status_cmd(self.fp_ctrl_channel)

                if reply is not None:
                    frames_already_processed = reply.attrs['params']['lpd']['frames_processed']
                    data_already_recieved = reply.attrs['params']['lpd']['bytes_received']
                    images_already_written = reply.attrs['params']['hdf']['frames_written']
            except Exception as e:
                print("Got exception requesting status from frame proccessor: %s" % e, file=sys.stderr)

            # Update UI values at regular intervals until all expected frames processed
            while frames_processed < self.num_frames and self.abort == False:
                # Status request for Frame Receiver
                reply = self.parent.send_status_cmd(self.fr_ctrl_channel)

                if reply is not None:
                    frames_received = (reply.attrs['params']['frames']['received'] - frames_already_received)

                # Status request for Frame Processor 
                reply = self.parent.send_status_cmd(self.fp_ctrl_channel)

                if reply is not None:
                    frames_processed = (reply.attrs['params']['lpd']['frames_processed'] - frames_already_processed)
                    data_recieved = (reply.attrs['params']['lpd']['bytes_received'] - data_already_recieved)
                    images_written = (reply.attrs['params']['hdf']['frames_written'] - images_already_written)

                print("Status message received: Rx: %s, Proc: %s, Data: %s, Images: %s" %(frames_received, frames_processed, data_recieved, images_written))

                run_status = LpdRunStatusContainer(frames_received, frames_processed, images_written, data_recieved)
                self.update_signal.emit(run_status)
                time.sleep(0.5)

            run_status = LpdRunStatusContainer(frames_received, frames_processed, images_written, data_recieved)
            self.update_signal.emit(run_status)
            self.running = False

        except Exception as e:
            print("Got exception in odin data monitor loop:%s" % e, file=sys.stderr)
            
class LiveViewReceiver(QtCore.QObject):

    def __init__(self, parent, live_view_signal):
        QtCore.QObject.__init__(self)
                
        self.parent = parent
        self.app_main = parent.app_main
        self.live_view_signal = live_view_signal
        
        self.live_view_divisor = parent.app_main.getCachedParam("liveViewDivisor")
        self.live_view_offset = parent.app_main.getCachedParam("liveViewOffset")
        self.run_number = parent.app_main.getCachedParam("runNumber")
        self.num_trains = parent.app_main.getCachedParam("numTrains")
        
        self.fp_ctrl_channel = parent.fp_ctrl_channel
    
    def receive_data(self):
        try:
            # Variables with preset values for later in the function
            endpoint_url = "tcp://127.0.0.1:5020"
            timeout = 1000
            data_polling = True
            current_image = 0
            
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.setsockopt(zmq.SUBSCRIBE, "")
            socket.connect(endpoint_url)
            
            # Create poller and register socket with the poller
            poller = zmq.Poller()
            poller.register(socket)
            
            # Polling loop - active while data is being sent via ZMQ
            while data_polling is True:
                socks = dict(poller.poll(timeout))
                
                if socket in socks and socks[socket] == zmq.POLLIN:
                    header = socket.recv_json()
                    msg = socket.recv()
                    array = np.fromstring(msg, dtype=header['dtype'])
                    frame_data = array.reshape([int(header['shape'][0]), int(header['shape'][1])])
                    
                    # 10 needs to be changed for a variable containing number of images in a frame
                    if header['frame_num'] % 10 == 0:
                        current_image = 0

                    # Signal live view update at appropriate rate if enabled
                    if (header['frame_num'] - self.live_view_offset) % self.live_view_divisor == 0:
                        try:
                            reply = self.parent.send_status_cmd(self.fp_ctrl_channel)
                            if reply is not None:
                                frames_processed = reply.attrs['params']['lpd']['frames_processed']
                        except Exception as e:
                            print("Got exception requesting status from frame proccessor: %s" % e, file=sys.stderr)
                        
                        lpd_image = LpdImageContainer(self.run_number, frames_processed, current_image)
                        lpd_image.image_array = frame_data.copy()
                        self.live_view_signal.emit(lpd_image)
                        
                    if header['frame_num'] % 20 == 0:
                        print("[Socket] received header of frame number: {}".format(header['frame_num']))
                        print("Received body of length: {}".format(len(msg)))
                    
                    current_image += 1     
                else:
                    # Timed out, break out of loop
                    data_polling = False
                    
            print("Left polling loop")
        except Exception as e:
            print("Got exception when receiving data using ZeroMQ:%s" % e)
            
            
            
            
            
