
'''
Created on Apr 19, 2013

@author: tcn45
'''

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *

from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from LpdAsicTester import *
import logging, logging.handlers

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

    messageSignal        = QtCore.pyqtSignal(object, bool)
    loggingSignal        = QtCore.pyqtSignal(str, bool)
    configDeviceSignal   = QtCore.pyqtSignal(str)
    femConnectionSignal  = QtCore.pyqtSignal(bool)

    def __init__(self, appMain, mainWindow):

        super(LpdFemGuiMainTestTab, self).__init__()    # Required for pyqtSignal
        '''
        Constructor
        '''
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        # Disable GUI components from start
        self.ui.asicBondingBtn.setEnabled(False)
        self.ui.sensorBondingBtn.setEnabled(False)
        self.ui.operatorEdit.setEnabled(False)
        self.ui.moduleNumberEdit.setEnabled(False)
        self.ui.commentEdit.setEnabled(False)
        self.ui.moduleLhsSel.setEnabled(False)
        self.ui.moduleRhsSel.setEnabled(False)

        self.msgPrint = self.testMsgPrint   # Use MessageBox element within this tab
        
        self.ui.moduleLhsSel.setChecked(True)
        self.moduleNumber   = LpdFemGuiMainTestTab.LHS_MODULE   # LHS = 0, RHS = 15
        self.moduleString   = ""
        self.setModuleType(self.moduleNumber)

        self.image          = 0
        self.train          = 0

        self.pathStem = "/data/lpd/testGui/"   #"/u/ckd27546/workspace/tinkering/"
        (self.logger, self.hdl) = (None, None)

        # Connect signals and slots
        QtCore.QObject.connect(self.ui.operatorEdit,          QtCore.SIGNAL("editingFinished()"),   self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,      QtCore.SIGNAL("editingFinished()"),   self.moduleNumberUpdate)
        QtCore.QObject.connect(self.ui.moduleTypeButtonGroup, QtCore.SIGNAL("buttonClicked(int)"),  self.moduleTypeUpdate)
        QtCore.QObject.connect(self.ui.asicBondingBtn,        QtCore.SIGNAL("clicked()"),           self.asicBondingTest)   # "ASIC Bonding"
        QtCore.QObject.connect(self.ui.sensorBondingBtn,      QtCore.SIGNAL("clicked()"),           self.sensorBondingTest) # "Sensor Bonding"
        
        # Allow LpdFemGuiMainDaqTab to signal Device configuration ok/fail
        self.configDeviceSignal.connect(self.configDeviceMessage)
        # Allow LpdFemGuiMainDaqTab to signal whether fem [dis]connected
        self.femConnectionSignal.connect(self.femConnectionStatus)
        # Let LpdFemGuiPowerTesting (and others) communicate results:
        self.messageSignal.connect(self.testMsgPrint)

    def __del__(self):
        
        pass

    def sensorBondingTest(self):
        ''' Execute Sensor Bonding Tests - specified on page 4 of the documentation '''
        # Lock tab's GUI components during test execution
        self.femConnectionStatus(False)
        try:
            # Also lock DAQ tab during text execution..
            self.appMain.mainWindow.ui.runGroupBox.setEnabled(False)
            self.appMain.mainWindow.ui.daqTab.setEnabled(False)
        except Exception as e:
            print >> sys.stderr, "Exception trying to lock DAQ tab: %s" % e
            return

        # Set up logger unless already set up
        if self.logger is None:
            self.createLogger()
        
        self.msgPrint("Executing Sensor Bonding Tests..")
        self.dumpGuiFieldsToLog()
        moduleDescription = str(self.ui.moduleNumberEdit.text())
        self.appMain.asicTester.setModuleDescription(moduleDescription)
        self.mainWindow.executeAsyncCmd('Executing Sensor Bonding Tests..', 
                                        partial(self.appMain.asicTester.executeSensorBondingTest, self.moduleNumber),
                                        self.sensorBondingTestDone)

    def sensorBondingTestDone(self):
        
        self.msgPrint("Finished testing ASIC Sensor Bonding")
        # Lock run button to prevent DAQ tab running with (contaminated) settings
        self.ui.runBtn.setEnabled(False)
        # Unlock tab's GUI components after test completed
        self.femConnectionStatus(True)
        try:
            # Also unlock DAQ tab during text execution..
            self.appMain.mainWindow.ui.runGroupBox.setEnabled(True)
            self.appMain.mainWindow.ui.daqTab.setEnabled(True)
        except Exception as e:
            print >> sys.stderr, "sensorBondingTestDone() Exception trying to unlock DAQ tab: %s" % e

    def asicBondingTest(self):
        ''' Execute ASIC Bonding Tests - specified on page 3 of the documentation '''
        # Lock tab's GUI components during test execution
        self.femConnectionStatus(False)
        try:
            # Also lock DAQ tab during text execution..
            self.appMain.mainWindow.ui.runGroupBox.setEnabled(False)
            self.appMain.mainWindow.ui.daqTab.setEnabled(False)
        except Exception as e:
            print >> sys.stderr, "Exception trying to lock DAQ tab: %s" % e
            return

        # Set up logger unless already set up
        if self.logger is None:
            self.createLogger()
            
        self.msgPrint("Executing ASIC Bond tests..")

        self.dumpGuiFieldsToLog()
        moduleDescription = str(self.ui.moduleNumberEdit.text())
        self.appMain.asicTester.setModuleDescription(moduleDescription)
        self.mainWindow.executeAsyncCmd('Executing ASIC Bond tests..', 
                                        partial(self.appMain.asicTester.executeAsicBondingTest, self.moduleNumber),
                                        self.asicBondingTestDone)
    
    def asicBondingTestDone(self):

        self.msgPrint("ASIC Bonding Tests Concluded")
        # Lock run button to prevent DAQ tab running with (contaminated) settings
        self.ui.runBtn.setEnabled(False)
        # Unlock tab's GUI components after test completed
        self.femConnectionStatus(True)
        try:
            # Also unlock DAQ tab during text execution..
            self.appMain.mainWindow.ui.runGroupBox.setEnabled(True)
            self.appMain.mainWindow.ui.daqTab.setEnabled(True)
        except Exception as e:
            print >> sys.stderr, "asicBondingTestDone() Exception trying to unlock DAQ tab: %s" % e

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdFemGuiMainTestTab.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdFemGuiMainTestTab.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)
        
    def configDeviceMessage(self, message):
        ''' Receives configuration ok/fail message '''
        self.testMsgPrint(message)
        
    def femConnectionStatus(self, bConnected):
        ''' Enables/Disable testTab's components according to bConnected argument '''
        self.ui.asicBondingBtn.setEnabled(bConnected)
        self.ui.sensorBondingBtn.setEnabled(bConnected)
        self.ui.operatorEdit.setEnabled(bConnected)
        self.ui.moduleNumberEdit.setEnabled(bConnected)
        self.ui.commentEdit.setEnabled(bConnected)
        self.ui.moduleLhsSel.setEnabled(bConnected)
        self.ui.moduleRhsSel.setEnabled(bConnected)

    def warning(self):
        ''' Testing using QMessageBox '''   # Not currently used
        ret = QMessageBox.warning(self, "Power Cycle",
                '''Ensure power switched on before  clicking ok or click cancel.''',
                QMessageBox.Ok, QMessageBox.Cancel);
        if ret == QMessageBox.Ok:
            print >> sys.stderr, "Answer was Ok"
        elif ret == QMessageBox.Cancel:
            print >> sys.stderr, "Answer was Cancel"
        else:
            print >> sys.stderr, "Error: Unknown answer"
 
    def createLogger(self):
        ''' Create logger (and its' folder, if it does not exist), return logger and its' path
            Adjusted from example:
            http://rlabs.wordpress.com/2009/04/09/python-closing-logging-file-getlogger/ '''

        timestamp = time.time()
        st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        #fileName = self.pathStem + "%s_%s/testResults.log" % (st, self.moduleString)
        fileName = self.pathStem + "%s/testResults.log" % st

        # Check whether logger already set up
        if self.logger is not None:
            # Logger already exists, remove it
            self.logger.removeHandler(self.hdl)
            self.hdl.close()
        # Setup logger
        self.logger = logging.getLogger('testLogger')
        # Strip filename from fileName
        filePathTuple = os.path.split(fileName)
        filePath = filePathTuple[0] + '/'
        # Create directory if it doesn't exist
        if not os.path.exists(filePath):
            os.makedirs( filePath )
        # Create and set handler, formatter
        self.hdl = logging.handlers.RotatingFileHandler(fileName, maxBytes=2097152, backupCount=5)
        #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        formatter = logging.Formatter('%(levelname)s %(message)s')
        self.hdl.setFormatter(formatter)
        self.logger.addHandler(self.hdl)
        self.logger.setLevel(logging.DEBUG)
        # Signal new file path
        self.appMain.asicWindow.logPathSignal.emit(filePath)

    def operatorUpdate(self):

        #QtCore.qDebug("LpdFemGuiMainTestTab, You changed operatorEdit (to be: " + self.ui.operatorEdit.text() + ")")
        pass
    
    def moduleNumberUpdate(self):

        #QtCore.qDebug("LpdFemGuiMainTestTab, You changed moduleNumberEdit (to be: " + self.ui.moduleNumberEdit.text() + ")")
        pass

    def moduleTypeUpdate(self):
        ''' Update module selection (right side versus left side) according to GUI choice made '''
        
        if self.ui.moduleLhsSel.isChecked():
            self.msgPrint("LHS module selected")
            self.moduleNumber = LpdFemGuiMainTestTab.LHS_MODULE
            #self.setModuleType(self.moduleNumber)

        elif self.ui.moduleRhsSel.isChecked():
            self.msgPrint("RHS module selected")
            self.moduleNumber = LpdFemGuiMainTestTab.RHS_MODULE
            
        self.setModuleType(self.moduleNumber)
        self.appMain.asicWindow.moduleSignal.emit(self.moduleNumber)
            
    def testMsgPrint(self, msg, bError=False):
        ''' Print message to this tab's message box, NOT main tab's '''
        
        # Setup logger unless already set up
        if self.logger is None:
            self.createLogger()

        constructedMessage = "%s %s" % (time.strftime("%H:%M:%S"), str(msg))
        # Log message as error if flagged as such
        if bError:
            self.logger.error(constructedMessage)
        else:
            self.logger.info(constructedMessage)

        self.ui.testMessageBox.appendPlainText(constructedMessage)
        self.ui.testMessageBox.verticalScrollBar().setValue(self.ui.testMessageBox.verticalScrollBar().maximum())
        self.ui.testMessageBox.repaint()
        self.appMain.app.processEvents()

    def dumpGuiFieldsToLog(self):
        
        self.testMsgPrint("Logging Operator: '%s'" % str(self.ui.operatorEdit.text()))
        self.testMsgPrint("Logging Module: '%s'" % str((self.ui.moduleNumberEdit.text()) + self.moduleString))
        self.testMsgPrint("Logging Comment: '%s'" % str(self.ui.commentEdit.text()))
