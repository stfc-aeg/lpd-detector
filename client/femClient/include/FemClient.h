/*
 * FemClient.h - header file definition of FemClient class
 *
 *  Created on: Sep 15, 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef FEMCLIENT_H_
#define FEMCLIENT_H_

#include <boost/asio.hpp>
#include <boost/bind.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/deadline_timer.hpp>
#include "FemTransaction.h"
#include "FemException.h"

using boost::asio::ip::tcp;

/** FemClient::error - error codes returned by FemClient methods, typically
 *  embodied in a thrown FemClientException. The specific FemClient errors
 *  in the enumeration are indexed from 10000, to allow standard errno and
 *  boost ASIO error codes to be used also.
 */
typedef enum
{
	femClientOK = 0,                    ///< OK
	femClientDisconnected = 10000,      ///< Client disconnected by peer
	femClientTimeout,                   ///< Timeout occurred on a socket operation
	femClientResponseMismatch,           ///< Mismatch between requested command and response
	femClientMissingAck,                ///< Transaction command was not acknowledged in reponse
	femClientSendMismatch,              ///< Mismatch in length of send operation
	femClientReadMismatch,              ///< Mismatch in requested versus received access in read transaction
	femClientWriteMismatch              ///< Mismatch in requested versus acknowledged access in write transaction
} FemClientErrorCode;

class FemClientException: public FemException
{
public:
	FemClientException(const std::string aExText): FemException(aExText) { };
	FemClientException(const FemClientErrorCode aExCode, const std::string aExText) :
		FemException((FemErrorCode)aExCode, aExText) { };
};

class FemClient
{

public:

	FemClient(const char* aHostString, int aPortNum, unsigned int aTimeoutInMsecs=0);
	virtual ~FemClient();

	void setTimeout(unsigned int aTimeoutInMsecs);
	void setTimeout(float aTimeoutInSecs);

	std::vector<u8> read(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
			             unsigned int aLength);
	u32 write(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
					  std::vector<u8>& aPayload);
	virtual void command(unsigned int command);

	std::size_t send(FemTransaction aTrans);
	FemTransaction receive(void);

	void runIoService(void); // test function

private:

	boost::asio::io_service     mIoService; ///< Boost asio IO service
	tcp::endpoint               mEndpoint;  ///< Boost asio TCP endpoint
	tcp::socket                 mSocket;    ///< Client connection socket
	boost::asio::deadline_timer mDeadline;  ///< Internal timeout deadline timer
	unsigned int                mTimeout;   ///< timeout in milliseconds

	std::size_t receivePart(std::vector<u8>& aBuffer, boost::system::error_code& aError);
	void checkDeadline(void);
	static void asyncCompletionHandler(
			const boost::system::error_code& aErrorCode, std::size_t aLength,
		    boost::system::error_code* apOutputErrorCode, std::size_t* apOutputLength);
};

#endif /* FEMCLIENT_H_ */
