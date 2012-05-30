/*
 * ExcaliburFemClient.cpp - EXCALIBUR FEM client class implementation
 *
 *  Created on: 7 Dec 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"
#include "ExcaliburFrontEndDevices.h"
#include "asicControlParameters.h"
#include "mpx3Parameters.h"
#include "time.h"
#include <map>
#include <iostream>
#include <iomanip>
#include <sstream>

ExcaliburFemClient::ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
		const CtlConfig* aConfig, unsigned int aTimeoutInMsecs) :
	FemClient(aConfig->femAddress, aConfig->femPort, aTimeoutInMsecs),
	mFemDataHostPort(kHostDataPort),
	mCtlHandle(aCtlHandle),
	mCallbacks(aCallbacks),
	mConfig(aConfig),
	mAsicDataReorderMode(reorderedDataMode),
	mNumSubFrames(2)
{

	// Initialize MPX3 DAC settings, values and pixel config caches to zero
	for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
	{
		for (unsigned int iDac = 0; iDac < numExcaliburDacs; iDac++)
		{
			mMpx3DacCache[iChip][iDac] = 0;
		}

		for (unsigned int iConfig= 0; iConfig < numPixelConfigs; iConfig++) {
			for (unsigned int iPixel = 0; iPixel < kNumPixelsPerAsic; iPixel++)
			{
				mMpx3PixelConfigCache[iChip][iConfig][iPixel]       = 0;
			}
		}

		// Initialise default values for some standard parameters used in all
		// OMR transactions
		mMpx3OmrParams[iChip].readWriteMode         = sequentialReadWriteMode;
		mMpx3OmrParams[iChip].polarity              = electronPolarity;
		mMpx3OmrParams[iChip].readoutWidth          = readoutWidth8;
		mMpx3OmrParams[iChip].unusedPTEnable        = 0;
		mMpx3OmrParams[iChip].testPulseEnable       = 0;
		mMpx3OmrParams[iChip].counterDepth          = counterDepth12;
		mMpx3OmrParams[iChip].columnBlock           = 0;
		mMpx3OmrParams[iChip].columnBlockSelect     = 0;
		mMpx3OmrParams[iChip].rowBlock              = 0;
		mMpx3OmrParams[iChip].rowBlockSelect        = 0;
		mMpx3OmrParams[iChip].equalizeTHH           = 0;
		mMpx3OmrParams[iChip].colourMode            = monochromeMode;
		mMpx3OmrParams[iChip].pixelComEnable        = 0;
		mMpx3OmrParams[iChip].shutterCtr            = 0;
		mMpx3OmrParams[iChip].fuseSel               = 0;
		mMpx3OmrParams[iChip].fusePulseWidth        = 0;
		mMpx3OmrParams[iChip].dacSense              = 0;
		mMpx3OmrParams[iChip].dacExternal           = 0;
		mMpx3OmrParams[iChip].externalBandGapSelect = 0;

		// Initialise chip column test pulse enables
		for (unsigned int iCol = 0; iCol < kNumColsPerAsic; iCol++)
		{
			mMpx3ColumnTestPulseEnable[iChip][iCol] = 0;
		}
	}

	// Build callback bundle to be registered with the data receiver
	mCallbackBundle.allocate = boost::bind(&ExcaliburFemClient::allocateCallback, this);
	mCallbackBundle.free     = boost::bind(&ExcaliburFemClient::freeCallback, this, _1);
	mCallbackBundle.receive  = boost::bind(&ExcaliburFemClient::receiveCallback, this, _1, _2);
	mCallbackBundle.signal   = boost::bind(&ExcaliburFemClient::signalCallback, this, _1);

	// Initialise 10GigE UDP firmware block
	// TODO some of these parameters need to be passed in config block and/or derived
	u32 hostPort = kHostDataPort;
	u32 fpgaPort = 8;
	char* fpgaIPAddress = "10.0.2.2";
	char* fpgaMacAddress = "62:00:00:00:00:01";
	char* hostIpAddress = "10.0.2.1";

	u32 rc = this->configUDP(fpgaMacAddress, fpgaIPAddress, fpgaPort, hostIpAddress, hostPort);
	if (rc != 0)
	{
		throw FemClientException((FemClientErrorCode)excaliburFemClientUdpSetupFailed, "Failed to set up FEM UDP firmware block");
	}

	try
	{
		mFemDataReceiver = new FemDataReceiver(mFemDataHostPort);
	}
	catch (boost::system::system_error &e)
	{
		std::ostringstream msg;
		msg << "Failed to create FEM data receiver: " << e.what();
		throw FemClientException((FemClientErrorCode)excaliburFemClientDataReceviverSetupFailed, msg.str());
	}
}


ExcaliburFemClient::~ExcaliburFemClient() {

	// Delete the data receiver object if it was created
	if (mFemDataReceiver)
	{
		delete (mFemDataReceiver);
	}

}

BufferInfo ExcaliburFemClient::allocateCallback(void)
{

	BufferInfo buffer;

	CtlFrame* frame = mCallbacks->ctlAllocate(mCtlHandle);
	mFrameQueue.push_back(frame);

	buffer.addr    = (u8*)(frame->buffer);
	buffer.length = (frame->bufferLength);

	return buffer;

}


void ExcaliburFemClient::freeCallback(int aVal)
{

	mCallbacks->ctlFree(mCtlHandle, 0);

}


void ExcaliburFemClient::receiveCallback(int aFrameCounter, time_t aRecvTime)
{

	// Get the first frame on our queu
	CtlFrame* frame = mFrameQueue.front();

	// Fill fields into frame metadata
	frame->frameCounter = aFrameCounter;
	frame->timeStamp    = aRecvTime;

	// Call the receive callback
	mCallbacks->ctlReceive(mCtlHandle,frame);

	// Pop the frame off the queue
	mFrameQueue.pop_front();

}


void ExcaliburFemClient::signalCallback(int aSignal)
{

	int theSignal;

	switch (aSignal)
	{

	case FemDataReceiverSignal::femAcquisitionComplete:

		theSignal = FEM_OP_ACQUISITIONCOMPLETE;
		std::cout << "Got acquisition complete signal" << std::endl;
		//this->acquireStop();
		//this->stopAcquisition();
		break;

	case FemDataReceiverSignal::femAcquisitionCorruptImage:
		theSignal = FEM_OP_CORRUPTIMAGE;
		std::cout << "Got corrupt image signal" << std::endl;
		break;

	default:
		theSignal = aSignal;
		break;

	}

	mCallbacks->ctlSignal(mCtlHandle, theSignal);

}


void ExcaliburFemClient::freeAllFrames(void)
{

	while (mFrameQueue.size() > 0)
	{
		CtlFrame* frame = mFrameQueue.front();
		mCallbacks->ctlFree(mCtlHandle, frame);
		mFrameQueue.pop_front();
	}

}
void ExcaliburFemClient::command(unsigned int aCommand)
{

	unsigned int theCommand = 0;
	switch (aCommand)
	{
	case FEM_OP_STARTACQUISITION:
		this->startAcquisition();
		//this->toyAcquisition();
		break;

	case FEM_OP_STOPACQUISITION:
		this->stopAcquisition();
		break;

	default:
		theCommand = aCommand;
		FemClient::command(theCommand);
		break;
	}


}

void ExcaliburFemClient::toyAcquisition(void)
{
	std::cout << "Running toy acquisition loop for numFrames=" << mNumFrames << std::endl;
	for (unsigned int iBuffer = 0; iBuffer < mNumFrames; iBuffer++)
	{
		BufferInfo aBuffer = this->allocateCallback();
		this->receiveCallback(iBuffer, (time_t)1234);
	}
	this->signalCallback(FemDataReceiverSignal::femAcquisitionComplete);
	std::cout << "Ending toy acq loop" << std::endl;

}


void ExcaliburFemClient::startAcquisition(void)
{

	// Register callbacks for data receiver
	mFemDataReceiver->registerCallbacks(&mCallbackBundle);

	// Set up the number of frames, acquisition period and time for the receiver thread
	mFemDataReceiver->setNumFrames(mNumFrames);
	mFemDataReceiver->setAcquisitionPeriod(mAcquisitionPeriodMs);
	mFemDataReceiver->setAcquisitionTime(mAcquisitionTimeMs);

	// Set up frame length and header sizes for the data receiver thread
	mFemDataReceiver->setFrameHeaderLength(8);
	mFemDataReceiver->setFrameHeaderPosition(headerAtStart);
	mFemDataReceiver->setNumSubFrames(mNumSubFrames);

	unsigned int frameDataLengthBytes = this->frameDataLengthBytes();
	mFemDataReceiver->setFrameLength(frameDataLengthBytes);

	// Start the data receiver thread
	mFemDataReceiver->startAcquisition();


	// Set up the acquisition DMA controller and arm it
	unsigned int dmaSize = this->asicReadoutDmaSize();
	this->acquireConfig(ACQ_MODE_NORMAL, dmaSize, 0, 0);
	this->acquireStart();

	// Set up counter depth for ASIC control based on current OMR settings
	this->asicControlCounterDepthSet(mMpx3OmrParams[0].counterDepth);

	// Set ASIC data reordering mode
	this->rdmaWrite(0x30000001, mAsicDataReorderMode);

	// Set ASIC mux select - TEMP hack for 1-chip system
	this->asicControlMuxChipSelect(0);

	// Set up the readout length in clock cycles for the ASIC control block
	unsigned int readoutLengthCycles = this->asicReadoutLengthCycles();
	this->asicControlReadoutLengthSet(readoutLengthCycles);

	// Set up the OMR
	{
		mpx3Omr theOmr = this->omrBuild(0, readPixelMatrixC0);
		this->asicControlOmrSet(theOmr);
	}

	// Execute the acquisition
	this->asicControlCommandExecute(asicRunSequentialC0);

}

void ExcaliburFemClient::stopAcquisition(void)
{

	// Send ACQUIRE stop command to the FEM
	// TODO check if stopped already?
	this->acquireStop();

	if (mFemDataReceiver != 0)
	{
		// Ensure that the data receiver has stopped cleanly
		mFemDataReceiver->stopAcquisition();

		// Delete the data receiver
		//delete(mFemDataReceiver);
		//mFemDataReceiver = 0;
	}

	// Reset ASIC control firmware block
	// TODO is this necessary - was put in to reset frame counter
	this->asicControlReset();

}

void ExcaliburFemClient::externalTriggerSet(unsigned int aExternalTrigger)
{
	// Store external trigger setup for use during acquisition start
	mExternalTrigger = aExternalTrigger;
}

void ExcaliburFemClient::operationModeSet(unsigned int aOperationMode)
{
	// Store operation mode for use during acquisition start
	mOperationMode = aOperationMode;
}

void ExcaliburFemClient::numFramesSet(unsigned int aNumFrames)
{

	// Store number of frames to be received locally for config phase
	mNumFrames = aNumFrames;

	// Set up the number of frames for the receiver thread
	//mFemDataReceiver.setNumFrames(aNumFrames);

	// Set up the number of frames in the FEM
	this->asicControlNumFramesSet(aNumFrames);

}

void ExcaliburFemClient::acquisitionPeriodSet(unsigned int aPeriodMs)
{

	mAcquisitionPeriodMs = aPeriodMs;
	// Set up the acquisition period for the receiver thread
	//mFemDataReceiver.setAcquisitionPeriod(aPeriodMs);

	// TODO - add FEM write transaction to set this in FEM too
}

void ExcaliburFemClient::acquisitionTimeSet(unsigned int aTimeMs)
{

	mAcquisitionTimeMs = aTimeMs;

	// Set up the acquisition period for the receiver thread
	//mFemDataReceiver.setAcquisitionTime(aTimeMs);

	// Set up shutter in microseconds
	unsigned long aTimeUs = aTimeMs * 1000;
	this->asicControlShutterDurationSet(aTimeUs);

}

unsigned int ExcaliburFemClient::asicReadoutDmaSize(void)
{

	// Get counter bit depth of ASIC
	unsigned int counterBitDepth = this->counterBitDepth(mMpx3OmrParams[0].counterDepth);

	// DMA size is (numRows * numCols * (numAsics/2) counterDepth /  8 bits per bytes
	unsigned int theLength = (kNumRowsPerAsic * kNumColsPerAsic * (kNumAsicsPerFem / 2) * counterBitDepth) / 8;

	return theLength;
}

unsigned int ExcaliburFemClient::asicReadoutLengthCycles(void)
{

	unsigned int counterBitDepth = this->counterBitDepth(mMpx3OmrParams[0].counterDepth);
	unsigned int readoutBitWidth = this->readoutBitWidth(mMpx3OmrParams[0].readoutWidth);

	unsigned int theLength = (kNumRowsPerAsic * kNumColsPerAsic * counterBitDepth) / readoutBitWidth;

	return theLength;

}

unsigned int ExcaliburFemClient::frameDataLengthBytes(void)
{

	unsigned int frameDataLengthBytes = 0;

	// Get the counter bit depth
	unsigned int counterBitDepth = this->counterBitDepth(mMpx3OmrParams[0].counterDepth);

	// Calculate raw length of ASIC data in bits
	unsigned int asicDataLengthBits = kNumRowsPerAsic * kNumColsPerAsic * kNumAsicsPerFem * counterBitDepth;

	// Get the frame length in bytes. In 12/24-bit re-ordered mode, reordering expands each 12 bit ASIC
	// counter up to 16 bits (two bytes)
	if (mAsicDataReorderMode == reorderedDataMode)
	{
		switch (mMpx3OmrParams[0].counterDepth)
		{
		case counterDepth1:
		case counterDepth4:
			frameDataLengthBytes = (asicDataLengthBits / 8);
			break;

		case counterDepth12:
		case counterDepth24:
			frameDataLengthBytes = ((asicDataLengthBits * 16)  / 12) / 8;
			break;

		default:
			break;
		}
	}

	// Add on size of frame counter(s), which is 8 bytes per subframe
	//frameDataLengthBytes += (mNumSubFrames * 8);

	return frameDataLengthBytes;

}

/// --- Private methods ---

/** getMpx3DacId - map API-level DAC IDs onto internal values
 *
 * This method maps the API-level MPX3 DAC IDs onto the the internal
 * index used to address and store DAC values. It will return a value
 * of unknownDacId for undefined API IDs.
 *
 * @param aId - API-level DAC ID to look up
 * @return excaliburMpx3Dac index for internal addressing of DAC values
 */
mpx3Dac ExcaliburFemClient::getmpx3DacId(int aId)
{
	// Set default resolved ID to unknown DAC
	mpx3Dac resolvedId = unknownDacId;

	// Static STL map to store mapping from API DAC IDs to internal.
	// If map is empty (i.e. at first call to this function, initialise
	// the values.
	static std::map<int, mpx3Dac> dacMap;
	if (dacMap.empty())
	{
		dacMap[FEM_OP_MPXIII_THRESHOLD0DAC]  = threshold0Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD1DAC]  = threshold1Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD2DAC]  = threshold2Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD3DAC]  = threshold3Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD4DAC]  = threshold4Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD5DAC]  = threshold5Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD6DAC]  = threshold6Dac;
		dacMap[FEM_OP_MPXIII_THRESHOLD7DAC]  = threshold7Dac;
		dacMap[FEM_OP_MPXIII_PREAMPDAC]      = preampDac;
		dacMap[FEM_OP_MPXIII_IKRUMDAC]       = ikrumDac;
		dacMap[FEM_OP_MPXIII_SHAPERDAC]      = shaperDac;
		dacMap[FEM_OP_MPXIII_DISCDAC]        = discDac;
		dacMap[FEM_OP_MPXIII_DISCLSDAC]      = discLsDac;
		dacMap[FEM_OP_MPXIII_THRESHOLDNDAC]  = thresholdNDac;
		dacMap[FEM_OP_MPXIII_DACPIXELDAC]    = dacPixelDac;
		dacMap[FEM_OP_MPXIII_DELAYDAC]       = delayDac;
		dacMap[FEM_OP_MPXIII_TPBUFFERINDAC]  = tpBufferInDac;
		dacMap[FEM_OP_MPXIII_TPBUFFEROUTDAC] = tpBufferOutDac;
		dacMap[FEM_OP_MPXIII_RPZDAC]         = rpzDac;
		dacMap[FEM_OP_MPXIII_GNDDAC]         = gndDac;
		dacMap[FEM_OP_MPXIII_TPREFDAC]       = tpRefDac;
		dacMap[FEM_OP_MPXIII_FBKDAC]         = fbkDac;
		dacMap[FEM_OP_MPXIII_CASDAC]         = casDac;
		dacMap[FEM_OP_MPXIII_TPREFADAC]      = tpRefADac;
		dacMap[FEM_OP_MPXIII_TPREFBDAC]      = tpRefBDac;
	}

	// Check if the DAC ID is present in the map. If so, resolve
	// to the internal value.
	if (dacMap.count(aId))
	{
		resolvedId = dacMap[aId];
	}

	return resolvedId;
}

mpx3PixelConfig ExcaliburFemClient::getMpx3PixelConfigId(int aConfigId)
{
	// Set default resolved ID to unknown config
	mpx3PixelConfig resolvedId = unknownPixelConfig;

	// Static STL map to store amping from API config IDs to internal.
	// If map is empty (i.e. at first call to this function, initialise
	// the values
	static std::map<int, mpx3PixelConfig> pixelConfigMap;
	if (pixelConfigMap.empty())
	{
		pixelConfigMap[FEM_OP_MPXIII_PIXELMASK]       = pixelMaskConfig;
		pixelConfigMap[FEM_OP_MPXIII_PIXELTHRESHOLDA] = pixelThresholdAConfig;
		pixelConfigMap[FEM_OP_MPXIII_PIXELTHRESHOLDB] = pixelThresholdBConfig;
		pixelConfigMap[FEM_OP_MPXIII_PIXELGAINMODE]   = pixelGainModeConfig;
		pixelConfigMap[FEM_OP_MPXIII_PIXELTEST]       = pixelTestModeConfig;
	}

	// Check if the config ID is present in the map. If so, resolve to
	// the internal value
	if (pixelConfigMap.count(aConfigId))
	{
		resolvedId = pixelConfigMap[aConfigId];
	}

	return resolvedId;
}

mpx3Omr ExcaliburFemClient::omrBuild(unsigned int aChipIdx, mpx3OMRMode aMode)
{

	mpx3Omr theOMR;

	theOMR.raw = (((u64)aMode                                          & 0x7  ) << 0 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].readWriteMode         & 0x1  ) << 3 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].polarity              & 0x1  ) << 4 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].readoutWidth          & 0x3  ) << 5 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].unusedPTEnable        & 0x1  ) << 7 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].testPulseEnable       & 0x1  ) << 8 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].counterDepth          & 0x3  ) << 9 ) |
				 (((u64)mMpx3OmrParams[aChipIdx].columnBlock           & 0x7  ) << 11) |
				 (((u64)mMpx3OmrParams[aChipIdx].columnBlockSelect     & 0x1  ) << 14) |
				 (((u64)mMpx3OmrParams[aChipIdx].rowBlock              & 0x7  ) << 15) |
				 (((u64)mMpx3OmrParams[aChipIdx].rowBlockSelect        & 0x1  ) << 18) |
			     (((u64)mMpx3OmrParams[aChipIdx].equalizeTHH           & 0x1  ) << 19) |
			     (((u64)mMpx3OmrParams[aChipIdx].colourMode            & 0x1  ) << 20) |
			     (((u64)mMpx3OmrParams[aChipIdx].pixelComEnable        & 0x1  ) << 21) |
			     (((u64)mMpx3OmrParams[aChipIdx].shutterCtr            & 0x1  ) << 22) |
			     (((u64)mMpx3OmrParams[aChipIdx].fuseSel               & 0x1F ) << 23) |
			     (((u64)mMpx3OmrParams[aChipIdx].fusePulseWidth        & 0x1FF) << 28) |
			     (((u64)mMpx3OmrParams[aChipIdx].dacSense              & 0x1F ) << 37) |
			     (((u64)mMpx3OmrParams[aChipIdx].dacExternal           & 0x1F ) << 42) |
			     (((u64)mMpx3OmrParams[aChipIdx].externalBandGapSelect & 0x1  ) << 47);

	return theOMR;
}

unsigned int ExcaliburFemClient::counterBitDepth(mpx3CounterDepth aCounterDepth)
{
	unsigned int counterBitDepth = 0;

	switch (aCounterDepth)
	{
	case counterDepth1:
		counterBitDepth = 1;
		break;

	case counterDepth4:
		counterBitDepth = 4;
		break;

	case counterDepth12:
		counterBitDepth = 12;
		break;

	case counterDepth24:
		counterBitDepth = 12; // 24bit counter = 2x12 readout
		break;

	default:
		break;
	}

	return counterBitDepth;

}

 unsigned int ExcaliburFemClient::readoutBitWidth(mpx3ReadoutWidth aReadoutWidth)
 {
	 unsigned int readoutBitWidth = 0;

	 switch (aReadoutWidth)
	 {
	 case readoutWidth1:
		 readoutBitWidth = 1;
		 break;
	 case readoutWidth2:
		 readoutBitWidth = 2;
		 break;

	 case readoutWidth4:
		 readoutBitWidth = 4;
		 break;

	 case readoutWidth8:
		 readoutBitWidth = 8;
		 break;

	 default:
		 break;
	 }

	 return readoutBitWidth;

 }
