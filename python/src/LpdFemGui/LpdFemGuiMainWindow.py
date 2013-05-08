from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from LpdFemGuiMainDaqTab import *
from LpdFemGuiMainPowerTab import *
from LpdFemGuiMainConfigTab import *
from LpdFemGuiMainEvrTab import *
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainWindow(QtGui.QMainWindow):
   
    messageSignal = QtCore.pyqtSignal(object)
    runStateSignal = QtCore.pyqtSignal()
    runStatusSignal = QtCore.pyqtSignal(object)
    powerStatusSignal = QtCore.pyqtSignal(object)
     
    def __init__(self, appMain):
        
        # Create main window UI
        
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.appMain = appMain
        
        self.asyncCmd = None
        self.asyncCmdRunning = False
        
        # Create helper objects to manage main window tabs
        self.daqTab = LpdFemGuiMainDaqTab(appMain, self)
        self.pwrTab = LpdFemGuiMainPowerTab(appMain, self)
        self.configTab = LpdFemGuiMainConfigTab(appMain, self)
        self.evrTab = LpdFemGuiMainEvrTab(appMain, self)

        # Initialise default fields based on appMain object
        self.ui.connectAddr.setText(self.appMain.getCachedParam('femAddr'))
        self.ui.connectPort.setText(str(self.appMain.getCachedParam('femPort')))        
                    
        # Create a status bar with a progress bar
        self.createStatusBar("Not connected")
       
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.connectButton, QtCore.SIGNAL("clicked()"), self.deviceConnectToggle)
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'), self.quitApplication)
        
        # Connect msgRecv function to message signal to allow other non-GUI threads to print messages
        self.messageSignal.connect(self.msgRecv)
        
        # Connect runStateUpdate function to signal to allow other non-GUI threads to push state updates
        self.runStateSignal.connect(self.runStateUpdate)
    
        # Connect run status update function to signal to data recevier to push updates
        self.runStatusSignal.connect(self.daqTab.runStatusUpdate)
        
        # Connect power status update function to signal
        self.powerStatusSignal.connect(self.pwrTab.powerStatusUpdateDisplay)
        
    def msgRecv(self, message):
        
        self.msgPrint(message)
        
    def runStateUpdate(self):
        
        self.daqTab.runStateUpdate(self.appMain.deviceState)
        self.updateEnabledWidgets()
                
    def executeAsyncCmd(self, message, cmdHandler, completionHandler):
        
        if self.asyncCmdRunning == True:
            ret = QtGui.QMessageBox.critical(self, "System busy", "Please wait for the current operation to complete")
        else:
            self.asyncCmd = AsyncExecutionThread(cmdHandler, self.completeAsyncCmd)
            self.asyncCompletion = completionHandler
            self.msgPrint(message)
            self.statusBar().showMessage(self.tr(message))
            self.progressBar.show()
            self.progressBar.setRange(0,0)
            self.asyncCmdRunning = True
            self.asyncCmd.start()
        
    def completeAsyncCmd(self):
        
        self.asyncCompletion()
        self.progressBar.hide() 
        self.statusBar().showMessage("Done")
        self.asyncCmdRunning = False
        
    def updateEnabledWidgets(self):
        
        if self.appMain.deviceState == LpdFemGui.DeviceDisconnected:

            self.ui.configGroupBox.setEnabled(False)
            self.ui.operateGroupBox.setEnabled(False)
            
        elif self.appMain.deviceState == LpdFemGui.DeviceIdle:
            
            self.ui.configGroupBox.setEnabled(True)
            self.ui.operateGroupBox.setEnabled(True)
            self.ui.configBtn.setEnabled(True)
            self.ui.runBtn.setEnabled(False)
            self.ui.stopBtn.setEnabled(False)
            
        elif self.appMain.deviceState == LpdFemGui.DeviceConfiguring:
            
            self.ui.configGroupBox.setEnabled(True)
            self.ui.operateGroupBox.setEnabled(True)
            self.ui.configBtn.setEnabled(False)
            self.ui.runBtn.setEnabled(False)
            self.ui.stopBtn.setEnabled(False)
            
        elif self.appMain.deviceState == LpdFemGui.DeviceReady:
            
            self.ui.configGroupBox.setEnabled(True)
            self.ui.operateGroupBox.setEnabled(True)
            self.ui.configBtn.setEnabled(True)
            self.ui.runBtn.setEnabled(True)
            self.ui.stopBtn.setEnabled(False)
            
        elif self.appMain.deviceState == LpdFemGui.DeviceRunning:
            
            self.ui.configGroupBox.setEnabled(True)
            self.ui.operateGroupBox.setEnabled(True)
            self.ui.configBtn.setEnabled(False)
            self.ui.runBtn.setEnabled(False)
            self.ui.stopBtn.setEnabled(True)
            
        self.daqTab.updateEnabledWidgets()
        self.pwrTab.updateEnabledWidgets()
        self.evrTab.updateEnabledWidgets()
            
        
    def createStatusBar(self, defaultMessage):
        sb = QtGui.QStatusBar()
        sb.setFixedHeight(18)
        self.setStatusBar(sb)
        self.statusBar().showMessage(self.tr(defaultMessage))
        self.progressBar = QtGui.QProgressBar(self.statusBar())
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.hide()
                            
    def deviceConnectToggle(self):
        
        if self.appMain.deviceState == LpdFemGui.DeviceDisconnected:

            # Extract address and port from GUI fields and validate
            deviceAddress = str(self.ui.connectAddr.text())
            devicePort = str(self.ui.connectPort.text())
            if not validIpAddress(deviceAddress) or not validPort(devicePort):
                ret = QtGui.QMessageBox.critical(self, "Connection error", "Please enter a valid address and port")
                return
            
            self.appMain.setCachedParam('femAddress', deviceAddress)
            self.appMain.setCachedParam('femPort', devicePort)
            
            self.ui.connectButton.setEnabled(False)
            cmdMsg = "Connecting to LPD device at address %s port %s ..." % (deviceAddress, devicePort)
            self.executeAsyncCmd(cmdMsg, partial(self.appMain.deviceConnect, deviceAddress, devicePort),
                                 self.connectDone)        
        else:
            self.appMain.deviceDisconnect()
            self.msgPrint("Device disconnected")
            self.statusBar().showMessage(self.tr("Not connected"))
            self.ui.connectStatus.setText("NO")
            self.ui.connectButton.setText("Connect")
            self.ui.lvStatus.setText("Unknown")
            self.ui.hvStatus.setText("Unknown")
            
        self.updateEnabledWidgets()
    
    def connectDone(self):
        
        self.progressBar.hide()
        self.ui.connectButton.setEnabled(True)
        # Toggle button text according to state
        if self.appMain.deviceState != LpdFemGui.DeviceDisconnected:
            
            self.msgPrint("Connected to device OK")
            self.statusBar().showMessage(self.tr("Connected to device"))
            self.ui.connectButton.setText("Disconnect")
            self.ui.connectStatus.setText("YES")
            self.appMain.femConfigGet()
            self.configTab.showConfig()

            self.appMain.pwrCard.statusUpdate()
            self.pwrTab.lvEnableToggleDone()            
            self.pwrTab.hvEnableToggleDone()
                        
            self.ui.configGroupBox.setEnabled(True)
            self.ui.operateGroupBox.setEnabled(True)

        else:
            self.statusBar().showMessage(self.tr("Not connected"))
            self.msgPrint(self.appMain.deviceErrString)
            
            self.ui.connectButton.setText("Connect")
            self.ui.connectStatus.setText("NO")
            self.ui.lvStatus.setText("Unknown")
            self.ui.hvStatus.setText("Unknown")
            
            self.ui.configGroupBox.setEnabled(False)
            self.ui.operateGroupBox.setEnabled(False)


        self.updateEnabledWidgets()
        
    def msgPrint(self, msg):
        
        self.ui.messageBox.appendPlainText("%s %s" % (time.strftime("%H:%M:%S"), str(msg)))
        self.ui.messageBox.verticalScrollBar().setValue(self.ui.messageBox.verticalScrollBar().maximum())
        self.ui.messageBox.repaint()
        self.appMain.app.processEvents()
                 
    def quitApplication(self):
            
        if self.appMain.deviceState != LpdFemGui.DeviceDisconnected:
            self.appMain.deviceDisconnect()

        self.appMain.cleanup()            
        self.appMain.app.quit()
        
    def closeEvent(self, theCloseEvent):
        
        if self.appMain.deviceState != LpdFemGui.DeviceDisconnected:
            self.appMain.deviceDisconnect()
            
        self.appMain.cleanup()    
        theCloseEvent.accept()
        
      
