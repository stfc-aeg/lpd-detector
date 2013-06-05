/*
 * FPM_stub.c
 *
 *  Created on: Jan 15, 2013
 *      Author: mt47
 */

#include "FPM_stub.h"

/**
 * Returns unique FPM ID
 * @return FPM ID
 */
int getFpmId(void)
{
	return FPM_ID;
}

/**
 * Application specific hardware initialisation function, called by main FEM at end of hardwareInit()
 * @return xstatus, XST_SUCCESS if no errors
 */
int fpmInitHardware()
{
	DBGOUT("\r\n************************************\r\n");
	DBGOUT("Personality Module: NONE\r\n");
	DBGOUT("************************************\r\n\r\n");

	return XST_SUCCESS;
}

/*
 * Validates the fields of a header for consistency
 * It is assumed that the header magic word has been verified and the fields are trusted to contain valid data.
 * @param pHeader pointer to header
 *
 * @return 0 if header logically correct, -1 if not
 */
int validatePersonalityHeaderContents(struct protocol_header *pHeader)
{
	// Always OK, no functions implemented!
	return 0;
}

/*
 * Processes personality-specific received commands over LWIP.  It is assumed that
 * packets are well formed and have been checked before passing to this function.
 * @param pRxHeader pointer to protocol_header for received packet
 * @param pTxHeader pointer to protocol_header for outbound packet
 * @param pRxPayload pointer to payload buffer of received packet
 * @param pTxPayload pointer to payload buffer for outbound packet
 * @param pResponseSize pointer to response size
 */
void handlePersonalityCommand(	struct protocol_header* pRxHeader,
								struct protocol_header* pTxHeader,
								u8* pRxPayload,
								u8* pTxPayload,
								int* pResponseSize
							)
{

	// Dummy function
	return;

}
