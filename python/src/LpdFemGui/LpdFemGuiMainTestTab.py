
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

    fileNameSignal       = QtCore.pyqtSignal(str)
    fileReadySignal      = QtCore.pyqtSignal()
    messageSignal        = QtCore.pyqtSignal(object, bool)
    loggingSignal        = QtCore.pyqtSignal(str)
    configDeviceSignal   = QtCore.pyqtSignal(str)
    powerStatusSignal    = QtCore.pyqtSignal(object)
    hardwareStatusSignal = QtCore.pyqtSignal(bool)
            
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

        self.lvState        = -1
        self.hardwareChanged = False
        
        self.pathStem = "/u/ckd27546/workspace/tinkering/" #"/data/lpd/test/testGui/"
        self.Logger = None
        # Debugging purposes, have a think about when/how naming the log file..
        self.logFileName = self.pathStem + "logGui_%s.log" % time.strftime("%Y%m%d_%H%M%S")
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

#        QtCore.QObject.connect(self.ui.asicBondingBtn,        QtCore.SIGNAL("clicked()"),           self.asicBondingTest)    # "ASIC Bonding"
        QtCore.QObject.connect(self.ui.asicBondingBtn,        QtCore.SIGNAL("clicked()"),           self.asicBondingAlternativeTest)
        
        # Copied from LpdFemGuiMainPowerTab (to obtain low voltage, high-voltage status flags)
        self.powerStatusSignal.connect(self.obtainLvState)

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
        # Called when hardwareStatusSignal emitted
        self.hardwareStatusSignal.connect(self.handleHardwareChanged)

        # Create the analysis window but don't show it initially
        self.appMain.analysis = LpdFemGuiAnalysis(self.messageSignal, self.loggingSignal)

    def __del__(self):
        
        # Close the log file upon program exit? (Redundant?)
        pass
    
    def handleHardwareChanged(self, bHardwareChanged):
        
        self.hardwareChanged = bHardwareChanged
        print >> sys.stderr, "handleHardwareChanged received: ", bHardwareChanged, "self.hardwareChanged is now: ", self.hardwareChanged
        
    def togglePowerSupplies(self):

        theWait = 3
        self.testMsgPrint("Enable low voltage, then wait %d seconds" % theWait)
        self.mainWindow.pwrTab.lvEnableToggle()
        time.sleep(theWait)
        self.testMsgPrint("Enable high voltage, then wait %d seconds" % theWait)
        self.mainWindow.pwrTab.hvEnableToggle()
        time.sleep(theWait)
        self.testMsgPrint("All done executing togglePowerSupplies()")

    def asicBondingAlternativeTest(self):
        
        # Set up logger unless already set up
        if self.Logger is None:
            print >> sys.stderr, "testRun() Logger not set up, setting it up now"
            # Create file path - Move this? Although beware createLogger()'s dependency..
            timestamp = time.time()
            st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
            loggerPath = self.pathStem + "test_%s_%s/testResults.log" % (st, self.moduleString)
            (self.logPath) = self.createLogger(loggerPath)
            # Signal new file path
            self.appMain.analysis.analysisWindow.logPathSignal.emit(self.logPath)
        else:
            print >> sys.stderr, "testRun() Logger already set up"
        
        self.testMsgPrint("ALTERNATIVE: Beginning ASIC Bonding Testing of module %s.." % self.moduleString)
#        self.logMsg("ALTERNATIVE: Beginning ASIC Bonding..")

#        print >> sys.stderr, "asic 1"
        #self.mainWindow.executeAsyncCmd('* 2. Check and record current', self.appMain.analysis.powerTesting.readCurrent(self.moduleNumber), self.asicCurrentReadDone)
        self.mainWindow.executeAsyncCmd('A simple test..', self.appMain.analysis.test, self.asicCurrentReadDone)
        #self.mainWindow.executeAsyncCmd('Updating power status...', self.appMain.pwrCard.statusUpdate, self.powerStatusUpdateDone)
        #TODO: Pass info back to this class?
        print >> sys.stderr, "ASIC 1.5"
    
    def asicCurrentReadDone(self):
        print >> sys.stderr, "asicCurrentReadDone -  If you see this, everything is kosher"
#        self. #Mimic this:    ??
        #         self.mainWindow.powerStatusSignal.emit(self.appMain.pwrCard.powerStateGet())
        #        e.g. LpdFemGuiMainPowerTab: 125
        
    def asicSerialLoad(self):
        print >> sys.stderr, "asic 2"

    def asicBondingTest(self):

        # Set up logger unless already set up
        if self.Logger is None:
            print >> sys.stderr, "testRun() Logger not set up, setting it up now"
            # Create file path - Move this? Although beware createLogger()'s dependency..
            timestamp = time.time()
            st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
            loggerPath = self.pathStem + "test_%s_%s/testResults.log" % (st, self.moduleString)
            (self.logPath) = self.createLogger(loggerPath)
            # Signal new file path
            self.appMain.analysis.analysisWindow.logPathSignal.emit(self.logPath)
        else:
            print >> sys.stderr, "testRun() Logger already set up"
        
        self.testMsgPrint("Beginning ASIC Bonding Testing of module %s.." % self.moduleString)
        self.logMsg("Beginning ASIC Bonding..")

        # Checking current LV status
        self.checkLvStatus()    # Read current status (of power cards)    -    Must consider Threading model?!
        
        # Wait for hardware to report LV status
        while self.hardwareChanged == False:
            self.testMsgPrint("Waiting.. Self.hardwareChanged: %s" % self.hardwareChanged) # Required or loop becomes permanent..!
            time.sleep(1)
        # Reset hardware status
        self.hardwareChanged = False
        
        # ASIC Bonding procedure:
        # 1.Power on
        
        if self.lvState == 0:
            self.testMsgPrint("Low voltage is off, switching it on..")
            self.togglePowerSupplies()
        else:
            self.testMsgPrint("Low voltage already on")

        # 2. Check and record current (1A < I < 4A)
        self.testMsgPrint("2. Check and record current (1A < I < 4A)")
        self.appMain.analysis.powerTesting.readCurrent(self.moduleNumber)

        # 3. Serial Load (complex)
        self.testMsgPrint("3. Serial Load (skipping - blindly doing a Configure")
        self.testConfigure()
        #     Ensure serial load XML file selected, then execute Configure..
        
        time.sleep(2)

        # 4. Check and record current (8A < I => 10A)
        self.testMsgPrint("4. Check and record current (8A < I => 10A)")
        self.appMain.analysis.powerTesting.readCurrent(self.moduleNumber)
        #TODO: Pass info back to this class?
        time.sleep(3)
        print >> sys.stderr, "Finished!"
        return
        # 5. Readout Data
        self.testMsgPrint("5. Readout Data")
        self.testRun()
        
        # 6.Check for out of range pixels. Are these full ASICs? Columns or individual pixels.
        self.testMsgPrint("6. Check for out of range pixels")
        self.pixelCheckTest()
        
        # 7. Power off
        self.testMsgPrint("7. Power Off")
        self.mainWindow.pwrTab.lvEnableToggle()
        
        # 8. Power on
        self.testMsgPrint("8. Power On")
        self.mainWindow.pwrTab.lvEnableToggle()
        
        # 9. Check and record current (1A < I < 4A)
        self.testMsgPrint("9. Check and record current (1A < I < 4A)")
        self.appMain.analysis.powerTesting.readCurrent(self.moduleNumber)
        
        # 10. Parallel load
        self.testMsgPrint("10. Parallel Load (skipping - blindly doing a Configure")
        self.testConfigure()
        #     Ensure Parallel load XML file selected, then execute Configure..
        
        # 11. Check and record current (8A <I =< 10A)
        self.testMsgPrint("11. Check and record current (8A <I =< 10A)")
        self.appMain.analysis.powerTesting.readCurrent(self.moduleNumber)
        
        # 12.Readout data
        self.testMsgPrint("12. Readout Data")
        self.testRun()
        
        # 13. Check for out of range pixels. Are these full ASICs? Columns or individual pixels. Is there are any different compared to test 6?
        self.testMsgPrint("13. Check for out of range pixels")
        self.pixelCheckTest()
    
    def checkLvStatus(self):
        ''' It's not really changing the status tho.. '''
        self.mainWindow.executeAsyncCmd('* Checking out the power status...', self.appMain.pwrCard.statusUpdate, self.checkLvStatusDone)
        
    def checkLvStatusDone(self):
        ''' Ask LpdPowerCardManager (pwrCard) for power statuses, pass these on to obtainLvState (via powerStatusSignal) '''
        self.powerStatusSignal.emit(self.appMain.pwrCard.powerStateGet())

    def obtainLvState(self, powerState):
        
        powerCardFlags = { 'asicPowerEnable'      : 'LvStatus'}
        
        # Loop over LHS and RHS power cards and update display
        for powerCard in range(self.appMain.pwrCard.numPowerCards):
            
            # Check asicPowerEnable value
            for paramStem, uiObjStem in powerCardFlags.iteritems():
                
                paramName = paramStem + str(powerCard)
                self.lvState = powerState[paramName]    # 0 = Off, 1 = On
#                status = False if self.lvState == 0 else True
#                print >> sys.stderr, "Obtained LV state: ", self.lvState#, " status: ", status
                self.hardwareStatusSignal.emit(True)

    def testReadCurrent(self):
        
        self.appMain.analysis.powerTesting.readCurrent(self.moduleNumber)

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdFemGuiMainTestTab.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdFemGuiMainTestTab.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

    def pixelCheckTest(self):
        ''' Perform analysis of data file, then check pixel health '''
        self.appMain.analysis.performAnalysis(self.train, self.image, self.moduleNumber, self.fileName)
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

        # Set up logger unless already set up
        if self.Logger is None:
            print >> sys.stderr, "testRun() Logger not set up, setting it up now"
            # Create file path - Move this? Although beware createLogger()'s dependency..
            timestamp = time.time()
            st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
            loggerPath = self.pathStem + "test_%s_%s/testResults.log" % (st, self.moduleString)
            (self.logPath) = self.createLogger(loggerPath)
            # Signal new file path
            self.appMain.analysis.analysisWindow.logPathSignal.emit(self.logPath)
        else:
            print >> sys.stderr, "testRun() Logger already set up"


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
