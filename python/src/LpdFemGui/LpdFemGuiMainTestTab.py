
'''
Created on Apr 19, 2013

@author: tcn45
'''

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *

from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from LpdFemGuiAnalysis import *
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

    fileNameSignal = QtCore.pyqtSignal(str)
    fileReadySignal = QtCore.pyqtSignal()
    messageSignal = QtCore.pyqtSignal(object, bool)
    loggingSignal = QtCore.pyqtSignal(str)
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
        self.moduleString   = ""
        self.setModuleType(self.moduleNumber)
        self.fileName       = ""
        self.image          = 0
        self.train          = 0
 
        # Debugging purposes, have a think about when/how naming the log file..
        self.logFileName = "/data/lpd/test/testGui/logGui_%s.log" % time.strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(filename=self.logFileName, level=logging.INFO)
        print >> sys.stderr, "self.logFileName: ", self.logFileName

        # Connect signals and slots
        QtCore.QObject.connect(self.ui.testConfigBtn,         QtCore.SIGNAL("clicked()"),           self.testConfigure) # "TestConfig" - DAQ tab replica
        QtCore.QObject.connect(self.ui.testRunBtn,            QtCore.SIGNAL("clicked()"),           self.testRun)       # "TestRun"    - DAQ tab replica
        QtCore.QObject.connect(self.ui.operatorEdit,          QtCore.SIGNAL("editingFinished()"),   self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,      QtCore.SIGNAL("editingFinished()"),   self.moduleNumberUpdate)
        QtCore.QObject.connect(self.ui.moduleTypeButtonGroup, QtCore.SIGNAL("buttonClicked(int)"),  self.moduleTypeUpdate)
        QtCore.QObject.connect(self.ui.readCurrentBtn,        QtCore.SIGNAL("clicked()"),           self.testReadCurrent)   # 
        QtCore.QObject.connect(self.ui.pixelCheckBtn,         QtCore.SIGNAL("clicked()"),           self.pixelCheckTest)    # "Pixel Check"

        # Allow LpdFemDataReceiver to communicate new filename (via LpdFemGui, LpdFemGuiMainWindow)
        self.fileNameSignal.connect(self.updateFileName)
        self.fileReadySignal.connect(self.fileReadyToBeProcessed)
        self.fileName = ""
        self.configDeviceSignal.connect(self.configDeviceMessage)
        # Let LpdFemGuiPowerTesting (and others) communicate results:
        self.messageSignal.connect(self.testMsgPrint)
        # Let LpdFemGuiAnalysis (and others?) communicate loggable results
        self.loggingSignal.connect(self.logMsg)
        (self.logger, self.hdl) = (None, None)

        # Create the analysis window but don't show it initially
        self.analysis = LpdFemGuiAnalysis(self.messageSignal, self.loggingSignal)

    def __del__(self):
        
        # Close the log file upon program exit? (Redundant?)
        pass
    
    def testReadCurrent(self):
        
        self.analysis.powerTesting.readCurrent(self.moduleNumber)

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdFemGuiMainTestTab.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdFemGuiMainTestTab.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

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

    def warning(self):
        ''' Testing using QMessageBox '''
        ret = QMessageBox.warning(self, "Power Cycle",
                '''Ensure power switched on before  clicking ok or click cancel.''',
                QMessageBox.Ok, QMessageBox.Cancel);
        if ret == QMessageBox.Ok:
            print >> sys.stderr, "Answer was Ok"
        elif ret == QMessageBox.Cancel:
            print >> sys.stderr, "Answer was Cancel"
        else:
            print >> sys.stderr, "Error: Unknown answer"
 
    def testRun(self):
        
        self.testMsgPrint("Running Acquisition ...")
        self.mainWindow.daqTab.deviceRun()
        
        #TODO: Assuming logging begins here.. ?
        # Create file path - Move this? Although beware createLogger()'s dependency..
        timestamp = time.time()
        st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        loggerPath = "/data/lpd/test/testGui/test_%s_%s/testResults.log" % (st, self.moduleString)
        
        # Set up logger
        (self.logPath) = self.createLogger(loggerPath)

        # Signal new file path
        self.analysis.analysisWindow.logPathSignal.emit(self.logPath)


    def createLogger(self, fileName):
        ''' Create logger (and its' folder if it does not exist), return logger and its' path
            Adjusted from example: 
            http://rlabs.wordpress.com/2009/04/09/python-closing-logging-file-getlogger/ '''
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
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdl.setFormatter(formatter)
        self.logger.addHandler(self.hdl)
        self.logger.setLevel(logging.DEBUG)
        return filePath

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
            self.setModuleType(self.moduleNumber)

        elif self.ui.moduleRhsSel.isChecked():
            self.msgPrint("RHS module selected")
            self.moduleNumber = LpdFemGuiMainTestTab.RHS_MODULE
            self.setModuleType(self.moduleNumber)
            
    def testMsgPrint(self, msg, bError=False):
        ''' Print message to this tab's message box, NOT main tab's '''
        
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
        

    def logMsg(self, string):
        ''' Log string to file (self.logger) '''
        
        print >> sys.stderr, "logMsg rx'd: %s.."% string[0:24]
        if self.logger is not None:
            self.logger.info(string)
        else:
            print >> sys.stderr, "ERROR: self.logger not set up!"
