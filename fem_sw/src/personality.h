/*
 * personality.h
 *
 * Generic header for FEM personality modules (FPMs)
 *
 * NOTE: All FPM_* directories should be tagged as 'Exclude from build' except the required module!
 *
 */

#ifndef PERSONALITY_H_
#define PERSONALITY_H_

#include "xmk.h"
#include <fem.h>
#include "protocol.h"
#include "xil_types.h"
#include "stdio.h"
#include "xstatus.h"

// Template header for FEM personality modules.  These methods must be implemented in the FPMs!
int fpmInitHardware(void);
int validatePersonalityHeaderContents(struct protocol_header *pHeader);
int handlePersonalityCommand(	struct protocol_header* pRxHeader,
								struct protocol_header* pTxHeader,
								u8* pRxPayload,
								u8* pTxPayload,
								int* pResponseSize
							);

#define PERS_ERROR_STRING_MAX_LENGTH 80
#define SETPERSERR(code, ...) state.error=code; \
							  snprintf(state.errorString, ERR_STRING_MAX_LENGTH, __VA_ARGS__); \
							  if (code != 0) { xil_printf("%s\r\n", state.errorString); }

typedef struct
{
	u32 state;		                                //!< Thread state (0=idle, 1=working)
	u32 numOps;		                                //!< Number of requested operations / steps
	u32 compOps;	                                //!< Number of completed operations
	u32 error;		                                //!< Error code, non zero denotes error!
	char errorString[PERS_ERROR_STRING_MAX_LENGTH]; //!< Error string
} threadState;

// Static (thread global) variables
int currentThreadType;		//! Non-zero if there is currently a thread running
threadState state;
u8 *pInput;
u8 *pOutput;
int outputSz;

#endif /* PERSONALITY_H_ */
