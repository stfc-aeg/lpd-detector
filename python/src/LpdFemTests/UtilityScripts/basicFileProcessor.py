'''
    basicFileProcessor.py -  A starting point for processing and analysing LCLS data using Python
	
	Created: 29 July 2013

	Author: ckd27546
'''

import matplotlib
import matplotlib.pyplot as plt
import argparse, h5py, os
import numpy as np

def basicFileProcessor():
	
	# Execute parser to obtain command line argument(s)
	args = parseArgs()

	fileName = args.filename
	
	# Check if file exists
	if not os.path.isfile(fileName):
		
		print "The file %r does not exist." % fileName, "\n"
		
	else:
		print "Processing %r.." % fileName

		try:
			# Open file
			hdfFile = h5py.File(fileName, 'r')
			# Read in the meta data
			meta = hdfFile['/lpd/metadata']
			# Count number of meta parameters
			numParams = meta.attrs.items()
	
			keys = meta.attrs.keys()
			values = meta.attrs.values()
			
			# Iterate over meta data and pick out Run Number and Number of Images
			for idx in range(len(numParams)):
	
				if keys[idx] == "runNumber":
					runNumber = values[idx]
				
				elif keys[idx] == "numTrains":
					numTrains = values[idx]
	
		except IOError as e:
			print "Error while extracting meta data: ", e, " aborting.."
			return
	
		try:
			imgData = hdfFile['/lpd/data/image']
			
			# Extract all trains of image data into numpy object
			pixelValues = imgData.value
			
			# Mask off gain selection bits from data (if present)
			pixelValues = pixelValues & 0xFFF
			
			# Create an array to contain  pixel processing results
			pixelArray = np.zeros([256*256], dtype=np.uint16)
			
			rowLength = len(pixelValues[0])
			# Go through every pixel of every image, and sum each pixel
			for image in range(len(pixelValues)):
				for row in range(len(pixelValues[0])):
					for col in range(len(pixelValues[0][0])):
						
						pixelArray[row*rowLength + col] += pixelValues[image][row][col]
			
			# Go through each index and divide by number of images
			for idx in range(len(pixelArray)):
				
				# Slower using floating point division but round to nearest integer
#				pixelArray[idx] = int( round(pixelArray[idx] / (numTrains + 0.0) ))
				
				#Quicker (~0.5 seconds)  using integer point precision..
				pixelArray[idx] = pixelArray[idx] / numTrains
	
			# Close file
			hdfFile.close()
	
		except Exception as e:
			print "Error extracting image data: ", e, " aborting.."
		
		# Plot the data
		fig = plt.figure(1)
		ax = fig.add_subplot(111)
		img = ax.imshow(pixelArray.reshape(256, 256), interpolation='nearest', vmin='0', vmax='4095')
		plt.title("Plot of Run %r's pixels' average values" % runNumber)
	
		# Add a colour bar
		axc, kw = matplotlib.colorbar.make_axes(ax)
		cb = matplotlib.colorbar.Colorbar(axc, img)
		img.colorbar = cb

		plt.show()

		#TODO: Write pixelArray to file


def parseArgs():

	parser = argparse.ArgumentParser(description="Process a specified HDF5 file working out each pixel average across images", epilog="Example: python basicFileProcessor.py /data/lpd/lpdData-00142.hdf5")

	parser.add_argument("filename", help='The absolute path to HDF5 data file to investigate')

	args = parser.parse_args()

	return args

if __name__ == '__main__':

	basicFileProcessor()
	
	
	

	########## EXTRA INFORMATION: META DATA CONTENTS ##########
	'''
	numTrains                      #= 100
	triggerDelay                   #= 925
	femAsicGainOverride            #= 11
	pixelGain                      #= 0
	hvBiasVolts                    #= 200.0
	runNumber                      #= 384
	femAsicPixelFeedbackOverride   #= 0
	'''
	'''
	#femAddress                     = 192.168.2.2
	#readoutParamFile               = /home/lpduser/lpdSoftware/config/superModuleReadout.xml
	#fastParamFile                  = /home/lpduser/lpdSoftware/config/ASIC_Commands_LCLS_10Triggers_MemoryWipe.xml
	numTrains                      = 100
	#evrRecordEnable                = 1
	#fileWriteEnable                = 1
	triggerDelay                   = 925
	#femPort                        = 6969
	#dataFilePath                   = /data/lpd
	femAsicGainOverride            = 11
	#evrMcastGroup                  = 239.255.16.17
	pixelGain                      = 0
	#slowParamFile                  = /home/lpduser/lpdSoftware/config/AsicSlowParameters.xml
	#liveViewEnable                 = 1
	hvBiasVolts                    = 200.0
	#liveViewOffset                 = 4
	#pwrAutoUpdate                  = 0
	runNumber                      = 384
	#liveViewDivisor                = 10
	#externalTrigger                = 1
	#evrMcastInterface              = 172.21.22.69
	#femAddr                        = 192.168.2.2
	#pwrUpdateInterval              = 2
	#connectionTimeout              = 5.0
	femAsicPixelFeedbackOverride   = 0
	'''
	
	'''
def lookup(value):
    for i1 in range(len(imageData[0])):
        for i2 in range(len(imageData[0][0])):
                for i3 in range(256):
                        if imageData[i1][i2][i3] == value:
                                print "imageData[%4i][%4i][%4i] = %4i" % (i1, i2, i3, imageData[i1][i2][i3])
                                return

################

len(imageData[imageOffsetPrev,:,:][0][0])

def test(threshold):
	for row in range(256):
		for col in range(256):
			pxlPrevImg = imageData[imageOffsetPrev,:,:][row][col]
			pxlNextImg = imageData[imageOffsetNext,:,:][row][col]

			# Update image by subtracting average of previous' and next' values
			imageData[imgOffset,:,:][row][col] -= (pxlPrevImg + pxlNextImg) / 2


			if pxlPrevImg == threshold:
				print "At [%4i][%4i], pxlPrevImg = %4i, pxlNextImg = %4i" % (row, col, pxlPrevImg, pxlNextImg)
				return



####### !!! #######

HDF5		filesystem
----		---------
dataset		file
attribute	metadata/header
group		directory
	'''
