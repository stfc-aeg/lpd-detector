'''
Created on Apr 19, 2013

@author: tcn45
'''
from __future__ import print_function

from LpdDataContainers import *
from LpdFemClient.LpdFemClient import LpdFemClient
from LpdFemGui import *

import os, sys, time, socket, json
import numpy as np
from PyQt4 import QtCore

import h5py

import subprocess

from odin_data.ipc_channel import IpcChannel, IpcChannelException
from odin_data.ipc_message import IpcMessage, IpcMessageException

# Test if running python 3
is_python3 = sys.version_info > (3,)

#Display received data in plots
bDisplayPlotData = True

class LpdFemOdinDataReceiver():

    MESSAGE_ID_MAX = 2**32
    _msg_id = 0

    def __init__(self, runStatusSignal, numFrames, appMain):

        try:
            self.runStatusSignal = runStatusSignal
            self.numFrames = numFrames
            self.appMain = appMain

            # TODO: Launch FR

            # TODO: Launch FP

            # Create the appropriate IPC channels for receiver and proccessor
            print("Connecting to Frame Receiver's IPC Control Channel")
            self.frCtrlChannel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
            self.frCtrlChannel.connect(self.appMain.getCachedParam('odinFrCtrlChannel'))

            print("Connecting to Frame Proccessor's IPC Control Channel")
            self.fpCtrlChannel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
            self.fpCtrlChannel.connect(self.appMain.getCachedParam('odinFpCtrlChannel'))

            # TODO: Set num of images based on gui's readout config

            # Load Odin Data config
            print("Loading ODIN Data config from {}".format(self.appMain.getCachedParam('odinDataConfigFile')))
            with open(self.appMain.getCachedParam('odinDataConfigFile')) as configFile:
                self.odinDataConfig = json.load(configFile)
                self.configReceiver = self.odinDataConfig['receiver_default_config']
                self.configProcessor = self.odinDataConfig['processor_default_config']
                self.configProcessorPlugins = self.odinDataConfig['processor_plugins']

            # Set number of expected number of datasets to:
                # (Expected number of images) * (Expected number of datasets per image) + 1
                # The +1 is to prevent closing the file as soon as the first dataset of the last images is written,
                # allowing the rest time to arrive before closing the file
            numImages = (self.numFrames * self.configReceiver['decoder_config']['numimages'])
            numDatasets = len(self.configProcessor['hdf']['dataset']) 
            self.configProcessor['hdf']['frames'] = ((numImages * numDatasets) + 1)
            
            # Set path and filename of output file
            print("Setting Path & Filename of Output File")
            file_path = self.appMain.getCachedParam('dataFilePath')
            self.configProcessor['hdf']['file']['path'] = file_path
            
            run_number = self.appMain.getCachedParam('runNumber')            
            file_name = "lpdData-{:05d}.hdf5".format(run_number)
            self.configProcessor['hdf']['file']['name'] = file_name

            # Send Frame Receiver config
            print("Sending Frame Receiver Config")
            self.send_config_msg(self.frCtrlChannel, self.configReceiver)
            
            # Send Frame Receiver info to Frame Processor
            print("Sending Receiver connection info to Frame Processor")
            params = {'fr_setup' : self.configProcessor['fr_setup']}
            self.send_config_msg(self.fpCtrlChannel, params)
            
            # Sending Processor plugin configs
            if len(self.configProcessorPlugins):
                print("Sending Processor plugin chain config to Frame Processor")
                for plugin in self.configProcessorPlugins:
                    self.send_config_msg(self.fpCtrlChannel, plugin)

            # Send Frame Processor config
            print("Sending Frame Processor Config")
            self.send_config_msg(self.fpCtrlChannel, self.configProcessor)

            # TODO: replace with wait for FR/FP handshake to complete
            print("Waiting for Receiver/Processor handshake to complete")
            
            # Around 8 seconds before timeout
            timeout_attempts = 40
            request_number = 0
            
            while True:
                reply = self.send_status_cmd(self.fpCtrlChannel)
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
            self.dataMonitor = OdinDataMonitor(self)
            self.dataMonitorThread = QtCore.QThread()
            self.dataMonitor.moveToThread(self.dataMonitorThread)

            # Connect monitor loop start signal to monitor loop function
            print("Starting Data Monitor Thread")
            self.dataMonitorThread.started.connect(self.dataMonitor.monitorLoop)
            self.dataMonitorThread.start()

        except Exception as e:
            print("LdpFemOdinDataReceiver got exception during initialisation: %s" % e)

    def awaitCompletion(self):

            print("Waiting for frame processing to complete")
            while (self.dataMonitor.running) and (self.appMain.abortRun == False):
                time.sleep(0.1)

            if self.appMain.abortRun:
                print("Run aborted by user")
                self.dataMonitor.abortRun()
            else:
                print("Frame processor handled all frames, terminating data monitor thread")

            self.dataMonitorThread.quit()
            self.dataMonitorThread.wait()

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

class OdinDataMonitor(QtCore.QObject):

    def __init__(self, parent):

        QtCore.QObject.__init__(self)

        self.parent = parent
        self.updateSignal = parent.runStatusSignal
        self.numFrames = parent.numFrames
        self.frCtrlChannel = parent.frCtrlChannel
        self.fpCtrlChannel = parent.fpCtrlChannel

        self.abort = False
        self.running = True

    def abortRun(self):
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
                reply = self.parent.send_status_cmd(self.frCtrlChannel)

                if reply is not None:
                    frames_already_received = reply.attrs['params']['frames']['received']

            except Exception as e:
                print("Got exception requesting status from frame receiver: %s" % e, file=sys.stderr)

            try:

                # Get values from previous runs in order to subtract them from current
                reply = self.parent.send_status_cmd(self.fpCtrlChannel)

                if reply is not None:
                    frames_already_processed = reply.attrs['params']['lpd']['frames_processed']
                    data_already_recieved = reply.attrs['params']['lpd']['bytes_received']
                    images_already_written = reply.attrs['params']['hdf']['frames_written']

            except Exception as e:
                print("Got exception requesting status from frame proccessor: %s" % e, file=sys.stderr)

            # Update UI values at regular intervals until all expected frames processed
            while frames_processed < self.numFrames and self.abort == False:

                # Status request for Frame Receiver
                reply = self.parent.send_status_cmd(self.frCtrlChannel)

                if reply is not None:
                    frames_received = (reply.attrs['params']['frames']['received'] - frames_already_received)

                # Status request for Frame Processor 
                reply = self.parent.send_status_cmd(self.fpCtrlChannel)

                if reply is not None:
                    frames_processed = (reply.attrs['params']['lpd']['frames_processed'] - frames_already_processed)
                    data_recieved = (reply.attrs['params']['lpd']['bytes_received'] - data_already_recieved)
                    images_written = (reply.attrs['params']['hdf']['frames_written'] - images_already_written)

                print("Status message received: Rx: %s, Proc: %s, Data: %s, Images: %s" %(frames_received, frames_processed, data_recieved, images_written))

                runStatus = LpdRunStatusContainer(frames_received, frames_processed, images_written, data_recieved)
                self.updateSignal.emit(runStatus)
                time.sleep(0.5)

            runStatus = LpdRunStatusContainer(frames_received, frames_processed, images_written, data_recieved)
            self.updateSignal.emit(runStatus)
            self.running = False

        except Exception as e:
            print("Got exception in odin data monitor loop:%s" % e, file=sys.stderr)