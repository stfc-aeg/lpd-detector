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
	//DUMPHDR(pRxHeader);

	// TODO: Remove debugging
	//xil_printf("FPM_Excalibur: Opmode %d\r\n", pRxHeader->address);

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
			pTxHeader->data_width = WIDTH_LONG;
			retVal = 1;

//			xil_printf("FPM_Excalibur: state.state   = %d\r\n", state.state);
//			xil_printf("FPM_Excalibur: state.numOps  = %d\r\n", state.numOps);
//			xil_printf("FPM_Excalibur: state.compOps = %d\r\n", state.compOps);
//			xil_printf("FPM_Excalibur: state.error   = %d\r\n", state.error);

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
	//xil_printf("FPM_Excalibur: TX payload sz =%d\r\n", pTxHeader->payload_sz);

	return retVal;
}


// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

int prepareDACScan(u8 *pRxPayload)
{

	pthread_t t;
	int tid;

	int dataSize = sizeof(dacScanParams);

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
	if (pInput == NULL)
	{
		pInput = malloc((size_t)dataSize);
	}
	else {
		realloc(pInput, (size_t)dataSize);
	}
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
	unsigned int scanDacVal;
	unsigned int iAsic;

	// Flag as busy
	state.state = 1;

	// This won't return any data but if it were to do so, something like this would happen:
	// malloc(pOutput, (size_t)n)
	// outputSz = n;

	xil_printf("FPM_Excalibur [DACscan]: Thread active!\r\n");

	// Decode scan parameters from input payload
	dacScanParams* scanParams = (dacScanParams*)pInput;


//	xil_printf("scan params: %d %d %d %d\r\n", scanParams->scanDac, scanParams->dacStart,
//			  scanParams->dacStop, scanParams->dacStep);
//	xil_printf("asic mask; %d\r\n", scanParams->asicMask);
//	xil_printf("C7 thresh 0: %d, C1 thresh 1: %d\r\n",
//			   scanParams->dacCache[7][0], scanParams->dacCache[1][1]);
//	xil_printf("DAC set OMR: 0x%x%08x  ACQ OMR: 0x%x%08x Execute: %d\r\n",
//				scanParams->omrDacSet.top, scanParams->omrDacSet.bottom,
//				scanParams->omrAcquire.top, scanParams->omrAcquire.bottom,
//				scanParams->executeCommand);

	// Loop over scan parameters and execute scan
	int rc = 0;
	for (scanDacVal = scanParams->dacStart; scanDacVal <= scanParams->dacStop; scanDacVal += scanParams->dacStep)
	{

		xil_printf("Scanning DAC %d val %d\r\n", scanParams->scanDac, scanDacVal);

		// Iterate over ASICs that are enabled in ASIC mask
		for (iAsic = 0; iAsic < kNumAsicsPerFem; iAsic++)
		{
			if ((scanParams->asicMask & ((u32)1<<(7-iAsic))) != 0)
			{
				// Update scanned DAC cache value for relevant ASIC
				scanParams->dacCache[iAsic][scanParams->scanDac] = scanDacVal;
				// Load DACs into the ASC
				rc = loadDacs(iAsic, scanParams);
			}
			if (rc != 0) {
				break;
			}
		}
		if (rc != 0) {
			break;
		}

		// Trigger an image acquisition
	}

	// TODO: Do actual DAC scan here!!
	// Sleep 2s
	usleep(2000000);

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

int loadDacs(unsigned int iAsic, dacScanParams* scanParams)
{
	int rc = 0;
	int status;
	u32 dacWords[kNumAsicDpmWords];
	unsigned int iWord;
	xil_printf("Loading DACs for ASIC %d\r\n", iAsic);

	// Zero out packed DAC values to be loaded into FEM
	for (iWord = 0; iWord < kNumAsicDpmWords; iWord++)
	{
		dacWords[iWord] = 0;
	}

	// Pack DACs values into the words to be loaded into FEM
    dacWords[0] |= (u32)(scanParams->dacCache[iAsic][tpRefBDac]      & 0x1FF) << 23;
    dacWords[0] |= (u32)(scanParams->dacCache[iAsic][tpRefADac]      & 0x1FF) << 14;
    dacWords[0] |= (u32)(scanParams->dacCache[iAsic][casDac]         & 0x0FF) << 6;
    dacWords[0] |= (u32)(scanParams->dacCache[iAsic][fbkDac]         & 0x0FC) >> 2;

    dacWords[1] |= (u32)(scanParams->dacCache[iAsic][fbkDac]         & 0x003) << 30;
    dacWords[1] |= (u32)(scanParams->dacCache[iAsic][tpRefDac]       & 0x0FF) << 22;
    dacWords[1] |= (u32)(scanParams->dacCache[iAsic][gndDac]         & 0x0FF) << 14;
    dacWords[1] |= (u32)(scanParams->dacCache[iAsic][rpzDac]         & 0x0FF) << 6;
    dacWords[1] |= (u32)(scanParams->dacCache[iAsic][tpBufferOutDac] & 0x0FC) >> 2;

    dacWords[2] |= (u32)(scanParams->dacCache[iAsic][tpBufferOutDac] & 0x003) << 30;
    dacWords[2] |= (u32)(scanParams->dacCache[iAsic][tpBufferInDac]  & 0x0FF) << 22;
    dacWords[2] |= (u32)(scanParams->dacCache[iAsic][delayDac]       & 0x0FF) << 14;
    dacWords[2] |= (u32)(scanParams->dacCache[iAsic][dacPixelDac]    & 0x0FF) << 6;
    dacWords[2] |= (u32)(scanParams->dacCache[iAsic][thresholdNDac]  & 0x0FC) >> 2;

    dacWords[3] |= (u32)(scanParams->dacCache[iAsic][thresholdNDac]  & 0x003) << 30;
    dacWords[3] |= (u32)(scanParams->dacCache[iAsic][discLsDac]      & 0x0FF) << 22;
    dacWords[3] |= (u32)(scanParams->dacCache[iAsic][discDac]        & 0x0FF) << 14;
    dacWords[3] |= (u32)(scanParams->dacCache[iAsic][shaperDac]      & 0x0FF) << 6;
    dacWords[3] |= (u32)(scanParams->dacCache[iAsic][ikrumDac]       & 0x0FC) >> 2;

    dacWords[4] |= (u32)(scanParams->dacCache[iAsic][ikrumDac]       & 0x003) << 30;
    dacWords[4] |= (u32)(scanParams->dacCache[iAsic][preampDac]      & 0x0FF) << 22;
    dacWords[4] |= (u32)(scanParams->dacCache[iAsic][threshold7Dac]  & 0x1FF) << 13;
    dacWords[4] |= (u32)(scanParams->dacCache[iAsic][threshold6Dac]  & 0x1FF) << 4;
    dacWords[4] |= (u32)(scanParams->dacCache[iAsic][threshold5Dac]  & 0x1E0) >> 5;

    dacWords[5] |= (u32)(scanParams->dacCache[iAsic][threshold5Dac]  & 0x01F) << 27;
    dacWords[5] |= (u32)(scanParams->dacCache[iAsic][threshold4Dac]  & 0x1FF) << 18;
    dacWords[5] |= (u32)(scanParams->dacCache[iAsic][threshold3Dac]  & 0x1DF) << 9;
    dacWords[5] |= (u32)(scanParams->dacCache[iAsic][threshold2Dac]  & 0x1FF) << 0;

    dacWords[6] |= (u32)(scanParams->dacCache[iAsic][threshold1Dac]  & 0x1FF) << 23;
    dacWords[6] |= (u32)(scanParams->dacCache[iAsic][threshold0Dac]  & 0x1FF) << 14;

    xil_printf("DAC words: ");
    for (iWord = 0; iWord < kNumAsicDpmWords; iWord++)
    {
    	xil_printf("0x%08x ", dacWords[iWord]);
    }
    xil_printf("\r\n");

    // Load the DAC words into the FEM (DPM area accessed via RDMA)
    for (iWord = 0; iWord < kNumAsicDpmWords; iWord++)
    {
    	status = writeRdma(kExcaliburAsicDpmRdmaAddress + iWord, dacWords[iWord]);
    	if (status != XST_SUCCESS)
    	{
    		// TODO: flag error
    		xil_printf("RDMA write of DAC words to BRAM failed on word %d status %d\r\n", iWord, status);
    		rc = 1;
    		break;
    	}
    }
    if (rc != 0) {
    	return rc;
    }

    // Set the ASIC MUX register
    u32 muxSelect = ((u32)1 << (7- iAsic));
    status = writeRdma(kExcaliburAsicMuxSelect, muxSelect);
    if (status != XST_SUCCESS)
    {
    	xil_printf("RDMA write of ASIC mux select failed, status %d", status);
    	rc = 1;
    	return rc;
    }

    // Set up the OMR registers for DAC write
    status = setOmr(scanParams->omrDacSet);
    if (status != XST_SUCCESS)
    {
    	xil_printf("RDMA write of DAC set OMR failed, status %d", status);
    	rc = 1;
    	return rc;
    }

    // Trigger DAC write transaction to ASIC
    status = writeRdma(kExcaliburAsicControlReg, 0x23);
    if (status != XST_SUCCESS)
    {
    	xil_printf("RDMA write to trigger DAC load failed, status %d", status);
    	rc = 1;
    	return rc;
    }

    // Read back control state register and check write transaction completed
    u32 ctrlState;
    status = readRdma(kExcaliburAsicCtrlState1, &ctrlState);
    if (status != XST_SUCCESS)
    {
    	xil_printf("RDMA read of ASIC ctrlState1 register failed, status %s", status);
    	rc = 1;
    	return rc;
    }
    if (ctrlState != 0x80000000)
    {
    	xil_printf("DAC load transaction to ASIC failed to complete, state=0x%08x", ctrlState);
    	rc = 1;
    	return rc;
    }

	return rc;
}

int setOmr(alignedOmr omr)
{
	int status;

	status = writeRdma(kExcaliburAsicOmrBottom, omr.bottom);
    if (status != XST_SUCCESS) {
    	return status;
    }
    status = writeRdma(kExcaliburAsicOmrTop, omr.top);

    return status;
}
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
