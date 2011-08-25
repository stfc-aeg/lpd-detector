/*
 * commandProcessor.h
 *
 *  Created on: Aug 4, 2011
 *      Author: mt47
 */

#ifndef COMMANDPROCESSOR_H_
#define COMMANDPROCESSOR_H_

#include "xil_types.h"
#include "fem.h"
#include "protocol.h"

#include "raw.h"
#include "rdma.h"
#include "i2c_lm82.h"
#include "i2c_24c08.h"

#include "lwip/sockets.h"

#define MAX_CONNECTIONS			2
#define CMD_PORT				6969

void commandProcessorThread();
void commandHandler(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload);
int socketRead(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs);

#endif /* COMMANDPROCESSOR_H_ */
