
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
    # Inheritance required for super() line within __init__() function
    '''
    Helper class to manager TEST tab in main window
    '''

    fileNameSignal = QtCore.pyqtSignal(str)
    fileReadySignal = QtCore.pyqtSignal()
    messageSignal = QtCore.pyqtSignal(object)
    
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
        self.msgPrint = self.testMsgPrint   # Use MessageBox element within this tab

        
        self.ui.moduleLhsSel.setChecked(True)
                
        self.module   = 0   # LHS = 0, RHS = 15
        self.fileName = ""
        self.image    = 0
        self.train    = 0

        # Initialise default fields based on appMain object cached parameters
        # ...
        
                
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.testBtn, QtCore.SIGNAL("clicked()"), self.executeTest)
        QtCore.QObject.connect(self.ui.testConfigBtn, QtCore.SIGNAL("clicked()"), self.mainWindow.daqTab.deviceConfigure)
        QtCore.QObject.connect(self.ui.testRunBtn, QtCore.SIGNAL("clicked()"), self.mainWindow.daqTab.deviceRun)
        QtCore.QObject.connect(self.ui.operatorEdit,   QtCore.SIGNAL("editingFinished()"), self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,   QtCore.SIGNAL("editingFinished()"), self.moduleNumberUpdate)
        QtCore.QObject.connect(self.ui.moduleTypeButtonGroup, QtCore.SIGNAL("buttonClicked(int)"), self.moduleTypeUpdate)
        
        # Allow LpdFemDataReceiver to communicate new filename (via LpdFemGui, LpdFemGuiMainWindow)
        self.fileNameSignal.connect(self.updateFileName)
        self.fileReadySignal.connect(self.enableTestButton)
        self.fileName = ""
        # Let LpdFemGuiPowerTesting communicate results:
        self.messageSignal.connect(self.testMsgPrint)

        
        # Create the analysis window but don't show it initially
        self.analysis = LpdFemGuiAnalysis(self.messageSignal)
        
    def executeTest(self):
        ''' Perform analysis '''
        self.analysis.performAnalysis(self.train, self.image, self.module, self.fileName)
        # Disable test button until next filename available
        self.ui.testBtn.setEnabled(False)
        
    def enableTestButton(self):
        ''' Enable test button when fileReadySignal received '''
        self.ui.testBtn.setEnabled(True)
        
    def updateFileName(self, filename):

        self.fileName = str(filename)

    def operatorUpdate(self):

        QtCore.qDebug("LpdFemGuiMainTestTab, You changed operatorEdit (to be: " + self.ui.operatorEdit.text() + ")")
    
    def moduleNumberUpdate(self):

        QtCore.qDebug("LpdFemGuiMainTestTab, You changed moduleNumberEdit (to be: " + self.ui.moduleNumberEdit.text() + ")")

    def moduleTypeUpdate(self):
        ''' Update module selection (right side versus left side) according to GUI choice made '''
        
        if self.ui.moduleLhsSel.isChecked():
            self.msgPrint("LHS module selected")
            self.module = 0
        elif self.ui.moduleRhsSel.isChecked():
            self.msgPrint("RHS module selected")
            self.module = 15

    def testMsgPrint(self, msg):
        ''' Print message to this tab's message box, NOT main tab's '''
        self.ui.testMessageBox.appendPlainText("%s %s" % (time.strftime("%H:%M:%S"), str(msg)))
        self.ui.testMessageBox.verticalScrollBar().setValue(self.ui.testMessageBox.verticalScrollBar().maximum())
        self.ui.testMessageBox.repaint()
        self.appMain.app.processEvents()
  
