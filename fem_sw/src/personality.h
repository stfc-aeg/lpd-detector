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

#include <fem.h>
#include "protocol.h"
#include "xil_types.h"
#include "xmk.h"
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

#endif /* PERSONALITY_H_ */
