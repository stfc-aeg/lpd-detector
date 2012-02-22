/*
 * commandProcessor.h
 *
 * Manages the decoding of received packets and generation
 * of response packets using LwIP library
 *
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
#include "mailbox.h"

#include "lwip/sockets.h"

#include "personality.h"

enum packetStatus {
	STATE_START = 0,
	STATE_GOT_HEADER = 1,
	STATE_HDR_VALID = 2,
	STATE_GOT_PYLD = 3,
	STATE_COMPLETE = 4
};

struct clientStatus {
	int state;						//! State machine status, of packetStatus
	int size;						//! Total number of bytes received on current packet
	struct protocol_header *pHdr;	//! Pointer to protocol header buffer
	u8 *pPayload;					//! Pointer to payload buffer
	int payloadBufferSz;			//! Currently allocated size for pPayload
	int timeoutCount;				//! Counter for timeouts
};

void commandProcessorThread();
void disconnectClient(struct clientStatus* pState, int *pIndex, fd_set* pFdSet, u8 *pNumConnectedClients);
void commandHandler(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload);
int socketRead(int sock, u8* pBuffer, unsigned int numBytes);
int validateHeaderContents(struct protocol_header *pHeader);
void generateBadPacketResponse(struct protocol_header *pHeader, int clientSocket);

#endif /* COMMANDPROCESSOR_H_ */

