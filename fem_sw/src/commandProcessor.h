/**
 * @file commandProcessor.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * Manages the decoding of received packets and generation of response packets using LwIP library
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

//! Packet status, used in packet processing state machine
enum packetStatus {
	STATE_START = 0,			//!< Packet reception has begun
	STATE_GOT_HEADER = 1,		//!< Received a chunk of data the size of a header
	STATE_HDR_VALID = 2,		//!< Validated header
	STATE_GOT_PYLD = 3,			//!< Received header + stated payload
	STATE_COMPLETE = 4			//!< Packet reception complete, now idle
};

#ifndef HW_PLATFORM_DEVBOARD
extern XSysAce sysace;			//!< SystemACE controller
#endif

extern u32 femErrorState;

//! Client status bundle
struct clientStatus {
	int state;									//!< State machine status, of type packetStatus
	int size;									//!< Total number of bytes received in current packet
	struct protocol_header *pHdr;				//!< Pointer to protocol header buffer
	u8 *pPayload;								//!< Pointer to payload buffer
	int payloadBufferSz;						//!< Currently allocated size for pPayload
	u8 gotData;									//!< Whether we received data on this loop cycle or not
	int timeoutCount;							//!< Timeout counter
	u8 *pBusDirect;								//!< Pointer for BUS_DIRECT writes
	int busDirectSize;							//!< Bytes received in BUS_DIRECT mode
	u8 errorCode;								//!< Error code
	char errorString[ERR_STRING_MAX_LENGTH];	//!< Error string
};

void commandProcessorThread(void* arg);
void disconnectClient(struct clientStatus* pState, int *pIndex, fd_set* pFdSet, u8 *pNumConnectedClients);
int commandHandler(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload, int* pReloadRequested, struct clientStatus *pClient);
int validateRequest(struct protocol_header *pHeader, struct clientStatus *pClient);
void flushSocket(int sock, void *mem, int len);
void generateErrorResponse(u8* pTxPayload, int clientSocket, struct clientStatus *pClient);

// Macro for setting errorString and errorCode on clientStatus
#define SETERR(client, code, ...)			client->errorCode=code; \
											snprintf(client->errorString, ERR_STRING_MAX_LENGTH, __VA_ARGS__);

#endif /* COMMANDPROCESSOR_H_ */

