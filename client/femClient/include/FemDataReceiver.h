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
#include <boost/scoped_ptr.hpp>



class FemDataReceiver {
public:

	typedef boost::function<void(void)> allocateCallback_t;
	typedef boost::function<void(int)> freeCallback_t;
	typedef boost::function<void(int)> receiveCallback_t;
	typedef boost::function<void(int)> signalCallback_t;

	FemDataReceiver();
	virtual ~FemDataReceiver();

	void start(void);
	void registerAllocateCallback(allocateCallback_t aCallback);
	void registerFreeCallback(freeCallback_t aCallback);
	void registerReceiveCallback(receiveCallback_t aCallback);
	void registerSignalCallback(signalCallback_t aCallback);

	static void completionCallback(void);

private:

	boost::asio::io_service   	      mIoService;
	boost::asio::deadline_timer       mDeadline;
	boost::scoped_ptr<boost::thread> mReceiverThread;

	allocateCallback_t mAllocateCallback;
	freeCallback_t     mFreeCallback;
	receiveCallback_t  mReceiveCallback;
	signalCallback_t   mSignalCallback;

	int mCallbackCount;

	void checkDeadline(void);
};

#endif /* FEMDATARECEIVER_H_ */
