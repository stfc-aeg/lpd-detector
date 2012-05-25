/*
 * ExcaliburFemClient.h
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#ifndef EXCALIBURFEMCLIENT_H_
#define EXCALIBURFEMCLIENT_H_

#include <femApi.h>
#include <FemClient.h>
#include <FemDataReceiver.h>
#include <list>
#include <time.h>
#include "asicControlParameters.h"
#include "mpx3Parameters.h"

const unsigned int kNumAsicsPerFem = 8;
const unsigned int kNumAsicDpmWords = 8;
const unsigned int kNumPixelsPerAsic = FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y;
const unsigned int kNumColsPerAsic = FEM_PIXELS_PER_CHIP_X;
const unsigned int kNumRowsPerAsic = FEM_PIXELS_PER_CHIP_Y;
const unsigned int kPixelConfigBitsPerPixel = 12;
const unsigned int kPixelConfigBufferSizeBytes = ((FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y * kPixelConfigBitsPerPixel)) / 8;
const unsigned int kPixelConfigBufferSizeWords = kPixelConfigBufferSizeBytes /sizeof(u32);

const unsigned int kHostDataPort = 61649;

typedef enum {
	frontEndEnable = 0,
	frontEndAVDD1  = 2,
	frontEndAVDD2  = 3,
	frontEndAVDD3  = 4,
	frontEndAVDD4  = 5,
	frontEndVDD    = 6,
	frontEndDVDD   = 7
} excaliburFrontEndSupply;


typedef enum
{
	excaliburFemClientIllegalDacId = femClientNextEnumRange,
	excaliburFemClientIllegalConfigId,
	excaliburFemClientIllegalChipId,
	excaliburFemClientIllegalConfigSize,
	excaliburFemClientIllegalCounterDepth,
	excaliburFemClientOmrTransactionTimeout,
	excaliburFemClientUdpSetupFailed,
	excaliburFemClientDataReceviverSetupFailed

} ExcaliburFemClientErrorCode;

class ExcaliburFemClient: public FemClient {
public:
	ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
			const CtlConfig* aConfig, unsigned int aTimeoutInMsecs = 0);
	virtual ~ExcaliburFemClient();

	BufferInfo allocateCallback(void);
	void freeCallback(int aVal);
	void receiveCallback(int aFrameCounter, time_t aRecvTime);
	void signalCallback(int aSignal);

	void command(unsigned int aCommand);

	void startAcquisition(void);
	void stopAcquisition(void);

	void toyAcquisition(void);

	void setNumFrames(unsigned int numFrames);
	void setAcquisitionPeriod(unsigned int aPeriodMs);
	void setAcquisitionTime(unsigned int aTimeMs);
	void freeAllFrames();

	// EXCALIBUR detector front-end functions in ExcaliburFemClientFrontEndDevices.cpp
	void setFrontEndEnable(unsigned int aVal);
	double frontEndTemperatureRead(void);
	double frontEndHumidityRead(void);
	double frontEndDacOutRead(unsigned int aChipId);
	int    frontEndSupplyStatusRead(excaliburFrontEndSupply aSupply);
	void   frontEndDacInWrite(unsigned int aChipId, unsigned int aDacValue);

	// MPX3 ASIC parameter control functions in ExcaliburFemClientMpx3.cpp
	void mpx3DacSet(unsigned int aChipId, int aDacId, unsigned int aDacValue);
	void mpx3DacSenseSet(unsigned int aChipId, int aDac);
	void mpx3DacExternalSet(unsigned int aChipId, int aDac);
	void mpx3DacsWrite(unsigned int aChipId);
	void mpx3CtprWrite(unsigned int aChipId);
	void mpx3PixelConfigSet(unsigned int aChipId, int aConfigId, std::size_t aSize, unsigned short* apValues);
	void mpx3PixelConfigWrite(unsigned int aChipId);
	unsigned int mpx3eFuseIdRead(unsigned int aChipId);
	void mpx3ColourModeSet(int aColourMode);
	void mpx3CounterDepthSet(int aCounterDepth);

	// ASIC control functions in ExcaliburFemClientAsicControl.cpp
	void asicControlOmrSet(mpx3Omr aOmr);
	void asicControlMuxChipSelect(unsigned int aChipIdx);
	void asicControlCommandExecute(asicControlCommand aCommand);
	void asicControlNumFramesSet(unsigned int aNumFrames);
	void asicControlShutterDurationSet(unsigned int aTimeUs);
	void asicControlCounterDepthSet(mpx3CounterDepth aCounterDepth);
	void asicControlReadoutLengthSet(unsigned int aLength);
	void asicControlReset(void);
	void asicControlAsicReset(void);

	unsigned int asicReadoutDmaSize(void);
	unsigned int asicReadoutLengthCycles(void);
	unsigned int frameDataLengthBytes(void);

private:

	u16 frontEndSht21Read(u8 cmdByte);
	u16 frontEndAD7994Read(unsigned int device, unsigned int aChan);
	u8 frontEndPCF8574Read(void);
	void frontEndPCF8574Write(unsigned int aVal);
	void frontEndAD5625Write(unsigned int aDevice, unsigned int aChan, unsigned int aVal);

	mpx3Dac getmpx3DacId(int aId);
	mpx3PixelConfig getMpx3PixelConfigId(int aConfigId);

	mpx3Omr omrBuild(unsigned int aChipId, mpx3OMRMode aMode);
	unsigned int counterBitDepth(mpx3CounterDepth aCounterDepth);
	unsigned int readoutBitWidth(mpx3ReadoutWidth aReadoutWidth);


	mpx3OMRParameters     mMpx3OmrParams[kNumAsicsPerFem];
	unsigned int          mMpx3DacCache[kNumAsicsPerFem][numExcaliburDacs];
	unsigned short        mMpx3PixelConfigCache[kNumAsicsPerFem][numPixelConfigs][kNumPixelsPerAsic];
	unsigned short        mMpx3ColumnTestPulseEnable[kNumAsicsPerFem][kNumColsPerAsic];

	FemDataReceiver*      mFemDataReceiver;
	unsigned int          mFemDataHostPort;
	void*                 mCtlHandle;
	const CtlCallbacks*   mCallbacks;
	const CtlConfig*      mConfig;

	CallbackBundle 		  mCallbackBundle;

	asicDataReorderMode   mAsicDataReorderMode;
	unsigned int          mNumSubFrames;

	std::list<CtlFrame*> mFrameQueue;

	unsigned int          mNumFrames;
	unsigned int          mAcquisitionPeriodMs;
	unsigned int          mAcquisitionTimeMs;

};

#endif /* EXCALIBURFEMCLIENT_H_ */
