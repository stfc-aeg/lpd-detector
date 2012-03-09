/*
 * Test PPC1 application
 *
 * Developed to test Xilinx mailbox and LLDMA engine functionality
 *
 */

// Todo list, in order of priority
// TODO: Complete event loop with mailbox/DMA
// TODO: Abstract armAsicRX, armTenGigTX to a more generic function
// TODO: Implement shared bram status flags
// TODO: Implement pixmem upload (base on armTenGigTx)

/*
 * MEMORY ORGANISATION
 * ---------------------------------------
 * ASIC readout size	= 0x18000 - bytes in 12-bit mode
 *
 * Total read / Spartan	= 0x18000 x 8
 *
 * Frame size			=
 * DDR2 size			= 0x3FFFFFFF
 *
 *
 */

/*
 * SHARED BRAM FLAGS / STATUS
 *
 * What to track?
 * 	- Total BD slots for RX (ASIC)
 *	- Total BD slots for TX (TenGig)
 *	- Num used BDs for RX (ASIC) (i.e. read pointer)
 *	- Num used BDs for TX (TenGig) (i.e. write pointer)
 *		- Can then calculate DDR2 occupancy
 *	- Number received frames
 *	- Number sent frames
 *		- Calculate total processed frames
 *	- Error count / engine
 *		- What do we consider an error?  Any BD that has DMA_ERROR set!
 *
 */

/*
 * Initialisation from PPC2 (mailbox message?)
 *	- Number frames expected (optional?)
 *	- Read segment size (per Spartan, not per ASIC)
 *
 * Use this information to:
 *
 * 	- Configure RX/TX BD rings (ddr2size / segment size / 2 = numBDs)
 *
 * MAILBOX MESSAGE
 * ---------------
 * u32 segment_sz
 * u32 num_segments
 *
 */

#include <stdio.h>
#include "xmbox.h"
#include "xparameters.h"
#include "platform.h"
#include "xlldma.h"
#include "xil_testmem.h"

// Device Control Register (DCR) offsets for PPC DMA engine (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_ASIC_BOT		0x80							// dma0:rx <- Bottom ASIC
#define LL_DMA_BASE_PIXMEM			0x98							// dma1:tx -> pixel configuration memory
#define LL_DMA_BASE_ASIC_TOP		0xB0							// dma2:rx <- Top ASIC
#define LL_DMA_BASE_TENGIG			0xC8							// dma3:tx -> 10GBE

#define LL_DMA_ALIGNMENT			XLLDMA_BD_MINIMUM_ALIGNMENT		// BD Alignment, set to minimum
#define LL_BD_BADDR					0x8D300000						// Bass address for BDs (Top quarter of SRAM)
#define LL_TOP_ASIC_OFFSET			0x00002000						// Offset at which top ASIC BDs start, from LL_BD_BADDR (space for 128 BDs)
#define LL_BOT_ASIC_OFFSET			0x00004000						// Offset at which bottom ASIC BDs start, from LL_BD_BADDR (space for 128 BDs)
#define LL_TENGIG_OFFSET			0x00006000						// Offset at which 10G BDs start, from LL_BD_BADDR (space for 128 BDs)
#define LL_PIXMEM_OFFSET			0x00008000						// Offset at which pixel configuration memory BDs start, from LL_BD_BADDR (space for 128 BDs)

#define LL_STSCTRL_RX_OK			0x1D000000						// STS/CTRL field in BD should be 0x1D when successfully RX (COMPLETE | SOP | EOP)
#define LL_STSCTRL_TX_OK			0x10000000						// STS/CTRL field in BD should be 0x10 when successfully TX (COMPLETE)

// New memory management stuff
#define DDR2_BADDR					0x00000000						// DDR2 base address
#define DDR2_SZ						0x40000000						// DDR2 size (1GB)
#define LL_BD_SZ					0x00100000						// Size of BD memory region (1MB) (so total LL_BD_SZ / LL_DMA_ALIGNMENT BDs possible), in our case 16384

#define LL_STSCTRL_RX_BD			0x0
#define LL_STSCTRL_TX_BD			XLLDMA_BD_STSCTRL_SOP_MASK | XLLDMA_BD_STSCTRL_EOP_MASK

// FUNCTION PROTOTYPES
// TODO: Move to header
int armAsicRX(XLlDma_BdRing *pRingAsicTop, XLlDma_BdRing *pRingAsicBot, u32 topAddr, u32 botAddr, unsigned int len, u32 sts);
int armTenGigTX(XLlDma_BdRing *pRingTenGig, u32 addr1, u32 addr2, unsigned int len);

int configureBds(XLlDma_BdRing *pRingTenGig, XLlDma_BdRing *pRingAsicTop, XLlDma_BdRing *pRingAsicBot, u32 segmentSz, u32 segmentCnt);

//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

int main()
{
    init_platform();

	// Clear serial console by spamming CR/LF
	int foo;
	for (foo=0; foo<100; foo++)
	{
		print("\r\n");
	}

    print("[INFO ] FEM PPC1 is alive!\r\n");

    int status;
    u32 mailboxBuffer[3] =	{0,0,0};
    u32 topAsicAddr =		0x08000000;
    u32 botAsicAddr =		0x04000000;

    // DEBUGGING
    // Fill memory locations with known test pattern data to verify DMA engine transfers
    /*
    if(Xil_TestMem32((u32*)topAsicAddr,0x18000, 0, XIL_TESTMEM_FIXEDPATTERN)==-1)
    {
    	printf("[DEBUG] Failed to memtest region 0x%08x, len=0x%08x!\r\n", (unsigned)topAsicAddr, (unsigned)0x18000);
    }
    if(Xil_TestMem32((u32*)botAsicAddr,0x18000, 0, XIL_TESTMEM_FIXEDPATTERN)==-1)
    {
    	printf("[DEBUG] Failed to memtest region 0x%08x, len=0x%08x!\r\n", (unsigned)botAsicAddr, (unsigned)0x18000);
    }
    */

    // Initialise DMA engines
    //XLlDma dmaAsicTop, dmaAsicBot, dmaTenGig, dmaPixMem;
    XLlDma dmaAsicTop, dmaAsicBot, dmaTenGig;

    XLlDma_BdRing *pRxTopAsicRing = &XLlDma_GetRxRing(&dmaAsicTop);
    XLlDma_BdRing *pRxBotAsicRing = &XLlDma_GetRxRing(&dmaAsicBot);
    XLlDma_BdRing *pTxTenGigRing = &XLlDma_GetTxRing(&dmaTenGig);
    //XLlDma_BdRing *pTxPixMemRing = &XLlDma_GetTxRing(&dmaPixMem);

    XLlDma_Initialize(&dmaAsicTop, LL_DMA_BASE_ASIC_TOP);
    XLlDma_Initialize(&dmaAsicBot, LL_DMA_BASE_ASIC_BOT);
    XLlDma_Initialize(&dmaTenGig, LL_DMA_BASE_TENGIG);
    //XLlDma_Initialize(&dmaPixMem, LL_DMA_BASE_PIXMEM);

    // This now done in new configureBds()
    /*
	status = XLlDma_BdRingCreate(pRxTopAsicRing, LL_BD_BADDR+LL_TOP_ASIC_OFFSET, LL_BD_BADDR+LL_TOP_ASIC_OFFSET, LL_DMA_ALIGNMENT, 128);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create top ASIC RX BD ring!  Error code %d\r\n", status);
		return 0;
	}

	status = XLlDma_BdRingCreate(pRxBotAsicRing, LL_BD_BADDR+LL_BOT_ASIC_OFFSET, LL_BD_BADDR+LL_BOT_ASIC_OFFSET, LL_DMA_ALIGNMENT, 128);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create bottom ASIC RX BD ring!  Error code %d\r\n", status);
		return 0;
	}

	status = XLlDma_BdRingCreate(pTxTenGigRing, LL_BD_BADDR+LL_TENGIG_OFFSET, LL_BD_BADDR+LL_TENGIG_OFFSET, LL_DMA_ALIGNMENT, 128);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create 10GBE TX BD ring!  Error code %d\r\n", status);
		return 0;
	}

	status = XLlDma_BdRingCreate(pTxPixMemRing, LL_BD_BADDR+LL_PIXMEM_OFFSET, LL_BD_BADDR+LL_PIXMEM_OFFSET, LL_DMA_ALIGNMENT, 128);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create pixel config TX BD ring!  Error code %d\r\n", status);
		return 0;
	}
	print("[INFO ] DMA engines initialised.\r\n");
	*/

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
    	print("[FATAL] Mailbox initialise failed, terminating...\r\n");
    	return 0;
    }
    print("[INFO ] Mailbox initialised.\r\n");

    u32 topAddr, botAddr;

    // Enter mailbox-driven outer loop
    while(1)
    {
    	unsigned short acquireRunning = 0;
    	print("[INFO ] Waiting for mailbox message...\r\n");

    	// [OLD] Blocking read of 1x 32bit word
    	/*
    	XMbox_ReadBlocking(&mbox, &mailboxBuffer[0], 4);
    	printf("[INFO ] Got message!  cmd=%d (0x%08x)\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[0]);
    	*/

    	// [NEW] Blocking read of 3x 32bit word
    	XMbox_ReadBlocking(&mbox, &mailboxBuffer[0], 12);
    	printf("[INFO ] Got message!  cmd=0x%08x, buffSz=0x%08x, buffCnt=0x%08x\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[1], (unsigned)mailboxBuffer[2]);

    	// TODO: Move this outside this loop, only here as a dirty hack to get the thing tested...
        configureBds(pTxTenGigRing, pRxTopAsicRing, pRxBotAsicRing, mailboxBuffer[1], mailboxBuffer[2]);

    	switch (mailboxBuffer[0])
    	{

			case 1:  // START_ACQUIRE
				printf("[INFO ] Entering acquire DMA event loop\r\n");
				acquireRunning = 1;
				while (acquireRunning)
				{

					print ("\r\n");

					// Arm RX engines for ASICs
					// TODO: Determine why certain addresses cause issues with DMA engine!?
					// NOTE: if these addresses are changed the DMA goes a bit mental, why should the address matter?!
					// Also, changing John's code to use other than 0x0400 0000, 0x0800 0000 (e.g. to 0x0040 0000, 0x0080 0000) has same effect!!!!
					status = armAsicRX(pRxTopAsicRing, pRxBotAsicRing, topAsicAddr, botAsicAddr, 0x18000, 0x0);
					if (status!=XST_SUCCESS)
					{
						printf("[ERROR] Failed to arm DMA engine for ASIC receive!  Error code %d\r\n", status);
						print("[ERROR] Fatal error, terminating.\r\n");
						return 0;
					}
					else
					{
						print("[INFO ] DMA engines armed for ASIC RX.\r\n");
					}

					// Wait for data to be received
					XLlDma_Bd *pTopAsicBd, *pBotAsicBd, *pTenGigBd;
					unsigned numRxTop = 0;
					unsigned numRxBot = 0;
					unsigned numTx = 0;
					unsigned totalRx = 0;
					unsigned short done=0;
					u32 sts;
					u32 addr;

					print("[INFO ] Waiting for ASIC RX...\r\n");

					// This is a very quick and dirty hacked up event loop
					while(done==0)
					{

						// See if DMA engine has completed receive from either Spartan
						numRxTop = XLlDma_BdRingFromHw(pRxTopAsicRing, 1, &pTopAsicBd);
						numRxBot = XLlDma_BdRingFromHw(pRxBotAsicRing, 1, &pBotAsicBd);

						if (numRxTop !=0 )
						{
							sts = (unsigned)XLlDma_BdGetStsCtrl(pTopAsicBd);
							addr = (unsigned)XLlDma_BdGetBufAddr(pTopAsicBd);
							printf("[INFO ] Got data from top ASIC.    (%d BD(s), STS/CTRL=0x%08x, ADDR=0x%08x)\r\n", numRxTop, (unsigned)sts, (unsigned)addr);
							if (!(sts&0xFF000000)&LL_STSCTRL_RX_OK)
							{
								// NOTE: Even if code passes this check there can be no DMA transfer received :(
								printf("[ERROR] STS/CTRL field for top ASIC RX did not show successful completion!  STS/CTRL=0x%08x\r\n", (unsigned)sts);
							}
							status = XLlDma_BdRingFree(pRxTopAsicRing, 1, pTopAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Failed to free RXed BD from top ASIC, error code %d\r\n.", status);
							}
							//Debug
							topAddr = XLlDma_BdGetBufAddr(pTopAsicBd);
							printf("[DEBUG] RX from top addr 0x%08x\r\n", (unsigned)topAddr);
							totalRx++;
						}

						if (numRxBot != 0 )
						{
							sts = (unsigned)XLlDma_BdGetStsCtrl(pBotAsicBd);
							addr = (unsigned)XLlDma_BdGetBufAddr(pBotAsicBd);
							printf("[INFO ] Got data from bottom ASIC. (%d BD(s), STS/CTRL=0x%08x, ADDR=0x%08x)\r\n", numRxBot, (unsigned)sts, (unsigned)addr);
							status = XLlDma_BdRingFree(pRxBotAsicRing, 1, pBotAsicBd);
							if (!(sts&0xFF000000)&LL_STSCTRL_RX_OK)
							{
								// NOTE: Even if code passes this check there can be no DMA transfer received :(
								printf("[ERROR] STS/CTRL field for bottom ASIC RX did not show successful completion!  STS/CTRL=0x%08x\r\n", (unsigned)sts);
							}
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Failed to free RXed BD from bottom ASIC, error code %d\r\n.", status);
							}
							//Debug
							botAddr = XLlDma_BdGetBufAddr(pBotAsicBd);
							printf("[DEBUG] RX from bottom addr 0x%08x\r\n", (unsigned)botAddr);
							totalRx++;
						}

						if (totalRx==2) {
							print("[INFO ] All ASICs data received OK.\r\n");
							// Arm TX for 10GBE
							print("[INFO ] Arming 10GBE TX...\r\n");
							status = armTenGigTX(pTxTenGigRing, topAddr, botAddr, 0x18000);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Failed to arm DMA engine for 10GBE send!  Error code %d\r\n", status);
								print("[ERROR] Fatal error, terminating.\r\n");
								return 0;
							}
							done = 1;
						}



						// -=-=-=-=-=- START UNTESTED -=-=-=-=-=-

						// Verify completion of TX packet
						print("[DEBUG] Waiting for DMA engine response for TX...\r\n");
						numTx = 0;
						while(numTx==0)		// TODO: Remove infinite wait loop!
						{
							numTx = XLlDma_BdRingFromHw(pTxTenGigRing, 1, &pTenGigBd);
						}
						sts = (unsigned)XLlDma_BdGetStsCtrl(pTenGigBd);
						if (!(sts&0xFF000000)&LL_STSCTRL_TX_OK)
						{
							printf("[DEBUG] Got TX BD, but looks incorrect:  Status=0x%08x\r\n", (unsigned)sts);
						}
						else
						{
							printf("[DEBUG] Got TX BD, looks OK!  Status=0x%08x\r\n", (unsigned)sts);
						}

						// Free BD
						status = XLlDma_BdRingFree(pTxTenGigRing, 1, pTenGigBd);
						if (status!=XST_SUCCESS)
						{
							printf("[ERROR] TX sent but could not free BD!  Error code %d\r\n", status);
						}
						else
						{
							print("[ INFO] TX sent, BD freed OK\r\n");
						}

						// -=-=-=-=-=- END UNTESTED -=-=-=-=-=-



						// Check if there are any pending mailbox messages
						u32 bytesRecvd = 0;
						XMbox_Read(&mbox, &mailboxBuffer[0], 4, &bytesRecvd);
						if (bytesRecvd == 4) {
							printf("[INFO ] Got message!  cmd=%d (0x%08x)\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[0]);
							switch (mailboxBuffer[0])
							{
							case 2: // STOP ACQUIRE
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

				break;

			case 2:  // STOP_ACQUIRE
				printf("[INFO ] Not doing anything with stop acquire command.\r\n");
				break;

			case 3: // DO_UPLOAD
				printf("[INFO ] Upload command not yet implemented.\r\n");
				break;

			default:
				printf("[ERROR] Unrecognised mailbox command %ld\r\n", mailboxBuffer[0]);
				break;
    	} // END switch(mailboxBuffer[0])

    }

    // Should never execute!
    print("[INFO ] Process terminating...\r\n");
    cleanup_platform();
    return 0;

}



/* Arms the 2 ASIC RX DMA channels to receive data
 * @param pRingAsicTop pointer to BdRing for top ASIC
 * @param pRingAsicBot pointer to BdRing for bottom ASIC
 * @param topAddr memory address that DMA transfer for top ASIC should be written to
 * @param botAddr memory address that DMA transfer for bottom ASIC should be written to
 * @param len length of payload to receive, in bytes (must always be 32bit word-aligned)
 * @param sts status word, most significant byte is status/control for DMA engine, other bytes application specific data
 *
 * @return XST_SUCCESS on success, or XST_? error code on failure
 */
int armAsicRX(XLlDma_BdRing *pRingAsicTop, XLlDma_BdRing *pRingAsicBot, u32 topAddr, u32 botAddr, unsigned int len, u32 sts)
{

	int status;

	int numBD = 2;

	// Get BDs and configure for a read
	XLlDma_Bd *pTopAsicBd;
	status = XLlDma_BdRingAlloc(pRingAsicTop, numBD, &pTopAsicBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate top ASIC RX BD!\r\n");
		return status;
	}

	XLlDma_Bd *pBotAsicBd;
	status = XLlDma_BdRingAlloc(pRingAsicBot, numBD, &pBotAsicBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate bottom ASIC RX BD!\r\n");
		return status;
	}

	// Configure BD for reads
	print("[INFO ] Configuring RX BDs for ASICs...\r\n");
	XLlDma_BdSetBufAddr(*pTopAsicBd, topAddr);
	XLlDma_BdSetBufAddr(*pBotAsicBd, botAddr);
	XLlDma_BdSetLength(*pTopAsicBd, len);
	XLlDma_BdSetLength(*pBotAsicBd, len);
	XLlDma_BdSetStsCtrl(*pTopAsicBd, sts);
	XLlDma_BdSetStsCtrl(*pBotAsicBd, sts);

	// Setup a second BD for a sequential read
	XLlDma_Bd *pSecondTopAsicBd, *pSecondBotAsicBd;
	pSecondTopAsicBd = XLlDma_BdRingNext(pRingAsicTop, pTopAsicBd);
	pSecondBotAsicBd = XLlDma_BdRingNext(pRingAsicBot, pBotAsicBd);
	XLlDma_BdSetBufAddr(*pSecondTopAsicBd, topAddr+len);
	XLlDma_BdSetBufAddr(*pSecondBotAsicBd, botAddr+len);
	XLlDma_BdSetLength(*pSecondTopAsicBd, len);
	XLlDma_BdSetLength(*pSecondBotAsicBd, len);
	XLlDma_BdSetStsCtrl(*pSecondTopAsicBd, sts);
	XLlDma_BdSetStsCtrl(*pSecondBotAsicBd, sts);


	// Commit BD(s) to DMA engines
	status = XLlDma_BdRingToHw(pRingAsicTop, numBD, pTopAsicBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send top ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}
	status = XLlDma_BdRingToHw(pRingAsicBot, numBD, pBotAsicBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send bottom ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}

	// Start engines!
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

	// Everything OK!
	return XST_SUCCESS;

}



/* Arms the 10GBE TX DMA channel to send data
 * @param pRingTenGig pointer to BdRing for 10GBE
 * @param addr1 memory address of start of data to be sent
 * @param addr2 memory address of start of data to be sent
 * @param len length of payload to send, in bytes (must always be 32bit word-aligned)
 *
 * @return XST_SUCCESS on success, or XST_? error code on failure
 */
int armTenGigTX(XLlDma_BdRing *pRingTenGig, u32 addr1, u32 addr2, unsigned int len)
{

	int status;

	XLlDma_Bd *pTenGigBd;

	// Configure BDs for transmit
	int i;
	u32 addr;
	for (i=0; i<2; i++)
	{
		if (i==0)
		{
			addr = addr2;
		}
		else if (i==1)
		{
			addr = addr1;
		}

		status = XLlDma_BdRingAlloc(pRingTenGig, 1, &pTenGigBd);
		if (status!=XST_SUCCESS) {
			printf("[ERROR] Failed to allocate 10GBE TX BD, index %d!\r\n", i);
			return status;
		}

		XLlDma_BdSetBufAddr(*pTenGigBd, addr);
		XLlDma_BdSetLength(*pTenGigBd, len);
		XLlDma_BdSetStsCtrl(*pTenGigBd, XLLDMA_BD_STSCTRL_SOP_MASK | XLLDMA_BD_STSCTRL_EOP_MASK);

		// Commit BD to DMA engine
		status = XLlDma_BdRingToHw(pRingTenGig, 1, pTenGigBd);
		if (status!=XST_SUCCESS)
		{
			printf("[ERROR] Failed to send 10GBE TX to HW, error code %d, index %d!\r\n", status, i);
			return status;
		}

	}

	// Send it!
	status = XLlDma_BdRingStart(pRingTenGig);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Can't start 10GBE TX engine, no initialised BDs!\r\n");
		return status;
	}

	// Everything OK!
	return XST_SUCCESS;
}

/*
 * New generic DMA setup function (to replace armAsicRX, armTenGigTX)
 * Also accepts segment size (size of data to RX from I/O Spartan), and
 * segment count (to limit the number of BDs created for debugging / #-frame mode)
 * @param pRingTenGig
 * @param pRingAsicTop
 * @param pRingAsicBot
 * @param segmentSz Size of data to RX from I/O Spartan
 * @param segmentCnt Number of segments to allocate, set to 0 for allocation of maximum BDs
 * @return XST_SUCCESS if OK, otherwise an XST_xxx error code
 *
 */
// TODO: Remove pointers to BdRings, pass array or struct of all BDRings instead?
int configureBds(XLlDma_BdRing *pRingTenGig, XLlDma_BdRing *pRingAsicTop, XLlDma_BdRing *pRingAsicBot, u32 segmentSz, u32 segmentCnt)
{

	unsigned status;

	u32 totalSegmentSz = segmentSz*2;		// Each DDR segment is actually segmentSz*2 (because we have 2 I/O spartans)
	u32 segmentMultiplier = 4;				// How many BDs form a 'complete' segment?  4! - 2x RX (1/ring), then 2x TX (2/ring)
	u32 totalNumSegments = 0;



	// Check DDR2 is large enough for requested number/size of segments
	if (segmentCnt==0)
	{
		// If segmentCnt==0 we allocate as many segments as possible
		totalNumSegments = DDR2_SZ / totalSegmentSz;
	}
	else
	{
		// Otherwise allocate the requested number of segments
		if ((totalSegmentSz * segmentCnt) <= DDR2_SZ) {
			totalNumSegments = segmentCnt;
		}
		else
		{
			// Not enough space to allocate that many segments
			printf("[ERROR] Cannot allocate %d x 0x%08x segments, exceeds DDR2 capacity!\r\n", (int)segmentCnt, (unsigned)totalSegmentSz);
			return XST_FAILURE;
		}
	}



	// Check there is enough space for BDs for requested number/size of segments
	if ( (totalNumSegments * segmentMultiplier * XLLDMA_BD_MINIMUM_ALIGNMENT) > LL_BD_SZ)
	{
		printf("[ERROR] Cannot allocate %d x x %d x 0x%08x segments, exceeds BD storage capacity!\r\n", (int)segmentCnt, (int)segmentMultiplier, (unsigned)totalSegmentSz);
		return XST_FAILURE;
	}

	printf("[DEBUG] Processing %d segments of 2*0x%08x bytes...\r\n", (unsigned)totalNumSegments, (unsigned)segmentSz);



	// Create BD rings of appropriate size
	/*
	 * topAsicRXBd
	 * botAsicRXBd
	 * TXBd
	 */
	// TODO: Give these better names... (hell give ALL the bd stuff better names...)
	u32 bdChunkSize =			XLLDMA_BD_MINIMUM_ALIGNMENT * totalNumSegments;
	u32 topAsicRXBdOffset =		LL_BD_BADDR;
	u32 botAsicRXBdOffset =		LL_BD_BADDR + bdChunkSize;
	u32 tenGigTXBdOffset =		LL_BD_BADDR + botAsicRXBdOffset + bdChunkSize;
	printf("[INFO ] BDs: TopASIC @ 0x%08x, Bottom ASIC @ 0x%08x, TenGig @ 0x%08x\r\n", (unsigned)topAsicRXBdOffset, (unsigned)botAsicRXBdOffset, (unsigned)tenGigTXBdOffset);

	status = XLlDma_BdRingCreate(pRingAsicTop, topAsicRXBdOffset, topAsicRXBdOffset, LL_DMA_ALIGNMENT, totalNumSegments);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create top ASIC RX BD ring!  Error code %d\r\n", status);
		return status;
	}

	status = XLlDma_BdRingCreate(pRingAsicBot, botAsicRXBdOffset, botAsicRXBdOffset, LL_DMA_ALIGNMENT, totalNumSegments);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create bottom ASIC RX BD ring!  Error code %d\r\n", status);
		return status;
	}

	// Note the TX ring is double the length of the RX rings!
	status = XLlDma_BdRingCreate(pRingTenGig, tenGigTXBdOffset, tenGigTXBdOffset, LL_DMA_ALIGNMENT, totalNumSegments*2);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Can't create 10GBE TX BD ring!  Error code %d\r\n", status);
		return status;
	}

	printf("[INFO ] Created %d BD rings OK!\r\n", (int)totalNumSegments);



	// Configure BDs in rings
	XLlDma_Bd *pTopRXBd;
	XLlDma_Bd *pBotRXBd;
	XLlDma_Bd *pTXBd;

	// First configure a master BD for each ring
	status = XLlDma_BdRingAlloc(pRingAsicTop, totalNumSegments, &pTopRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate top ASIC RX BD!\r\n");
		return status;
	}
	printf("[DEBUG] Top ASIC RX BD template: STS/CTRL=0x%08x, len=0x%08x\r\n", (unsigned)LL_STSCTRL_RX_BD, (unsigned)segmentSz);
	XLlDma_BdSetLength(*pTopRXBd, segmentSz);
	XLlDma_BdSetStsCtrl(*pTopRXBd, LL_STSCTRL_RX_BD);

	status = XLlDma_BdRingAlloc(pRingAsicBot, totalNumSegments, &pBotRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate bottom ASIC RX BD!\r\n");
		return status;
	}
	printf("[DEBUG] Bottom ASIC RX BD template: STS/CTRL=0x%08x, len=0x%08x\r\n", (unsigned)LL_STSCTRL_RX_BD, (unsigned)segmentSz);
	XLlDma_BdSetLength(*pBotRXBd, segmentSz);
	XLlDma_BdSetStsCtrl(*pBotRXBd, LL_STSCTRL_RX_BD);

	status = XLlDma_BdRingAlloc(pRingTenGig, totalNumSegments, &pTXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate tengig TX BD!\r\n");
		return status;
	}
	printf("[DEBUG] TenGig TX BD template: STS/CTRL=0x%08x, len=0x%08x\r\n", (unsigned)LL_STSCTRL_TX_BD, (unsigned)segmentSz);
	XLlDma_BdSetLength(*pTXBd, segmentSz);
	XLlDma_BdSetStsCtrl(*pTXBd, LL_STSCTRL_TX_BD);

	// Clone the master BD to all BDs in ring
	status = XLlDma_BdRingClone(pRingAsicTop, pTopRXBd);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Failed to clone master BD (Top ASIC ring)\r\n");
		return status;
	}
	status = XLlDma_BdRingClone(pRingAsicBot, pBotRXBd);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Failed to clone master BD (Bottom ASIC ring)\r\n");
		return status;
	}
	status = XLlDma_BdRingClone(pRingTenGig, pTXBd);
	if (status!=XST_SUCCESS)
	{
		print("[ERROR] Failed to clone master BD (TenGig ring)\r\n");
		return status;
	}



	// Update address field in every BD
	int i=0;
	u32 currentAddr = 0;
	// Snapshot pointer to first BDs
	XLlDma_Bd *pTopFirstBd = pTopRXBd;
	XLlDma_Bd *pBotFirstBd = pBotRXBd;
	XLlDma_Bd *pTenGigFirstBd = pTXBd;

	// RX rings
	for (i=0; i<totalNumSegments; i++)
	{
		XLlDma_BdSetBufAddr(*pTopRXBd, topAsicRXBdOffset + currentAddr);
		XLlDma_BdSetBufAddr(*pBotRXBd, botAsicRXBdOffset + currentAddr);

		currentAddr += segmentSz;

		pTopRXBd = XLlDma_BdRingNext(pRingAsicTop, pTopRXBd);
		pBotRXBd = XLlDma_BdRingNext(pRingAsicBot, pBotRXBd);
	}

	// TX ring
	currentAddr = 0;
	for (i=0; i<(totalNumSegments*2); i++)
	{
		XLlDma_BdSetBufAddr(*pTenGigFirstBd, topAsicRXBdOffset + currentAddr);
		pTenGigFirstBd = XLlDma_BdRingNext(pRingTenGig, pTenGigFirstBd);

		XLlDma_BdSetBufAddr(*pTenGigFirstBd, botAsicRXBdOffset + currentAddr);
		pTenGigFirstBd = XLlDma_BdRingNext(pRingTenGig, pTenGigFirstBd);

		currentAddr += segmentSz;
	}



	// Commit BD(s) to DMA engines
	status = XLlDma_BdRingToHw(pRingAsicTop, totalNumSegments, pTopFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send top ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}
	status = XLlDma_BdRingToHw(pRingAsicBot, totalNumSegments, pBotFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send bottom ASIC RX to HW, error code %d!\r\n", status);
		return status;
	}
	status = XLlDma_BdRingToHw(pRingTenGig, totalNumSegments, pTenGigFirstBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to send TenGig TX to HW, error code %d!\r\n", status);
		return status;
	}

	// Start RX engines, but not TX engine...
	// TODO: Do we want to do this here or leave to main event ring?
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



	// Everything OK!
	return XST_SUCCESS;
}
