'''
Created on July 17, 2014

@author: ckd27546    (Based upon LpdFemGuiLiveViewWindow.py)
'''

from LpdDataContainers import LpdImageContainer
from LpdFemClient.LpdFemClient import LpdFemClient

from PyQt4 import QtCore, QtGui
from utilities import *
import sys, time

import numpy as np

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

class LpdFemGuiAnalysisWindow(QtGui.QDialog):
    
    trainSignal  = QtCore.pyqtSignal(object)
    imageSignal  = QtCore.pyqtSignal(object)
    moduleSignal = QtCore.pyqtSignal(object)
    timeStampSignal = QtCore.pyqtSignal(object)
    runNumberSignal = QtCore.pyqtSignal(object)
    dataSignal   = QtCore.pyqtSignal(object)
    
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
        
        self.axes = self.fig.add_subplot(111)
 
        # Disable up the X and Y ticks
        self.axes.set_xticks([])
        self.axes.set_yticks([])
       
        self.imageSize = self.nrows * self.ncols

        # Create an empty plot
        self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)                   
        self.imgObject = self.axes.imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')

        cBarPosn = 'horizontal'
        # Place plot closer to center of figure
        self.axes.set_position([0.125, 0.4, 0.8, 0.5])

        # Create nd show a colourbar
        axc, kw = matplotlib.colorbar.make_axes(self.axes, orientation=cBarPosn)
        cb = matplotlib.colorbar.Colorbar(axc, self.imgObject, orientation=cBarPosn)
        self.imgObject.colorbar = cb

        # Add vertical lines to differentiate between the ASICs
        for i in range(16, self.ncols, 16):
            self.axes.vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
        
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
        self.runNumberSignal.connect(self.runNumberUpdate)
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
        print >> sys.stderr, "moduleUpdate received: %s" % module
        
    def timeStampUpdate(self, timeStamp):
        self.timeStamp = timeStamp
#        print >> sys.stderr, "timeStampUpdate received: %s" % timeStamp

    def runNumberUpdate(self, runNumber):
        self.runNumber = runNumber
#        print >> sys.stderr, "runNumberUpdate received: %s" % runNumber

    def windowUpdate(self, lpdImage):
        
#        print >> sys.stderr, "windowUpdate successfully called !"

#        # Mask off gain bits
#        lpdImage.imageArray = lpdImage.imageArray & 0xfff
#        self.imgObject.set_data(lpdImage.imageArray)
#        self.axes.draw_artist(self.imgObject)
#        self.axes.set_title("Run %d Train %d Image %d" % (lpdImage.runNumber, lpdImage.frameNumber, lpdImage.imageNumber))
        self.imgObject.set_data(lpdImage)
#        self.axes.draw_artist(self.imgObject)
        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Run %d Train %d Image %d%sModule %d: %s' % (self.runNumber, self.train, self.image, "\n", self.module, dateStr)
        self.axes.set_title(self.titleText)
        self.canvas.draw()

