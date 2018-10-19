'''
Created on July 17, 2014

@author: ckd27546    (Based upon LpdFemGuiLiveViewWindow.py)
'''

from LpdDataContainers import LpdImageContainer
from LpdFemClient.LpdFemClient import LpdFemClient

from PyQt4 import QtCore, QtGui
from utilities import *
import sys, os, time, datetime

import numpy as np
import h5py

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class LpdFemGuiAsicWindow(QtGui.QDialog):

    REALIMAGE   = 0
    FAULTYIMAGE = 1
    THRESHIMAGE = 2

    trainSignal     = QtCore.pyqtSignal(object)
    imageSignal     = QtCore.pyqtSignal(object)
    moduleSignal    = QtCore.pyqtSignal(object)
    timeStampSignal = QtCore.pyqtSignal(object)
    logPathSignal   = QtCore.pyqtSignal(str)
    dataSignal      = QtCore.pyqtSignal(object, object, object, str, int, int, str)
    
    matplotlib.rcParams.update({'font.size': 8})
    
    def __init__(self, app_main): #, parent=None):
 
        QtGui.QDialog.__init__(self) #, parent)
        
        self.app_main = app_main
        self.messageSignal = self.app_main.mainWindow.testTab.messageSignal
        
        self.nrows = 32
        self.ncols = 128
        
        self.moduleString = "LHS"
        self.moduleNumber = self.app_main.asicTester.LHS_MODULE
        
        self.setWindowTitle('Plotting data from Asic Module')

        self.plotFrame =QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((8.0, 6.0), dpi=self.dpi)       
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.plotFrame)
        self.imageSize = self.nrows * self.ncols
        
        #self.axes = self.fig.add_subplot(111)
        self.axes = []
        self.img  = []

        # Obtain default colour map before creating plots
        defaultColourMap = cm.get_cmap()
        numberPlots = 3
        for idx in range(numberPlots):
            
            axesObject = self.fig.add_subplot(numberPlots, 1, idx+1)
            self.axes.extend([axesObject])

            # Disable up the X and Y ticks
            self.axes[idx].set_xticks([])
            self.axes[idx].set_yticks([])
    
            # Create an empty plot
            self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)

            # Define colour range, colourmap according to plot number
            if idx == 0:
                vMax = 4095
                cMap = defaultColourMap
                cTicks = [0, 511, 1023, 1535, 2047, 2559, 3071, 3583, 4095]
            elif idx == 1:
                maximum = 2000
                vMax = maximum
                cMap = 'binary'
                cTicks = [0, int(maximum/4), int(maximum/2), int(3*maximum/4), maximum]
            else:
                maximum = 1
                vMax = maximum
                cMap = 'binary'
                cTicks = [0, maximum]

            imgObject = self.axes[idx].imshow(self.data, cmap=cMap, interpolation='nearest', vmin=0, vmax=vMax)
            self.img.extend([imgObject])

            # Create and show a colourbar
            axc, kw = matplotlib.colorbar.make_axes(self.axes[idx], orientation='vertical')
            cb = matplotlib.colorbar.Colorbar(axc, self.img[idx], orientation='vertical')
            cb.set_ticks(ticks=cTicks, update_ticks=True)
            self.img[idx].colorbar = cb

            # Add vertical lines to differentiate between the ASICs
            for i in range(16, self.ncols, 16):
                self.axes[idx].vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
            
            self.canvas.draw()

        # Create the navigation toolbar, tied to the canvas
        #
        self.mplToolbar = NavigationToolbar(self.canvas, self.plotFrame)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mplToolbar)
        vbox.addWidget(self.canvas)
        
        self.setLayout(vbox)
        
        self.setWindowTitle("Analysis Window")
        self.setModal(False)

        # Connect the data update signal
        self.trainSignal.connect(self.trainUpdate)
        self.imageSignal.connect(self.imageUpdate)
        self.moduleSignal.connect(self.moduleUpdate)
        self.timeStampSignal.connect(self.timeStampUpdate)
        self.logPathSignal.connect(self.logPathUpdate)
        self.dataSignal.connect(self.windowUpdate)
        
    def closeEvent(self, event):
        event.accept()
        
    def trainUpdate(self, train):
        self.train = train
        
    def imageUpdate(self, image):
        self.image = image
        
    def moduleUpdate(self, module):
        self.module = module
        
    def timeStampUpdate(self, timeStamp):
        self.timeStamp = timeStamp

    def logPathUpdate(self, logPath):
        self.logPath = str(logPath)

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == self.app_main.asicTester.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == self.app_main.asicTester.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

    def windowUpdate(self, lpdActualImage, lpdFaultyImage, lpdThresholdImage, moduleDescription, moduleNumber, thresholdLevel, miscDescription):

        #print >> sys.stderr, "moduleDescription ", moduleDescription, " \nmoduleNumber", moduleNumber, "\nmiscDescription", miscDescription
        # Convert module number into the string e.g. "RHS"
        self.setModuleType(moduleNumber)
        # Save module description, e.g. "00135"
        self.moduleDescription = moduleDescription
        
        # Plot the captured image
        self.img[LpdFemGuiAsicWindow.REALIMAGE].set_data(lpdActualImage)

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Train %d Image %d %sModule %s: %s' % (self.train, self.image, miscDescription+"\n", self.moduleDescription+self.moduleString, dateStr)
        self.axes[LpdFemGuiAsicWindow.REALIMAGE].set_title(self.titleText)

        # Plot the black/white image (which shows which pixel(s) are dead)
        self.img[LpdFemGuiAsicWindow.FAULTYIMAGE].set_data(lpdFaultyImage)

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Module %s: Faulty pixel(s)' % (self.moduleDescription+self.moduleString)
        self.axes[LpdFemGuiAsicWindow.FAULTYIMAGE].set_title(self.titleText)

        # Plot the black/white image of dead pixels AFTER THRESHOLD APPLIED

        self.img[LpdFemGuiAsicWindow.THRESHIMAGE].set_data(lpdThresholdImage)

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Faulty pixel(s) above threshold: %s' % (thresholdLevel)
        self.axes[LpdFemGuiAsicWindow.THRESHIMAGE].set_title(self.titleText)

        self.canvas.draw()

        # Save image to hdf5 file (but not the black/white image)
        self.savePlot(lpdActualImage, moduleDescription+self.moduleString)

        # Save plotted figure to file
        try:
            fname = self.logPath + "savedFig_%s_%s" % (moduleDescription+self.moduleString, time.strftime("%H%M%S"))
            #print >> sys.stderr, "Fig:  %s" % (fname + ".png")
        except Exception as e:
            self.msgPrint("windowUpdate() Exception: %s" % e, bError=True)

        self.fig.savefig(fname)

    def savePlot(self, lpdImage, fullModuleName):
        try:
            fileName = self.logPath + "lpdData_%s_%s.hdf5" % (fullModuleName, time.strftime("%H%M%S"))
            #print >> sys.stderr, "HDF5: %s" % (fileName)
        except Exception as e:
            self.msgPrint("savePlot() Exception: %s" % e, bError=True)

        try:
            self.hdfFile = h5py.File(fileName, 'w')
        except IOError as e:
            self.msgPrint("Failed to open HDF file with error: %s" % e, bError=True)
            raise(e)

        self.nrows = 32
        self.ncols = 128

        self.imagesWritten = 0
        currentImage = 0
        
        # Create group structure
        self.lpdGroup = self.hdfFile.create_group('lpd')
        self.metaGroup = self.lpdGroup.create_group('metadata')
        self.dataGroup = self.lpdGroup.create_group('data')
        
        # Create data group entries    
        self.imageDs = self.dataGroup.create_dataset('image', (1, self.nrows, self.ncols), 'uint16', chunks=(1, self.nrows, self.ncols), 
                                        maxshape=(None,self.nrows, self.ncols))
        self.timeStampDs   = self.dataGroup.create_dataset('timeStamp',   (1,), 'float64', maxshape=(None,))
        self.trainNumberDs = self.dataGroup.create_dataset('trainNumber', (1,), 'uint32', maxshape=(None,))
        self.imageNumberDs = self.dataGroup.create_dataset('imageNumber', (1,), 'uint32', maxshape=(None,))

        # Write data and info to file
        self.imageDs.resize((self.imagesWritten+1, self.nrows, self.ncols))
        self.imageDs[self.imagesWritten,...] = lpdImage
        
        self.trainNumberDs.resize((self.imagesWritten+1, ))
        self.trainNumberDs[self.imagesWritten] = 0
        
        self.imageNumberDs.resize((self.imagesWritten+1, ))
        self.imageNumberDs[self.imagesWritten] = currentImage

        # Close the file
        self.hdfFile.close()

    def msgPrint(self, message, bError=False):
        ''' Send message to LpdFemGuiMainTestTab to be displayed there '''
        self.messageSignal.emit(message, bError)
