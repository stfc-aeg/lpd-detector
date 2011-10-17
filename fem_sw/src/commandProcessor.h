/*
 * commandProcessor.h
 *
 * Manages the decoding of received packets and generation
 * of response packets using LwIP library
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

void commandProcessorThread();
void commandHandler(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload);
int socketRead(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs);
int validateHeaderContents(struct protocol_header *pHeader);
void generateBadPacketResponse(struct protocol_header *pHeader, int clientSocket);

#endif /* COMMANDPROCESSOR_H_ */
