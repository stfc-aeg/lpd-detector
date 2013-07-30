'''
    dumpRunParameters.py -  Process all files would in a specified directory, obtaining and displaying a few choice meta
	
	Created: 17 May 2013

	Author: ckd27546
'''

import argparse
import numpy as np
import h5py
#import matplotlib
#import matplotlib.pyplot as plt
import os, sys, time
import glob

def dumpRunParameters():

	args = parseArgs()

	# Is it a valid directory?
	if not os.path.isdir(args.filePath):
		
		print "The directory %r does not exist." % args.filePath, "\n"

	else:

		try:
			targetFiles = glob.glob(args.filePath+"*.hdf5")
	
			#paramLabels = ["runNumber", "numTrains", "triggerDelay", "femAsicGainOverride", "pixelGain", "hvBiasVolts", "femAsicPixelFeedbackOverride"]
			# Temporary storage for each run's meta data
			paramValues = []
			# Placefolder for each run and it's six associated meta variables
			resultsList = []
	
			
			for fileName in targetFiles:
				# Open file
				hdfFile = h5py.File(fileName, 'r')
				# Read in the meta data
				meta = hdfFile['/lpd/metadata']
				# Count number of meta parameters
				numParams = meta.attrs.items()
	
				# Clear values from previous iteration
				paramValues = [-1, -1, -1, -1, -1, -1, -1]
				
				keys = meta.attrs.keys()
				values = meta.attrs.values()
				
				# Iterate over meta data and pick out the interesting info
				for idx in range(len(numParams)):
	
					if keys[idx] == "runNumber":
						runNumber = values[idx]
						paramValues[0] = runNumber
					
					elif keys[idx] == "numTrains":
						numTrains = values[idx]
						paramValues[1] = numTrains
						
					elif keys[idx] == "triggerDelay":
						triggerDelay = values[idx]
						paramValues[2] = triggerDelay
						
					elif keys[idx] == "femAsicGainOverride":
						femAsicGainOverride = values[idx]
	
						#Map 0, 8, 9, 11 => default, 100x, 10x, 1x
						strDescribe = ""
						if femAsicGainOverride == 0:
							strDescribe = "(default) "
						elif femAsicGainOverride == 8:
							strDescribe = "(100x)    "
						elif femAsicGainOverride == 9:
							strDescribe = "(10x)     "
						elif femAsicGainOverride == 11:
							strDescribe = "(1x)      "
						else:
							strDescribe == "(Invalid)"
	
						paramValues[3] = str(femAsicGainOverride) + strDescribe 
						
					elif keys[idx] == "pixelGain":
						pixelGain = values[idx]
						paramValues[4] = pixelGain
								
					elif keys[idx] == "hvBiasVolts":
						hvBiasVolts = values[idx]
						paramValues[5] = hvBiasVolts
						
					elif keys[idx] == "femAsicPixelFeedbackOverride":
						femAsicPixelFeedbackOverride = values[idx]
	
						#Map 0, 1 => 0 = 5pF, 50pF
						strDescribe = ""
						if femAsicPixelFeedbackOverride == 0:
							strDescribe = "(5pF)    "
						elif femAsicPixelFeedbackOverride == 1:
							strDescribe = "(50pF)   "
						else:
							strDescribe = "(Invalid)"
	
						paramValues[6] = str(femAsicPixelFeedbackOverride) + strDescribe
	
				# Temporary string to store meta data
				strResults = ""
	
				# Concatenate contents for each different quantities - skip runNumber (index 0)
				for idx in range(1, len(paramValues)):
					strResults += "{0:<19} ".format(paramValues[idx])
				
				# Append meta data from each file
				resultsList.append([runNumber, strResults])
				
	
		except IOError as e:
			print "Error: ", e, " aborting.."
			return
	
		# Print labels for each column if any hdf5 files found
		if len(resultsList) > 0:
			print "run", "   numTrains", "          triggerDelay", "       femAsicGainOverride", "pixelGain", "          hvBiasVolts", "        femAsicPixelFeedbackOverride"
	
			# Sort list after run number
			resultsList.sort()
			
			# print information
			for idx in resultsList:
				print idx
		else:
			print "No hdf5 files in %r to analyse.\n" % args.filePath

def parseArgs():

	parser = argparse.ArgumentParser(description="Extract predefined set of meta parameters from all HDF files in a folder", epilog="Example: python dumpRunParameters.py /u/ckd27546/LCLS_Data/")

	parser.add_argument("filePath", help='The path to HDF5 data file(s) to investigate')

	args = parser.parse_args()

	return args

if __name__ == '__main__':

	dumpRunParameters()
	
	
	

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
