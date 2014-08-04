
'''
Created on Apr 19, 2013

@author: tcn45
'''

from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from LpdFemGuiAnalysis import *
import logging

from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainTestTab(QtGui.QMainWindow):
    # Inheritance required for super() line within __init__() function
    '''
    Helper class to manager TEST tab in main window
    '''

    RHS_MODULE = 15
    LHS_MODULE = 14 #0 # 0 is the REAL LHS module !

    fileNameSignal = QtCore.pyqtSignal(str)
    fileReadySignal = QtCore.pyqtSignal()
    messageSignal = QtCore.pyqtSignal(object, bool)
    configDeviceSignal = QtCore.pyqtSignal(str)
    
    def __init__(self, appMain, mainWindow):

        super(LpdFemGuiMainTestTab, self).__init__()    # Required for pyqtSignal
        '''
        Constructor
        '''
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        # Disable test button from start
        self.ui.pixelCheckBtn.setEnabled(False)
        self.msgPrint = self.testMsgPrint   # Use MessageBox element within this tab
        
        self.ui.moduleLhsSel.setChecked(True)
                
        self.moduleNumber   = LpdFemGuiMainTestTab.LHS_MODULE   # LHS = 0, RHS = 15
        self.fileName       = ""
        self.image          = 0
        self.train          = 0
 
        # Debugging purposes, have a think about when/how naming the log file..
        self.logFileName = "/u/ckd27546/workspace/lpdSoftware/log_file_%s.log" % time.strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(filename=self.logFileName, level=logging.INFO)
        print >> sys.stderr, "self.logFileName: ", self.logFileName

        # Connect signals and slots
        QtCore.QObject.connect(self.ui.pixelCheckBtn,         QtCore.SIGNAL("clicked()"),           self.pixelCheckTest)   # "Pixel Check"
        QtCore.QObject.connect(self.ui.testConfigBtn,         QtCore.SIGNAL("clicked()"),           self.testConfigure) # "TestConfig"
        QtCore.QObject.connect(self.ui.testRunBtn,            QtCore.SIGNAL("clicked()"),           self.testRun)       # "TestRun"
        QtCore.QObject.connect(self.ui.operatorEdit,          QtCore.SIGNAL("editingFinished()"),   self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,      QtCore.SIGNAL("editingFinished()"),   self.moduleNumberUpdate)
        QtCore.QObject.connect(self.ui.moduleTypeButtonGroup, QtCore.SIGNAL("buttonClicked(int)"),  self.moduleTypeUpdate)
        QtCore.QObject.connect(self.ui.readCurrentBtn,        QtCore.SIGNAL("clicked()"),           self.testReadCurrent)
        
        # Allow LpdFemDataReceiver to communicate new filename (via LpdFemGui, LpdFemGuiMainWindow)
        self.fileNameSignal.connect(self.updateFileName)
        self.fileReadySignal.connect(self.fileReadyToBeProcessed)
        self.fileName = ""
        self.configDeviceSignal.connect(self.configDeviceMessage)
        # Let LpdFemGuiPowerTesting communicate results:
        self.messageSignal.connect(self.testMsgPrint)

        
        # Create the analysis window but don't show it initially
        self.analysis = LpdFemGuiAnalysis(self.messageSignal)

    def __del__(self):
        
        # Close the log file upon program exit? (Redundant?)
        pass
    
    def testReadCurrent(self):
        
        self.analysis.powerTesting.readCurrent(self.moduleNumber)
        
    def pixelCheckTest(self):
        ''' Perform analysis of data file, then check pixel health '''
        self.analysis.performAnalysis(self.train, self.image, self.moduleNumber, self.fileName)
        # Disable test button until next filename available
        self.ui.pixelCheckBtn.setEnabled(False)

    def fileReadyToBeProcessed(self):
        ''' When fileReadySignal received, enable test button '''
        self.testMsgPrint("File %s ready to be processed" % self.fileName)
        self.testMsgPrint("Acquisition completed")
        self.ui.pixelCheckBtn.setEnabled(True)
        
    def configDeviceMessage(self, message):

        self.testMsgPrint(message)
        
    def testConfigure(self):
        
        self.testMsgPrint("Configuring device ...")
        self.mainWindow.daqTab.deviceConfigure()
#        self.testMsgPrint("Device configured OK")

    def testRun(self):
        
        self.testMsgPrint("Running Acquisition ...")
        self.mainWindow.daqTab.deviceRun()

    def updateFileName(self, filename):

        self.fileName = str(filename)
        self.testMsgPrint("Debug: File %s being created.." % self.fileName)

    def operatorUpdate(self):

        QtCore.qDebug("LpdFemGuiMainTestTab, You changed operatorEdit (to be: " + self.ui.operatorEdit.text() + ")")
    
    def moduleNumberUpdate(self):

        QtCore.qDebug("LpdFemGuiMainTestTab, You changed moduleNumberEdit (to be: " + self.ui.moduleNumberEdit.text() + ")")

    def moduleTypeUpdate(self):
        ''' Update module selection (right side versus left side) according to GUI choice made '''
        
        if self.ui.moduleLhsSel.isChecked():
            self.msgPrint("LHS module selected")
            self.moduleNumber = LpdFemGuiMainTestTab.LHS_MODULE

        elif self.ui.moduleRhsSel.isChecked():
            self.msgPrint("RHS module selected")
            self.moduleNumber = LpdFemGuiMainTestTab.RHS_MODULE

    def testMsgPrint(self, msg, bError=False):
        ''' Print message to this tab's message box, NOT main tab's '''
        
#        # Debugging info:
#        print >> sys.stderr, "LpdFemGuiMainTestTab testMsgPrint function called"
        
        constructedMessage = "%s %s" % (time.strftime("%H:%M:%S"), str(msg))
        self.ui.testMessageBox.appendPlainText(constructedMessage)
        self.ui.testMessageBox.verticalScrollBar().setValue(self.ui.testMessageBox.verticalScrollBar().maximum())
        self.ui.testMessageBox.repaint()
        self.appMain.app.processEvents()
        # Log message as error if flagged as such
        if bError:
            logging.error(constructedMessage)
        else:
            logging.info(constructedMessage)
        
