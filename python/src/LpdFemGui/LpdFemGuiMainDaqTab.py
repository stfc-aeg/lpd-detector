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
        self.ui.fastParamEdit.setText(self.appMain.getCachedParam('fastParamFile'))
        self.ui.slowParamEdit.setText(self.appMain.getCachedParam('slowParamFile'))
        self.ui.dataPathEdit.setText(self.appMain.getCachedParam('dataFilePath'))
        self.ui.numTrainsEdit.setText(str(self.appMain.getCachedParam('numTrains')))
        if self.appMain.getCachedParam('externalTrigger') == True:
            self.ui.externalTriggerSel.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.externalTriggerSel.setCheckState(QtCore.Qt.Unchecked)
        self.ui.triggerDelayEdit.setText(str(self.appMain.getCachedParam('triggerDelay')))
        self.ui.pixelGainEdit.setText(str(self.appMain.getCachedParam('pixelGain')))
        
        self.ui.fileWriteSel.setCheckState(checkButtonState(self.appMain.getCachedParam('fileWriteEnable')))            
        self.ui.liveViewSel.setCheckState(checkButtonState(self.appMain.getCachedParam('liveViewEnable')))
        self.ui.liveViewDivisorEdit.setText(str(self.appMain.getCachedParam('liveViewDivisor')))
        self.ui.liveViewOffsetEdit.setText(str(self.appMain.getCachedParam('liveViewOffset')))

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
        QtCore.QObject.connect(self.ui.externalTriggerSel, QtCore.SIGNAL("toggled(bool)"), self.externalTriggerSelect)
        QtCore.QObject.connect(self.ui.triggerDelayEdit, QtCore.SIGNAL("editingFinished()"), self.triggerDelayUpdate)
        QtCore.QObject.connect(self.ui.pixelGainEdit,   QtCore.SIGNAL("editingFinished()"), self.pixelGainUpdate)
        QtCore.QObject.connect(self.ui.fileWriteSel,    QtCore.SIGNAL("toggled(bool)"), self.fileWriteSelect)
        QtCore.QObject.connect(self.ui.liveViewSel,     QtCore.SIGNAL("toggled(bool)"), self.liveViewSelect)
        QtCore.QObject.connect(self.ui.liveViewDivisorEdit, QtCore.SIGNAL("editingFinished()"), self.liveViewDivisorUpdate)
        QtCore.QObject.connect(self.ui.liveViewOffsetEdit, QtCore.SIGNAL("editingFinished()"), self.liveViewOffsetUpdate)
        
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
        fileName = QtGui.QFileDialog.getOpenFileName(self.mainWindow, 'Select slow parameter file', self.appMain.defaultConfigPath, "XML Files (*.xml)")
        if fileName != "":
            self.appMain.setCachedParam('slowParamFile', str(fileName))
            self.ui.slowParamEdit.setText(fileName)
            self.mainWindow.updateEnabledWidgets()
        
    def fastParamFileSelect(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self.mainWindow, 'Select fast parameter file', self.appMain.defaultConfigPath, "XML Files (*.xml)")
        if fileName != "":
            self.appMain.setCachedParam('fastParamFile', str(fileName))
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
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.numTrainsEdit.setText(str(self.appMain.getCachedParam('numTrains')))
            
    def externalTriggerSelect(self, state):
        self.msgPrint("External trigger select is %d" % int(state))
        self.appMain.setCachedParam('externalTrigger', state)
        self.mainWindow.updateEnabledWidgets()
        
    def triggerDelayUpdate(self):
        delay = self.ui.triggerDelayEdit.text()
        try:
            delayVal = int(delay)
            self.appMain.setCachedParam('triggerDelay', delayVal) 
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.triggerDelayEdit.setText(str(self.appMain.getCachedParam('triggerDelay')))
        
    def pixelGainUpdate(self):
        pixelGain = self.ui.pixelGainEdit.text()
        try:
            pixelGainVal = int(pixelGain)
            self.appMain.setCachedParam('pixelGain', pixelGainVal)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.pixelGainEdit.setText(str(self.appMain.getCachedParam('pixelGain')))
            
    def fileWriteSelect(self, state):
        self.appMain.setCachedParam('fileWriteEnable', state)
        self.mainWindow.updateEnabledWidgets()
        
    def liveViewSelect(self, state):
        self.appMain.setCachedParam('liveViewEnable', state)
        self.mainWindow.updateEnabledWidgets()
        
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
        else:
            self.msgPrint("Failed to configure device")
            
        self.mainWindow.updateEnabledWidgets()
        
    def deviceRun(self):
        
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
        
        self.msgPrint("Stop not yet implemented")
        
    def runStateUpdate(self, deviceState):

        self.ui.runNumber.setText(str(self.appMain.getCachedParam('runNumber')))
        
        deviceStateMapping = {  LpdFemGui.DeviceDisconnected : 'Disconn',
                                LpdFemGui.DeviceIdle         : 'Idle',
                                LpdFemGui.DeviceConfiguring  : 'Configuring',
                                LpdFemGui.DeviceReady        : 'Ready',
                                LpdFemGui.DeviceRunning      : 'Running'
                              }
        
        if deviceStateMapping.has_key(deviceState):
            stateStr = deviceStateMapping[deviceState]
        else:
            stateStr = "Unknown"
        

        self.ui.runState.setText(stateStr)
        
    def runStatusUpdate(self, runStatus):
        
        self.ui.frameRx.setText(str(runStatus.framesReceived))
        self.ui.frameProc.setText(str(runStatus.framesProcessed))
        self.ui.imageProc.setText(str(runStatus.imagesProcessed))
        
        kB = 1024
        MB = kB*1024
        GB = MB*1024
        
        dataRxText = ""
        if (runStatus.dataBytesReceived < kB):
            dataRxText = "{:d} B".format(runStatus.dataBytesReceived)
        elif (runStatus.dataBytesReceived < MB):
            dataRxText = "{:.1f} kB".format(runStatus.dataBytesReceived / kB)
        elif (runStatus.dataBytesReceived < GB):
            dataRxText = "{:.1f} MB".format(runStatus.dataBytesReceived / MB)
        else:
            dataRxText = "{.1f}G B".format(runStatus.dataBytesReceived / GB)
            
        self.ui.dataRx.setText(dataRxText)

      
