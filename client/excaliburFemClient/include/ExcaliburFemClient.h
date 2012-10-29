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
#include "ExcaliburPersonality.h"

const unsigned int kNumAsicDpmWords = 8;
const unsigned int kNumPixelsPerAsic = FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y;
const unsigned int kNumColsPerAsic = FEM_PIXELS_PER_CHIP_X;
const unsigned int kNumRowsPerAsic = FEM_PIXELS_PER_CHIP_Y;
const unsigned int kPixelConfigBitsPerPixel = 12;
const unsigned int kPixelConfigBufferSizeBytes = ((FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y * kPixelConfigBitsPerPixel)) / 8;
const unsigned int kPixelConfigBufferSizeWords = kPixelConfigBufferSizeBytes /sizeof(u32);

const unsigned int kHostDataPort = 61649;

typedef enum
{
	excaliburFemClientIllegalDacId = femClientNextEnumRange,
	excaliburFemClientIllegalConfigId,
	excaliburFemClientIllegalChipId,
	excaliburFemClientIllegalConfigSize,
	excaliburFemClientIllegalCounterDepth,
	excaliburFemClientOmrTransactionTimeout,
	excaliburFemClientUdpSetupFailed,
	excaliburFemClientDataReceviverSetupFailed,
	excaliburFemClientIllegalOperationMode,
	excaliburFemClientIllegalCounterSelect,
	excaliburFemClientBufferAllocateFailed,
	excaliburFemClientPersonalityStatusError,
	excaliburFemClientBadDacScanParameters,
	excaliburFemClientMissingScanFunction

} ExcaliburFemClientErrorCode;

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
	coolantTempStatus = 0,
	humidityStatus,
	coolantFlowStatus,
	airTempStatus,
	fanFaultStatus
} excaliburPowerCardStatus;

typedef enum
{
	p5vAVoltageMonitor = 0,
	p5vBVoltageMonitor,
	p5vFem0CurrentMonitor,
	p5vFem1CurrentMonitor,
	p5vFem2CurrentMonitor,
	p5vFem3CurrentMonitor,
	p5vFem4CurrentMonitor,
	p5vFem5CurrentMonitor,
	p48vVoltageMonitor,
	p48vCurrentMonitor,
	p5vSupVoltageMonitor,
	p5vSupCurrentMonitor,
	humidityMonitor,
	airTempMonitor,
	coolantTempMonitor,
	coolantFlowMonitor,
	p3v3CurrentMonitor,
	p1v8ACurrentMonitor,
	biasCurrentMonitor,
	p3v3VoltageMonitor,
	p1v8AVoltageMonitor,
	biasVoltageMontor,
	p1v8BCurrentMonitor,
	p1v8BVoltageMonitor
} excaliburPowerCardMonitor;

typedef enum
{

	excaliburOperationModeNormal    = 0,
	excaliburOperationModeBurst     = 1,
	excaliburOperationModeHistogram = 2,
	excaliburOperationModeDacScan   = 3

} excaliburOperationMode;

typedef enum
{
	excaliburPersonalityCommandDacScan = 1,
	excaliburPersonalityCommandStatus  = 20,
	excaliburPersonaliutyCommandResult = 21

} excaliburPersonalityCommand;

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


	void externalTriggerSet(unsigned int aExternalTrigger);
	void operationModeSet(unsigned int aOperationMode);
	void numFramesSet(unsigned int aNumFrames);
	void acquisitionPeriodSet(unsigned int aPeriodMs);
	void acquisitionTimeSet(unsigned int aTimeMs);
	void burstModeSubmitPeriodSet(double aPeriod);
	void numTestPulsesSet(unsigned int aNumTestPulses);
	void preallocateFrames(unsigned int aNumFrames);
	void releaseAllFrames(void);
	void freeAllFrames();
	void frontEndInitialise(void);

	// EXCALIBUR detector front-end functions in ExcaliburFemClientFrontEndDevices.cpp
	void   frontEndEnableSet(unsigned int aVal);
	double frontEndTemperatureRead(void);
	double frontEndHumidityRead(void);
	double frontEndDacOutRead(unsigned int aChipId);
	int    frontEndSupplyStatusRead(excaliburFrontEndSupply aSupply);
	void   frontEndDacInWrite(unsigned int aChipId, unsigned int aDacValue);
	void   frontEndDacInWrite(unsigned int aChipId, double aDacVolts);
	void   frontEndDacInitialise(void);

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
	void mpx3CounterSelectSet(int aCounterSelect);
	void mpx3DisableSet(unsigned int aChipId, unsigned int aDisable);

	// EXCALIBUR power card control functions in ExcaliburFemClientPowerCardDevices.cpps

	void  powerCardBiasEnableWrite(unsigned int aEnable);
	void  powerCardLowVoltageEnableWrite(unsigned int aEnable);
	unsigned int powerCardLowVoltageEnableRead(void);
	unsigned int powerCardBiasEnableRead(void);
	void  powerCardBiasLevelWrite(float aBiasLevel);
	int   powerCardStatusRead(excaliburPowerCardStatus aStatus);
	float powerCardMonitorRead(excaliburPowerCardMonitor aMonitor);

	// EXCALIBUR FEM personality module functions in ExcaliburFemClientPersonality.cpp
	personalityCommandStatus personalityCommandStatusGet(void);

	// EXCALIBUR autonomous scanning functions in ExcaliburFemClientScan.cpp
	void dacScanDacSet(unsigned int aDac);
	void dacScanStartSet(unsigned int aDacStart);
	void dacScanStopSet(unsigned int aDacStop);
	void dacScanStepSet(unsigned int aDacStep);
	unsigned int dacScanNumSteps(void);
	void dacScanExecute(void);

private:

	// Private functions in ExcaliburFemClient.cpp
	// TODO Move this out of main class file to preserve interface??
	unsigned int asicReadoutDmaSize(void);
	unsigned int asicReadoutLengthCycles(void);
	unsigned int frameDataLengthBytes(void);

	// ASIC control functions in ExcaliburFemClientAsicControl.cpp
	void asicControlOmrSet(mpx3Omr aOmr);
	void asicControlMuxChipSelect(unsigned int aChipIdx);
	void asicControlMuxSet(unsigned int aMuxValue);
	void asicControlCommandExecute(asicControlCommand aCommand);
	void asicControlNumFramesSet(unsigned int aNumFrames);
	void asicControlShutterDurationSet(unsigned int aTimeUs);
	void asicControlCounterDepthSet(mpx3CounterDepth aCounterDepth);
	void asicControlReadoutLengthSet(unsigned int aLength);
	void asicControlTestPulseCountSet(unsigned int aCount);
	void asicControlConfigRegisterSet(unsigned int aConfigRegister);
	void asicControlReset(void);
	void asicControlAsicReset(void);

	// Private functions in ExcaliburFemClientFrontEndDevices.cpp
	u16 frontEndSht21Read(u8 cmdByte);
	u16 frontEndAD7994Read(unsigned int device, unsigned int aChan);
	u8 frontEndPCF8574Read(void);
	void frontEndPCF8574Write(unsigned int aVal);
	void frontEndAD5625Write(unsigned int aDevice, unsigned int aChan, unsigned int aVal);
	void frontEndAD5625InternalReferenceEnable(unsigned int aDevice, bool aEnable);

	// Private functions in ExcaliburFemClientPowerCardDevices.cpp
	int  powerCardPCF8574BitRead(int aBit);
	void powerCardPCF8574BitWrite(int aBit, int aVal);
	void powerCardAD5301Write(u8 aDacValue);
	u16 powerCardAD7998Read(unsigned int aDevice, unsigned int aChan);

	mpx3Dac mpx3DacIdGet(int aId);
	mpx3PixelConfig mpx3PixelConfigIdGet(int aConfigId);

	mpx3Omr mpx3OMRBuild(unsigned int aChipId, mpx3OMRMode aMode);
	unsigned int mpx3CounterBitDepth(mpx3CounterDepth aCounterDepth);
	unsigned int mpx3ReadoutBitWidth(mpx3ReadoutWidth aReadoutWidth);


	mpx3OMRParameters     mMpx3OmrParams[kNumAsicsPerFem];
	unsigned int          mMpx3DacCache[kNumAsicsPerFem][numExcaliburDacs];
	unsigned short        mMpx3PixelConfigCache[kNumAsicsPerFem][numPixelConfigs][kNumPixelsPerAsic];
	unsigned short        mMpx3ColumnTestPulseEnable[kNumAsicsPerFem][kNumColsPerAsic];
	unsigned short        mMpx3GlobalTestPulseEnable;
	mpx3CounterSelect     mMpx3CounterSelect;
	bool	              mMpx3Enable[kNumAsicsPerFem];
	unsigned int          mMpx3TestPulseCount;

	FemDataReceiver*      mFemDataReceiver;
	unsigned int          mFemDataHostPort;
	void*                 mCtlHandle;
	const CtlCallbacks*   mCallbacks;
	const CtlConfig*      mConfig;

	CallbackBundle 		  mCallbackBundle;

	asicDataReorderMode   mAsicDataReorderMode;
	unsigned int          mNumSubFrames;

	std::list<CtlFrame*>  mFrameQueue;
	std::list<CtlFrame*>  mReleaseQueue;

	unsigned int          mExternalTrigger;
	excaliburOperationMode mOperationMode;
	unsigned int          mNumFrames;
	unsigned int          mAcquisitionPeriodMs;
	unsigned int          mAcquisitionTimeMs;
	double                mBurstModeSubmitPeriod;

	bool				  mEnableDeferredBufferRelease;

	unsigned int		  mDacScanDac;
	unsigned int		  mDacScanStart;
	unsigned int		  mDacScanStop;
	unsigned int		  mDacScanStep;

};

#endif /* EXCALIBURFEMCLIENT_H_ */
