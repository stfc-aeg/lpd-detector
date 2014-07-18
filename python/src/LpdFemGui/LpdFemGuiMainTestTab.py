
'''
Created on Apr 19, 2013

@author: tcn45
'''

from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from LpdFemGuiAnalysis import *
#from AsicTesting import *

from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainTestTab(QtGui.QMainWindow):
    '''
    Helper class to manager TEST tab in main window
    '''

    fileNameSignal = QtCore.pyqtSignal(str)
    fileReadySignal = QtCore.pyqtSignal()
    
    def __init__(self, appMain, mainWindow):

        super(LpdFemGuiMainTestTab, self).__init__()    # Required for pyqtSignal
        '''
        Constructor
        '''
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        # Disable test button from start
        self.ui.testBtn.setEnabled(False)
        self.msgPrint = self.testMsgPrint   # Use GUI element within this tab
        
        # Initialise default fields based on appMain object cached parameters
        # ...
        
                
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.testBtn, QtCore.SIGNAL("clicked()"), self.executeTest)
        QtCore.QObject.connect(self.ui.testConfigBtn, QtCore.SIGNAL("clicked()"), self.mainWindow.daqTab.deviceConfigure)
        QtCore.QObject.connect(self.ui.testRunBtn, QtCore.SIGNAL("clicked()"), self.mainWindow.daqTab.deviceRun)
        QtCore.QObject.connect(self.ui.operatorEdit,   QtCore.SIGNAL("editingFinished()"), self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,   QtCore.SIGNAL("editingFinished()"), self.moduleNumberUpdate)
#        QtCore.QObject.connect(self.ui.externalTriggerSel, QtCore.SIGNAL("toggled(bool)"), self.externalTriggerSelect)
        QtCore.QObject.connect(self.ui.moduleTypeButtonGroup, QtCore.SIGNAL("buttonClicked(int)"), self.moduleTypeUpdate)
        
        # Allow LpdFemDataReceiver to communicate new filename (via LpdFemGui, LpdFemGuiMainWindow)
        self.fileNameSignal.connect(self.updateFileName)
        self.fileReadySignal.connect(self.enableTestButton)
        self.fileName = ""
        
        # Create the analysis window but don't show it initially
        self.analysisWindow = LpdFemGuiAnalysis()
        
    def executeTest(self):

        self.msgPrint("LpdFemGuiMainTestTab, this will start tests (in the future)")

        self.fileName = str(self.fileName)
        self.analysisWindow.performAnalysis(self.fileName)
        # Disable test button until next filename available
        self.ui.testBtn.setEnabled(False)
        
    def enableTestButton(self):
        
        self.msgPrint("File closed, you may now perform analysis if you wish")
        self.ui.testBtn.setEnabled(True)
#        self.executeTest()
        
    def updateFileName(self, filename):

        self.msgPrint("LpdFemGuiMainTestTab received filename: " + filename)
        self.fileName = filename

    def operatorUpdate(self):

        QtCore.qDebug("LpdFemGuiMainTestTab, You changed operatorEdit (to be: " + self.ui.operatorEdit.text() + ")")
    
    def moduleNumberUpdate(self):

        QtCore.qDebug("LpdFemGuiMainTestTab, You changed moduleNumberEdit (to be: " + self.ui.moduleNumberEdit.text() + ")")
    
#    def externalTriggerSelect(self, state):
#        self.msgPrint("External trigger select is %d" % int(state))
#        self.appMain.setCachedParam('externalTrigger', state)
#        self.mainWindow.updateEnabledWidgets()

    def moduleTypeUpdate(self):

        moduleType = -1 
        if self.ui.moduleLhsSel.isChecked():
            moduleType = 0
        elif self.ui.moduleRhsSel.isChecked():
            moduleType = 1
        else:
            self.msgPrint("Illegal Module Type selection - should not happen")
            return
        # Debug info:
        if moduleType == 0:
            self.msgPrint("LHS module selected")
            QtCore.qDebug("LHS module selected")
        else:
            self.msgPrint("RHS module selected")
            QtCore.qDebug("RHS module selected")


    def testMsgPrint(self, msg):
        
        self.ui.testMessageBox.appendPlainText("%s %s" % (time.strftime("%H:%M:%S"), str(msg)))
        self.ui.testMessageBox.verticalScrollBar().setValue(self.ui.testMessageBox.verticalScrollBar().maximum())
        self.ui.testMessageBox.repaint()
        self.appMain.app.processEvents()
  
