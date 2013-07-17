from PyQt4 import QtCore, QtGui
from LpdDataDisplay import *
from utilities import *
import time
from functools import partial

class LpdDataDisplayMainWindow(QtGui.QMainWindow):
   
    runStatusSignal = QtCore.pyqtSignal(object)
     
    def __init__(self, appMain):
        
        # Create main window UI
        
        QtGui.QMainWindow.__init__(self)
        
        self.appMain = appMain
        
        self.asyncCmd = None
        self.asyncCmdRunning = False
    
        # Connect run status update function to signal to data recevier to push updates
        self.runStatusSignal.connect(self.runStatusUpdate)

    #HACKED from LpdFemGuiMainDaqTab:
    def deviceRun(self):
        
        # Show live view window
        self.appMain.liveViewWindow.show()
        
        self.executeAsyncCmd('Running acquisition ...', self.appMain.deviceRun, self.runDone)

    #HACKED from LpdFemGuiMainDaqTab:
    def runDone(self):

        self.msgPrint("Acquisition completed")

    #BLANK PLACEHOLDER
    def runStatusUpdate(self, runStatus):
        
        pass
        
    def executeAsyncCmd(self, message, cmdHandler, completionHandler):
        # Only executed by deviceRun() above..
        if self.asyncCmdRunning == True:
            print "System busy, Please wait for the current operation to complete"
        else:
            self.asyncCmd = AsyncExecutionThread(cmdHandler, self.completeAsyncCmd)
            self.asyncCompletion = completionHandler
            self.msgPrint(message)
            self.asyncCmdRunning = True
            self.asyncCmd.start()
        
    def completeAsyncCmd(self):
        
        self.asyncCompletion()
        self.asyncCmdRunning = False
        
    def msgPrint(self, msg):
        
        print "%s %s" % (time.strftime("%H:%M:%S"), str(msg))
                 

