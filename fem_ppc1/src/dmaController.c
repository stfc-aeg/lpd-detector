/*
 * dmaController.c
 * ---------------
 *
 * FEM PPC1 main application (for use with standalone BSP)
 *
 * Responsible for allocating memory buffers and controlling the PPC DMA engines to arbitrate
 * transfers from ASIC(s) -> DDR2 -> 10GBe, as well as uploading configuration data from DDR2 -> ASIC(s).
 *
 * Controlled by PPC2 via Xilinx Mailbox commands.
 *
 */

// Todo list, in order of priority
// TODO: Implement configuration upload
// TODO: Fix configure for acquire, respect config BD storage area
// TODO: Respect doTx / doRx flags
// TODO: Move BD Free into recycleBuffer (not in validateBuffer)
// TODO: Complete event loop with mailbox/DMA
// TODO: Complete shared bram status flags

#include <stdio.h>
#include "xmbox.h"
#include "xparameters.h"
#include "platform.h"
#include "xlldma.h"
#include "xil_testmem.h"

// TODO: Move defines, function prototypes to header!
// Device Control Register (DCR) offsets for PPC DMA engine (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_ASIC_BOT		0x80							//! DCR offset for DMA0 (RX from bottom ASIC)
#define LL_DMA_BASE_UPLOAD			0x98							//! DCR offset for DMA1 (TX to ASIC configuration)
#define LL_DMA_BASE_ASIC_TOP		0xB0							//! DCR offset for DMA2 (RX from top ASIC)
#define LL_DMA_BASE_TENGIG			0xC8							//! DCR offset for DMA3 (TX to 10GBE)

// DMA engine info
#define LL_DMA_ALIGNMENT			XLLDMA_BD_MINIMUM_ALIGNMENT		//! BD Alignment, set to minimum
#define LL_BD_BADDR					0x8D280000						//! Bass address for BDs
#define LL_BD_SZ					0x00180000						//! Size of BD memory region
#define LL_STSCTRL_RX_OK			0x1D000000						//! STS/CTRL field in BD should be 0x1D when successfully RX (COMPLETE | SOP | EOP)
#define LL_STSCTRL_TX_OK			0x10000000						//! STS/CTRL field in BD should be 0x10 when successfully TX (COMPLETE)
#define LL_STSCTRL_RX_BD			0x0															//! STS/CTRL field for a RX BD
#define LL_STSCTRL_TX_BD			XLLDMA_BD_STSCTRL_SOP_MASK | XLLDMA_BD_STSCTRL_EOP_MASK		//! STS/CTRL field for a TX BD
#define LL_MAX_CONFIG_BD			64								//! Maximum number of config upload BDs

// Buffer management
#define DDR2_BADDR					0x00000000						//! DDR2 base address
#define DDR2_SZ						0x40000000						//! DDR2 size (1GB)

// Shared BRAM area
#define BRAM_BADDR					XPAR_SHARED_BRAM_IF_CNTLR_PPC_1_BASEADDR

// Ring indexes
#define BD_RING_TOP_ASIC			0								//! Top I/O Spartan / ASIC connection
#define BD_RING_BOT_ASIC			1								//! Bottom I/O Spartan / ASIC connection
#define BD_RING_TENGIG				2								//! 10GBe
#define BD_RING_UPLOAD				3								//! Configuration upload

// TODO: Remove these once common protocol.h
// TODO: Change to enum
#define ACQ_MODE_NORMAL				1
#define ACQ_MODE_RX_ONLY			2
#define ACQ_MODE_TX_ONLY			3
#define ACQ_MODE_UPLOAD				4

#define CMD_ACQ_CONFIG				1
#define CMD_ACQ_START				2
#define CMD_ACQ_STOP				3
#define CMD_ACQ_STATUS				4

typedef enum
{
	BD_RX,
	BD_TX
} bufferType;

//! Data structure to store in shared BRAM for status information
// TODO: Store this in common header file!
typedef struct
{
	u32 state;			//! Current mode?
	u32 bufferCnt;		//! Number of buffers allocated
	u32 bufferSize;		//! Size of buffers
	u32 numAcq;			//! Number of acquisitions in this run
	u32 numConfigBds;	//! Number of configuration BDs set
	u32 readPtr;		//! 'read pointer'
	u32 writePtr;		//! 'write pointer'
	u32 totalRecv;		//! Total number of buffers received from I/O Spartans
	u32 totalSent;		//! Total number of buffers sent to 10GBe DMA channel
	u32 totalErrors;	//! Total number of DMA errors (do we need to track for each channel?)
} acqStatusBlock;



// FUNCTION PROTOTYPES
int configureBdsForAcquisition(XLlDma_BdRing *pBdRings[], XLlDma_Bd **pTxBd, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock);
int configureBdsForUpload(XLlDma_BdRing *pUploadBdRing, XLlDma_Bd **pFirstConfigBd, u32 bufferAddr, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock);
int validateBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType);
int recycleBuffer(XLlDma_BdRing *pBdRings, XLlDma_Bd *pBd, bufferType bType);

//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

int main()
{
    init_platform();

	// Clear serial console
	int foo;
	for (foo=0; foo<100; foo++) { print("\r\n"); }

	// Dump a little diagnostic info
    print("[INFO ] FEM PPC1 DMA Controller starting up...\r\n");
    print("[INFO ] ------------------------------------------------\r\n");
    printf("[INFO ] Total DDR2 space for buffers:         0x%08x\r\n", DDR2_SZ);
    printf("[INFO ] Total SRAM space for BDs:             0x%08x\r\n", LL_BD_SZ);
    printf("[INFO ] Maximum number of readout BDs:        %d\r\n", ((LL_BD_SZ/LL_DMA_ALIGNMENT)/4)-LL_MAX_CONFIG_BD);
    printf("[INFO ] Maximum number of config upload BDs:  %d\r\n", LL_MAX_CONFIG_BD);
    print("[INFO ] ------------------------------------------------\r\n");

    // Flags and main loop variables
    int status;
    int i;
    short doRx = 0;			// RX control flag for main loop
    short doTx = 0;			// TX control flag for main loop
    unsigned numTx = 0;

    // Initialise BRAM status
    acqStatusBlock* pStatusBlock = (acqStatusBlock*)BRAM_BADDR;
    pStatusBlock->state =			0;
    pStatusBlock->bufferCnt =		0;
    pStatusBlock->bufferSize =		0;
    pStatusBlock->numAcq =			0;
    pStatusBlock->numConfigBds =	0;
    pStatusBlock->readPtr =			0;
    pStatusBlock->writePtr =		0;
    pStatusBlock->totalRecv =		0;
    pStatusBlock->totalSent =		0;
    pStatusBlock->totalErrors =		0;

    u32 mailboxBuffer[5] =	{0,0,0,0,0};

    XLlDma dmaAsicTop, dmaAsicBot, dmaTenGig, dmaPixMem;

    XLlDma_BdRing *pBdRings[4];

    pBdRings[BD_RING_TOP_ASIC]	= &XLlDma_GetRxRing(&dmaAsicTop);
    pBdRings[BD_RING_BOT_ASIC]	= &XLlDma_GetRxRing(&dmaAsicBot);
    pBdRings[BD_RING_TENGIG]	= &XLlDma_GetTxRing(&dmaTenGig);
    pBdRings[BD_RING_UPLOAD]	= &XLlDma_GetTxRing(&dmaPixMem);

    // Initialise DMA engines
    XLlDma_Initialize(&dmaAsicTop, LL_DMA_BASE_ASIC_TOP);
    XLlDma_Initialize(&dmaAsicBot, LL_DMA_BASE_ASIC_BOT);
    XLlDma_Initialize(&dmaTenGig, LL_DMA_BASE_TENGIG);
    XLlDma_Initialize(&dmaPixMem, LL_DMA_BASE_UPLOAD);

    // Initialise mailbox
    XMbox mbox;
    XMbox_Config mboxCfg;
    mboxCfg.BaseAddress =	XPAR_MAILBOX_0_IF_0_BASEADDR;
    mboxCfg.DeviceId =		XPAR_MAILBOX_0_IF_0_DEVICE_ID;
    mboxCfg.RecvID =		XPAR_MAILBOX_0_IF_0_RECV_FSL;
    mboxCfg.SendID =		XPAR_MAILBOX_0_IF_0_SEND_FSL;
    mboxCfg.UseFSL =		XPAR_MAILBOX_0_IF_0_USE_FSL;
    status = XMbox_CfgInitialize(&mbox, &mboxCfg, XPAR_MAILBOX_0_IF_0_BASEADDR);
    if (status!=XST_SUCCESS) {
    	print("[ERROR] Mailbox initialise failed, terminating...\r\n");
    	return 0;
    }
    print("[INFO ] Mailbox initialised.\r\n");



    // Enter mailbox-driven outer loop
    while(1)
    {

    	XLlDma_Bd *pTenGigBd;
    	XLlDma_Bd *pConfigBd;

    	unsigned short acquireRunning = 0;
    	print("[INFO ] Waiting for mailbox message...\r\n");

    	// Blocking read of 5x 32bit word
    	XMbox_ReadBlocking(&mbox, &mailboxBuffer[0], 20);
    	printf("[INFO ] Got message!  cmd=0x%08x, buffSz=0x%08x, buffCnt=0x%08x, modeParam=%d, mode=%d\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[1], (unsigned)mailboxBuffer[2], (unsigned)mailboxBuffer[3], (unsigned)mailboxBuffer[4]);

    	switch (mailboxBuffer[0])
    	{

			case CMD_ACQ_CONFIG:
		    	// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
		    	switch(mailboxBuffer[4])
		    	{
		    		case ACQ_MODE_NORMAL:
		    			doTx = 1;
		    			doRx = 1;
		    			status = configureBdsForAcquisition(pBdRings, &pTenGigBd, mailboxBuffer[1], mailboxBuffer[2], pStatusBlock);
		    			break;
		    		case ACQ_MODE_RX_ONLY:
		    			doTx = 0;
		    			doRx = 1;
		    			status = configureBdsForAcquisition(pBdRings, &pTenGigBd, mailboxBuffer[1], mailboxBuffer[2], pStatusBlock);
		    			break;
		    		case ACQ_MODE_TX_ONLY:
		    			doTx = 1;
		    			doRx = 0;
		    			status = configureBdsForAcquisition(pBdRings, &pTenGigBd, mailboxBuffer[1], mailboxBuffer[2], pStatusBlock);
		    			break;
		    		case ACQ_MODE_UPLOAD:
		    			// TODO: Refactor numAcq to something more generic (ACQ_MODE_NORMAL->numAcq, ACQ_MODE_UPLOAD->configStartAddr) --> modeParam?
		    			status = configureBdsForUpload(pBdRings[BD_RING_UPLOAD], &pConfigBd, mailboxBuffer[3], mailboxBuffer[1], mailboxBuffer[2], pStatusBlock);
		    			break;
		    		default:
		    			printf("[ERROR] Unknown ACQ mode %d - Ignoring.\r\n", (int)mailboxBuffer[4]);
		    			break;
		    	}

		        if (status==XST_SUCCESS)
		        {
		        	// All OK, update status struct with buffer details
		        	if (mailboxBuffer[4] != ACQ_MODE_UPLOAD)
		        	{
						pStatusBlock->bufferSize = mailboxBuffer[1];
						pStatusBlock->bufferCnt = mailboxBuffer[2];
						pStatusBlock->numAcq = mailboxBuffer[3];
						pStatusBlock->state = mailboxBuffer[4];
		        	}
		        }
		        else
		        {
		        	printf("[ERROR] An error occurred configuring BDs!  Error code %d\r\n", status);
		        	print("[ERROR] Terminating process...\r\n");
		        	return 0;
		        }
		        // -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
		        break;

		    case CMD_ACQ_START:
		    	switch(mailboxBuffer[4])
		    		case ACQ_MODE_NORMAL:
		    		case ACQ_MODE_RX_ONLY:
		    		case ACQ_MODE_TX_ONLY:
					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
					printf("[INFO ] Entering acquire DMA event loop\r\n");
					acquireRunning = 1;
					while (acquireRunning)
					{

						print ("\r\n");

						// Wait for data to be received
						XLlDma_Bd *pTopAsicBd, *pBotAsicBd;
						unsigned numRxTop = 0;
						unsigned numRxBot = 0;
						unsigned totalRx = 0;
						unsigned short done = 0;

						print("[INFO ] Waiting for ASIC RX...\r\n");

						while(done==0)
						{

							// See if DMA engine has completed receive from either Spartan
							numRxTop = XLlDma_BdRingFromHw(pBdRings[BD_RING_TOP_ASIC], 1, &pTopAsicBd);
							numRxBot = XLlDma_BdRingFromHw(pBdRings[BD_RING_BOT_ASIC], 1, &pBotAsicBd);

							if (numRxTop !=0 )
							{
								status = validateBuffer(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd, BD_RX);
								if (status==XST_SUCCESS) {
									totalRx++;
								}
								else
								{
									printf("[ERROR] RX from top ASIC failed validation, error code %d\r\n", status);
									return 0;
								}
							}

							if (numRxBot != 0 )
							{
								status = validateBuffer(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd, BD_RX);
								if (status==XST_SUCCESS) {
									totalRx++;
								}
								else
								{
									printf("[ERROR] RX from bottom ASIC failed validation, error code %d\r\n", status);
									return 0;
								}
							}

							// TODO: Check we got 1 top / 1 bottom!

							// Once we have both RX, we can arm the TX engine
							if (totalRx==2)
							{
								print("[INFO ] Got RX from ASICs!\r\n");

								pStatusBlock->totalRecv++;

								// Do a proper TX
								// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

								// Commit next 2 BDs in TX ring to hardware control
								status = XLlDma_BdRingToHw(pBdRings[BD_RING_TENGIG], 2, pTenGigBd);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Could not commit TX BDs!  Error code %d\r\n", status);
									return 0;
								}

								/*
								status = XLlDma_BdRingStart(pBdRings[BD_RING_TENGIG]);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Can't start 10GBe TX engine, error code %d\r\n", status);
									return 0;
								}
								*/

								// Confirm TX was OK
								// TODO: This will keep RX/TX in lock step which we don't want to do!  Fix.
								print("[INFO ] Waiting for TX BDs to return...\r\n");
								numTx = 0;
								while (numTx!=2)
								{
									numTx = XLlDma_BdRingFromHw(pBdRings[BD_RING_TENGIG], 2, &pTenGigBd);
								}

								// -------------------- TX1 --------------------
								status = validateBuffer(pBdRings[BD_RING_TENGIG], pTenGigBd, BD_TX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Error validating TX BD 1, error code %d\r\n", status);
									return 0;
								}
								status = recycleBuffer(pBdRings[BD_RING_TENGIG], pTenGigBd, BD_TX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Error on recycleBuffer for TX, error code %d\r\n", status);
									return 0;
								}

								pTenGigBd = XLlDma_BdRingNext(pBdRings[BD_RING_TENGIG], pTenGigBd);

								// -------------------- TX2 --------------------
								status = validateBuffer(pBdRings[BD_RING_TENGIG], pTenGigBd, BD_TX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Error validating TX BD 2, error code %d\r\n", status);
									return 0;
								}
								status = recycleBuffer(pBdRings[BD_RING_TENGIG], pTenGigBd, BD_TX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Error on recycleBuffer for TX, error code %d\r\n", status);
									return 0;
								}

								print("[INFO ] Validated TX BDs OK!\r\n");

								pTenGigBd = XLlDma_BdRingNext(pBdRings[BD_RING_TENGIG], pTenGigBd);

								pStatusBlock->totalSent++;
								// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

								// Recycle RX BDs
								status = recycleBuffer(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd, BD_RX);
								if (status!=XST_SUCCESS) { printf("[ERROR] Failed to recycle buffer for top ASIC!  Error code = %d\r\n", status); }
								status = recycleBuffer(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd, BD_RX);
								if (status!=XST_SUCCESS) { printf("[ERROR] Failed to recycle buffer for bottom ASIC!  Error code = %d\r\n", status); }

								// All finished, flag complete
								done=1;
							}

							// Check if there are any pending mailbox messages
							u32 bytesRecvd = 0;
							XMbox_Read(&mbox, &mailboxBuffer[0], 20, &bytesRecvd);
							if (bytesRecvd == 20) {
								printf("[INFO ] Got message!  cmd=%d (0x%08x)\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[0]);
								switch (mailboxBuffer[0])
								{
								case CMD_ACQ_STOP: // STOP ACQUIRE
									print("[INFO ] Got stop acquire message, exiting acquire loop\r\n");
									done = 1;
									acquireRunning = 0;
									break;

								default:
									print("[ERROR] Unexpected command in acquire loop, ignoring for now\r\n");
									break;
								}
							}
						} // END while(done==0)

					} // END while(acquireRunning)
					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
					break;
		    	break;

		    	// -------------------------------------------------------------------------------------

		    	case ACQ_MODE_UPLOAD:

		    		printf("[INFO ] Sending %d configuration upload TXes...\r\n", (int)pStatusBlock->numConfigBds);

	    			// Send TX BDs to hardware control
	    			status = XLlDma_BdRingToHw(pBdRings[BD_RING_UPLOAD], pStatusBlock->numConfigBds, pConfigBd);
	    			if (status!=XST_SUCCESS)
	    			{
	    				printf("[ERROR] Could not commit %d upload BD(s) to hardware control!  Error code %d\r\n", (unsigned)mailboxBuffer[2], status);
	    			}

	    			// Retrieve TX BDs
					numTx = 0;
					print("[INFO ] Waiting for upload TX...\r\n");
					while (numTx!=pStatusBlock->numConfigBds)
					{
						numTx = XLlDma_BdRingFromHw(pBdRings[BD_RING_UPLOAD], pStatusBlock->numConfigBds, &pConfigBd);
					}

					// Verify / free BDs
					for(i=0; i<pStatusBlock->numConfigBds; i++)
					{
						status = validateBuffer(pBdRings[BD_RING_UPLOAD], pConfigBd, BD_TX);
						if (status!=XST_SUCCESS)
						{
							printf("[ERROR] Error validating upload TX BD %d, error code %d\r\n", i, status);
						}
						status = recycleBuffer(pBdRings[BD_RING_UPLOAD], pTenGigBd, BD_TX);
						if (status!=XST_SUCCESS)
						{
							printf("[ERROR] Error on recycleBuffer for upload TX, error code %d\r\n", status);
						}
					}

		    		break;

			case CMD_ACQ_STOP:
				// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
				printf("[INFO ] Not doing anything with stop acquire command.\r\n");
				// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
				break;

			default:
				// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
				printf("[ERROR] Unrecognised mailbox command %d\r\n", (unsigned)mailboxBuffer[0]);
				// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
				break;

    	} // END switch(mailboxBuffer[0])

    }

    // Should never execute!
    print("[INFO ] Process terminating...\r\n");
    cleanup_platform();
    return 0;

}



/*
 * Generic DMA setup function, accepts segment size (size of data to RX from I/O Spartan),
 * and segment count (to limit the number of BDs created for debugging / #-frame mode)
 * @param pBdRings pointer to array of BD rings
 * @param pFirstTxBd set by function to be first BD in TX ring
 * @param segmentSz Size of data to RX from I/O Spartan
 * @param segmentCnt Number of segments to allocate, set to 0 for allocation of maximum BDs
 * @return XST_SUCCESS if OK, otherwise an XST_xxx error code
 *
 */
int configureBdsForAcquisition(XLlDma_BdRing *pBdRings[], XLlDma_Bd **pFirstTxBd, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock)
{

	// TODO: Check what the last configuration was for and if it matches the request, don't reconfigure BDs!

	// TODO: Take into account the reserved BD config area!

	XLlDma_BdRing *pRingTenGig = pBdRings[BD_RING_TENGIG];
	XLlDma_BdRing *pRingAsicTop = pBdRings[BD_RING_TOP_ASIC];
	XLlDma_BdRing *pRingAsicBot = pBdRings[BD_RING_BOT_ASIC];

	unsigned status;
	u32 totalNumBuffers = 0;				// Maximum number of buffers we can allocate
	u32 bankSize = DDR2_SZ / 2;				// We have 2 DDR2 'banks', one for each I/O Spartan

	u32 maxPossibleBds = (LL_BD_SZ / XLLDMA_BD_MINIMUM_ALIGNMENT) / 4;

	// Check DDR2 is large enough for requested number/size of segments
	if (bufferCnt==0)
	{
		// If segmentCnt==0 we allocate as many segments as will fit in a bank
		totalNumBuffers = bankSize / bufferSz;
	}
	else
	{
		// Otherwise allocate the requested number of segments
		if ((bufferSz * bufferCnt) <= bankSize) {
			totalNumBuffers = bufferCnt;
		}
		else
		{
			// Not enough space to allocate that many segments
			printf("[ERROR] Cannot allocate %d x 0x%08x segments, exceeds DDR2 capacity!\r\n", (int)bufferCnt, (unsigned)bufferSz);
			return XST_FAILURE;
		}
	}

	// Now check there is enough space to store the BDs for that amount of buffers
	if ( (totalNumBuffers * 4 * XLLDMA_BD_MINIMUM_ALIGNMENT) > LL_BD_SZ)		// 4 because we need 2x RX and 2x TX BDs per 'read'
	{
		printf("[INFO ] Cannot allocate %d x 4 x 0x%08x buffers, exceeds BD storage capacity...\r\n", (int)totalNumBuffers, (unsigned)bufferSz);

		// Reduce buffer allocation to fit BD storage space
		printf("[INFO ] Reducing buffer depth to %d to fit BDs!\r\n", (int)maxPossibleBds);
		totalNumBuffers = maxPossibleBds;
	}

	printf("[DEBUG] Requested %d buffers of (2 x 0x%08x) bytes...\r\n", (unsigned)totalNumBuffers, (unsigned)bufferSz);


	// Create BD rings of appropriate size
	// TODO: Should we have an assert to make sure we don't exceed our allocated space (doing so will overwrite PPC2 code!)
	u32 bdChunkSize =			XLLDMA_BD_MINIMUM_ALIGNMENT * totalNumBuffers;			// Total space required for all BDs for a given channel, we'll call that a chunk
	u32 topAsicRXBdOffset =		LL_BD_BADDR;
	u32 botAsicRXBdOffset =		topAsicRXBdOffset + bdChunkSize;
	u32 tenGigTXBdOffset =		botAsicRXBdOffset + bdChunkSize;
	printf("[INFO ] BDs: \r\n");
	printf("[INFO ] TopASIC      0x%08x\r\n", (unsigned)topAsicRXBdOffset);
	printf("[INFO ] Bottom ASIC  0x%08x\r\n", (unsigned)botAsicRXBdOffset);
	printf("[INFO ] TenGig       0x%08x\r\n", (unsigned)tenGigTXBdOffset);

	status = XLlDma_BdRingCreate(pRingAsicTop, topAsicRXBdOffset, topAsicRXBdOffset, LL_DMA_ALIGNMENT, totalNumBuffers);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create top ASIC RX BD ring!  Error code %d\r\n", status);
		return status;
	}

	status = XLlDma_BdRingCreate(pRingAsicBot, botAsicRXBdOffset, botAsicRXBdOffset, LL_DMA_ALIGNMENT, totalNumBuffers);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create bottom ASIC RX BD ring!  Error code %d\r\n", status);
		return status;
	}

	// Note the TX ring is double the length of the RX rings!
	status = XLlDma_BdRingCreate(pRingTenGig, tenGigTXBdOffset, tenGigTXBdOffset, LL_DMA_ALIGNMENT, totalNumBuffers*2);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create 10GBE TX BD ring!  Error code %d\r\n", status);
		return status;
	}

	printf("[INFO ] Created BD rings w/%d buffers each.\r\n", (int)totalNumBuffers);


	// Configure BDs in rings
	XLlDma_Bd *pTopRXBd;
	XLlDma_Bd *pBotRXBd;
	XLlDma_Bd *pTXBd;

	// First allocate a BD for each ring
	status = XLlDma_BdRingAlloc(pRingAsicTop, totalNumBuffers, &pTopRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate top ASIC RX BD!\r\n");
		return status;
	}

	status = XLlDma_BdRingAlloc(pRingAsicBot, totalNumBuffers, &pBotRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate bottom ASIC RX BD!\r\n");
		return status;
	}

	status = XLlDma_BdRingAlloc(pRingTenGig, totalNumBuffers*2, &pTXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate tengig TX BD!\r\n");
		return status;
	}

	// Pass back a pointer to the first TX BD
	*pFirstTxBd = pTXBd;

	// Snapshot pointer to first BDs
	XLlDma_Bd *pTopFirstBd = pTopRXBd;
	XLlDma_Bd *pBotFirstBd = pBotRXBd;
	XLlDma_Bd *pTenGigFirstBd = pTXBd;

	// Update address field in every BD
	int i=0;
	u32 currentOffset = 0;
	u32 topAsicBufferAddress = DDR2_BADDR;
	u32 botAsicBufferAddress = bankSize;

	// RX rings
	for (i=0; i<totalNumBuffers; i++)
	{

		// Configure DMA addresses
		XLlDma_BdSetBufAddr(*pTopRXBd, topAsicBufferAddress + currentOffset);
		XLlDma_BdSetBufAddr(*pBotRXBd, botAsicBufferAddress + currentOffset);
		currentOffset += bufferSz;

		// Set length / STS/CTRL fields
		// TODO: Store BD index in STS/CTRL field, application data (at present this is overwritten by ASIC/Spartan??)
		XLlDma_BdSetLength(*pTopRXBd, bufferSz);
		XLlDma_BdSetLength(*pBotRXBd, bufferSz);
		XLlDma_BdSetStsCtrl(*pTopRXBd, LL_STSCTRL_RX_BD);
		XLlDma_BdSetStsCtrl(*pBotRXBd, LL_STSCTRL_RX_BD);

		//printf("[INFO ] TopASIC BD %d: addr=0x%08x, len=0x%08x, sts=0x%08x\r\n", i, (unsigned)(topAsicBufferAddress + currentAddr), (unsigned)segmentSz, (unsigned)LL_STSCTRL_RX_BD);

		pTopRXBd = XLlDma_BdRingNext(pRingAsicTop, pTopRXBd);
		pBotRXBd = XLlDma_BdRingNext(pRingAsicBot, pBotRXBd);
	}

	// TX ring
	currentOffset = 0;
	for (i=0; i<totalNumBuffers; i++)
	{
		XLlDma_BdSetBufAddr(*pTenGigFirstBd, topAsicBufferAddress + currentOffset);
		XLlDma_BdSetLength(*pTenGigFirstBd, bufferSz);
		XLlDma_BdSetStsCtrl(*pTenGigFirstBd, LL_STSCTRL_TX_BD);
		pTenGigFirstBd = XLlDma_BdRingNext(pRingTenGig, pTenGigFirstBd);

		XLlDma_BdSetBufAddr(*pTenGigFirstBd, botAsicBufferAddress + currentOffset);
		XLlDma_BdSetLength(*pTenGigFirstBd, bufferSz);
		XLlDma_BdSetStsCtrl(*pTenGigFirstBd, LL_STSCTRL_TX_BD);
		pTenGigFirstBd = XLlDma_BdRingNext(pRingTenGig, pTenGigFirstBd);

		currentOffset += bufferSz;
	}


	// Commit all RX BDs to DMA engines
	status = XLlDma_BdRingToHw(pRingAsicTop, totalNumBuffers, pTopFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send top ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}
	status = XLlDma_BdRingToHw(pRingAsicBot, totalNumBuffers, pBotFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send bottom ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}

	// Start RX engines
	status = XLlDma_BdRingStart(pRingAsicTop);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Can't start top ASIC RX engine, no initialised BDs!\r\n");
		return status;
	}
	status = XLlDma_BdRingStart(pRingAsicBot);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Can't start top ASIC RX engine, no initialised BDs!\r\n");
		return status;
	}

	// Start TX engine
	status = XLlDma_BdRingStart(pRingTenGig);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Can't start 10GBe TX engine, no initialised BDs!\r\n");
		return status;
	}

	print("[INFO ] Committed BDs to HW and started DMA engines!\r\n");

	// Everything OK!
	return XST_SUCCESS;
}



/* Configures DMA engine for upstream configuration upload
 * @param pUploadBdRing pointer to BD ring for upload channel
 * @param pFirstConfigBd set by function to be first BD in TX ring
 * @param bufferAddr address at which configuration data is stored
 * @param bufferSz size of configuration data
 * @param bufferCnt number of configuration datas
 * @return XST_SUCCESS, or error code
 */
int configureBdsForUpload(XLlDma_BdRing *pUploadBdRing, XLlDma_Bd **pFirstConfigBd, u32 bufferAddr, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock)
{
	int status;

	// Check we won't exceed BD storage allocation
	if (bufferCnt > LL_MAX_CONFIG_BD)
	{
		printf("[ERROR] Configuration buffer count exceeds maximum BD storage! (%d>%d)\r\n", (int)bufferCnt, LL_MAX_CONFIG_BD);
		return XST_FAILURE;
	}

	u32 bdStartAddr = LL_BD_BADDR + LL_BD_SZ - (LL_MAX_CONFIG_BD * LL_DMA_ALIGNMENT);
	printf("[INFO ] Creating config BDs at 0x%08x (%d max.)\r\n", (unsigned)bdStartAddr, LL_MAX_CONFIG_BD);

	// Create BD ring & BD
	status = XLlDma_BdRingCreate(pUploadBdRing, bdStartAddr, bdStartAddr, LL_DMA_ALIGNMENT, bufferCnt);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Error creating config BDs!  Error code %d\r\n", status);
		return status;
	}

	XLlDma_Bd *pUploadBd;
	*pFirstConfigBd = pUploadBd;			// Pass back pointer to first BD
	status = XLlDma_BdRingAlloc(pUploadBdRing, bufferCnt, &pUploadBd);
	if (status!=XST_SUCCESS) {
		printf("[ERROR] Failed to allocate config BD!  Error code %d\r\n", status);
		return status;
	}

	// Configure BDs (We assume configurations are contiguous starting at bufferAddr)
	int i=0;
	u32 currentOffset = 0;
	for (i=0; i<bufferCnt; i++)
	{
		XLlDma_BdSetBufAddr(*pUploadBd, bufferAddr + currentOffset);
		XLlDma_BdSetLength(*pUploadBd, bufferSz);
		XLlDma_BdSetStsCtrl(*pUploadBd, LL_STSCTRL_TX_BD);
		currentOffset += bufferSz;
		pUploadBd = XLlDma_BdRingNext(pUploadBdRing, pUploadBd);
	}

	// Update status
	pStatusBlock->numConfigBds = bufferCnt;

	return XST_SUCCESS;
}



/* Verifies a buffer by checking the STS/CTRL field of the BD matches the value expected.
 * Frees BD ready for processing
 * @param pRing pointer to BD ring
 * @param pBd pointer to BD
 * @param buffType buffer type, either BD_RX or BD_TX
 * @return XST_SUCCESS, or error code
 */
int validateBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType)
{
	int status;
	u32 sts, validSts;

	switch(buffType)
	{
		case BD_RX:
			validSts = LL_STSCTRL_RX_OK;
			break;
		case BD_TX:
			validSts = LL_STSCTRL_TX_OK;
			break;
		default:
			// Invalid buffType
			return XST_FAILURE;
			break;
	}

	sts = XLlDma_BdGetStsCtrl(pBd);

	status = XLlDma_BdRingFree(pRing, 1, pBd);
	if (status!=XST_SUCCESS)
	{
		return status;
	}

	// TODO: Check and report if DMA_ERROR bit set! (What return code to use?)

	if (!(sts&0xFF000000)&validSts)
	{
		// NOTE: Even if code passes this check there can be no DMA transfer received :(
		printf("[ERROR] STS/CTRL field for bottom ASIC RX did not show successful completion!  STS/CTRL=0x%08x\r\n", (unsigned)sts);
		return XST_FAILURE;
	}

	return XST_SUCCESS;
}



/* Resets and re-allocates a buffer into the current BD ring
 * @param pRing pointer to BD ring
 * @param pBd pointer to BD
 * @param buffType buffer type, either BD_RX or BD_TX
 * @return XST_SUCCESS, or error code
 */
int recycleBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType)
{
	int status;
	u32 sts;

	// Re-alloc BDs into ring
	status = XLlDma_BdRingAlloc(pRing, 1, &pBd);
	if (status!=XST_SUCCESS)
	{
		return status;
	}

	// Reset STS/CTRL field on BDs
	switch(buffType)
	{
		case BD_RX:
			sts = LL_STSCTRL_RX_BD;
			break;
		case BD_TX:
			sts = LL_STSCTRL_TX_BD;
			break;
		default:
			// Invalid buffType
			return XST_FAILURE;
			break;
	}
	XLlDma_BdSetStsCtrl(*pBd, sts);

	// Return BDs to hardware control, if RX
	if (buffType==BD_RX)
	{
		status = XLlDma_BdRingToHw(pRing, 1, pBd);
		if (status!=XST_SUCCESS)
		{
			return status;
		}
	}

	return XST_SUCCESS;
}
