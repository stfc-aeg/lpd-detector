/*
 * FPM_excalibur.c
 *
 *  Created on: Nov 15, 2011
 *      Author: mt47
 */

#include "FPM_excalibur.h"

/**
 * Application specific hardware initialisation function, called by main FEM at end of hardwareInit()
 * @return xstatus, XST_SUCCESS if no errors
 */
int fpmInitHardware()
{
	DBGOUT("\r\n************************************\r\n");
	DBGOUT("Personality Module: EXCALIBUR\r\n");
	DBGOUT("************************************\r\n\r\n");

	int status;

	// Reset ASIC block (bit 22) and ASICs (bit 23), then clear those bits
	DBGOUT("fpmInitHardware: Resetting ASIC control block / ASICs\r\n");
	status = writeRdma(0x48000001, 0xC00000);
	if (status!=XST_SUCCESS)
	{
		//return status;
		// Don't skip reset as if the command DID work we leave ASICs held in reset
		// which draws a lot of current...
	}

	status = writeRdma(0x48000001, 0x0);

	return status;
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
	// TODO: Implement
	return -1;
}

/*
 * Processes personality-specific received commands over LWIP.  It is assumed that
 * packets are well formed and have been checked before passing to this function.
 * @param pRxHeader pointer to protocol_header for received packet
 * @param pTxHeader pointer to protocol_header for outbound packet
 * @param pRxPayload pointer to payload buffer of received packet
 * @param pTxPayload pointer to payload buffer for outbound packet
 */
void handlePersonalityCommand(	struct protocol_header* pRxHeader,
								struct protocol_header* pTxHeader,
								u8* pRxPayload,
								u8* pTxPayload
							)
{

	// TODO: Implement Excalibur-specific command handling here!

}
