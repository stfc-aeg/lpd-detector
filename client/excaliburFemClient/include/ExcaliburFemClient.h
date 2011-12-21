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

private:
	FemDataReceiver       mFemDataReceiver;
	void*                 mCtlHandle;
	const CtlCallbacks*   mCallbacks;
	const CtlConfig*      mConfig;

	std::list<CtlFrame*> mFrameQueue;
};

#endif /* EXCALIBURFEMCLIENT_H_ */
