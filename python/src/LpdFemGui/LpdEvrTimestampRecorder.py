import os, sys, time, socket, struct
import numpy as np
from PyQt4 import QtCore

class LpdEvrData(object):

    def __init__(self, initLen = 1):
        self.event = [] # np.empty(initLen, dtype=int)
        self.fiducial = [] # np.empty(initLen, dtype=int)
        self.timestamp = [] #np.empty(initLen, dtype=float)
        
class LpdEvrTimestampRecorder():

    def __init__(self, cachedParams, appMain):

        try:
            self.appMain = appMain

            self.evrData = LpdEvrData()
            self.timestampReceiver = TimestampMcastReceiver(cachedParams['evrMcastGroup'], cachedParams['evrMcastPort'],
                                                            cachedParams['evrMcastInterface'], self.evrData)
            self.timestampReceiverThread = QtCore.QThread()
            self.timestampReceiver.moveToThread(self.timestampReceiverThread)

            self.timestampReceiverThread.started.connect(self.timestampReceiver.receiveLoop)
            self.timestampReceiverThread.start()
            

        except Exception as e:
            print("LpdEvrTimestampRecorder got exception during initialisation: %s" % e)

    def awaitCompletion(self):

        print("Waiting for EVR timestamp receiver to complete")
        self.timestampReceiver.terminateLoop()
        while self.timestampReceiver.running == True:
            time.sleep(0.1)
        self.timestampReceiverThread.quit()
        self.timestampReceiverThread.wait()

class TimestampMcastReceiver(QtCore.QObject):

    def __init__(self, mcastGroup, mcastPort, interfaceAddr, evrData):

        super(TimestampMcastReceiver, self).__init__()

        self.runReceiver = True
        self.running = False
        self.daqEventsReceived = 0
        self.evrData = evrData

        # Create the socket
        self.mcastSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Tell the operating system to add the socket to the multicast group
        # on the specified interface
        self.mcastSock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, 
                 socket.inet_aton(mcastGroup)+socket.inet_aton(interfaceAddr))

        # Set timeout on socket to allow loop to interrupt
        self.mcastSock.settimeout(0.5)

        # Bind the socket to the server address
        self.mcastSock.bind((mcastGroup, mcastPort))

        print("EVR timestamp receiver thread listening on MCAST group %s port %d interface %s)" % \
            (mcastGroup, mcastPort, interfaceAddr))


    def receiveLoop(self):

        evrDatagramHdrFormat = '7I'
        evrDatagramHdrSize = struct.calcsize(evrDatagramHdrFormat)

        self.running = True

        while self.runReceiver:

            try:
                data, address = self.mcastSock.recvfrom(1024)
    
                cmdLen = len(data) - evrDatagramHdrSize
                dgFormat = evrDatagramHdrFormat + '%dB' % cmdLen
                unpackedDg = struct.unpack(dgFormat, data)
                (nsecs, secs, low, high, env, evr, ncmds) = unpackedDg[0:7]
                fiducial = high & 0x1ffff
                timestamp = float(secs) + (float(nsecs) / 1.0E9)
                is_event  = True if ((low >> 24)&0xF) == 0xC else False
                if is_event:
                    self.daqEventsReceived += 1
                    #is_eventStr = '*' if is_event else ' '
                    #print >> sys.stderr, '{:06d}  {:06d}  {:09d}.{:09d}  {:.09f}   {:s}'.format(evr, fiducial, secs, nsecs, timestamp, is_eventStr)
                    self.evrData.event.append(evr)
                    self.evrData.fiducial.append(fiducial)
                    self.evrData.timestamp.append(timestamp)

            except socket.timeout:
                pass

        print("EVR timestamp receiver finished after receiving %d DAQ events" % self.daqEventsReceived)

        self.mcastSock.close()
        self.running = False

    def terminateLoop(self):
        
        self.runReceiver = False

