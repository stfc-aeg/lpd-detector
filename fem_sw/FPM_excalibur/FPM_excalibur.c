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

			xil_printf("FPM_Excalibur: state.state   = %d\r\n", state.state);
			xil_printf("FPM_Excalibur: state.numOps  = %d\r\n", state.numOps);
			xil_printf("FPM_Excalibur: state.compOps = %d\r\n", state.compOps);
			xil_printf("FPM_Excalibur: state.error   = %d\r\n", state.error);
			xil_printf("FPM_Excalibur: error msg     = %s\r\n", state.errorString);
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
	int rc = 0;

	xil_printf("FPM_Excalibur [DACscan]: Thread active!\r\n");

	// Flag as busy
	state.state = 1;

	// Clear error state
	SETPERSERR(FPM_EXCALIBUR_NO_ERROR, "No error");

	// This won't return any data but if it were to do so, something like this would happen:
	// malloc(pOutput, (size_t)n)
	// outputSz = n;

	// Decode scan parameters from input payload
	dacScanParams* scanParams = (dacScanParams*)pInput;

	// Calculate number of operations and load into thread state
	state.numOps = ((scanParams->dacStop - scanParams->dacStart) / scanParams->dacStep) + 1;
	state.compOps = 0;

	// Set up scan in system
	rc = setupScan(scanParams);

	// Only execute scan if setup succeeded
	if (rc == 0)
	{
		// Loop over scan parameters and execute scan

		for (scanDacVal = scanParams->dacStart; scanDacVal <= scanParams->dacStop; scanDacVal += scanParams->dacStep)
		{

			//xil_printf("Scanning DAC %d val %d\r\n", scanParams->scanDac, scanDacVal);

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
				// Stop ASIC loop if failure
				if (rc != 0) {
					break;
				}
			}
			// Stop scan if failure
			if (rc != 0) {
				break;
			}

			// Acquire an image
			rc = acquireImage(scanParams);
			if (rc != 0) {
				break;
			}
			state.compOps++;
		}
	}

	// Flag as idle
	state.state = 0;
	currentThreadType = 0;

	// Set datasize (none in this case)
	outputSz = 0;

	// TODO: free(pInput)

	xil_printf("FPM_Excalibur [DACscan]: Thread complete\r\n");

	// Terminate
	pthread_exit(NULL);

	// This statement never executes but suppresses warning on compiler
	return 0;
}

int setupScan(dacScanParams* scanParams)
{
	int rc = 0;
	int status;
	u32 shutterCounter;

	// Set number of frames to be triggered in ASIC control block - single frame at a time
	status = writeRdma(kExcaliburAsicFrameCounter, 1);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_EXCALIBUR_SETUP_FAILED,
				"Failed to set up ASIC control frame counter, status=%d", status);
		rc = 1;
		return rc;
	}

	// Set shutter resolution to 500ns (register value 0x64)
	status = writeRdma(kExcaliburAsicShutterResolution, 0x64);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_EXCALIBUR_SETUP_FAILED,
				"Failed to set ASIC shutter resolution register, status=%d", status);
		rc =1 ;
		return rc;
	}

	// Set up the acquisition time in the ASIC shutter duration registers based on 500ns resolution
	shutterCounter = scanParams->acquisitionTimeMs * 2000;
	status = writeRdma(kExcaliburAsicShutter0Counter, shutterCounter);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_EXCALIBUR_SETUP_FAILED,
				"Failed to set ASIC shutter 0 counter register, status=%d", status);
		rc =1 ;
		return rc;
	}
	status = writeRdma(kExcaliburAsicShutter1Counter, shutterCounter);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_EXCALIBUR_SETUP_FAILED,
				"Failed to set ASIC shutter 1 counter register, status=%d", status);
		rc =1 ;
		return rc;
	}

	return rc;
}

int loadDacs(unsigned int iAsic, dacScanParams* scanParams)
{
	int rc = 0;
	int status;
	u32 dacWords[kNumAsicDpmWords];
	unsigned int iWord;
	//xil_printf("Loading DACs for ASIC %d\r\n", iAsic);

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

//    xil_printf("DAC words: ");
//    for (iWord = 0; iWord < kNumAsicDpmWords; iWord++)
//    {
//    	xil_printf("0x%08x ", dacWords[iWord]);
//    }
//    xil_printf("\r\n");

    // Load the DAC words into the FEM (DPM area accessed via RDMA)
    for (iWord = 0; iWord < kNumAsicDpmWords; iWord++)
    {
    	status = writeRdma(kExcaliburAsicDpmRdmaAddress + iWord, dacWords[iWord]);
    	if (status != XST_SUCCESS)
    	{
    		SETPERSERR(FPM_EXCALIBUR_DAC_LOAD_FAILED,
    				"RDMA write of DAC words for ASIC %d failed on word %d status %d", iAsic, iWord, status);
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
    	SETPERSERR(FPM_EXCALIBUR_DAC_LOAD_FAILED,
    			"RDMA write of ASIC mux select for ASIC %d failed, status %d", iAsic, status);
    	rc = 1;
    	return rc;
    }

    // Set up the OMR registers for DAC write
    status = setOmr(scanParams->omrDacSet);
    if (status != XST_SUCCESS)
    {
    	SETPERSERR(FPM_EXCALIBUR_DAC_LOAD_FAILED,
    			"RDMA write of DAC set OMR for ASIC %d failed, status %d", iAsic, status);
    	rc = 1;
    	return rc;
    }

    // Trigger DAC write transaction to ASIC
    status = writeRdma(kExcaliburAsicControlReg, 0x23);
    if (status != XST_SUCCESS)
    {
    	SETPERSERR(FPM_EXCALIBUR_DAC_LOAD_FAILED,
    			"RDMA write to trigger DAC load for ASIC %d failed, status %d", iAsic, status);
    	rc = 1;
    	return rc;
    }

    // Wait for transaction to finish
    usleep(50);

    // Read back control state register and check write transaction completed
    u32 ctrlState;
    status = readRdma(kExcaliburAsicCtrlState1, &ctrlState);
    if (status != XST_SUCCESS)
    {
    	SETPERSERR(FPM_EXCALIBUR_DAC_LOAD_FAILED,
    			"RDMA read of ASIC ctrlState1 register for ASIC %d failed, status %d", iAsic, status);
    	rc = 1;
    	return rc;
    }
    if (ctrlState != 0x80000000)
    {
    	SETPERSERR(FPM_EXCALIBUR_DAC_LOAD_FAILED,
    			"DAC load transaction to ASIC %d failed to complete, state=0x%08x", iAsic, (unsigned int)ctrlState);
    	rc = 1;
    	return rc;
    }

	return rc;
}

int acquireImage(dacScanParams* scanParams)
{
	int rc = 0;
	int status;
    u32 ctrlState;
    unsigned int completionRetries = 0;
    unsigned int completionRetrySleep = 100; // 100us
    unsigned int completionMaxRetries = (scanParams->acquisitionTimeMs * 1000 * 10) / completionRetrySleep;
    u32 completionState = 0x81000000;

	// Set up ASIC mux select register based on active ASICS
	status = writeRdma(kExcaliburAsicMuxSelect, scanParams->asicMask);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
				"RDMA write to ASIC MUX select for image acquisition failed, status=%d", status);
		rc = 1;
		return rc;
	}

	// Set up the OMR transaction for an image acquisition
	status = setOmr(scanParams->omrAcquire);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
				"RDMA write of ASIC OMR for image acquisition failed, status=%d", status);
		rc = 1 ;
		return rc;
	}

	// Trigger image acquisition
	status = writeRdma(kExcaliburAsicControlReg, scanParams->executeCommand);
	if (status != XST_SUCCESS)
	{
		SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
				"RDMA write to trigger image acquisition failed, status=%d", status);
		rc = 1 ;
		return rc;
	}

	// Sleep for the duration of the image acquisition
	usleep(scanParams->acquisitionTimeMs * 1000);

    // Read back control state register and check image acquisition completed
    status = readRdma(kExcaliburAsicCtrlState1, &ctrlState);
    if (status != XST_SUCCESS)
    {
    	SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
    			"RDMA read of ASIC ctrlState1 register during image acq failed, status %d", status);
    	rc = 1;
    	return rc;
    }

    while ((completionRetries < completionMaxRetries) && (ctrlState != completionState))
    {
    	usleep(completionRetrySleep);
        status = readRdma(kExcaliburAsicCtrlState1, &ctrlState);
        if (status != XST_SUCCESS)
        {
        	SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
        			"RDMA read of ASIC ctrlState1 register during image acq failed, status %d", status);
        	rc = 1;
        	return rc;
        }
        completionRetries++;
    }
    if (ctrlState != 0x81000000)
    {
    	SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
    			"Image acquisition failed to complete, state=0x%08x", (unsigned int)ctrlState);
    	rc = 1;
    	return rc;
    }

    // Poll the DMA controller ACQUIRE status block to determine how many images have
    // been transferred to TenGigE. Wait until this matches the number of completed operations
    // in the scan (i.e. this image is complete) before continuing. This avoids any DMA
    // contention between ASIC readout and image transfer off the FEM.
    unsigned int numImagesTransferred = getNumImagesTransferred();
    unsigned int numImageRetries = 0;
    unsigned int maxImageRetries = 100;
    unsigned int imageRetrySleep = 100;

    while ((numImageRetries < maxImageRetries) && (numImagesTransferred != (state.compOps+1)))
    {
    	usleep(imageRetrySleep);
    	numImagesTransferred = getNumImagesTransferred();
    	numImageRetries++;
    }

    if (numImagesTransferred != (state.compOps+1))
    {
    	SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
    			"DMA of image %ld failed to complete", (state.compOps+1));
    	rc = 1;
    	return rc;

    }
    // Send ASIC control block reset
    status = writeRdma(kExcaliburAsicControlReg, 0x400000);
    if (status != XST_SUCCESS)
    {
    	SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
    			"RDMA write to reset ASIC control during image acq failed, status %d", status);
    	rc = 1;
    	return rc;
    }
    status = writeRdma(kExcaliburAsicControlReg, 0x0);
    if (status != XST_SUCCESS)
    {
    	SETPERSERR(FPM_IMAGE_ACQUIRE_FAILED,
    			"RDMA write to clear ASIC ctrl register during image acq failed, status %d", status);
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

unsigned int getNumImagesTransferred(void)
{
	acqStatus* theStatus = (acqStatus*)BADDR_BRAM;
	return (unsigned int)(theStatus->totalSent / 2);
}
// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
