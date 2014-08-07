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
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

class LpdFemGuiAnalysisWindow(QtGui.QDialog):

    REALIMAGE   = 0
    FAULTYIMAGE = 1

    RHS_MODULE = 15
    LHS_MODULE = 14 #0 # 0 is the REAL LHS module !

    trainSignal  = QtCore.pyqtSignal(object)
    imageSignal  = QtCore.pyqtSignal(object)
    moduleSignal = QtCore.pyqtSignal(object)
    timeStampSignal = QtCore.pyqtSignal(object)
    logPathSignal = QtCore.pyqtSignal(str)
    dataSignal   = QtCore.pyqtSignal(object, object, int)
    
    matplotlib.rcParams.update({'font.size': 8})
    
    def __init__(self, parent=None):
 
        QtGui.QDialog.__init__(self, parent)

        moduleType = "Asic Module"
        self.nrows = 32
        self.ncols = 128
        
        self.setWindowTitle('Plotting data from %s' % moduleType)

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
        for idx in range(2):
            
            axesObject = self.fig.add_subplot(2, 1, idx+1)
            self.axes.extend([axesObject])

            # Disable up the X and Y ticks
            self.axes[idx].set_xticks([])
            self.axes[idx].set_yticks([])
    
            # Create an empty plot
            self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)

            # Define colour range, colourmap according to plot number
            if idx == 0:
                vMax = '4095'
                cMap = defaultColourMap
            else:
                vMax = '1'
                cMap = 'binary'

            imgObject = self.axes[idx].imshow(self.data, cmap=cMap, interpolation='nearest', vmin='0', vmax=vMax)
            self.img.extend([imgObject])

            # Place plot closer to center of figure
#            self.axes[idx].set_position([0.125, 0.4, 0.8, 0.5])
    
            # Create nd show a colourbar
            axc, kw = matplotlib.colorbar.make_axes(self.axes[idx], orientation='horizontal')
            cb = matplotlib.colorbar.Colorbar(axc, self.img[idx], orientation='horizontal')
            self.img[idx].colorbar = cb

            # Add vertical lines to differentiate between the ASICs
            for i in range(16, self.ncols, 16):
                self.axes[idx].vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
            
            self.canvas.draw()

        # Bind the 'pick' event for clicking on one of the bars
        #
        #self.canvas.mpl_connect('pick_event', self.on_pick)
        
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
#        print >> sys.stderr, "trainUpdate received:  %s" % train
        
    def imageUpdate(self, image):
        self.image = image
#        print >> sys.stderr, "imageUpdate received: %s" % image
        
    def moduleUpdate(self, module):
        self.module = module
#        print >> sys.stderr, "moduleUpdate received: %s" % module
        
    def timeStampUpdate(self, timeStamp):
        self.timeStamp = timeStamp
#        print >> sys.stderr, "timeStampUpdate received: %s" % timeStamp

    def logPathUpdate(self, logPath):
        self.logPath = str(logPath)
#        print >> sys.stderr, "logPathUpdate received    : %s, %s" % (logPath, type(logPath))
#        print >> sys.stderr, "logPathUpdate self.logPath: %s, %s" % (self.logPath, type(self.logPath))

    def setModuleType(self, moduleNumber):
        ''' Helper function '''

        self.moduleNumber = moduleNumber
        if moduleNumber == LpdFemGuiAnalysisWindow.LHS_MODULE:    self.moduleString = "LHS"
        elif moduleNumber == LpdFemGuiAnalysisWindow.RHS_MODULE:  self.moduleString = "RHS"
        else:
            self.msgPrint("Error setting module type: Unrecognised module number: %d" % moduleNumber, bError=True)

    def windowUpdate(self, lpdActualImage, lpdFaultyImage, moduleNumber):
        
        # Convert module number into the string
        self.setModuleType(moduleNumber)
        
        # Plot the captured image
        self.img[LpdFemGuiAnalysisWindow.REALIMAGE].set_data(lpdActualImage)

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Train %d Image %d %sModule %s: %s' % (self.train, self.image, "\n", self.moduleString, dateStr)
        self.axes[LpdFemGuiAnalysisWindow.REALIMAGE].set_title(self.titleText)

        # Plot the black/white image (which shows which pixel(s) are dead)
        self.img[LpdFemGuiAnalysisWindow.FAULTYIMAGE].set_data(lpdFaultyImage)

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Module %s: Map of faulty pixel(s)' % self.moduleString
        self.axes[LpdFemGuiAnalysisWindow.FAULTYIMAGE].set_title(self.titleText)
        self.canvas.draw()

#        # Create new folder
#        self.prepareFilePath()
        # Save image to hdf5 file (but not the black/white image)
        self.savePlot(lpdActualImage)

        # Testing saving figure to file.. (which contains both images)
#        timestamp = time.time()
#        st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        fname = self.logPath + "savedFigure" #_%s" % st
        self.fig.savefig(fname)

#    def prepareFilePath(self):
#
#        timestamp = time.time()
#        st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
#        self.filePath = "/u/ckd27546/workspace/tinkering/savedData_%s/" % st
#
        # Create directory if it doesn't exist - NOT required, sorted by LpdFemGuiMainTestTab instance
#        self.ensure_dir(self.filePath)
#
#    def ensure_dir(self, f):
#        ''' Create the argument as a directory unless it already exists '''
#        d = os.path.dirname(f)
#        if not os.path.exists(d):
#            os.makedirs(d)
#        else:
#            print >> sys.stderr, "WARNING: the folder '%s' already exists" % f

    def savePlot(self, lpdImage):

        fileName = self.logPath + "lpdData.hdf5"
#        print >> sys.stderr, "Creating HDF5 data file %s" % fileName

        print "Creating HDF5 data file %s, of type: %s" % (fileName, type(fileName))
        try:
            self.hdfFile = h5py.File(fileName, 'w')
        except IOError as e:
            print "Failed to open HDF file with error: %s" % e
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
        self.imageDs[self.imagesWritten,...] = lpdImage # self.imageArray
        
#        self.timeStampDs.resize((self.imagesWritten+1, ))
#        self.timeStampDs[self.imagesWritten] = lpdFrame.timeStampSof

#        print "arguments: ", type(args), dir(args)
        
        self.trainNumberDs.resize((self.imagesWritten+1, ))
        self.trainNumberDs[self.imagesWritten] = 0  # self.args.train
        
        self.imageNumberDs.resize((self.imagesWritten+1, ))
        self.imageNumberDs[self.imagesWritten] = currentImage

        # Close the file
        self.hdfFile.close()

