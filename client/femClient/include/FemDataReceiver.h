/*
 * FemDataReceiver.h
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#ifndef FEMDATARECEIVER_H_
#define FEMDATARECEIVER_H_

#include <boost/thread/thread.hpp>
#include <boost/asio.hpp>
#include <boost/function.hpp>
#include <boost/bind.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/deadline_timer.hpp>
#include <boost/shared_ptr.hpp>

#include <dataTypes.h>

typedef struct bufferInfo_t
{
	u8*          addr;
	unsigned int length;
} BufferInfo;


typedef boost::function<BufferInfo(void)> allocateCallback_t;
typedef boost::function<void(int)> freeCallback_t;
typedef boost::function<void(int)> receiveCallback_t;
typedef boost::function<void(int)> signalCallback_t;

typedef struct callbackBundle_t
{
	allocateCallback_t allocate;
	freeCallback_t     free;
	receiveCallback_t  receive;
	signalCallback_t   signal;

} CallbackBundle;

namespace FemDataReceiverSignal {
	typedef enum {
		femAcquisitionComplete
	} FemDataReceiverSignals;
}

class FemDataReceiver {
public:

	FemDataReceiver();
	virtual ~FemDataReceiver();

	void startAcquisition(void);
	void stopAcquisition(void);
	void registerCallbacks(CallbackBundle* aBundle);

	void setNumFrames(unsigned int aNumFrames);
	void setAcquisitionPeriod(unsigned int aPeriodMs);
	void setAcquisitionTime(unsigned int aTimeMs);

	void handleReceive(const boost::system::error_code& errorCode, std::size_t bytesReceived);

private:

	boost::asio::io_service   	      mIoService;
	boost::asio::ip::udp::endpoint	  mRemoteEndpoint;
	boost::asio::ip::udp::socket      mRecvSocket;
	boost::asio::deadline_timer       mDeadline;
	boost::shared_ptr<boost::thread>  mReceiverThread;

	CallbackBundle     				  mCallbacks;

	bool							  mAcquiring;
	unsigned int                      mCurrentFrame;

	unsigned int                      mNumFrames;
	unsigned int                      mAcquisitionPeriod;
	unsigned int                      mAcquisitionTime;


	void checkDeadline(BufferInfo aFramePtr);
};

#endif /* FEMDATARECEIVER_H_ */
