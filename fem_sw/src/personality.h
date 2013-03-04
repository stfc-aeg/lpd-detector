/**
 * @file personality.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * Generic header for FEM personality modules (FPMs)
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
int getFpmId(void);
int fpmInitHardware(void);												//!< Personality module hardware initialisation
int validatePersonalityHeaderContents(struct protocol_header *pHeader);	//!< Validates header for personality commands
int handlePersonalityCommand(	struct protocol_header* pRxHeader,
								struct protocol_header* pTxHeader,
								u8* pRxPayload,
								u8* pTxPayload,
								int* pResponseSize
							);											//!< Personality command handler, hands off requests to functions

#define PERS_ERROR_STRING_MAX_LENGTH 80		//!< Maximum error string length

#define SETPERSERR(code, ...) state.error=code; \
							  snprintf(state.errorString, ERR_STRING_MAX_LENGTH, __VA_ARGS__); \
							  if (code != 0) { xil_printf("%s\r\n", state.errorString); }

//! Thread state bundle
typedef struct
{
	u32 state;		                                //!< Thread state (0=idle, 1=working)
	u32 numOps;		                                //!< Number of requested operations / steps
	u32 compOps;	                                //!< Number of completed operations
	u32 error;		                                //!< Error code, non zero denotes error!
	char errorString[PERS_ERROR_STRING_MAX_LENGTH]; //!< Error string
} threadState;

int currentThreadType;		//!< Thread global variable: Non-zero if there is currently a thread running
threadState state;			//!< Thread global variable: Thread state
u8 *pInput;					//!< Thread global variable: Pointer to input payload (passed to thread)
u8 *pOutput;				//!< Thread global variable: Pointer to output payload (response from thread)
int outputSz;				//!< Thread global variable: Size of output payload

#endif /* PERSONALITY_H_ */
