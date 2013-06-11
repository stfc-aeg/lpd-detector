from PyQt4 import QtCore, QtGui
from LpdDataDisplayMainWindow_ui import Ui_MainWindow
from LpdDataDisplay import *
from utilities import *
import time
import sys
from functools import partial

class LpdDataDisplayMainWindow(QtGui.QMainWindow):
   
    messageSignal = QtCore.pyqtSignal(object)
    runStateSignal = QtCore.pyqtSignal()
    runStatusSignal = QtCore.pyqtSignal(object)
     
    def __init__(self, appMain):
        
        # Create main window UI
        
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.appMain = appMain
        
        self.asyncCmd = None
        self.asyncCmdRunning = False
            

        # Create a status bar with a progress bar
        self.createStatusBar("Not connected")
       
        # Connect signals and slots
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'), self.quitApplication)
        
        # Connect msgRecv function to message signal to allow other non-GUI threads to print messages
        self.messageSignal.connect(self.msgRecv)
        
        # Connect runStateUpdate function to signal to allow other non-GUI threads to push state updates
        self.runStateSignal.connect(self.runStateUpdate)
    
        # Connect run status update function to signal to data recevier to push updates
        self.runStatusSignal.connect(self.runStatusUpdate)
        
        #HACKED from LpdFemGuiMainDaqTab:
        QtCore.QObject.connect(self.ui.runBtn,          QtCore.SIGNAL("clicked()"), self.deviceRun)

        #OVERRIDE GUI settings
        self.ui.runBtn.setEnabled(True)

    #HACKED from LpdFemGuiMainDaqTab:
    def deviceRun(self):
        
        # Show live view window
        self.appMain.liveViewWindow.show()
        
        self.executeAsyncCmd('Running acquisition ...', self.appMain.deviceRun, self.runDone)

    #HACKED from LpdFemGuiMainDaqTab:
    def runDone(self):
        
        if self.appMain.deviceState == LpdDataDisplay.DeviceReady:
            self.msgPrint("Acquisition completed")
        else:
            self.msgPrint("Acquisition failed")

    #BLANK PLACEHOLDER
    def runStatusUpdate(self, runStatus):
        
        pass
        
    def msgRecv(self, message):
        
        self.msgPrint(message)
        
    def runStateUpdate(self):
        pass

    def executeAsyncCmd(self, message, cmdHandler, completionHandler):
        # Only executed by deviceRun() above..
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
        
    def createStatusBar(self, defaultMessage):
        sb = QtGui.QStatusBar()
        sb.setFixedHeight(18)
        self.setStatusBar(sb)
        self.statusBar().showMessage(self.tr(defaultMessage))
        self.progressBar = QtGui.QProgressBar(self.statusBar())
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.hide()
                            
    def msgPrint(self, msg):
        
        self.ui.messageBox.appendPlainText("%s %s" % (time.strftime("%H:%M:%S"), str(msg)))
        self.ui.messageBox.verticalScrollBar().setValue(self.ui.messageBox.verticalScrollBar().maximum())
        self.ui.messageBox.repaint()
        self.appMain.app.processEvents()
                 
    def quitApplication(self):
            
        if self.appMain.deviceState != LpdDataDisplay.DeviceDisconnected:
            self.appMain.deviceDisconnect()

        self.appMain.app.quit()
        

