'''
Created on Apr 19, 2013

@author: tcn45
'''

from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainDaqTab(object):
    '''
    Helper class to manager DAQ tab in main window
    '''

    def __init__(self, appMain, mainWindow):
        '''
        Constructor
        '''
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.mainWindow.msgPrint
        
        # Initialise default fields based on appMain object cached parameters
        self.ui.readoutParamEdit.setText(self.appMain.getCachedParam('readoutParamFile'))
        self.ui.fastParamEdit.setText(self.appMain.getCachedParam('cmdSequenceFile'))
        self.ui.slowParamEdit.setText(self.appMain.getCachedParam('setupParamFile'))
        self.ui.dataPathEdit.setText(self.appMain.getCachedParam('dataFilePath'))
        self.ui.numTrainsEdit.setText(str(self.appMain.getCachedParam('numTrains')))
#         if self.appMain.getCachedParam('externalTrigger') == True:
#             self.ui.externalTriggerSel.setCheckState(QtCore.Qt.Checked)
#         else:
#             self.ui.externalTriggerSel.setCheckState(QtCore.Qt.Unchecked)
        self.ui.triggerDelayEdit.setText(str(self.appMain.getCachedParam('triggerDelay')))
        
        self.ui.fileWriteSel.setCheckState(checkButtonState(self.appMain.getCachedParam('fileWriteEnable')))         
        self.ui.liveViewSel.setCheckState(checkButtonState(self.appMain.getCachedParam('liveViewEnable')))
        self.ui.liveViewDivisorEdit.setText(str(self.appMain.getCachedParam('liveViewDivisor')))
        self.ui.liveViewOffsetEdit.setText(str(self.appMain.getCachedParam('liveViewOffset')))
        self.ui.shutterSel.setCheckState(checkButtonState(self.appMain.getCachedParam('arduinoShutterEnable')))
        self.ui.multiRunSel.setCheckState(checkButtonState(self.appMain.getCachedParam('multiRunEnable')))
        self.ui.multiRunEdit.setText(str(self.appMain.getCachedParam('multiRunNumRuns')))
        # Support scanning a range of trigger delays
        self.ui.triggerDelayIncrementEdit.setText(str(self.appMain.getCachedParam('triggerDelayIncrement')))

        serialPort = self.appMain.getCachedParam('arduinoShutterPort')

        fbkOverride = self.appMain.getCachedParam('femAsicPixelFeedbackOverride')
        if fbkOverride == 1:
            self.ui.pixelFbk5Sel.setChecked(True)
        elif fbkOverride == 0:
            self.ui.pixelFbk50Sel.setChecked(True)
        else:
            pass
            
        gainOverride = self.appMain.getCachedParam('femAsicGainOverride')
        if gainOverride == 0:
            self.ui.gainModeAutoSel.setChecked(True)
        elif gainOverride == 100:
            self.ui.gainModex100Sel.setChecked(True)
        elif gainOverride == 10:
            self.ui.gainModex10Sel.setChecked(True)
        elif gainOverride == 1:
            self.ui.gainModex1Sel.setChecked(True)
        else:
            pass

        self.runStateUpdate(self.appMain.deviceState)

        # Connect signals and slots
        QtCore.QObject.connect(self.ui.readoutParamBtn, QtCore.SIGNAL("clicked()"), self.readoutParamFileSelect)
        QtCore.QObject.connect(self.ui.slowParamBtn,    QtCore.SIGNAL("clicked()"), self.slowParamFileSelect)
        QtCore.QObject.connect(self.ui.fastParamBtn,    QtCore.SIGNAL("clicked()"), self.fastParamFileSelect)
        QtCore.QObject.connect(self.ui.dataPathBtn,     QtCore.SIGNAL("clicked()"), self.dataPathSelect)
        QtCore.QObject.connect(self.ui.configBtn,       QtCore.SIGNAL("clicked()"), self.deviceConfigure)
        QtCore.QObject.connect(self.ui.runBtn,          QtCore.SIGNAL("clicked()"), self.deviceRun)
        QtCore.QObject.connect(self.ui.stopBtn,         QtCore.SIGNAL("clicked()"), self.deviceStop)
        QtCore.QObject.connect(self.ui.numTrainsEdit,   QtCore.SIGNAL("editingFinished()"), self.numTrainsUpdate)
#         QtCore.QObject.connect(self.ui.externalTriggerSel, QtCore.SIGNAL("toggled(bool)"), self.externalTriggerSelect)
        QtCore.QObject.connect(self.ui.triggerDelayEdit, QtCore.SIGNAL("editingFinished()"), self.triggerDelayUpdate)
        QtCore.QObject.connect(self.ui.fileWriteSel,    QtCore.SIGNAL("toggled(bool)"), self.fileWriteSelect)
        QtCore.QObject.connect(self.ui.liveViewSel,     QtCore.SIGNAL("toggled(bool)"), self.liveViewSelect)
        QtCore.QObject.connect(self.ui.liveViewDivisorEdit, QtCore.SIGNAL("editingFinished()"), self.liveViewDivisorUpdate)
        QtCore.QObject.connect(self.ui.liveViewOffsetEdit, QtCore.SIGNAL("editingFinished()"), self.liveViewOffsetUpdate)
        QtCore.QObject.connect(self.ui.pixelFbkButtonGroup, QtCore.SIGNAL("buttonClicked(int)"), self.pixelFbkOverrideUpdate)
        QtCore.QObject.connect(self.ui.gainOverrideButtonGroup, QtCore.SIGNAL("buttonClicked(int)"), self.gainOverrideUpdate)
        # Arduino Shutter
        QtCore.QObject.connect(self.ui.shutterSel,    QtCore.SIGNAL("toggled(bool)"), self.shutterSelect)
        # Multi-run parameters
        QtCore.QObject.connect(self.ui.multiRunSel,   QtCore.SIGNAL("toggled(bool)"), self.multiRunSelect)
        QtCore.QObject.connect(self.ui.multiRunEdit,  QtCore.SIGNAL("editingFinished()"), self.multiRunNumRunsUpdate)
        QtCore.QObject.connect(self.ui.triggerDelayIncrementEdit, QtCore.SIGNAL("editingFinished()"), self.triggerDelayIncrementUpdate)
        # LCLS mod: Disable external triggering - Do not allow user to change external trigger source
#         self.ui.externalTriggerSel.setEnabled(False)

    def updateEnabledWidgets(self):
        
        self.ui.runNumber.setText(str(self.appMain.getCachedParam('runNumber')))
        self.runStateUpdate(self.appMain.deviceState)        
        
    def readoutParamFileSelect(self):

        fileName = QtGui.QFileDialog.getOpenFileName(self.mainWindow, 'Select readout parameter file', self.appMain.defaultConfigPath, "XML Files (*.xml)")
        if fileName != "":
            self.appMain.setCachedParam('readoutParamFile', str(fileName))
            self.ui.readoutParamEdit.setText(fileName)
            self.mainWindow.updateEnabledWidgets()

    def slowParamFileSelect(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self.mainWindow, 'Select setup parameter file', self.appMain.defaultConfigPath, "XML Files (*.xml)")
        if fileName != "":
            self.appMain.setCachedParam('setupParamFile', str(fileName))
            self.ui.slowParamEdit.setText(fileName)
            self.mainWindow.updateEnabledWidgets()
        
    def fastParamFileSelect(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self.mainWindow, 'Select command sequence file', self.appMain.defaultConfigPath, "XML Files (*.xml)")
        if fileName != "":
            self.appMain.setCachedParam('cmdSequenceFile', str(fileName))
            self.ui.fastParamEdit.setText(fileName)
            self.mainWindow.updateEnabledWidgets()
        
    def dataPathSelect(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self.mainWindow, "Select data directory", self.appMain.getCachedParam('dataFilePath'))
        if dirName != "":
            self.appMain.setCachedParam('dataFilePath', str(dirName))
            self.ui.dataPathEdit.setText(dirName)
            self.mainWindow.updateEnabledWidgets()

    def numTrainsUpdate(self):
        numTrains = self.ui.numTrainsEdit.text()
        try:
            numTrainsVal = int(numTrains)
            self.appMain.setCachedParam('numTrains', numTrainsVal)
        except ValueError:
            self.ui.numTrainsEdit.setText(str(self.appMain.getCachedParam('numTrains')))
 
    def triggerDelayUpdate(self):

        delay = self.ui.triggerDelayEdit.text()
        try:
            delayVal = int(delay)
            self.appMain.setCachedParam('triggerDelay', delayVal) 
        except ValueError:
            self.ui.triggerDelayEdit.setText(str(self.appMain.getCachedParam('triggerDelay')))
        
    def triggerDelayIncrementUpdate(self):

        delayIncrement = self.ui.triggerDelayIncrementEdit.text()
        try:
            delayIncrementVal = int(delayIncrement)
            self.appMain.setCachedParam('triggerDelayIncrement', delayIncrementVal) 
        except ValueError:
            self.ui.triggerDelayIncrementEdit.setText(str(self.appMain.getCachedParam('triggerDelayIncrement')))

    def pixelFbkOverrideUpdate(self):

        fbkOverride = -1
        if self.ui.pixelFbk5Sel.isChecked():
            fbkOverride = 1
        elif self.ui.pixelFbk50Sel.isChecked():
            fbkOverride = 0
        else:
            self.msgPrint("Illegal pixel feedback override selection - should not happen")
            return

        self.appMain.setCachedParam('femAsicPixelFeedbackOverride', fbkOverride)
        self.mainWindow.updateEnabledWidgets()

    def gainOverrideUpdate(self):

        gainOverride = -1
        if self.ui.gainModeAutoSel.isChecked():
            gainOverride = 0
        elif self.ui.gainModex100Sel.isChecked():
            gainOverride = 100
        elif self.ui.gainModex10Sel.isChecked():
            gainOverride = 10
        elif self.ui.gainModex1Sel.isChecked():
            gainOverride = 1
        else:
            self.msgPrint("Illegal gain override selection - should not happen")
            return

        self.appMain.setCachedParam('femAsicGainOverride', gainOverride)
    
    def fileWriteSelect(self, state):
        self.appMain.setCachedParam('fileWriteEnable', state)
        self.mainWindow.updateEnabledWidgets()
        
    def liveViewSelect(self, state):
        self.appMain.setCachedParam('liveViewEnable', state)
        self.mainWindow.updateEnabledWidgets()
        
    def shutterSelect(self, state):
        
        self.appMain.setCachedParam('arduinoShutterEnable', state)
        # Hack, force user to hit configure before next run:
        self.appMain.deviceState = LpdFemGui.DeviceIdle
        self.mainWindow.updateEnabledWidgets()

    def multiRunSelect(self, state):

        self.appMain.setCachedParam('multiRunEnable', state)
        self.mainWindow.updateEnabledWidgets()

    def multiRunNumRunsUpdate(self):
        multiRunNumRuns = self.ui.multiRunEdit.text()
        try:
            multiRunNumRunsVal = int(multiRunNumRuns)

            self.appMain.setCachedParam('multiRunNumRuns', multiRunNumRunsVal)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.multiRunEdit.setText(str(self.appMain.getCachedParam('multiRunNumRuns')))

    def liveViewDivisorUpdate(self):
        liveViewDivisor = self.ui.liveViewDivisorEdit.text()
        try:
            liveViewDivisorVal = int(liveViewDivisor)
            
            if liveViewDivisorVal < 1:
                QtGui.QMessageBox.critical(self.mainWindow, "Illegal value", "The value of the live view divisor must be greater than zero")
                self.ui.liveViewDivisorEdit.setText(str(self.appMain.getCachedParam('liveViewDivisor')))
            else:
                self.appMain.setCachedParam('liveViewDivisor', liveViewDivisorVal)
                self.mainWindow.updateEnabledWidgets()
            
        except ValueError:
            self.ui.liveViewDivisorEdit.setText(str(self.appMain.getCachedParam('liveViewDivisor')))

    def liveViewOffsetUpdate(self):
        liveViewOffset = self.ui.liveViewOffsetEdit.text()
        try:
            liveViewOffsetVal = int(liveViewOffset)
            self.appMain.setCachedParam('liveViewOffset', liveViewOffsetVal)
            self.mainWindow.updateEnabledWidgets()

        except ValueError:
            self.ui.liveViewOffsetEdit.setText(str(self.appMain.getCachedParam('liveViewOffset')))
        
    def deviceConfigure(self):

        self.mainWindow.executeAsyncCmd('Configuring device ...', self.appMain.deviceConfigure, self.configureDone)
        self.mainWindow.updateEnabledWidgets()

    def configureDone(self):

        if self.appMain.deviceState == LpdFemGui.DeviceReady:
            self.msgPrint("Device configured OK")
            if (self.appMain.asicTestingEnabled):
                self.appMain.mainWindow.testTab.configDeviceSignal.emit("Device configured OK")
        else:
            self.msgPrint("Failed to configure device")
            if (self.appMain.asicTestingEnabled):
                self.appMain.mainWindow.testTab.configDeviceSignal.emit("Failed to configure device")
            
        self.mainWindow.updateEnabledWidgets()
        
    def deviceRun(self):
        
        if (self.appMain.receiveDataInternally):
            # Show live view window if live view enabled
            if self.appMain.cachedParams['liveViewEnable']:
                self.appMain.liveViewWindow.show()
        
        self.mainWindow.executeAsyncCmd('Running acquisition ...', self.appMain.deviceRun, self.runDone)
        self.mainWindow.updateEnabledWidgets()
                
    def runDone(self):
        
        if self.appMain.deviceState == LpdFemGui.DeviceReady:
            self.msgPrint("Acquisition completed")
        else:
            self.msgPrint("Acquisition failed")
            
        self.mainWindow.updateEnabledWidgets()
        
    def deviceStop(self):
        
        self.msgPrint("Aborting acquisition ...")
        self.appMain.abortRun = True
        
    def runStateUpdate(self, deviceState):

        self.ui.runNumber.setText(str(self.appMain.getCachedParam('runNumber')))
        
        deviceStateMapping = {  LpdFemGui.DeviceDisconnected : 'Disconn',
                                LpdFemGui.DeviceIdle         : 'Idle',
                                LpdFemGui.DeviceConfiguring  : 'Configuring',
                                LpdFemGui.DeviceReady        : 'Ready',
                                LpdFemGui.DeviceRunning      : 'Running'
                              }
        
        if deviceState in deviceStateMapping:
            stateStr = deviceStateMapping[deviceState]
        else:
            stateStr = "Unknown"
        

        self.ui.runState.setText(stateStr)
        
    def runStatusUpdate(self, runStatus):
        
        self.ui.frameRx.setText(str(runStatus.framesReceived))
        self.ui.frameProc.setText(str(runStatus.framesProcessed))
        self.ui.imageProc.setText(str(runStatus.imagesProcessed))
        
        kB = 1024.0
        MB = kB*1024.0
        GB = MB*1024.0
        
        dataRxText = ""
        if (runStatus.dataBytesReceived < kB):
            dataRxText = "{:d} B".format(runStatus.dataBytesReceived)
        elif (runStatus.dataBytesReceived < MB):
            dataRxText = "{:.1f} kB".format(runStatus.dataBytesReceived / kB)
        elif (runStatus.dataBytesReceived < GB):
            dataRxText = "{:.1f} MB".format(runStatus.dataBytesReceived / MB)
        else:
            dataRxText = "{:.1f} GB".format(runStatus.dataBytesReceived / GB)
            
        self.ui.dataRx.setText(dataRxText)

      
