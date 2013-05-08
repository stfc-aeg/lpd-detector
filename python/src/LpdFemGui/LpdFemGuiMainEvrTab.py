
from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainEvrTab(object):
    '''
    Helper class to manage EVR tab in main window
    '''

    def __init__(self, appMain, mainWindow):
        '''
        Constructor
        '''
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.mainWindow.msgPrint

        # Initialise default fields based on appMain object cached parameters
        self.ui.evrMcastGroupEdit.setText(self.appMain.getCachedParam('evrMcastGroup'))
        self.ui.evrMcastPortEdit.setText(str(self.appMain.getCachedParam('evrMcastPort')))
        self.ui.evrMcastInterfaceEdit.setText(self.appMain.getCachedParam('evrMcastInterface'))
        if self.appMain.getCachedParam('evrRecordEnable') == True:
            self.ui.evrRecordEnableSel.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.evrRecordEnableSel.setCheckState(QtCore.Qt.Unchecked)

                                         
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.evrMcastGroupEdit, QtCore.SIGNAL("editingFinished()"), self.evrMcastGroupUpdate)
        QtCore.QObject.connect(self.ui.evrMcastPortEdit, QtCore.SIGNAL("editingFinished()"), self.evrMcastPortUpdate)
        QtCore.QObject.connect(self.ui.evrMcastInterfaceEdit, QtCore.SIGNAL("editingFinished()"), self.evrMcastInterfaceUpdate)
        QtCore.QObject.connect(self.ui.evrRecordEnableSel, QtCore.SIGNAL("toggled(bool)"), self.evrRecordSelect)

    def updateEnabledWidgets(self):
        pass

    def evrMcastGroupUpdate(self):
        evrMcastGroup = self.ui.evrMcastGroupEdit.text()
        try:
            evrMcastGroupStr = str(evrMcastGroup)
            self.appMain.setCachedParam('evrMcastGroup', evrMcastGroupStr)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.evrMcastGroupEdit.setText(self.appMain.getCachedParam('evrMcastGroup'))

    def evrMcastPortUpdate(self):
        evrMcastPort = self.ui.evrMcastPortEdit.text()
        try:
            evrMcastPortVal = int(evrMcastPort)
            self.appMain.setCachedParam('evrMcastPort', evrMcastPortVal)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.evrMcastPortEdit.setText(str(self.appMain.getCachedParam('evrMcastPort')))

    def evrMcastInterfaceUpdate(self):
        evrMcastInterface = self.ui.evrMcastInterfaceEdit.text()
        try:
            evrMcastInterfaceStr = str(evrMcastInterface)
            self.appMain.setCachedParam('evrMcastInterface', evrMcastInterfaceStr)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.evrMcastInterfaceEdit.setText(self.appMain.getCachedParam('evrMcastInterface'))

    def evrRecordSelect(self, state):
        self.appMain.setCachedParam('evrRecordEnable', state)
        self.mainWindow.updateEnabledWidgets()



