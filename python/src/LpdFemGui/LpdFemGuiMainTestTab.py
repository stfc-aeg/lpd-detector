
'''
Created on Apr 19, 2013

@author: tcn45
'''

from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainTestTab(object):
    '''
    Helper class to manager TEST tab in main window
    '''

    def __init__(self, appMain, mainWindow):
        '''
        Constructor
        '''
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.testMsgPrint   # Use GUI element within this tab
        
        # Initialise default fields based on appMain object cached parameters
        # ...
        
        
#        QtCore.qDebug("LpdFemGuiMainTestTab, __init__()")
        self.msgPrint("te!sting")

#        if self.appMain.getCachedParam('externalTrigger') == True:
#            self.ui.externalTriggerSel.setCheckState(QtCore.Qt.Checked)
#        else:
#            self.ui.externalTriggerSel.setCheckState(QtCore.Qt.Unchecked)
#        self.ui.triggerDelayEdit.setText(str(self.appMain.getCachedParam('triggerDelay')))        
        
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.testBtn, QtCore.SIGNAL("clicked()"), self.executeTest)
        QtCore.QObject.connect(self.ui.operatorEdit,   QtCore.SIGNAL("editingFinished()"), self.operatorUpdate)
        QtCore.QObject.connect(self.ui.moduleNumberEdit,   QtCore.SIGNAL("editingFinished()"), self.moduleNumberUpdate)
#        QtCore.QObject.connect(self.ui.externalTriggerSel, QtCore.SIGNAL("toggled(bool)"), self.externalTriggerSelect)
        QtCore.QObject.connect(self.ui.moduleTypeButtonGroup, QtCore.SIGNAL("buttonClicked(int)"), self.moduleTypeUpdate)

    def executeTest(self):

#        fileName = QtGui.QFileDialog.getOpenFileName(self.mainWindow, 'Select readout parameter file', self.appMain.defaultConfigPath, "XML Files (*.xml)")
        self.msgPrint("LpdFemGuiMainTestTab, You pressed the Test button! ")

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
  
