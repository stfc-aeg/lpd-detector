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
// ----------------------------------------------------------------------
// TODO: Implement ACQ_MODE_BURST
// TODO: Implement TIME_DMA
// TODO: Fix acqStatusBlock so when config for acquire with buffCnt==0 (put calculated buffCnt in here, also fix reconfig checking)
// TODO: Fix configure for acquire, respect config. BD storage area
// TODO: Improve conditional for BD config skipping
// TODO: Update state variable->state when config in process / complete
// TODO: Update state variables during event loop (read/writePtr)
// TODO: Fix main loop acquireRunning=0 loop (is off by factor of 2 at present)
// TODO: Graceful stop when pending events exist
// TODO: Refactor data counter variables and main event loop

#include <stdio.h>
#include "xmbox.h"
#include "xparameters.h"
#include "platform.h"
#include "xlldma.h"
#include "xil_testmem.h"
#include "xtime_l.h"

// Compile time switches
#define DEBUG_BD			1			// Outputs DMA BDs as received
//#define TIME_DMA		1				// Times DMA operations

// TODO: Remove this once DMA event loop verified OK!
#define VERBOSE_DEBUG		1

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
#define LL_DMA_ERROR				0x80000000						//! DMA error bit
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
// TODO: Change to enum?
#define ACQ_MODE_NORMAL				1
#define ACQ_MODE_RX_ONLY			2
#define ACQ_MODE_TX_ONLY			3
#define ACQ_MODE_UPLOAD				4
#define ACQ_MODE_BURST				5

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
	u32 state;			//! Current mode -> TODO: Define states!
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

//! Data structure for mailbox messages
// TODO: Store this in common header file!
typedef struct
{
	u32 cmd;
	u32 buffSz;
	u32 buffCnt;
	u32 param;
	u32 mode;
} mailMsg;


// FUNCTION PROTOTYPES
int configureBdsForAcquisition(XLlDma_BdRing *pBdRings[], XLlDma_Bd **pTxBd, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock);
int checkForMailboxMessage(XMbox *pMailBox, mailMsg *pMsg);
int configureBdsForUpload(XLlDma_BdRing *pUploadBdRing, XLlDma_Bd **pFirstConfigBd, u32 bufferAddr, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock);
unsigned short sendConfigRequestAckMessage(XMbox *pMailbox);
int validateBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType);
int recycleBuffer(XLlDma_BdRing *pBdRings, XLlDma_Bd *pBd, bufferType bType);

//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

int main()
{
    init_platform();

    int i;

	// Clear serial console
	for (i=0; i<100; i++) { print("\r\n"); }

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
    unsigned short ackOK = 0;

    // BD pointers
    XLlDma_Bd *pTenGigPreHW;
	XLlDma_Bd *pTenGigPostHW;
	XLlDma_Bd *pConfigBd;
	XLlDma_Bd *pTopAsicBd;		// Moved from main acquire loop
	XLlDma_Bd *pBotAsicBd;		// Moved from main acquire loop

	// Mailbox stuff
	mailMsg msg;
    mailMsg *pMsg = &msg;

    // State variables
    u32 lastMode = 0;					// Caches last mode used for acquire
	unsigned short acquireRunning = 0;	// Acquire control flag
	unsigned short doRx = 0;			// RX control flag for main loop
	unsigned short doTx = 0;			// TX control flag for main loop

	// Data counters
    unsigned short numUploadTx = 0;		// Number of configuration upload BDs
    u64 numTopAsicRxComplete = 0;		// Counts number of RXes from top ASIC
    u64 numBotAsicRxComplete = 0;		// Counts number of RXes from bottom ASIC
    u64 lastNumTopAsicRxComplete = 0;
    u64 lastNumBotAsicRxComplete = 0;
    u64 numRxPairsComplete = 0;			// Counter for number of completed & validated RX across both ASICs
    u64 numTxPairsSent = 0;				// Counter for TXes sent (but not verified as complete)
    unsigned short tempTxCounter = 0;	// Used to track how many single TXes (before they are grouped into pairs)
    u64 numTenGigTxComplete = 0;		// Counter for number of completed TX for 10GBe
    unsigned short numConfigBdsToProcess = 0;

#ifdef DEBUG_BD
    // For BD debugging
    u32 bdSts, bdLen, bdAddr;
#endif

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

    	print("[INFO ] Waiting for mailbox message...\r\n");

    	// Blocking read of mailbox message
    	XMbox_ReadBlocking(&mbox, (u32 *)pMsg, sizeof(mailMsg));
    	//printf("[INFO ] Got message!  cmd=0x%08x, buffSz=0x%08x, buffCnt=0x%08x, modeParam=%d, mode=%d\r\n",	(unsigned)pMsg->cmd, (unsigned)pMsg->buffSz, (unsigned)pMsg->buffCnt, (unsigned)pMsg->param, (unsigned)pMsg->mode );

    	// Send ACK
    	ackOK = sendConfigRequestAckMessage(&mbox);
    	if (!ackOK)
    	{
    		print("[ERROR] Could not send config ACK to PPC1!\r\n");
    	}

    	switch(pMsg->cmd)
    	{

    	case CMD_ACQ_CONFIG:
    		// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    		// Ensure DMA engines are in a stable state, and stopped!
			XLlDma_Reset(&dmaAsicTop);
			XLlDma_Reset(&dmaAsicBot);
			XLlDma_Reset(&dmaTenGig);
			XLlDma_Reset(&dmaPixMem);

    	    // Cache last mode
    		lastMode = pMsg->mode;

    		switch(pMsg->mode)
    		{
    		case ACQ_MODE_NORMAL:
    			doTx = 1;
    			doRx = 1;
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			break;
    		case ACQ_MODE_RX_ONLY:
    			doTx = 0;
    			doRx = 1;
    			print("[INFO ] Using ACQ_MODE_RX_ONLY.\r\n");
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			break;
    		case ACQ_MODE_TX_ONLY:
    			doTx = 1;
    			doRx = 0;
    			print("[INFO ] Using ACQ_MODE_TX_ONLY.\r\n");
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			break;
    		case ACQ_MODE_UPLOAD:
    			// TODO: Refactor numAcq to something more generic (ACQ_MODE_NORMAL->numAcq, ACQ_MODE_UPLOAD->configStartAddr) --> modeParam?
    			status = configureBdsForUpload(pBdRings[BD_RING_UPLOAD], &pConfigBd, pMsg->param, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			break;
    		case ACQ_MODE_BURST:
    			// Initially set to RX only then main event will switch to TX
    			doTx = 0;
    			doRx = 1;
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			break;
    		default:
    			printf("[ERROR] Unknown ACQ mode %d - Ignoring.\r\n", (int)pMsg->mode);
    			break;
    		} // END switch(pMsg->mode)

    		if (status==XST_SUCCESS)
    		{
    			// All OK, update status struct with buffer details
    			if (pMsg->mode != ACQ_MODE_UPLOAD)
    			{
    				pStatusBlock->bufferSize = pMsg->buffSz;
    				pStatusBlock->bufferCnt = pMsg->buffCnt;
    				pStatusBlock->numAcq = pMsg->param;
    				pStatusBlock->state = pMsg->mode;
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

			printf("[INFO ] Starting acquisition, mode %d!\r\n", (int)lastMode);
			switch(lastMode)
			{
			case ACQ_MODE_NORMAL:
			case ACQ_MODE_BURST:
			case ACQ_MODE_RX_ONLY:
			case ACQ_MODE_TX_ONLY:
				// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
				printf("[INFO ] Entering acquire DMA event loop\r\n");

				// Reset BRAM struct
				// TODO: Update readPtr / writePtr in event loop! (store index in BD?)
			    pStatusBlock->readPtr = 0;
			    pStatusBlock->writePtr = 0;
			    pStatusBlock->totalRecv = 0;
			    pStatusBlock->totalSent = 0;
			    pStatusBlock->totalErrors = 0;

	    		// Reset counters
	    	    numTopAsicRxComplete = 0;
	    	    numBotAsicRxComplete = 0;
	    	    numRxPairsComplete = 0;
	    	    lastNumTopAsicRxComplete = 0;
	    	    lastNumBotAsicRxComplete = 0;
	    	    numTxPairsSent = 0;
	    	    numTenGigTxComplete = 0;

				int numBDFromTopAsic = 0;
				int numBDFromBotAsic = 0;

				int numBDFromTenGig = 0;

	    	    pTenGigPostHW = pTenGigPreHW;		// PreHW is first BD in TX ring

	    	    // Quick fix for doTx
	    	    if (lastMode == ACQ_MODE_TX_ONLY)
	    	    {
	    	    	printf("[DEBUG] ACQ_MODE_TX_ONLY detected, setting TX count to %d\r\n", (int)pStatusBlock->numAcq);
	    	    	numRxPairsComplete = pStatusBlock->numAcq;
	    	    }

	    	    acquireRunning = 1;

				while (acquireRunning)
				{

					// Process RX
					if (doRx)
					{

						// Pull down any completed RX BDs
						numBDFromTopAsic = XLlDma_BdRingFromHw(pBdRings[BD_RING_TOP_ASIC], XLLDMA_ALL_BDS, &pTopAsicBd);
						numBDFromBotAsic = XLlDma_BdRingFromHw(pBdRings[BD_RING_BOT_ASIC], XLLDMA_ALL_BDS, &pBotAsicBd);

						// DEBUGGING
#ifdef VERBOSE_DEBUG
						if (numBDFromBotAsic!=0 || numBDFromTopAsic!=0)
						{
							print("[-----]\r\n");
						}
#endif

						// **************************************************************************************
						// Top ASIC RX
						// **************************************************************************************
						if(numBDFromTopAsic>0)
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] Got %d RX from top ASIC\r\n", numBDFromTopAsic);
#endif

							// Validate and recycle BDs
							for (i=0; i<numBDFromTopAsic; i++)
							{
								status = validateBuffer(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to validate buffer index %llu from top ASIC!\r\n", numTopAsicRxComplete+i);
									return 0;
								}

								status = recycleBuffer(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to recycle buffer index %llu from top ASIC!\r\n", numTopAsicRxComplete+i);
									return 0;
								}
#ifdef DEBUG_BD
								bdSts = XLlDma_BdGetStsCtrl(pTopAsicBd);
								bdLen = XLlDma_BdGetLength(pTopAsicBd);
								bdAddr = XLlDma_BdGetBufAddr(pTopAsicBd);
								printf("[DEBUG] TopASIC RX: sts=0x%08x, len=0x%08x, addr=0x%08x\r\n", (unsigned)bdSts, (unsigned)bdLen, (unsigned)bdAddr);
#endif
								pTopAsicBd = XLlDma_BdRingNext(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd);
							}

							numTopAsicRxComplete += numBDFromTopAsic;
						}



						// **************************************************************************************
						// Bottom ASIC RX
						// **************************************************************************************
						if(numBDFromBotAsic>0)
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] Got %d RX from bottom ASIC\r\n", numBDFromBotAsic);
#endif

							// Validate and recycle BDs
							for (i=0; i<numBDFromBotAsic; i++)
							{

								status = validateBuffer(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to validate buffer index %llu from bottom ASIC!\r\n", numBotAsicRxComplete+i);
									return 0;
								}

								status = recycleBuffer(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to recycle buffer index %llu from bottom ASIC!\r\n", numBotAsicRxComplete+i);
									return 0;
								}
#ifdef DEBUG_BD
								bdSts = XLlDma_BdGetStsCtrl(pBotAsicBd);
								bdLen = XLlDma_BdGetLength(pBotAsicBd);
								bdAddr = XLlDma_BdGetBufAddr(pBotAsicBd);
								printf("[DEBUG] BotASIC RX: sts=0x%08x, len=0x%08x, addr=0x%08x\r\n", (unsigned)bdSts, (unsigned)bdLen, (unsigned)bdAddr);
#endif
								pBotAsicBd = XLlDma_BdRingNext(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd);
							}

							numBotAsicRxComplete = numBDFromBotAsic;
						}


						// **************************************************************************************
						// Update BD counters and pointers
						// **************************************************************************************
						// If we've received anything since last time
						if ( (numBotAsicRxComplete!=lastNumBotAsicRxComplete) || (numTopAsicRxComplete!=lastNumTopAsicRxComplete) )
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] Got RX this loop, calculating num completed RX pairs...\r\n");
							printf("[DEBUG] Total TopASIC RX = %llu\r\n", numTopAsicRxComplete);
							printf("[DEBUG] Total BotASIC RX = %llu\r\n", numBotAsicRxComplete);
#endif

							// Determine how many completed pairs of RX we have and prepare them for TX
							if (numBotAsicRxComplete == numTopAsicRxComplete)
							{
								numRxPairsComplete += numBotAsicRxComplete;
								numBotAsicRxComplete = 0;
								numTopAsicRxComplete = 0;
							}
							else if (numBotAsicRxComplete < numTopAsicRxComplete)
							{
								numRxPairsComplete += numBotAsicRxComplete;
								numTopAsicRxComplete -= numBotAsicRxComplete;
								numBotAsicRxComplete = 0;
							}
							else // numBot>numTop
							{
								numRxPairsComplete += numTopAsicRxComplete;
								numBotAsicRxComplete -= numTopAsicRxComplete;
								numTopAsicRxComplete = 0;
							}

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] -- OK --\r\n");
							printf("[DEBUG] numRxPairsComplete = %llu\r\n", numRxPairsComplete);
							printf("[DEBUG] NOW TopASIC RX = %llu\r\n", numTopAsicRxComplete);
							printf("[DEBUG] NOW BotASIC RX = %llu\r\n", numBotAsicRxComplete);
#endif

							pStatusBlock->totalRecv += numRxPairsComplete;

						}

						// Update loop variables
						lastNumBotAsicRxComplete = numBotAsicRxComplete;
						lastNumTopAsicRxComplete = numTopAsicRxComplete;

					} // END if(doRx)



					// Process TX
					// TODO: Fix logic if doTx & !doRx
					if (doTx)
					{

						// **************************************************************************************
						// Dispatch any waiting TX BD pairs
						// **************************************************************************************
						if (numRxPairsComplete>0)
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] %llu TX pairs ready to send\r\n", numRxPairsComplete);
#endif

							status = XLlDma_BdRingToHw(pBdRings[BD_RING_TENGIG], numRxPairsComplete*2, pTenGigPreHW);

							numTxPairsSent += numRxPairsComplete;

							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Could not commit TX BD pair(s)!  Error code %d\r\n", status);
								return 0;
							}
							else
							{
								// Sent all to HW, none left!
#ifdef VERBOSE_DEBUG
								printf("[INFO ] Committed %llu BD pairs to TX!\r\n", numRxPairsComplete);
#endif

								// Advance our BD pointer
								for (i=0; i<numRxPairsComplete*2; i++)
								{
									pTenGigPreHW = XLlDma_BdRingNext(pBdRings[BD_RING_TENGIG], pTenGigPreHW);
								}
								numRxPairsComplete = 0;
							}
						}

						// **************************************************************************************
						// If we have any uncompleted TX, process them
						// **************************************************************************************
						if (numTxPairsSent>0)
						{

							numBDFromTenGig = XLlDma_BdRingFromHw(pBdRings[BD_RING_TENGIG], XLLDMA_ALL_BDS, &pTenGigPostHW);

							if (numBDFromTenGig>0)
							{
#ifdef VERBOSE_DEBUG
								printf("[DEBUG] Got %d TX BD back to check...\r\n", numBDFromTenGig);
#endif

								for (i=0; i<numBDFromTenGig; i++)
								{
									// Validate TX response
									status = validateBuffer(pBdRings[BD_RING_TENGIG], pTenGigPostHW, BD_TX);
									if (status!=XST_SUCCESS)
									{
										printf("[ERROR] Error validating TX BD %d, error code %d\r\n", i, status);
										return 0;
									}

									// Re-allocate BD into active ring
									status = recycleBuffer(pBdRings[BD_RING_TENGIG], pTenGigPostHW, BD_TX);
									if (status!=XST_SUCCESS)
									{
										printf("[ERROR] Error on recycleBuffer for TX BD %d, error code %d\r\n", i, status);
										return 0;
									}
#ifdef DEBUG_BD
									bdSts = XLlDma_BdGetStsCtrl(pTenGigPostHW);
									bdLen = XLlDma_BdGetLength(pTenGigPostHW);
									bdAddr = XLlDma_BdGetBufAddr(pTenGigPostHW);
									printf("[DEBUG] 10GBe TX: sts=0x%08x, len=0x%08x, addr=0x%08x\r\n", (unsigned)bdSts, (unsigned)bdLen, (unsigned)bdAddr);
#endif
									// Move to next BD in set
									pTenGigPostHW = XLlDma_BdRingNext(pBdRings[BD_RING_TENGIG], pTenGigPostHW);
								}

								numTenGigTxComplete += numBDFromTenGig;
							} // END if (numBDFromTenGig>0)

							// Calculate how many pairs processed, update counters
							tempTxCounter += numBDFromTenGig;
							while (tempTxCounter>1)
							{
								tempTxCounter -= 2;
								numTxPairsSent--;
								pStatusBlock->totalSent++;
#ifdef VERBOSE_DEBUG
								printf("[DEBUG] Pair TX validated, tempTx=%d, numTxpairsSent=%llu\r\n", (int)tempTxCounter, numTxPairsSent);
#endif
							}

						} // END if (numTxPairsSent>0)

					} // END if(doTx)



					// **************************************************************************************
					// Check if we have received the expected number of events
					// **************************************************************************************
					if (pStatusBlock->numAcq == (pStatusBlock->totalRecv*2) && pStatusBlock->numAcq!=0)
					{
						if (lastMode==ACQ_MODE_BURST)
						{
							// If in burst mode, switch from RX to TX
							doRx = 0;
							doTx = 1;
							numRxPairsComplete = pStatusBlock->numAcq;
							printf("[DEBUG] Got %d events and using ACQ_MODE_BURST, disabling RX and enabling TX (%d pairs)!\r\n", (int)pStatusBlock->numAcq, (int)numRxPairsComplete);
						}
						else
						{
							// Any other mode, we're finished so stop acquiring
							printf("[DEBUG] Got %d events, stopping...\r\n", (int)pStatusBlock->numAcq);
							acquireRunning = 0;
						}
					}



					// **************************************************************************************
					// Check for mailbox messages
					// **************************************************************************************
					if (checkForMailboxMessage(&mbox, pMsg))
					{
						switch (pMsg->cmd)
						{
						case CMD_ACQ_STOP:
							// TODO: Gracefully handle outstanding DMA operations when stop is received

							if (numRxPairsComplete==0 && numTopAsicRxComplete==numBotAsicRxComplete)
							{
								print("[INFO ] Got stop acquire message, exiting acquire loop\r\n");
								acquireRunning = 0;
							}
							else
							{
								printf("[ERROR] Got stop acquire message but there are pending events! (rxTop=%llu, rxBot=%llu, tx=%llu)\r\n", numTopAsicRxComplete, numBotAsicRxComplete, numRxPairsComplete);
								printf("[DEBUG] Stopping anyway...\r\n");
								acquireRunning = 0;
							}

							break;

						default:
							print("[ERROR] Unexpected command in acquire loop, ignoring for now\r\n");
							break;
						}
					}

				} // END while(acquireRunning)
				// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
				break;

				// -------------------------------------------------------------------------------------

			case ACQ_MODE_UPLOAD:

				if (pStatusBlock->numConfigBds > 0)
				{

					printf("[INFO ] Sending %d configuration upload TXes...\r\n", (int)pStatusBlock->numConfigBds);

					// Send TX BDs to hardware control
					status = XLlDma_BdRingToHw(pBdRings[BD_RING_UPLOAD], pStatusBlock->numConfigBds, pConfigBd);
					if (status!=XST_SUCCESS)
					{
						printf("[ERROR] Could not commit %d upload BD(s) to hardware control!  Error code %d\r\n", (int)pStatusBlock->numConfigBds, status);
					}

					numConfigBdsToProcess = pStatusBlock->numConfigBds;
					while (numConfigBdsToProcess>0)
					{

						numUploadTx = XLlDma_BdRingFromHw(pBdRings[BD_RING_UPLOAD], pStatusBlock->numConfigBds, &pConfigBd);
						for(i=0; i<numUploadTx; i++)
						{
							status = validateBuffer(pBdRings[BD_RING_UPLOAD], pConfigBd, BD_TX);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Error validating upload TX BD %d, error code %d\r\n", i, status);
							}
							status = recycleBuffer(pBdRings[BD_RING_UPLOAD], pConfigBd, BD_TX);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Error on recycleBuffer for upload TX, error code %d\r\n", status);
							}
							pConfigBd = XLlDma_BdRingNext(pBdRings[BD_RING_UPLOAD], pConfigBd);
						}
						numConfigBdsToProcess -= numUploadTx;

					}

					printf("[INFO ] Verified %d config. upload BD(s) OK!\r\n", (int)pStatusBlock->numConfigBds);

					// Subsequent calls to start configure will fail because we moved pConfigBd, so this prevents a config operation running again
					pStatusBlock->numConfigBds = 0;

				}
				else
				{
					print("[INFO ] Received CMD_ACQ_START for ACQ_MODE_UPLOAD, but no configured upload BDs (or already uploaded)!  Ignoring...\r\n");
				}

				break;
			} // END switch(lastMode)
			break;
		case CMD_ACQ_STOP:
			// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
			printf("[INFO ] Not doing anything with stop acquire command.\r\n");
			// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
			break;

		default:
			// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
			printf("[ERROR] Unrecognised mailbox command %d\r\n", (unsigned)pMsg->cmd);
			// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
			break;

    	} // END switch(pMsg->cmd)

    }

    // Should never execute!
    print("[INFO ] Process terminating...\r\n");
    cleanup_platform();
    return 0;

}



/*
 * Generic DMA setup function, accepts segment size (size of data to RX from I/O FPGA),
 * and segment count (to limit the number of BDs created for debugging / #-frame mode)
 * @param pBdRings pointer to array of BD rings
 * @param pFirstTxBd set by function to be first BD in TX ring
 * @param bufferSz Size of data buffer to RX from I/O FPGA
 * @param bufferCnt Number of buffers to allocate, set to 0 for allocation of maximum BDs
 * @param pStatusBlock pointer to status struct, updated by function
 * @return XST_SUCCESS if OK, otherwise an XST_xxx error code
 *
 */
int configureBdsForAcquisition(XLlDma_BdRing *pBdRings[], XLlDma_Bd **pFirstTxBd, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock)
{

	// TODO: Respect the reserved BD config. area!

	unsigned status;
	XLlDma_BdRing *pRingTenGig = pBdRings[BD_RING_TENGIG];
	XLlDma_BdRing *pRingAsicTop = pBdRings[BD_RING_TOP_ASIC];
	XLlDma_BdRing *pRingAsicBot = pBdRings[BD_RING_BOT_ASIC];

	// Check if we can re-use BDs to save time configuring them
	if ( bufferSz==pStatusBlock->bufferSize && (bufferCnt<=pStatusBlock->bufferCnt) )			// Size must match, count can be equal or less than
	{
		printf("[INFO ] Parameters for buffer size and count match last configuration, reusing existing BDs!\r\n");

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

		return XST_SUCCESS;
	}

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

	print("[INFO ] Starting BD configuration...\r\n");

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

		// Bottom ASIC sent first, then top ASIC
		XLlDma_BdSetBufAddr(*pTenGigFirstBd, botAsicBufferAddress + currentOffset);
		XLlDma_BdSetLength(*pTenGigFirstBd, bufferSz);
		XLlDma_BdSetStsCtrl(*pTenGigFirstBd, LL_STSCTRL_TX_BD);
		pTenGigFirstBd = XLlDma_BdRingNext(pRingTenGig, pTenGigFirstBd);

		XLlDma_BdSetBufAddr(*pTenGigFirstBd, topAsicBufferAddress + currentOffset);
		XLlDma_BdSetLength(*pTenGigFirstBd, bufferSz);
		XLlDma_BdSetStsCtrl(*pTenGigFirstBd, LL_STSCTRL_TX_BD);
		pTenGigFirstBd = XLlDma_BdRingNext(pRingTenGig, pTenGigFirstBd);

		currentOffset += bufferSz;
	}

	print("[INFO ] Completed BD configuration!\r\n");

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
	printf("[INFO ] Creating %d config BDs at 0x%08x (%d max.)\r\n", (int)bufferCnt, (unsigned)bdStartAddr, LL_MAX_CONFIG_BD);

	// Create BD ring & BD
	status = XLlDma_BdRingCreate(pUploadBdRing, bdStartAddr, bdStartAddr, LL_DMA_ALIGNMENT, bufferCnt);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Error creating config BDs!  Error code %d\r\n", status);
		return status;
	}

	XLlDma_Bd *pUploadBd;
	status = XLlDma_BdRingAlloc(pUploadBdRing, bufferCnt, &pUploadBd);
	if (status!=XST_SUCCESS) {
		printf("[ERROR] Failed to allocate config BD!  Error code %d\r\n", status);
		return status;
	}
	*pFirstConfigBd = pUploadBd;			// Pass back pointer to first BD

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

	// Start TX engine
	status = XLlDma_BdRingStart(pUploadBdRing);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Can't start config TX engine, no initialised BDs!\r\n");
		return status;
	}

	// Generate test pattern at a fixed memory address
	u32 testPatternAddr = 0x30000000;
	u32 testPatternLen = 0x18000;		// In bytes!
	u32 testPatternPat = 0xAEAEAEAE;
	printf("[INFO ] Generating test pattern 0x%08x at 0x%08x, 0x%08x bytes in length.\r\n", (unsigned)testPatternPat, (unsigned)testPatternAddr, (unsigned)testPatternLen);
	status = Xil_TestMem32((u32*)testPatternAddr, testPatternLen/4, testPatternPat, XIL_TESTMEM_FIXEDPATTERN);

	return XST_SUCCESS;
}



/* Checks for a mailbox message (non-blocking)
 * @param pMailBox pointer to XMbox
 * @param pMsg pointer to mailMsg buffer to receive to
 * @return 1 on success, 0 otherwise
 */
int checkForMailboxMessage(XMbox *pMailBox, mailMsg *pMsg)
{
	u32 bytesRecvd = 0;

	XMbox_Read(pMailBox, (u32*)pMsg, sizeof(mailMsg), &bytesRecvd);
	if (bytesRecvd == sizeof(mailMsg)) {
		return 1;
	}
	else
	{
		return 0;
	}
}



/* Sends an ack mailbox message to PPC2 to tell it we're
 * starting BD configuration for acquisition.
 * @param pMailbox pointer to XMbox
 * @return 1 on success, 0 otherwise
 */
unsigned short sendConfigRequestAckMessage(XMbox *pMailbox)
{
	int status;
	u32 sentBytes;
	u32 buf = 0xA5A5FACE;		// TODO: Make constant, put in header
	status = XMbox_Write(pMailbox, &buf, 4, &sentBytes);
	if (status==XST_SUCCESS)
	{
		return 1;
	}
	else
	{
		return 0;
	}
}



/* Verifies a buffer by checking the STS/CTRL field of the BD matches the value expected.
 * @param pRing pointer to BD ring
 * @param pBd pointer to BD
 * @param buffType buffer type, either BD_RX or BD_TX
 * @return XST_SUCCESS, or XST_DMA_ERROR if an error was flagged
 */
int validateBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType)
{
	u32 sts, validSts;

#ifdef DEBUG_BD
    u32 len, addr;
#endif

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

#ifdef DEBUG_BD
	len =  XLlDma_BdGetLength(pBd);
	addr = XLlDma_BdGetBufAddr(pBd);
#endif

	// Check DMA_ERROR bit
	if ((sts&0xFF000000)&LL_DMA_ERROR)
	{
		print("[ERROR] DMA transfer signalled error!\r\n");
#ifdef DEBUG_BD
		printf("[ERROR] BD sts=%08x, len=%08x, addr=%08x\r\n", (unsigned)sts, (unsigned)len, (unsigned)addr);
#endif
		return XST_DMA_ERROR;
	}

	// Verify STS/CTRL matches what we expect to see
	if (!(sts&0xFF000000)&validSts)
	{
		// NOTE: Even if code passes this check there can be no DMA transfer received :(
		printf("[ERROR] STS/CTRL field for bottom ASIC RX did not show successful completion!  STS/CTRL=0x%08x\r\n", (unsigned)sts);
		return XST_FAILURE;
	}

	return XST_SUCCESS;
}



/* Resets, frees and re-allocates a buffer into the current BD ring
 * @param pRing pointer to BD ring
 * @param pBd pointer to BD
 * @param buffType buffer type, either BD_RX or BD_TX
 * @return XST_SUCCESS, or error code
 */
int recycleBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType)
{
	int status;
	u32 sts;

	// Free BD
	status = XLlDma_BdRingFree(pRing, 1, pBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] recycleBuffer:Free failed\r\n");
		return status;
	}

	// Re-alloc BDs into ring
	status = XLlDma_BdRingAlloc(pRing, 1, &pBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] recycleBuffer:Alloc failed\r\n");
		return status;
	}

	// Reset STS/CTRL field
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
			printf("[ERROR] recycleBuffer:ToHw failed\r\n");
			return status;
		}
	}

	return XST_SUCCESS;
}



/* Starts the provided engines
 * @return XST_SUCCESS, or error code
 */
int startDmaEngines(void)
{
	// TODO: Implement!
	return XST_FAILURE;
}
