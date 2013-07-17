'''
Created on Jun 06, 2013

    Common data receiver. User need only specify if it's data from:
    0: super module
    1: single ASIC    (redundant?)
    2: 2-tile module
    3: stand-alone fem
    (4: raw data ?)

@author: ckd27546
'''

from PyQt4 import QtCore, QtGui
from LpdFemGui.utilities import *
#from LpdFemGui.LpdFemGuiLiveViewWindow import *
from LpdFemGui.LpdFemDataReceiver import *
from LpdFemGui.LpdFemGui import *

import sys

#import numpy as np


class LpdDataDisplay(QtGui.QDialog):

    #From LpdFemGuiMainWindow
    runStatusSignal = QtCore.pyqtSignal(object)

    def __init__(self, femHost=None, femPort=None, asicModuleType=None):
        #TODO: Pass any argument(s) to superclass?
        super(LpdDataDisplay, self).__init__()
        
        print "femHost = %s, femPort = %s, asicModuleType = %s" % (femHost, femPort, asicModuleType)

        #TODO: Expand dictionary with all relevant keys and set actual values..!
        self.cachedParams = {'runNumber' : 0,
                             'fileWriteEnable' : 0,
                             'dataFilePath' : 0,
                             'numTrains' : 2,
                             'liveViewEnable' : 1,
                             'liveViewDivisor' : 1,
                             'liveViewOffset' : 0,}

        #TODO: Make accessible instead of hard code these values? 
        #Define current loaded configuration 
        self.loadedConfig= {'tenGig0DestIp':    '10.0.0.1',
                            'tenGig0DestPort':  61649}
        
        # Change IP and Port if these have been provided from command line
        if femHost != None:
            self.loadedConfig['tenGig0DestIp'] = femHost
        if femPort != None:
            self.loadedConfig['tenGig0DestPort'] = femPort
        
        #Show own object
        self.show()
        
        # Create the live view window but don't show it
        self.liveViewWindow = LpdFemGuiLiveViewWindow()
        #TODO: Show window from the word go?
        self.liveViewWindow.show()

        # Abort run flag used to signal to data receiver
        self.abortRun = False

        #From LpdFemGuiMainWindow.__init__()
        
        # Connect run status update function to signal to data recevier to push updates
        self.runStatusSignal.connect(self.runStatusUpdate)

#        # Connect runStateUpdate function to signal to allow other non-GUI threads to push state updates
#        self.runStateSignal.connect(self.runStateUpdate)
        
    def runStateUpdate(self):
        ''' Copied from LpdFemGuiMainWindow - Do nothing '''
        pass
#        self.daqTab.runStateUpdate(self.appMain.deviceState)
#        self.updateEnabledWidgets()


    #From LpdFemGuiMainDaqTab:
    def runStatusUpdate(self, runStatus):

        if runStatus.framesReceived > 0:
            print "frames Rx'd, processed: %3i, %3i" % (runStatus.framesReceived, runStatus.framesProcessed),
            print "imagesProcessed: %3i" % runStatus.imagesProcessed
#        self.ui.frameRx.setText(str(runStatus.framesReceived))
#        self.ui.frameProc.setText(str(runStatus.framesProcessed))
#        self.ui.imageProc.setText(str(runStatus.imagesProcessed))
#        
#        kB = 1024
#        MB = kB*1024
#        GB = MB*1024
#        
#        dataRxText = ""
#        if (runStatus.dataBytesReceived < kB):
#            dataRxText = "{:d} B".format(runStatus.dataBytesReceived)
#        elif (runStatus.dataBytesReceived < MB):
#            dataRxText = "{:.1f} kB".format(runStatus.dataBytesReceived / kB)
#        elif (runStatus.dataBytesReceived < GB):
#            dataRxText = "{:.1f} MB".format(runStatus.dataBytesReceived / MB)
#        else:
#            dataRxText = "{:.1f}G B".format(runStatus.dataBytesReceived / GB)
#            
#        self.ui.dataRx.setText(dataRxText)
        
    def deviceConfigure(self):
        '''
            Selected bits taken from LpdFemGui.deviceConfigure()..
        '''

        # Set up number of frames based on cached parameter value of number of trains
        self.numFrames = self.cachedParams['numTrains']

        # Store values of data receiver address, port and number of frames
        try:
            self.dataListenAddr = self.loadedConfig['tenGig0DestIp']
            self.dataListenPort = self.loadedConfig['tenGig0DestPort']
        except Exception as e:
            print >> sys.stderr, "Got exception storing reaodut config variables", e 


    def deviceRun(self):
        '''
            Contains only some of the stuff from LpdFemGui.deviceRun()..
        '''
        
        # Create an LpdFemDataReceiver instance to launch readout threads
        try:
            dataReceiver = LpdFemDataReceiver(self.liveViewWindow.liveViewUpdateSignal, self.runStatusSignal, 
                                              self.dataListenAddr, self.dataListenPort, self.numFrames, self.cachedParams, self)
        except Exception as e:
            self.msgPrint("ERROR: failed to create data receiver: %s" % e)
#            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Wait for the data receiver threads to complete
        try:
            dataReceiver.awaitCompletion()
        except Exception as e:
            self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)


    def msgPrint(self, message):
        '''
            Print message to console (kinda redundant but useful while I add functions from LpdFemGui's (various) classes..)
        '''
        #self.mainWindow.messageSignal.emit(message)
        print message

if __name__ == '__main__':

    #print sys.argv
    # Check command line for host and port info    
    if len(sys.argv) == 4:
        femHost = sys.argv[1]
        femPort = int(sys.argv[2])
        asicModuleType = int(sys.argv[3])
    else:
        # Nothing provided from command line; Use defaults
        femHost = None
        femPort = None
        asicModuleType = 0  # Assume super module, for now..

    app = QtGui.QApplication(sys.argv)
    widget = LpdDataDisplay(femHost, femPort, asicModuleType)
#    widget.show()
    
    print "devicConfigure().."
    
    widget.deviceConfigure()
    
    print "deviceRun().."
    widget.deviceRun()
    
#    # Quit application; Prevent stale code remaining in memory..?
#    print "app.quit()"
#    app.quit()

    sys.exit(app.exec_())
