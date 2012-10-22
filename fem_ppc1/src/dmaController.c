/*
 * dmaController.c
 * ---------------
 *
 * FEM PPC1 main application (for use with Xilinx standalone BSP)
 *
 * Responsible for allocating memory buffers and controlling the PPC DMA engines to arbitrate
 * transfers from ASIC(s) -> DDR2 -> 10GBe, as well as uploading configuration data from DDR2 -> ASIC(s).
 *
 * Controlled by PPC2 via Xilinx Mailbox commands.
 */

#include <stdio.h>
#include "xmbox.h"
#include "xparameters.h"
#include "platform.h"
#include "xlldma.h"
#include "xil_testmem.h"
#include "xtime_l.h"

// Compile time switches
//#define VERBOSE_DEBUG			1			//! Verbose output during acquire loop
//#define DEBUG_BD				1			//! Outputs DMA BDs as received

// DMA timing tuning - these specify how many RX or TX descriptors are requested / sent per loop.
#define LL_DMA_RX_NUM_BD_PER_LOOP		1			//! Valid values are 1...XLLDMA_ALL_BDS
#define LL_DMA_TX_NUM_BD_PER_LOOP		2			//! Valid values are 2...XLLDMA_ALL_BDS

#define MAX_STOP_ATTEMPTS				500			//! Number of main event loops we'll wait for TX DMA operations to clear

#define DDR2_BADDR					XPAR_DDR2_SDRAM_MEM_BASEADDR	//! DDR2 base address
#define DDR2_SZ						0x40000000						//! DDR2 size (1GB)
#define BRAM_BADDR					XPAR_SHARED_BRAM_IF_CNTLR_PPC_1_BASEADDR
#define LL_BD_BADDR					0x90280000						//! Bass address for BDs
#define LL_BD_SZ					0x00180000						//! Size of BD memory region
#define LL_MAX_CONFIG_BD			64								//! Maximum number of upstream configuration BDs

// ----------- CONSTANTS -----------
#define LL_DMA_BASE_ASIC_BOT		0x80							//! DCR offset for DMA0 (RX from bottom ASIC) (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_UPLOAD			0x98							//! DCR offset for DMA1 (TX to ASIC configuration) (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_ASIC_TOP		0xB0							//! DCR offset for DMA2 (RX from top ASIC) (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_TENGIG			0xC8							//! DCR offset for DMA3 (TX to 10GBE) (See Xilinx UG200, chapter 13)
#define LL_DMA_ALIGNMENT			XLLDMA_BD_MINIMUM_ALIGNMENT		//! BD Alignment, set to minimum
#define LL_STSCTRL_RX_OK			0x1D000000						//! STS/CTRL field in BD should be 0x1D when successfully RX (COMPLETE | SOP | EOP)
#define LL_STSCTRL_TX_OK			0x10000000						//! STS/CTRL field in BD should be 0x10 when successfully TX (COMPLETE)
#define LL_STSCTRL_RX_BD			0x0															//! STS/CTRL field for an RX BD
#define LL_STSCTRL_TX_BD			XLLDMA_BD_STSCTRL_SOP_MASK | XLLDMA_BD_STSCTRL_EOP_MASK		//! STS/CTRL field for an TX BD (SOP | EOP)
#define LL_DMA_ERROR				0x80000000						//! DMA error bit

// Ring indexes
#define BD_RING_TOP_ASIC			0								//! Top I/O Spartan / ASIC connection
#define BD_RING_BOT_ASIC			1								//! Bottom I/O Spartan / ASIC connection
#define BD_RING_TENGIG				2								//! 10GBe
#define BD_RING_UPLOAD				3								//! Upstream configuration

// TODO: Move to common protocol.h
enum dmaModes {
	ACQ_MODE_NORMAL = 1,					// Sustained data taking mode (RX-TX cycle)
	ACQ_MODE_BURST,							// Burst mode, RX only to fill DDR2 then switch to TX to flush to 10GBe
	ACQ_MODE_RX_ONLY,						// Only RX (Debugging only)
	ACQ_MODE_TX_ONLY,						// Only TX (Debugging only)
	ACQ_MODE_UPLOAD							// Configuration upload
};

// TODO: Move to common protocol.h
enum dmaCmds {
	CMD_ACQ_CONFIG = 1,
	CMD_ACQ_START,
	CMD_ACQ_STOP,
	CMD_ACQ_STATUS
};

//! Buffer type identifier for BDs (used by validateBuffer / recycleBuffer)
typedef enum
{
	BD_RX,
	BD_TX
} bufferType;

//! Acquisition state
typedef enum
{
	STATE_IDLE,			//! Idle, waiting for mailbox command
	STATE_CFG_BSY,		//! Configuring DMA engines (BDs), unable to use DMA at this time
	STATE_ACQ_NORMAL,	//! DMA engines normal operation (data taking)
	STATE_ACQ_UPLOAD,	//! DMA engines sending upstream configuration
	STATE_ACQ_STOPPING	//! Waiting for all events to process on RX/TX after a stop has been issued
} acqState;

//! Data structure to store in shared BRAM for status information
// TODO: Move to common include
typedef struct
{
	u32 state;			//! Acquisition state
	u32 bufferCnt;		//! Number of buffers allocated
	u32 bufferSize;		//! Size of buffers
	u32 bufferDirty;	//! If non-zero a problem occurred last run and the buffers / engines need to be reconfigured
	u32 readPtr;		//! Read pointer
	u32 writePtr;		//! Write pointer
	u32 numAcq;			//! Number of acquisitions in this run
	u32 numConfigBds;	//! Number of configuration BDs set
	u32 totalRecvTop;	//! Total number of BDs received from top ASIC
	u32 totalRecvBot;	//! Total number of BDs received from bot ASIC
	u32 totalSent;		//! Total number of BDs sent to 10GBe block
	u32 totalErrors;	//! Total number of DMA errors (do we need to track for each channel?)
} acqStatusBlock;

//! Data structure for mailbox messages
// TODO: Move to common include
typedef struct
{
	u32 cmd;
	u32 buffSz;
	u32 buffCnt;
	u32 param;
	u32 mode;
	u32 bdCoalesceCnt;
} mailMsg;

// ------- DCR Debugging -----------
typedef enum
{
	DCR_TOP_ASIC_RX,
	DCR_BOT_ASIC_RX,
	DCR_GBE_TX,
	DCR_UPLOAD_TX
} dcrRegistersBase;

typedef enum
{
	DCR_CHANNEL_RX,
	DCR_CHANNEL_TX
} dcrRegistersChannelType;

//! Storage for DMA DCR registers
// Note this can be for either an RX or TX channel!
typedef struct
{
	dcrRegistersChannelType type;
	u32 nxtDescPtr;
	u32 curBufAddr;
	u32 curBufLength;
	u32 curDescPtr;
	u32 tailDescPtr;
	u32 channelCtrl;
	u32 irqReg;
	u32 statusReg;
	u32 controlReg;
} dcrRegisters;
// ------- DCR Debugging -----------


// FUNCTION PROTOTYPES
int configureBdsForAcquisition(XLlDma_BdRing *pBdRings[], XLlDma_Bd **pTxBd, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock);
int configureBdsForUpload(XLlDma_BdRing *pUploadBdRing, XLlDma_Bd **pFirstConfigBd, u32 bufferAddr, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock);
int startAcquireEngines(XLlDma_BdRing* pRingAsicTop, XLlDma_BdRing* pRingAsicBot, XLlDma_BdRing* pRingTenGig);

// TODO: Refactor to sendFemMailMsg(), recvFemMailMsg() - make common?
int checkForMailboxMessage(XMbox *pMailBox, mailMsg *pMsg);
unsigned short sendAcquireAckMessage(XMbox *pMailbox, u32 state);

int checkRingConsistency(XLlDma_Bd *pTop, XLlDma_Bd *pBot, XLlDma_Bd *pTx);

int validateBuffer(XLlDma_BdRing *pRing, XLlDma_Bd *pBd, bufferType buffType);
int recycleBuffer(XLlDma_BdRing *pBdRings, XLlDma_Bd *pBd, bufferType bType);

int readDcrs(dcrRegistersBase type, dcrRegisters *pReg);
void printDcr(dcrRegisters *pReg);

//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

int main()
{
    init_platform();

    int i;

	// Clear serial console
	for (i=0; i<100; i++) { print("\r\n"); }

	// Dump a little diagnostic info
    print( "[INFO ] FEM PPC1 DMA Controller starting up...\r\n");
    print( "[INFO ] ------------------------------------------------\r\n");
    printf("[INFO ] Total DDR2 space for buffers:         0x%08x\r\n", DDR2_SZ);
    printf("[INFO ] Total SRAM space for BDs:             0x%08x\r\n", LL_BD_SZ);
    printf("[INFO ] Maximum number of readout BDs:        %d\r\n", ((LL_BD_SZ/LL_DMA_ALIGNMENT)/4)-LL_MAX_CONFIG_BD);
    printf("[INFO ] Maximum number of config upload BDs:  %d\r\n", LL_MAX_CONFIG_BD);
    print( "[INFO ] ------------------------------------------------\r\n");

    int status;

    // BD pointers
    XLlDma_Bd *pTenGigPreHW;
	XLlDma_Bd *pTenGigPostHW;
	XLlDma_Bd *pConfigBd;
	XLlDma_Bd *pTopAsicBd;
	XLlDma_Bd *pBotAsicBd;

	// Mailbox
	mailMsg msg;
    mailMsg *pMsg = &msg;

    // DCR debugging
    /*
    dcrRegisters dcrTopAsic;
    dcrRegisters dcrBotAsic;
    dcrRegisters dcrGbe;
    dcrRegisters dcrUpload;
	*/

    // Coalescing count
    int numRxBDPerLoop;// = LL_DMA_RX_NUM_BD_PER_LOOP;
    int numTxBDPerLoop;// = LL_DMA_TX_NUM_BD_PER_LOOP;

    // State variables
    u32 lastMode = 0;					// Caches last mode used for acquire
	unsigned short acquireRunning = 0;	// Acquire control flag
	unsigned short doRx = 0;			// RX control flag for main loop
	unsigned short doTx = 0;			// TX control flag for main loop
    unsigned short ackOK = 0;
    unsigned short sendStopAck = 0;

	// Data counters
    unsigned short numUploadTx = 0;		// Number of configuration upload BDs
    u64 numTopAsicRx = 0;				// Number of RXes from top ASIC in current loop
    u64 numBotAsicRx = 0;				// Number of RXes from bottom ASIC in current loop
    u64 lastNumTopAsicRx = 0;			// Number of RXes from top ASIC, last loop
    u64 lastNumBotAsicRx = 0;			// Number of RXes from top ASIC, last loop
    u64 numRxPairsToSend = 0;			// Number of completed & validated RX across both ASICs
    u64 numTxPairsSent = 0;				// Number of TXes sent but not verified as complete
    unsigned short numTxBds = 0;		// Number of TX BDs (before they're grouped into pairs)
    u64 numTenGigTxComplete = 0;		// Counter for number of completed TX for 10GBe
    unsigned short numConfigBdsToProcess = 0;

    u32 numStopAttempts = 0;

#ifdef DEBUG_BD
    // For BD debugging
    u32 bdSts, bdLen, bdAddr;
#endif

    // Initialise BRAM status
    acqStatusBlock* pStatusBlock = (acqStatusBlock*)BRAM_BADDR;
    pStatusBlock->state =			STATE_IDLE;
    pStatusBlock->bufferCnt =		0;
    pStatusBlock->bufferSize =		0;
    pStatusBlock->numAcq =			0;
    pStatusBlock->numConfigBds =	0;
    pStatusBlock->readPtr =			0;
    pStatusBlock->writePtr =		0;
    pStatusBlock->totalRecvTop =	0;
    pStatusBlock->totalRecvBot =	0;
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
    status = XMbox_Flush(&mbox);
    if (status!=XST_SUCCESS)
    {
    	print("[ERROR] Mailbox flush failed!\r\n");
    }

    // Enter mailbox-driven outer loop
    while(1)
    {

    	//print("[INFO ] Waiting for mailbox message...\r\n");

    	//sendStopAck = 1;

    	// Blocking read of mailbox message
    	XMbox_ReadBlocking(&mbox, (u32 *)pMsg, sizeof(mailMsg));

    	switch(pMsg->cmd)
    	{

    	case CMD_ACQ_CONFIG:
    		// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

        	// Send config request ACK (currently hardcoded as 0xA5A5FACE!)
        	ackOK = sendAcquireAckMessage(&mbox, 0xA5A5FACE);
        	if (!ackOK)
        	{
        		print("[ERROR] Could not send config ACK to PPC1!\r\n");
        	}

    		// Ensure DMA engines are in a stable state, and stopped!
			XLlDma_Reset(&dmaAsicTop);
			XLlDma_Reset(&dmaAsicBot);
			XLlDma_Reset(&dmaTenGig);
			XLlDma_Reset(&dmaPixMem);

    	    // Cache this operation mode so if we receive a start command we know what to do
    		lastMode = pMsg->mode;

    		// Set coalescing counters
    		if (pMsg->mode != ACQ_MODE_UPLOAD)
    		{
    			numRxBDPerLoop = pMsg->bdCoalesceCnt;
    			numTxBDPerLoop = numRxBDPerLoop*2;
    		}

    		switch(pMsg->mode)
    		{
    		case ACQ_MODE_NORMAL:
    			doTx = 1;
    			doRx = 1;
    			pStatusBlock->state = STATE_CFG_BSY;
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			pStatusBlock->state = STATE_IDLE;
    			break;

    		case ACQ_MODE_BURST:
    			//print("[INFO ] Received ACQ_MODE_BURST, starting in ACQ_RX_ONLY mode...\r\n");		// Same initial set up but just let user know we know it's burst mode really!
    		case ACQ_MODE_RX_ONLY:
    			doTx = 0;
    			doRx = 1;
    			//print("[INFO ] Using ACQ_MODE_RX_ONLY.\r\n");
    			pStatusBlock->state = STATE_CFG_BSY;
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			pStatusBlock->state = STATE_IDLE;
    			break;

    		case ACQ_MODE_TX_ONLY:
    			doTx = 1;
    			doRx = 0;
    			//print("[INFO ] Using ACQ_MODE_TX_ONLY.\r\n");
    			pStatusBlock->state = STATE_CFG_BSY;
    			status = configureBdsForAcquisition(pBdRings, &pTenGigPreHW, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			pStatusBlock->state = STATE_IDLE;
    			break;

    		case ACQ_MODE_UPLOAD:
    			// TODO: Refactor numAcq to something more generic (ACQ_MODE_NORMAL->numAcq, ACQ_MODE_UPLOAD->configStartAddr) --> modeParam?
    			pStatusBlock->state = STATE_CFG_BSY;
    			status = configureBdsForUpload(pBdRings[BD_RING_UPLOAD], &pConfigBd, pMsg->param, pMsg->buffSz, pMsg->buffCnt, pStatusBlock);
    			pStatusBlock->state = STATE_IDLE;
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
    				pStatusBlock->numAcq = pMsg->param;
    			}
    		}
    		else
    		{
    			printf("[ERROR] An error occurred configuring BDs!  Error code %d\r\n", status);
    		}
    		// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    		break;

		case CMD_ACQ_START:

			//printf("[INFO ] Starting acquisition, mode %d!\r\n", (int)lastMode);
			switch(lastMode)
			{
			case ACQ_MODE_NORMAL:
			case ACQ_MODE_BURST:
			case ACQ_MODE_RX_ONLY:
			case ACQ_MODE_TX_ONLY:

				pStatusBlock->state = STATE_ACQ_NORMAL;
				//printf("[INFO ] Entering acquire DMA event loop\r\n");

				// Reset BRAM struct
			    pStatusBlock->readPtr = 0;
			    pStatusBlock->writePtr = 0;
			    pStatusBlock->totalRecvTop = 0;
			    pStatusBlock->totalRecvBot = 0;
			    pStatusBlock->totalSent = 0;
			    pStatusBlock->totalErrors = 0;

	    		// Reset counters
	    	    numTopAsicRx = 0;
	    	    numBotAsicRx = 0;
	    	    numRxPairsToSend = 0;
	    	    lastNumTopAsicRx = 0;
	    	    lastNumBotAsicRx = 0;
	    	    numTxPairsSent = 0;
	    	    numTenGigTxComplete = 0;
	    	    numStopAttempts = 0;

				int numBDFromTopAsic = 0;
				int numBDFromBotAsic = 0;
				int numBDFromTenGig = 0;

	    	    pTenGigPostHW = pTenGigPreHW;		// PreHW is first BD in TX ring

	    	    // Quick fix for doTx
	    	    if (lastMode == ACQ_MODE_TX_ONLY)
	    	    {
	    	    	//printf("[DEBUG] ACQ_MODE_TX_ONLY detected, setting TX count to %d\r\n", (int)pStatusBlock->numAcq);
	    	    	numRxPairsToSend = pStatusBlock->numAcq;
	    	    }

				acquireRunning = 1;

	    	    // TODO: Parse result from sendAcquireAckMessage
	    	    sendAcquireAckMessage(&mbox, 0xFFFFFFFF);		// All OK so ACK PPC2

				while (acquireRunning)
				{

					// Process RX
					if (doRx)
					{

						// Pull down any completed RX BDs
						numBDFromTopAsic = XLlDma_BdRingFromHw(pBdRings[BD_RING_TOP_ASIC], numRxBDPerLoop, &pTopAsicBd);
						numBDFromBotAsic = XLlDma_BdRingFromHw(pBdRings[BD_RING_BOT_ASIC], numRxBDPerLoop, &pBotAsicBd);

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

							pStatusBlock->totalRecvTop += numBDFromTopAsic;

							// Validate and recycle BDs
							for (i=0; i<numBDFromTopAsic; i++)
							{
								status = validateBuffer(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to validate buffer index %llu from top ASIC!\r\n", numTopAsicRx+i);
									return 0;
								}

								status = recycleBuffer(pBdRings[BD_RING_TOP_ASIC], pTopAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to recycle buffer index %llu from top ASIC!\r\n", numTopAsicRx+i);
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

							numTopAsicRx += numBDFromTopAsic;
						}



						// **************************************************************************************
						// Bottom ASIC RX
						// **************************************************************************************
						if(numBDFromBotAsic>0)
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] Got %d RX from bottom ASIC\r\n", numBDFromBotAsic);
#endif

							pStatusBlock->totalRecvBot += numBDFromBotAsic;

							// Validate and recycle BDs
							for (i=0; i<numBDFromBotAsic; i++)
							{

								status = validateBuffer(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to validate buffer index %llu from bottom ASIC!\r\n", numBotAsicRx+i);
									return 0;
								}

								status = recycleBuffer(pBdRings[BD_RING_BOT_ASIC], pBotAsicBd, BD_RX);
								if (status!=XST_SUCCESS)
								{
									printf("[ERROR] Failed to recycle buffer index %llu from bottom ASIC!\r\n", numBotAsicRx+i);
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

							numBotAsicRx += numBDFromBotAsic;
						}


						// **************************************************************************************
						// Update BD counters and pointers
						// **************************************************************************************
						// If we've received anything since last time
						if ( (numBotAsicRx!=lastNumBotAsicRx) || (numTopAsicRx!=lastNumTopAsicRx) )
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] Got RX this loop, calculating num completed RX pairs...\r\n");
							printf("[DEBUG] Total TopASIC RX = %llu\r\n", numTopAsicRx);
							printf("[DEBUG] Total BotASIC RX = %llu\r\n", numBotAsicRx);
#endif

							// Determine how many completed pairs of RX we have and prepare them for TX
							if (numBotAsicRx == numTopAsicRx)
							{
								numRxPairsToSend += numBotAsicRx;
								numBotAsicRx = 0;
								numTopAsicRx = 0;
							}
							else if (numBotAsicRx < numTopAsicRx)
							{
								numRxPairsToSend += numBotAsicRx;
								numTopAsicRx -= numBotAsicRx;
								numBotAsicRx = 0;
							}
							else // numBot>numTop
							{
								numRxPairsToSend += numTopAsicRx;
								numBotAsicRx -= numTopAsicRx;
								numTopAsicRx = 0;
							}

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] -- OK --\r\n");
							printf("[DEBUG] numRxPairsComplete = %llu\r\n", numRxPairsToSend);
							printf("[DEBUG] NOW TopASIC RX = %llu\r\n", numTopAsicRx);
							printf("[DEBUG] NOW BotASIC RX = %llu\r\n", numBotAsicRx);
#endif

						}

						// Update loop variables
						lastNumBotAsicRx = numBotAsicRx;
						lastNumTopAsicRx = numTopAsicRx;

					} // END if(doRx)



					// Process TX
					if (doTx)
					{

						// **************************************************************************************
						// Dispatch any waiting TX BD pairs
						// **************************************************************************************
						if (numRxPairsToSend>0)
						{

#ifdef VERBOSE_DEBUG
							printf("[DEBUG] %llu TX pairs ready to send\r\n", numRxPairsToSend);
#endif

							status = XLlDma_BdRingToHw(pBdRings[BD_RING_TENGIG], numRxPairsToSend*2, pTenGigPreHW);

							numTxPairsSent += numRxPairsToSend;

							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Could not commit TX BD pair(s)!  Error code %d\r\n", status);
								return 0;
							}
							else
							{
								// Sent all to HW, none left!
#ifdef VERBOSE_DEBUG
								printf("[INFO ] Committed %llu BD pairs to TX!\r\n", numRxPairsToSend);
#endif

								// Advance our BD pointer
								for (i=0; i<numRxPairsToSend*2; i++)
								{
									pTenGigPreHW = XLlDma_BdRingNext(pBdRings[BD_RING_TENGIG], pTenGigPreHW);
								}
								numRxPairsToSend = 0;
							}
						}

						// **************************************************************************************
						// If we have any uncompleted TX, process them
						// **************************************************************************************
						if (numTxPairsSent>0)
						{

							numBDFromTenGig = XLlDma_BdRingFromHw(pBdRings[BD_RING_TENGIG], numTxBDPerLoop, &pTenGigPostHW);

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
							numTxBds += numBDFromTenGig;
							while (numTxBds>1)
							{
								numTxBds -= 2;
								numTxPairsSent--;
								pStatusBlock->totalSent = numTenGigTxComplete;
#ifdef VERBOSE_DEBUG
								printf("[DEBUG] Pair TX validated, tempTx=%d, numTxpairsSent=%llu\r\n", (int)numTxBds, numTxPairsSent);
#endif
							}

						} // END if (numTxPairsSent>0)

					} // END if(doTx)



					// **************************************************************************************
					// Stop acquiring if we are running a limited number of frames
					// This block also responsible for switching from RX -> TX in burst mode
					// **************************************************************************************
					if (	pStatusBlock->numAcq!=0 &&
							pStatusBlock->numAcq==pStatusBlock->totalRecvTop &&
							pStatusBlock->numAcq==pStatusBlock->totalRecvBot
						)
					{

						// Burst mode RX -> TX logic
						if (lastMode==ACQ_MODE_BURST)
						{
							if(doTx==0)
							{
								// Burst mode, completed RX so switch to TX
								doRx = 0;
								doTx = 1;
								numRxPairsToSend = pStatusBlock->numAcq;		// Queue all RX to be TXed
								//printf("[DEBUG] Got %d events and using ACQ_MODE_BURST, disabling RX and enabling TX (%d pairs)!\r\n", (int)pStatusBlock->numAcq, (int)numRxPairsToSend);
							}
							else
							{
								// Burst mode, completed TX
								if (pStatusBlock->numAcq==(pStatusBlock->totalSent/2))
								{
									//print("[DEBUG] Burst mode halting...\r\n");
									//sendStopAck = 0;
									pStatusBlock->state = STATE_ACQ_STOPPING;
								}
							}
						}
						else
						{
							// Any other mode, we're finished so stop acquiring
							//printf("[DEBUG] Got %d events, stopping...\r\n", (int)pStatusBlock->numAcq);
							pStatusBlock->state = STATE_ACQ_STOPPING;
						}
					}



					// **************************************************************************************
					// Are we trying to stop?
					// **************************************************************************************
					if (pStatusBlock->state == STATE_ACQ_STOPPING)
					{

						// Cleanly stopped?
						if (	pStatusBlock->totalRecvTop + pStatusBlock->totalRecvBot == pStatusBlock->totalSent &&
								pStatusBlock->totalRecvTop == pStatusBlock->totalRecvBot )
						{
							//print("[INFO ] Stop OK.\r\n");
							pStatusBlock->state = STATE_IDLE;
							acquireRunning = 0;

				    	    // TODO: Parse result from sendAcquireAckMessage
							if (sendStopAck == 1) {
								sendAcquireAckMessage(&mbox, 0xFFFFFFFF);		// All OK so ACK PPC2
								sendStopAck = 0;
							}

							// *****************************************************
							// Debugging - dump loop counters
							/*
							printf("[DEBUG] numTopAsicRxComplete=%d\r\n", (int)numTopAsicRx);
				    	    printf("[DEBUG] numBotAsicRxComplete=%d\r\n", (int)numBotAsicRx);
				    	    printf("[DEBUG] numRxPairsComplete=%d\r\n", (int)numRxPairsToSend);
				    	    printf("[DEBUG] lastNumTopAsicRxComplete=%d\r\n", (int)lastNumTopAsicRx);
				    	    printf("[DEBUG] lastNumBotAsicRxComplete=%d\r\n", (int)lastNumBotAsicRx);
				    	    printf("[DEBUG] numTxPairsSent=%d\r\n", (int)numTxPairsSent);
				    	    printf("[DEBUG] numTenGigTxComplete=%d\r\n", (int)numTenGigTxComplete);
				    	    print("[-----]\r\n");
				    	    */
				    	    //printf("[DEBUG] pStat->totalRecvTop=%d\r\n", (int)pStatusBlock->totalRecvTop);
				    	    //printf("[DEBUG] pStat->totalRecvBot=%d\r\n", (int)pStatusBlock->totalRecvBot);
				    	    //printf("[DEBUG] pStat->totalSent=%d\r\n", (int)pStatusBlock->totalSent);
				    	    // *****************************************************

						}
						else
						{
							if (numStopAttempts++ == MAX_STOP_ATTEMPTS)
							{
								// Emergency stop!
								printf("[ERROR] Doing emergency stop! (I waited %d loops.)\r\n", MAX_STOP_ATTEMPTS);
								pStatusBlock->state = STATE_IDLE;
								pStatusBlock->bufferDirty = 1;
								acquireRunning = 0;

								// TODO: Parse result from sendAcquireAckMessage
								sendAcquireAckMessage(&mbox, 0);		// NACK because we didn't stop cleanly
							}
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
							// Triggers a stop next cycle of event loop
							//print("[INFO ] Got stop acquire message, trying to stop...\r\n");
							pStatusBlock->state = STATE_ACQ_STOPPING;
							sendStopAck = 1;
							break;

						default:
							//print("[ERROR] Unexpected command in acquire loop, ignoring for now\r\n");
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

					pStatusBlock->state = STATE_ACQ_UPLOAD;

					//printf("[INFO ] Sending %d configuration upload TXes...\r\n", (int)pStatusBlock->numConfigBds);

					// Send TX BDs to hardware control
					status = XLlDma_BdRingToHw(pBdRings[BD_RING_UPLOAD], pStatusBlock->numConfigBds, pConfigBd);
					if (status!=XST_SUCCESS)
					{
						printf("[ERROR] Could not commit %d upload BD(s) to hardware control!  Error code %d\r\n", (int)pStatusBlock->numConfigBds, status);
					}

					sendAcquireAckMessage(&mbox, 0xFFFFFFFF);

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

					//printf("[INFO ] Verified %d config. upload BD(s) OK!\r\n", (int)pStatusBlock->numConfigBds);

					// Subsequent calls to start configure will fail because we moved pConfigBd, so this prevents a config operation running again
					pStatusBlock->numConfigBds = 0;
					pStatusBlock->state = STATE_IDLE;

				}
				else
				{
					//print("[INFO ] Received CMD_ACQ_START for ACQ_MODE_UPLOAD, but no configured upload BDs (or already uploaded)!  Ignoring...\r\n");
				}

				break;
			} // END switch(lastMode)
			break;
		case CMD_ACQ_STOP:
    	    // TODO: Parse result from sendAcquireAckMessage
			sendAcquireAckMessage(&mbox, 0xFFFFFFFF);		// All OK so ACK PPC2
			// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
			//printf("[INFO ] Not doing anything with stop acquire command.\r\n");
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



/**
 * Generic DMA setup function, accepts segment size (size of data to RX from I/O FPGA),
 * and segment count (to limit the number of BDs created for debugging / #-frame mode)
 * @param pBdRings pointer to array of BD rings
 * @param pFirstTxBd set by function to be first BD in TX ring
 * @param bufferSz Size of data buffer to RX from I/O FPGA
 * @param bufferCnt Number of buffers to allocate, set to 0 for allocation of maximum BDs
 * @param pStatusBlock pointer to status struct, updated by function
 *
 * @return XST_SUCCESS if OK, otherwise an XST_xxx error code
 */
int configureBdsForAcquisition(XLlDma_BdRing *pBdRings[], XLlDma_Bd **pFirstTxBd, u32 bufferSz, u32 bufferCnt, acqStatusBlock* pStatusBlock)
{

	// TODO: Respect the reserved BD config. area!

	unsigned status;
	XLlDma_BdRing *pRingTenGig = pBdRings[BD_RING_TENGIG];
	XLlDma_BdRing *pRingAsicTop = pBdRings[BD_RING_TOP_ASIC];
	XLlDma_BdRing *pRingAsicBot = pBdRings[BD_RING_BOT_ASIC];

	// Determine maximum number of buffers possible given DDR and BD storage space
	u32 maxBufferCnt = DDR2_SZ / 2 / bufferSz;
	if ( (maxBufferCnt * 4 * XLLDMA_BD_MINIMUM_ALIGNMENT) > LL_BD_SZ)		// *4 because we need 2x RX and 2x TX BDs per single read
	{
		// DDR OK but too big for BDs, so reduce to as many will fit in BD space
		maxBufferCnt = (LL_BD_SZ / XLLDMA_BD_MINIMUM_ALIGNMENT) / 4;
	}

	if (bufferCnt==0)
	{
		// Allocate maximum number of buffers
		bufferCnt = maxBufferCnt;
	}
	else
	{
		// Verify we can fit the requested number of buffers
		if ( bufferCnt>maxBufferCnt )
		{
			printf("[ERROR] Cannot allocate requested %d buffers of (2 x 0x%08x) bytes!\r\n", (unsigned)bufferCnt, (unsigned)bufferSz);
			return XST_FAILURE;
		}
	}
	//printf("[DEBUG] Requested %d buffers of (2 x 0x%08x) bytes...\r\n", (unsigned)bufferCnt, (unsigned)bufferSz);

	// Check if we can re-use BDs to save time configuring them
	// i.e. !dirty, size matched last run and count is equal or smaller than last run
	if ( !pStatusBlock->bufferDirty && (bufferSz==pStatusBlock->bufferSize && (bufferCnt<=pStatusBlock->bufferCnt)) )
	{
		//printf("[INFO ] Parameters for buffer size and count match last configuration, reusing existing BDs!\r\n");

		status = startAcquireEngines(pRingAsicTop, pRingAsicBot, pRingTenGig);
		if (status!=XST_SUCCESS)
		{
			print("[ERROR] Can't start top ASIC RX engine, no initialised BDs!\r\n");
			return status;
		}

		return XST_SUCCESS;
	}

	// Create BD rings of appropriate size
	// TODO: Add assert to make sure we don't exceed our allocated space (doing so will overwrite PPC2 code!)
	u32 bdChunkSize =			XLLDMA_BD_MINIMUM_ALIGNMENT * bufferCnt;			// Total space required for all BDs for a given channel
	u32 topAsicRXBdOffset =		LL_BD_BADDR;
	u32 botAsicRXBdOffset =		topAsicRXBdOffset + bdChunkSize;
	u32 tenGigTXBdOffset =		botAsicRXBdOffset + bdChunkSize;
	//printf("[INFO ] BDs: \r\n");
	//printf("[INFO ] TopASIC      0x%08x\r\n", (unsigned)topAsicRXBdOffset);
	//printf("[INFO ] Bottom ASIC  0x%08x\r\n", (unsigned)botAsicRXBdOffset);
	//printf("[INFO ] TenGig       0x%08x\r\n", (unsigned)tenGigTXBdOffset);

	status = XLlDma_BdRingCreate(pRingAsicTop, topAsicRXBdOffset, topAsicRXBdOffset, LL_DMA_ALIGNMENT, bufferCnt);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create top ASIC RX BD ring!  Error code %d\r\n", status);
		return status;
	}

	status = XLlDma_BdRingCreate(pRingAsicBot, botAsicRXBdOffset, botAsicRXBdOffset, LL_DMA_ALIGNMENT, bufferCnt);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create bottom ASIC RX BD ring!  Error code %d\r\n", status);
		return status;
	}

	// Note the TX ring is double the length of the RX rings!
	status = XLlDma_BdRingCreate(pRingTenGig, tenGigTXBdOffset, tenGigTXBdOffset, LL_DMA_ALIGNMENT, bufferCnt*2);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create 10GBE TX BD ring!  Error code %d\r\n", status);
		return status;
	}

	//printf("[INFO ] Created BD rings w/%d buffers each.\r\n", (int)bufferCnt);


	// Configure BDs in rings
	XLlDma_Bd *pTopRXBd;
	XLlDma_Bd *pBotRXBd;
	XLlDma_Bd *pTXBd;

	// First allocate a BD for each ring
	status = XLlDma_BdRingAlloc(pRingAsicTop, bufferCnt, &pTopRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate top ASIC RX BD!\r\n");
		return status;
	}

	status = XLlDma_BdRingAlloc(pRingAsicBot, bufferCnt, &pBotRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate bottom ASIC RX BD!\r\n");
		return status;
	}

	status = XLlDma_BdRingAlloc(pRingTenGig, bufferCnt*2, &pTXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate 10GBe TX BD!\r\n");
		return status;
	}

	//print("[INFO ] Starting BD configuration...\r\n");

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
	u32 botAsicBufferAddress = DDR2_BADDR + (DDR2_SZ / 2);

	// RX rings
	for (i=0; i<bufferCnt; i++)
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

		// Move to next BD
		pTopRXBd = XLlDma_BdRingNext(pRingAsicTop, pTopRXBd);
		pBotRXBd = XLlDma_BdRingNext(pRingAsicBot, pBotRXBd);
	}

	// TX ring
	currentOffset = 0;
	for (i=0; i<bufferCnt; i++)
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

	//print("[INFO ] Completed BD configuration!\r\n");

	// Commit all RX BDs to DMA engines
	status = XLlDma_BdRingToHw(pRingAsicTop, bufferCnt, pTopFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send top ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}
	status = XLlDma_BdRingToHw(pRingAsicBot, bufferCnt, pBotFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send bottom ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}

	// Start engines
	status = startAcquireEngines(pRingAsicTop, pRingAsicBot, pRingTenGig);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Could not start DMA engines for acquisition!\r\n");
		return status;
	}

	//print("[INFO ] Committed BDs to HW and started DMA engines!\r\n");

	// Update status
	pStatusBlock->bufferCnt = bufferCnt;
	pStatusBlock->bufferDirty = 0;

	// Everything OK!
	return XST_SUCCESS;
}



/**
 * Configures DMA engine for upstream configuration upload
 * @param pUploadBdRing pointer to BD ring for upload channel
 * @param pFirstConfigBd set by function to be first BD in TX ring
 * @param bufferAddr address at which configuration data is stored
 * @param bufferSz size of configuration data
 * @param bufferCnt number of configurations
 *
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
	//printf("[INFO ] Creating %d config BDs at 0x%08x (%d max.)\r\n", (int)bufferCnt, (unsigned)bdStartAddr, LL_MAX_CONFIG_BD);

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

	return XST_SUCCESS;
}



/**
 * Starts both ASIC RX and 10GBe TX engines
 * @param pRingAsicTop pointer to top ASIC BD ring
 * @param pRingAsicBot pointer to bottom ASIC BD ring
 * @param pRingTenGig pointer to 10GBe BD ring
 *
 * @return XST_SUCCESS, or XST_* error
 */
int startAcquireEngines(XLlDma_BdRing* pRingAsicTop, XLlDma_BdRing* pRingAsicBot, XLlDma_BdRing* pRingTenGig)
{
	int status;

	// RX engines
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



/**
 * Checks for a mailbox message (non-blocking)
 * @param pMailBox pointer to XMbox
 * @param pMsg pointer to mailMsg buffer to receive to
 *
 * @return 1 on success, 0 otherwise
 */
int checkForMailboxMessage(XMbox *pMailBox, mailMsg *pMsg)
{
	u32 bytesRecvd = 0;
	u32 totalRecvd = 0;
	u32 status;

	u8 *pBytePtr =  (u8*)pMsg;

	// Mailbox receive is only atomic on 4 byte level
	while(totalRecvd<sizeof(mailMsg))
	{
		status = XMbox_Read(pMailBox, (u32*)pBytePtr, (sizeof(mailMsg)-totalRecvd), &bytesRecvd);
		if (status == XST_SUCCESS)
		{
			// Got some data!
			pBytePtr += bytesRecvd;
			totalRecvd += bytesRecvd;

		}
		else if (status==XST_NO_DATA && totalRecvd==0)
		{
			return 0;		// Nothing to read
		}

	}

	return 1;
}



/**
 * Sends a response to PPC2 on the request status of the CMD_ACQ_START or CMD_ACQ_STOP requests.
 * @param state 0 for NACK, anthing else for ACK
 *
 * @return 1 on success, 0 on failure (mailbox)
 */
unsigned short sendAcquireAckMessage(XMbox *pMailbox, u32 state)
{
	int status;
	u32 sentBytes;
	status = XMbox_Write(pMailbox, &state, 4, &sentBytes);
	if (status==XST_SUCCESS)
	{
		return 1;
	}
	else
	{
		return 0;
	}
}



/**
 * Verifies a buffer by checking the STS/CTRL field of the BD matches the value expected.
 * @param pRing pointer to BD ring
 * @param pBd pointer to BD
 * @param buffType buffer type, either BD_RX or BD_TX
 *
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



/**
 * Resets, frees and re-allocates a buffer into the current BD ring
 * @param pRing pointer to BD ring
 * @param pBd pointer to BD
 * @param buffType buffer type, either BD_RX or BD_TX
 *
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



/**
 * Reads DCR registers into a struct
 * @param type
 * @param pReg
 *
 * @return 1 if successful or 0 if type is invalid
 */
int readDcrs(dcrRegistersBase type, dcrRegisters *pReg)
{

	// You cannot pass variables into mfdcr only constants, so we have to do this the long way!
	switch(type)
	{

	case DCR_TOP_ASIC_RX:
		pReg->type = DCR_CHANNEL_RX;
		pReg->nxtDescPtr = mfdcr(0xB8);
		pReg->curBufAddr = mfdcr(0xB9);
		pReg->curBufLength = mfdcr(0xBA);
		pReg->curDescPtr = mfdcr(0xBB);
		pReg->tailDescPtr = mfdcr(0xBC);
		pReg->channelCtrl = mfdcr(0xBD);
		pReg->irqReg = mfdcr(0xBE);
		pReg->statusReg = mfdcr(0xBF);
		pReg->controlReg = mfdcr(0xC0);
		break;

	case DCR_BOT_ASIC_RX:
		pReg->type = DCR_CHANNEL_RX;
		pReg->nxtDescPtr = mfdcr(0x88);
		pReg->curBufAddr = mfdcr(0x89);
		pReg->curBufLength = mfdcr(0x8A);
		pReg->curDescPtr = mfdcr(0x8B);
		pReg->tailDescPtr = mfdcr(0x8C);
		pReg->channelCtrl = mfdcr(0x8D);
		pReg->irqReg = mfdcr(0x8E);
		pReg->statusReg = mfdcr(0x8F);
		pReg->controlReg = mfdcr(0x90);
		break;

	case DCR_GBE_TX:
		pReg->type = DCR_CHANNEL_TX;
		pReg->nxtDescPtr = mfdcr(0xC8);
		pReg->curBufAddr = mfdcr(0xC9);
		pReg->curBufLength = mfdcr(0xCA);
		pReg->curDescPtr = mfdcr(0xCB);
		pReg->tailDescPtr = mfdcr(0xCC);
		pReg->channelCtrl = mfdcr(0xCD);
		pReg->irqReg = mfdcr(0xCE);
		pReg->statusReg = mfdcr(0xCF);
		pReg->controlReg = mfdcr(0xD8);
		break;

	case DCR_UPLOAD_TX:
		pReg->type = DCR_CHANNEL_TX;
		pReg->nxtDescPtr = mfdcr(0x98);
		pReg->curBufAddr = mfdcr(0x99);
		pReg->curBufLength = mfdcr(0x9A);
		pReg->curDescPtr = mfdcr(0x9B);
		pReg->tailDescPtr = mfdcr(0x9C);
		pReg->channelCtrl = mfdcr(0x9D);
		pReg->irqReg = mfdcr(0x9E);
		pReg->statusReg = mfdcr(0x9F);
		pReg->controlReg = mfdcr(0xA8);
		break;

	default:
		// Invalid DCR
		return 0;

	} // END switch(type)

	return 1;
}



/**
 * Prints out a DCR struct
 * @param pReg pointer to DCR struct
 */
void printDcr(dcrRegisters *pReg)
{
	char type;
	if (pReg->type==DCR_CHANNEL_RX)
	{
		type = 'R';
	}
	else
	{
		type = 'T';
	}

	printf("[ DCR ] Channel is %cX\r\n", type);
	printf("[ DCR ] %cX_NXTDESC_PTR    0x%08x\r\n", type, (unsigned int)pReg->nxtDescPtr);
	printf("[ DCR ] %cX_CURBUF_ADDR    0x%08x\r\n", type, (unsigned int)pReg->curBufAddr);
	printf("[ DCR ] %cX_CURBUF_LENGTH  0x%08x\r\n", type, (unsigned int)pReg->curBufLength);
	printf("[ DCR ] %cX_CURDESC_PTR    0x%08x\r\n", type, (unsigned int)pReg->curDescPtr);
	printf("[ DCR ] %cX_TAILDESC_PTR   0x%08x\r\n", type, (unsigned int)pReg->tailDescPtr);
	printf("[ DCR ] %cX_CHANNEL_CTRL   0x%08x\r\n", type, (unsigned int)pReg->channelCtrl);
	printf("[ DCR ] %cX_IRQ_REG        0x%08x\r\n", type, (unsigned int)pReg->irqReg);
	printf("[ DCR ] %cX_STATUS_REG     0x%08x\r\n", type, (unsigned int)pReg->statusReg);
	printf("[ DCR ] DMA_CONTROL_REG   0x%08x\r\n", (unsigned int)pReg->controlReg);
}
