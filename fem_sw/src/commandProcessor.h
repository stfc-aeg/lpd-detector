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
#include "xgpio.h"
#include "mailbox.h"

#ifndef HW_PLATFORM_DEVBOARD
#include "sysace.h"
#endif

#include "lwip/sockets.h"

#include "personality.h"

enum packetStatus {
	STATE_START = 0,
	STATE_GOT_HEADER = 1,
	STATE_HDR_VALID = 2,
	STATE_GOT_PYLD = 3,
	STATE_COMPLETE = 4
};

#ifndef HW_PLATFORM_DEVBOARD
extern u8 mux;
extern XGpio gpioMux;
extern XSysAce sysace;
#endif

struct clientStatus {
	int state;						//! State machine status, of packetStatus
	int size;						//! Total number of bytes received on current packet
	struct protocol_header *pHdr;	//! Pointer to protocol header buffer
	u8 *pPayload;					//! Pointer to payload buffer
	int payloadBufferSz;			//! Currently allocated size for pPayload
	u8 gotData;						//! Whether we got data on this loop cycle or not
	int timeoutCount;				//! Counter for timeouts
	u8 *pBusDirect;					//! Pointer for BUS_DIRECT writes
	int busDirectSize;				//! Bytes received in BUS_DIRECT mode
};

void commandProcessorThread(void* arg);
void disconnectClient(struct clientStatus* pState, int *pIndex, fd_set* pFdSet, u8 *pNumConnectedClients);
void commandHandler(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload, u8* pMux, XGpio *pGpio, u8* pReloadRequested);
int socketRead(int sock, u8* pBuffer, unsigned int numBytes);
int validateHeaderContents(struct protocol_header *pHeader);
void flushSocket(int sock, void *mem, int len);
void generateBadPacketResponse(struct protocol_header *pHeader, int clientSocket);

#endif /* COMMANDPROCESSOR_H_ */

