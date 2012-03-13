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

typedef enum {
	frontEndEnable = 0,
	frontEndAVDD1  = 2,
	frontEndAVDD2  = 3,
	frontEndAVDD3  = 4,
	frontEndAVDD4  = 5,
	frontEndVDD    = 6,
	frontEndDVDD   = 7
} excaliburFrontEndSupply;

class ExcaliburFemClient: public FemClient {
public:
	ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
			const CtlConfig* aConfig, unsigned int aTimeoutInMsecs = 0);
	virtual ~ExcaliburFemClient();

	BufferInfo allocateCallback(void);
	void freeCallback(int aVal);
	void receiveCallback(int aVal);
	void signalCallback(int aSignal);

	void command(unsigned int aCommand);

	void setNumFrames(unsigned int numFrames);
	void setAcquisitionPeriod(unsigned int aPeriodMs);
	void setAcquisitionTime(unsigned int aTimeMs);

	void setFrontEndEnable(unsigned int aVal);

	double frontEndTemperatureRead(void);
	double frontEndHumidityRead(void);
	double frontEndDacOutRead(unsigned int aChipId);
	int    frontEndSupplyStatusRead(excaliburFrontEndSupply aSupply);
	void   frontEndDacInWrite(unsigned int aChipId, unsigned int aDacValue);

private:

	u16 frontEndSht21Read(u8 cmdByte);
	u16 frontEndAD7994Read(unsigned int device, unsigned int aChan);
	u8 frontEndPCF8574Read(void);
	void frontEndPCF8574Write(unsigned int aVal);
	void frontEndAD5625Write(unsigned int aDevice, unsigned int aChan, unsigned int aVal);

	FemDataReceiver       mFemDataReceiver;
	void*                 mCtlHandle;
	const CtlCallbacks*   mCallbacks;
	const CtlConfig*      mConfig;

	std::list<CtlFrame*> mFrameQueue;

};

#endif /* EXCALIBURFEMCLIENT_H_ */
