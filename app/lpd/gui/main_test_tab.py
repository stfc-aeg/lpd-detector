'''
Created on Apr 19, 2013

@author: tcn45
'''


import time
import sys
import os
from functools import partial
import logging, logging.handlers
import datetime
import main_power_tab
import re

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *

from asic_tester import LpdAsicTester


class LpdFemGuiMainTestTab(QtGui.QMainWindow):
    # Inheritance required for super() line within __init__() function
    '''
    Helper class to manager TEST tab in main window
    '''

    messageSignal        = QtCore.pyqtSignal(object, bool)
    loggingSignal        = QtCore.pyqtSignal(str, bool)
    configDeviceSignal   = QtCore.pyqtSignal(str)
    femConnectionSignal  = QtCore.pyqtSignal(bool)

    def __init__(self, app_main, mainWindow):

        super(LpdFemGuiMainTestTab, self).__init__()    # Required for pyqtSignal
        '''
        Constructor
        '''
        self.app_main = app_main
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        # Disable GUI components from start
        self.ui.asicBondingBtn.setEnabled(False)
        self.ui.sensorBondingBtn.setEnabled(False)
        self.ui.operatorEdit.setEnabled(False)
        self.ui.moduleNumberEdit.setEnabled(False)
        self.ui.commentEdit.setEnabled(False)
        self.miniConnectorSelect = False
        self.ui.analysisPathEdit.setEnabled(False)
        self.ui.analysisPathBtn.setEnabled(False)
        self.ui.testHvBiasEdit.setEnabled(False)
        self.ui.testHvBiasSetBtn.setEnabled(False)

        self.msgPrint = self.testMsgPrint   # Use MessageBox element within this tab
        
        self.moduleNumber   = LpdAsicTester.RHS_MODULE
        self.moduleString   = ""
        self.setModuleType(self.moduleNumber)
        self.ui.analysisPathEdit.setText(self.app_main.getCachedParam('analysisPdfPath'))
        self.ui.testHvBiasEdit.setText(str(self.app_main.getCachedParam('hvBiasVolts')))

        self.image          = 0
        self.train          = 0

        self.pathStem = "/data/lpd/testGui/"   #"/u/ckd27546/workspace/tinkering/"
        (self.logger, self.hdl) = (None, None)

        # Connect signals and slots
#        QtCore.QObject.connect(self.ui.operatorEdit,          QtCore.SIGNAL("editingFinished()"),   self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,      QtCore.SIGNAL("editingFinished()"),   self.moduleNumberUpdate)
        QtCore.QObject.connect(self.ui.connectorButtonGroup,  QtCore.SIGNAL("buttonClicked(int)"),  self.moduleTypeUpdate)
        QtCore.QObject.connect(self.ui.analysisPathBtn,       QtCore.SIGNAL("clicked()"),           self.analysisPathSelect)
        QtCore.QObject.connect(self.ui.testHvBiasSetBtn,      QtCore.SIGNAL("clicked()"),           self.hvBiasSetUpdate)
        QtCore.QObject.connect(self.ui.asicBondingBtn,        QtCore.SIGNAL("clicked()"),           self.asicBondingTest)   # "ASIC Bonding"
        QtCore.QObject.connect(self.ui.sensorBondingBtn,      QtCore.SIGNAL("clicked()"),           self.sensorBondingTest) # "Sensor Bonding"
        
        #Set the id for the connector radio buttons
        self.connector_btns = []
        for btn in range(1, 17):      
            btn_name = 'connectorBtn' + str(btn)
            connector_btn = getattr(self.ui, btn_name)
            self.connector_btns.append(connector_btn)
            self.ui.connectorButtonGroup.setId(connector_btn, btn)
            connector_btn.setEnabled(False)

        # Allow LpdFemGuiMainDaqTab to signal Device configuration ok/fail
        self.configDeviceSignal.connect(self.configDeviceMessage)
        # Allow LpdFemGuiMainDaqTab to signal whether fem [dis]connected
        self.femConnectionSignal.connect(self.femConnectionStatus)
        # Let LpdFemGuiPowerTesting (and others) communicate results:
        self.messageSignal.connect(self.testMsgPrint)


    def __del__(self):
        pass

    def asicBondingTest(self):
        ''' Execute ASIC Bonding Tests - specified on page 3 of the documentation '''
        self.bondingTest("ASIC")

    def sensorBondingTest(self):
        ''' Execute Sensor Bonding Tests - specified on page 4 of the documentation '''
        self.bondingTest("Sensor")

    def bondingTest(self, testType):
        ''' Execute Bonding Tests - specified on page 3-4 of the documentation '''
        # Lock tab's GUI components during test execution
        self.femConnectionStatus(False)
        try:
            # Also lock DAQ tab during text execution..
            self.app_main.mainWindow.ui.runGroupBox.setEnabled(False)
            self.app_main.mainWindow.ui.daqTab.setEnabled(False)

        except Exception as e:
            print >> sys.stderr, "Exception trying to lock DAQ tab: %s" % e
            return

        self.msgPrint("Executing %s Bonding Tests.." % testType)
        self.dumpGuiFieldsToLog()
        moduleDescription = str(self.ui.moduleNumberEdit.text())
        self.app_main.asic_tester.setModuleDescription(moduleDescription)
        self.app_main.asic_tester.setHvEditBox(self.ui.hvBiasEdit.text())
        self.mainWindow.executeAsyncCmd(("Executing %s Bonding Tests.." % testType), 
                                        partial(self.app_main.asic_tester.executeBondingTest,self.moduleNumber, self.originalConnectorId, testType),
                                        partial(self.bondingTestDone, testType))


    def bondingTestDone(self, testType):
        
        self.msgPrint("Finished %s Bonding tests" % testType)
        # Lock run button to prevent DAQ tab running with (contaminated) settings
        self.ui.runBtn.setEnabled(False)
        # Unlock tab's GUI components after test completed
        self.femConnectionStatus(True)
        try:
            # Also unlock DAQ tab during text execution..
            self.app_main.mainWindow.ui.runGroupBox.setEnabled(True)
            self.app_main.mainWindow.ui.daqTab.setEnabled(True)

        except Exception as e:
            print >> sys.stderr, "sensorBondingTestDone() Exception trying to unlock DAQ tab: %s" % e
   
    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdAsicTester.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdAsicTester.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

    def setMiniConnector(self, miniConnectorId):
        '''Helper function ''' 
        if miniConnectorId < 9:
            self.connectorId = miniConnectorId
        elif miniConnectorId > 8: 
            self.connectorId = (miniConnectorId - 8)
        else: 
            self.msgPrint("Error setting the tile selection: Unrecognised mini connection: %d" % self.connectorId , bError=True)  
        self.app_main.asic_tester.setMiniConnector(self.connectorId)

    def configDeviceMessage(self, message):
        ''' Receives configuration ok/fail message '''
        self.testMsgPrint(message)
        
    def femConnectionStatus(self, bConnected):
        ''' Enables/Disable testTab's components according to bConnected argument '''
        # Fix checking of QLineEdit's contents that both python 2 & 3 compatible
        moduleNumString = self.ui.moduleNumberEdit.text()
        moduleNumLength = moduleNumString.count("")
        # Buttons remained locked until moduleNumber entered
        if moduleNumLength != 1:
            self.ui.asicBondingBtn.setEnabled(bConnected)
            self.ui.sensorBondingBtn.setEnabled(bConnected)
        self.ui.operatorEdit.setEnabled(bConnected)
        self.ui.moduleNumberEdit.setEnabled(bConnected)
        self.ui.commentEdit.setEnabled(bConnected)
        self.ui.analysisPathEdit.setEnabled(bConnected)
        self.ui.analysisPathBtn.setEnabled(bConnected)
        self.ui.testHvBiasEdit.setEnabled(bConnected)
        self.ui.testHvBiasSetBtn.setEnabled(bConnected)
        

        for connector_btn in self.connector_btns:
            connector_btn.setEnabled(bConnected)
         
    def createLogger(self):
        ''' Create logger (and its' folder, if it does not exist), return logger and its' path
            Adjusted from example:
            http://rlabs.wordpress.com/2009/04/09/python-closing-logging-file-getlogger/ '''

        timestamp = time.time()
        time_stamp = datetime.datetime.fromtimestamp(timestamp).strftime('%H%M%S')
        date_stamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
        moduleNumber = str(self.ui.moduleNumberEdit.text())
        fileName = self.pathStem + "%s/%s/testResults_%s.log" % (moduleNumber, date_stamp, time_stamp)
        
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
        formatter = logging.Formatter('%(levelname)s %(message)s')
        self.hdl.setFormatter(formatter)
        self.logger.addHandler(self.hdl)
        self.logger.setLevel(logging.DEBUG)
        # Signal new file path
        self.app_main.asic_window.logPathSignal.emit(filePath)

    def operatorUpdate(self):
        pass
    
    def moduleNumberUpdate(self):
        self.msgPrint("module number changed ")
        isModuleNumber = re.match('^[a-zA-Z]-[0-9]{4}-[0-9]{3}$', self.ui.moduleNumberEdit.text())

        if isModuleNumber:
            self.moduleStringSet = True
        else:
            self.msgPrint("Illegal value entered for module number: %s" % self.ui.moduleNumberEdit.text())
            self.msgPrint("Please enter a valid module number format")
            self.moduleStringSet = False

        checkForm(self)

        # Setup logger at this point, regardless
        self.createLogger()

    def moduleTypeUpdate(self , buttonId):
        ''' Update module selection (right side versus left side) according to GUI choice made '''
        #Using radion buttons ID to get LHS or RHS 
        if buttonId <= 8: 
            self.msgPrint("RHS module selected")
            self.moduleNumber = LpdAsicTester.RHS_MODULE
            self.miniConnectorSelect = True
            self.originalConnectorId = buttonId+7
        elif buttonId > 8: 
            self.msgPrint("LHS module selected") 
            self.moduleNumber = LpdAsicTester.LHS_MODULE
            self.miniConnectorSelect = True
            self.originalConnectorId = buttonId-9
        else:
            self.femConnectionStatus(False)
            self.miniConnectorSelect = False
        checkForm(self)
        self.setModuleType(self.moduleNumber)
        self.setMiniConnector(buttonId)
        self.app_main.asic_window.moduleSignal.emit(self.moduleNumber)
            
    def testMsgPrint(self, msg, bError=False):
        ''' Print message to this tab's message box, NOT main tab's '''
        
        constructedMessage = "%s %s" % (time.strftime("%H:%M:%S"), str(msg))

        # Log message if logger already set up
        if self.logger:
            # Log message as error if flagged as such
            if bError:
                self.logger.error(constructedMessage)
            else:
                self.logger.info(constructedMessage)

        self.ui.testMessageBox.appendPlainText(constructedMessage)
        self.ui.testMessageBox.verticalScrollBar().setValue(self.ui.testMessageBox.verticalScrollBar().maximum())
        self.ui.testMessageBox.repaint()
        self.app_main.app.processEvents()

    def dumpGuiFieldsToLog(self):
        ''' Using testMsgPrint() also logs the message to file '''
        
        self.testMsgPrint("Logging Operator: '%s'" % str(self.ui.operatorEdit.text()))
        self.testMsgPrint("Logging Module: '%s'" % str((self.ui.moduleNumberEdit.text()) + self.moduleString))
        self.testMsgPrint("Logging Comment: '%s'" % str(self.ui.commentEdit.text()))
    
    def analysisPathSelect(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self.mainWindow, "Select  analysis creation directory:", self.app_main.getCachedParam('analysisPdfPath'))
        if dirName != "":
            self.app_main.setCachedParam('analysisPdfPath', str(dirName))
            self.ui.analysisPathEdit.setText(dirName)
            self.mainWindow.updateEnabledWidgets()
    
    def hvBiasSetUpdate(self):
        
        biasStr = self.ui.testHvBiasEdit.text()
        try:
            hvBias = float(biasStr)
            self.app_main.setCachedParam('hvBiasVolts', hvBias)
            self.mainWindow.executeAsyncCmd('Setting HV bias to {:.1f} V'.format(hvBias), partial(self.app_main.pwr_card.hvBiasSet, hvBias), self.hvBiasSetDone)
            self.ui.hvBiasEdit.setText(biasStr)

        except ValueError:
            self.msgPrint("Illegal value entered for HV bias: %s" % biasStr)
            self.msgPrint("Please enter a number")
            self.ui.TestHvBiasEdit.setText(str(self.app_main.getCachedParam('hvBiasVolts')))
            
    def hvBiasSetDone(self):

        self.powerStatusUpdateDone()        
        self.msgPrint("HV bias set complete")

    def getTestHvBias(self):
        return self.ui.testHvBiasEdit.text() 
    
    def powerStatusUpdate(self):
        
        self.mainWindow.executeAsyncCmd('Updating power status...', self.app_main.pwr_card.statusUpdate, self.powerStatusUpdateDone)
        
    def powerStatusUpdateDone(self):
        
        self.mainWindow.powerStatusSignal.emit(self.app_main.pwr_card.powerStateGet())

def checkForm(self):
    ''' Check all areas of the form have been filled out
    '''
    # Fix checking of QLineEdit's contents that both python 2 & 3 compatible

    if self.moduleStringSet is True and self.miniConnectorSelect == True:
        self.ui.asicBondingBtn.setEnabled(True)
        self.ui.sensorBondingBtn.setEnabled(True)
    else:
        self.testMsgPrint("Module number is not formatted correctly or a mini connector has not been selected, buttons remains locked..")
        self.ui.asicBondingBtn.setEnabled(False)
        self.ui.sensorBondingBtn.setEnabled(False)

