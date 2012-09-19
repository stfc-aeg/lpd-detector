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

	// This assumes mux defaults to 0!

	// Reset ASIC block (bit 22) and ASICs (bit 23), then clear those bits
	DBGOUT("fpmInitHardware: Resetting ASIC control block / ASICs\r\n");
	status = writeRdma(0x90000001, 0xC00000);
	if (status!=XST_SUCCESS)
	{
		// Don't skip reset as if the command DID work we leave ASICs held in reset
		// which draws a lot of current...
		//return status;
	}

	status = writeRdma(0x90000001, 0x0);

	// Initialise static variables
	currentThreadType = 0;

	state.state = 0;
	state.numOps = 0;
	state.compOps = 0;
	state.error = 0;

	pInput = NULL;
	pOutput = NULL;
	outputSz = 0;

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
	// TODO: Implement validatePersonalityHeaderContents
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
 *
 * @return 1 for ACK, 0 for NACK
 */
int handlePersonalityCommand(	struct protocol_header* pRxHeader,
								struct protocol_header* pTxHeader,
								u8* pRxPayload,
								u8* pTxPayload,
								int* pResponseSize
							)
{

	int retVal;

	// Debugging, print header information
	DUMPHDR(pRxHeader);

	// TODO: Remove debugging
	xil_printf("FPM_Excalibur: Opmode %d\r\n", pRxHeader->address);

	// For personality module address is overloaded to be command
	switch(pRxHeader->address)
	{
		case FPM_DACSCAN:
			retVal = prepareDACScan(pRxPayload);
			break;

		case FPM_GET_STATUS:
			// Transfer threadState to payload, increment payload size
			memcpy(pTxPayload, &state, sizeof(threadState));
			pTxHeader->payload_sz += sizeof(threadState);
			retVal = 1;

			xil_printf("FPM_Excalibur: state.state   = %d\r\n", state.state);
			xil_printf("FPM_Excalibur: state.numOps  = %d\r\n", state.numOps);
			xil_printf("FPM_Excalibur: state.compOps = %d\r\n", state.compOps);
			xil_printf("FPM_Excalibur: state.error   = %d\r\n", state.error);

			break;

		case FPM_GET_RESULT:
			if (state.state!=0)
			{
				// Thread still executing
				retVal = 0;
			}
			else
			{
				// Return data
				pTxHeader->payload_sz += outputSz;
				memcpy(pTxPayload, &state, (size_t)outputSz);
			}
			break;

		default:
			retVal = 0;
			break;
	}

	// TODO: Remove debugging
	xil_printf("FPM_Excalibur: TX payload sz =%d\r\n", pTxHeader->payload_sz);

	return retVal;
}


// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

int prepareDACScan(u8 *pRxPayload)
{

	pthread_t t;
	int tid;

	int dataSize = 12;	// TODO: What payload will we receive for DACscan?  (sizeof(u32) x 3)?

	if (currentThreadType!=0) {
		// Already a thread running!
		// TODO: Remove debugging
		xil_printf("FPM_Excalibur: Worker thread already running, not starting another...\r\n");
		return 0;
	}

	// Signal a worker thread is launching
	currentThreadType = FPM_DACSCAN;

	// Initialise thread state
	state.state = 0;
	state.numOps = 0;
	state.compOps = 0;
	state.error = 0;

	// Copy payload to static variable
	realloc(pInput, (size_t)dataSize);
	memcpy(pInput, pRxPayload, (size_t)dataSize);

	// Launch thread
	tid = pthread_create(&t, NULL, doDACScanThread, NULL);
	if(tid==-1)
	{
		xil_printf("FPM_excalibur: Failed to launch thread!\r\n");
		return 0;	// NACK
	}
	else
	{
		xil_printf("FPM_excalibur: Launched worker thread, ID=%d\r\n", tid);
		return 1;	// ACK
	}

}


/*
 * Excalibur personality command: DAC scan
 * Executes a DAC scan
 * @param pArg NULL
 */
void *doDACScanThread(void *pArg)
{

	// Flag as busy
	state.state = 1;

	// This won't return any data but if it were to do so, something like this would happen:
	// malloc(pOutput, (size_t)n)
	// outputSz = n;

	xil_printf("FPM_Excalibur [DACscan]: Thread active!\r\n");

	// TODO: Do actual DAC scan here!!
	// Sleep 20s
	usleep(20000000);

	// Flag as idle
	state.state = 0;
	currentThreadType = 0;

	// Set datasize (none in this case)
	outputSz = 0;

	// TODO: free(pInput)

	// Terminate
	pthread_exit(NULL);

	// This statement never executes but suppresses warning on compiler
	return 0;
}

// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
