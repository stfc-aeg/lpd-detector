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

        self.imgObject.set_data(lpdImage)
#        self.axes.draw_artist(self.imgObject)
        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(self.timeStamp))
        self.titleText = 'Train %d Image %d %sModule %d: %s' % (self.train, self.image, "\n", self.module, dateStr)
        self.axes.set_title(self.titleText)
        self.canvas.draw()

        # Create new folder
        self.prepareFilePath()
        # Save image to hdf5 file
        self.savePlot(lpdImage)

        # Testing saving figured file..
        timestamp = time.time()
        st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S_%f')
        fname = self.filePath + "savedFigure_%s" % st
        self.fig.savefig(fname)

    def prepareFilePath(self):

        timestamp = time.time()
        st = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        self.filePath = "/u/ckd27546/workspace/tinkering/savedData_%s/" % st
        
        # Create directory if it doesn't exist
        self.ensure_dir(self.filePath)

    def ensure_dir(self, f):
        ''' Create the argument as a directory unless it already exists '''
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
        else:
            print >> sys.stderr, "WARNING: the folder '%s' already exists" % f

    def savePlot(self, lpdImage):

        fileName = self.filePath + "lpdData.hdf5"
        print >> sys.stderr, "Creating HDF5 data file %s" % fileName

        print "Creating HDF5 data file %s" % fileName
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

