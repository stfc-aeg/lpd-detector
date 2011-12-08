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

class ExcaliburFemClient: public FemClient {
public:
	ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
			const CtlConfig* aConfig, unsigned int aTimeoutInMsecs = 0);
	virtual ~ExcaliburFemClient();

	void allocateCallback(void);
	void freeCallback(int aVal);
	void receiveCallback(int aVal);
	void signalCallback(int aSignal);

private:
	FemDataReceiver       mFemDataReceiver;
	void*                 mCtlHandle;
	const CtlCallbacks*   mCallbacks;
	const CtlConfig*      mConfig;
};

#endif /* EXCALIBURFEMCLIENT_H_ */
