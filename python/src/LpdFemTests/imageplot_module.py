from matplotlib import cbook
import matplotlib.pyplot as plt
import matplotlib.text as text
from matplotlib.widgets import Button

import argparse
import numpy as np
import h5py
import matplotlib
import sys, time
from LpdFemGui.LpdReadoutConfig import *

class imagePlot():
    
    def __init__(self):

        # Ask the user for data file, image, train..
        self.args = parseArgs()

        (self.numRows, self.numCols) = (32, 128)
        
        # Set X and Y ticks to match data size
        (xStart, xStop, xStep)  = (16, 128, 16)
        (yStart, yStop, yStep)  = (8, 32, 8)
        (self.xlist, self.ylist) = ([], [])
        # Generate list of xticks to label the x axis
        for i in range(xStart, xStop, xStep):
            self.xlist.append(i)
        
        # Generate yticks for the y-axis
        for i in range(yStart, yStop, yStep):
            self.ylist.append(i)

        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        # Create the figure and title
        self.fig = plt.figure(1)
        self.ax = self.fig.add_subplot(111)
        self.mainTitle = plt.title("")
        
        # Previous, next buttons inspired by example: matplotlib.org/1.3.1/examples/widgets/buttons.html

        # Previous, Next ASIC module buttons..
        decModule = plt.axes([0.85, 0.115, 0.07, 0.045])
        incModule = plt.axes([0.92, 0.115, 0.07, 0.045])    #  [left, bottom, width, height] 
        incrementModule = Button(incModule, '+M')
        incrementModule.on_clicked(self.nextModule)
        decrementModule = Button(decModule, '-M')
        decrementModule.on_clicked(self.prevModule)

        # Previous, Next image buttons..
        decImage = plt.axes([0.85, 0.06, 0.07, 0.045])
        incImage = plt.axes([0.92, 0.06, 0.07, 0.045])    #  [left, bottom, width, height] 
        incrementImg = Button(incImage, '+I')
        incrementImg.on_clicked(self.nextImage)
        decrementImg = Button(decImage, '-I')
        decrementImg.on_clicked(self.prevImage)

        # Previous, Next train buttons..
        decTrain = plt.axes([0.85, 0.005, 0.07, 0.045])
        incTrain = plt.axes([0.92, 0.005, 0.07, 0.045])    #  [left, bottom, width, height] 
        incrementTrain = Button(incTrain, '+T')
        incrementTrain.on_clicked(self.nextTrain)
        decrementTrain = Button(decTrain, '-T')
        decrementTrain.on_clicked(self.prevTrain)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        self.img = self.ax.imshow(imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols], interpolation='nearest', vmin='0', vmax='4095')
        self.ax.set_xticks(self.xlist)
        self.ax.set_yticks(self.ylist)

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Add a colour bar
        axc, kw = matplotlib.colorbar.make_axes(self.ax)
        cb = matplotlib.colorbar.Colorbar(axc, self.img)
        self.img.colorbar = cb

        self.artist = self.fig.get_children()
        
        DataCursor(self.artist[1], imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])

        plt.show()    
    
    def asicStartingRowColumn(self, module):
        ''' Determining upper left corner's row/col coordinates according to selected ASIC module '''

        (row, column) = (-1, -1)
        if module == 0:   (row, column) = (0, 128)    # ASIC module #1
        elif module == 1: (row, column) = (32, 128)   # ASIC module #2
        elif module == 2: (row, column) = (64, 128)   # ASIC module #3
        elif module == 3: (row, column) = (96, 128)   # ASIC module #4
        elif module == 4: (row, column) = (128, 128)  # ASIC module #5
        elif module == 5: (row, column) = (160, 128)  # ASIC module #6
        elif module == 6: (row, column) = (192, 128)  # ASIC module #7
        elif module == 7: (row, column) = (224, 128)  # ASIC module #8

        elif module == 15:(row, column) = (0, 0)      # ASIC module #16
        elif module == 14:(row, column) = (32, 0)     # ASIC module #15
        elif module == 13:(row, column) = (64, 0)     # ASIC module #14
        elif module == 12:(row, column) = (96, 0)     # ASIC module #13
        elif module == 11:(row, column) = (128, 0)    # ASIC module #12
        elif module == 10:(row, column) = (160, 0)    # ASIC module #11
        elif module == 9: (row, column) = (192, 0)    # ASIC module #10
        elif module == 8: (row, column) = (224, 0)    # ASIC module #9

        return (row, column)
    

    def nextModule(self, event):

        self.args.module += 1
        # Is current module number now greater than 15? (max: 16 ASIC/supermodule)
        if self.args.module > 15:
            self.args.module = 0
            # Yes, is the current image number = maximum number of images per train?
            if self.args.image == self.maxImageNumber:
                self.args.image = 0
                # Yes. Is current train number = max train number?
                if self.args.train == self.maxTrainNumber:
                    # Train maximum reached, start over with first image in first train
                    self.args.train = 0
                else:
                    # Image number exceeded but not train number; Increment train
                    self.args.train += 1
            else:
                # No, need only increment current image
                self.args.image += 1

        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        self.img.set_data(imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])

        DataCursor(self.artist[1], imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])
        plt.draw()

    def prevModule(self, event):

        self.args.module -= 1
        # Is current module number now sub zero?
        if self.args.module < 0:
            self.args.module = 15
            # Yes, is the current image number = 0
            if self.args.image == 0:
                self.args.image = self.maxImageNumber            
                # Yes. Is current train number sub zero?
                if self.args.train == 0:
                    # Train minimum reached, start over with last image in last train
                    self.args.train = self.maxTrainNumber
                else:
                    # Image number exceeded but not train number; Decrement train
                    self.args.train -= 1
            else:
                # No, need only decrement current image
                self.args.image -= 1
        
        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        self.img.set_data(imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])

        DataCursor(self.artist[1], imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])
        plt.draw()



    def nextImage(self, event):

        self.args.image += 1
        # Is current image number now greater than images per train?
        if self.args.image > self.maxImageNumber:
            # Yes. Is current train number = max train number?
            if self.args.train == self.maxTrainNumber:
                # Both image and train maximum reached, start over with first image in first train
                self.args.train = 0
                self.args.image = 0
            else:
                # Image number exceeded but not train number; Increment train and reset image
                self.args.train += 1
                self.args.image = 0

        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        thisImage = imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols]
        self.img.set_data(thisImage)

        DataCursor(self.artist[1], thisImage)
        plt.draw()
        # Calculate image average value
        print >> sys.stderr, "Train: %d Image: %d. image average: %f" % (trainNumber, imageNumber, np.average(thisImage))

    def prevImage(self, event):

        self.args.image -= 1
        # Is current image number now sub zero?
        if self.args.image < 0:
            # Yes. Is current train number sub zero?
            if self.args.train == 0:
                # Both image and train minimum reached, start over with last image in last train
                self.args.train = self.maxTrainNumber
                self.args.image = self.maxImageNumber
            else:
                # Image number exceeded but not train number; Decrement train and set image to highest in train
                self.args.train -= 1
                self.args.image = self.maxImageNumber

        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        thisImage = imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols]
        self.img.set_data(thisImage)

        DataCursor(self.artist[1], thisImage)
        plt.draw()
        # Calculate image average
        print >> sys.stderr, "Train: %d Image: %d. image average: %f" % (trainNumber, imageNumber, np.average(thisImage))

    def nextTrain(self, event):

        self.args.train += 1
        # Is current train number now greater than number of trains?
        if self.args.train > self.maxTrainNumber:
            # Yes. Start with first train
                self.args.train = 0

        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        self.img.set_data(imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])

        DataCursor(self.artist[1], imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])
        plt.draw()
    
    def prevTrain(self, event):

        self.args.train -= 1
        # Is current image number now sub zero?
        if self.args.train < 0:
            # Yes. Start over with last train
                self.args.train = self.maxTrainNumber

        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d Module %d : %s' % (runNumber, trainNumber, imageNumber, self.args.module, dateStr)
        self.mainTitle.set_text(titleText)

        # Determine row/col coordinates according to selected ASIC module
        (rowStart, colStart) = self.asicStartingRowColumn(self.args.module)
        self.img.set_data(imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])

        DataCursor(self.artist[1], imageData[rowStart:rowStart+self.numRows, colStart:colStart+self.numCols])
        plt.draw()

    def obtainImageWithInfo(self):
        ''' Open file specified by parser reading specified image'''
        with h5py.File(self.args.fileName, 'r') as hdfFile:
    
            # Read in the train, image counter and timestamp arrays
            trainNumber = hdfFile['/lpd/data/trainNumber'][...]
            imageNumber = hdfFile['/lpd/data/imageNumber'][...]
            timeStamp   = hdfFile['/lpd/data/timeStamp'][...]
    
            # Get max train and image number form arrays
            self.maxTrainNumber = np.amax(trainNumber)
            self.maxImageNumber = np.amax(imageNumber)
    
            # Read in the metadata
            meta = hdfFile['/lpd/metadata']
    
            # Parse the readout configuration XML blob
            readoutConfig = LpdReadoutConfig(meta['readoutParamFile'][0])
            readoutParams = {}
            for (param, val) in readoutConfig.parameters():
                readoutParams[param] = val
    
            # print readoutParams
    
            # Get number of trains from metadata and check array against argument
            numTrains = meta.attrs['numTrains']
            if numTrains != self.maxTrainNumber + 1:
                print "WARNING: mismatch in number of trains between metadata and file"
    
            if self.args.train > self.maxTrainNumber:
                print "ERROR: train number specified (%d) is bigger than maximum in data (%d), quitting" \
                    % (self.args.train, self.maxTrainNumber)
                sys.exit(1)
    
            # Check image number requested in argument is in range too
            if self.args.image > self.maxImageNumber:
                print "ERROR: images number specified (%d) is bigger than maximum in data (%d), quitting" \
                % (self.args.image, self.maxImageNumber)
                sys.exit(1)
    
            # Calculate image offset into array and range check (should be OK)
            imgOffset = (self.args.train * (self.maxImageNumber + 1)) + self.args.image
            if imgOffset > imageNumber.size:
                print "ERROR: calculated image offset (%d) is larger than images stored in data (%d), quitting" \
                % (imgOffset, imageNumber.size)
                sys.exit(1)
    
            # Read in the image array
            image = hdfFile['/lpd/data/image']
            imageData = image[imgOffset,:,:]    # Only read in the specified image

            # Mask off or select gain range from image data
            if self.args.gain == 0:
                imageData[:] = imageData[:] & 0xFFF

            # Invert image if specified
            if self.args.invert != None:
                imageData[:] = 4095 - imageData[:]

            return (imgOffset, timeStamp[imgOffset], meta.attrs['runNumber'], trainNumber[imgOffset], imageNumber[imgOffset], imageData) 

def parseArgs():

    parser = argparse.ArgumentParser(description="Read and Plot one ASIC from a specific LPD image in an HDF file, into a figure where clicking inside the image will produce pixel coordinates and value.")

    parser.add_argument("fileName", help='Name of HDF5 data file to open')
    parser.add_argument("-t", "--train", type=int, default=0,
        help="Select train number to plot")
    parser.add_argument("-i", "--image", type=int, default=0,
        help="Select image number with train to plot")
    parser.add_argument("--invert", help="Invert image data")
    parser.add_argument("-g", "--gain", type=int, default=0, choices=[0, 1, 10, 100],
        help="Select gain range from image (0=mask off gain bits)")
    parser.add_argument("-m", "--module", type=int, default=0,
                        help="ASIC module to select (SuperModule: 0=top right, 16=top left)")

    args = parser.parse_args()

    # Check ASIC module number within the range
    if  not (-1 < args.module < 16):
        print "ERROR: Specified ASIC module number (%d)  is outside the valid range of 0-15, quitting" \
        % ( args.module)
        sys.exit(1)

    return args

# -------           Modified example from stack overflow:                --------- #

class DataCursor(object):
    ''' Modified from example at: http://stackoverflow.com/a/13306887/2903608 '''
    """A simple data cursor widget that displays the x,y location of a
    matplotlib artist when it is selected."""
    def __init__(self, artists, imageData, tolerance=5, offsets=(-20, 20), 
                 #template='x: %0.2f\ny: %0.2f\nPxl: %i',
                 template='Column: %i\nRow: %i\nPixel: %i', display_all=False):
        """Create the data cursor and connect it to the relevant figure.
        "artists" is the matplotlib artist or sequence of artists that will be 
            selected. 
        "imageData" is LPD image data for a super module.
        "tolerance" is the radius (in points) that the mouse click must be
            within to select the artist.
        "offsets" is a tuple of (x,y) offsets in points from the selected
            point to the displayed annotation box
        "template" is the format string to be used. Note: For compatibility
            with older versions of python, this uses the old-style (%) 
            formatting specification.
        "display_all" controls whether more than one annotation box will
            be shown if there are multiple axes.  Only one will be shown
            per-axis, regardless. 
        """
        self.imageData = imageData
        self.template = template
        self.offsets = offsets
        self.display_all = display_all
        if not cbook.iterable(artists):
            artists = [artists]
        self.artists = artists
        self.axes = tuple(set(art.axes for art in self.artists))
        self.figures = tuple(set(ax.figure for ax in self.axes))

        self.annotations = {}
        for ax in self.axes:
            self.annotations[ax] = self.annotate(ax)

        for artist in self.artists:
            artist.set_picker(tolerance)
        for fig in self.figures:
            fig.canvas.mpl_connect('pick_event', self)

    def annotate(self, ax):
        """Draws and hides the annotation box for the given axis "ax"."""
        annotation = ax.annotate(self.template, xy=(0, 0), ha='right',
                xytext=self.offsets, textcoords='offset points', va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
        annotation.set_visible(False)
        return annotation

    def __call__(self, event):
        """Intended to be called through "mpl_connect"."""
        # Rather than trying to interpolate, just display the clicked coords
        # This will only be called if it's within "tolerance", anyway.
        x, y = event.mouseevent.xdata, event.mouseevent.ydata
        annotation = self.annotations[event.artist.axes]
        if x is not None:
            if not self.display_all:
                # Hide any other annotation boxes...
                for ann in self.annotations.values():
                    ann.set_visible(False)
            # Update the annotation in the current axis..
            annotation.xy = x, y
            # Is borders enabled, update x, y were necessary
            (x_offset, y_offset, pixelValue) = (0, 0, -1)
            pixelValue = self.imageData[y, x]
            
            annotation.set_text(self.template % (x+x_offset, y+y_offset, pixelValue))
            annotation.set_visible(True)
            event.canvas.draw()
            
    def borderValueSelected(self, x, y):
        """ Check whether the users clicked on one of the borders """
#        print "=========================="
        # Ensure we are using integer values
        (x, y) = int(x), int(y)
        bBorderValueSelected = False
        if x in range(128, 132):
#            print "x within the border!"
            bBorderValueSelected = True
#        else:
#            print "Not xborder, x: ", x, " range: ", range(128, 132)
        
        # Note: Border adds 4 pixels between adjacent ASICs        
        yBorders = [32, 33, 34, 35, 68, 69, 70, 71, 104, 105, 106, 107, 140, 141, 142, 143, 176, 177, 178, 179, 212, 213, 214, 215, 248, 249, 250, 251]
        
        if y in yBorders:
#            print "y within a  Border!"
            bBorderValueSelected = True
#        else:
#            print "Not yborder, y: ", y, " range: ", yBorders
        return bBorderValueSelected
             
    def adjustCoordByBorders(self, x, y):
        """ Subtract the width of the border(s) from x/y values where applicable """
        (x_offset, y_offset) = (0, 0)
        if (127 < x < (255+4)):
            x_offset -= 4
        
        if (31 < y < (63+4*1)):
            y_offset -= 4
        elif ( (63+4*1) < y < (95+4*2) ):
            y_offset -= 4*2
        elif ( (95+4*2) < y < (127+4*3) ):
            y_offset -= 4*3
        elif ( (127+4*3) < y < (159+4*4) ):
            y_offset -= 4*4
        elif ( (159+4*4) < y < (191+4*5) ):
            y_offset -= 4*5
        elif ( (191+4*5) < y < (223+4*6) ):
            y_offset -= 4*6
        elif ( (223+4*6) < y < (255+4*7) ):
            y_offset -= 4*7
        return x_offset, y_offset
            
if __name__ == '__main__':

    imagePlot()
        
