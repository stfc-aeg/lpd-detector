/*
 * Test PPC1 application
 *
 * Developed to test Xilinx mailbox and LLDMA engine functionality
 *
 */

// Todo list, in order of priority
// TODO: Store BDRings in array to remove duplicated code
// TODO: Abstract armAsicRX, armTenGigTX to a more generic function
// TODO: Complete event loop with mailbox/DMA
// TODO: Implement shared bram status flags
// TODO: Implement pixmem upload

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

// TODO: Move defines, function prototypes to header!
// Device Control Register (DCR) offsets for PPC DMA engine (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_ASIC_BOT		0x80							//! DCR offset for DMA0 (RX from bottom ASIC)
#define LL_DMA_BASE_PIXMEM			0x98							//! DCR offset for DMA1 (TX to pixel configuration memory)
#define LL_DMA_BASE_ASIC_TOP		0xB0							//! DCR offset for DMA2 (RX from top ASIC)
#define LL_DMA_BASE_TENGIG			0xC8							//! DCR offset for DMA3 (TX to 10GBE)

// DMA engine info
#define LL_DMA_ALIGNMENT			XLLDMA_BD_MINIMUM_ALIGNMENT		//! BD Alignment, set to minimum
#define LL_BD_BADDR					0x8D300000						//! Bass address for BDs (Top quarter of SRAM)
#define LL_BD_SZ					0x00100000						//! Size of BD memory region (1MB) (so total LL_BD_SZ / LL_DMA_ALIGNMENT BDs possible), in our case 16384
#define LL_STSCTRL_RX_OK			0x1D000000						//! STS/CTRL field in BD should be 0x1D when successfully RX (COMPLETE | SOP | EOP)
#define LL_STSCTRL_TX_OK			0x10000000						//! STS/CTRL field in BD should be 0x10 when successfully TX (COMPLETE)
#define LL_STSCTRL_RX_BD			0x0															//! STS/CTRL field for a RX BD
#define LL_STSCTRL_TX_BD			XLLDMA_BD_STSCTRL_SOP_MASK | XLLDMA_BD_STSCTRL_EOP_MASK		//! STS/CTRL field for a TX BD

// Buffer management
#define DDR2_BADDR					0x00000000						//! DDR2 base address
#define DDR2_SZ						0x40000000						//! DDR2 size (1GB)



// FUNCTION PROTOTYPES
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

    // Initialise DMA engines
    XLlDma dmaAsicTop, dmaAsicBot, dmaTenGig;

    XLlDma_BdRing *pRxTopAsicRing = &XLlDma_GetRxRing(&dmaAsicTop);
    XLlDma_BdRing *pRxBotAsicRing = &XLlDma_GetRxRing(&dmaAsicBot);
    XLlDma_BdRing *pTxTenGigRing = &XLlDma_GetTxRing(&dmaTenGig);

    XLlDma_Initialize(&dmaAsicTop, LL_DMA_BASE_ASIC_TOP);
    XLlDma_Initialize(&dmaAsicBot, LL_DMA_BASE_ASIC_BOT);
    XLlDma_Initialize(&dmaTenGig, LL_DMA_BASE_TENGIG);

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

    	// Blocking read of 3x 32bit word
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

					// Wait for data to be received
					XLlDma_Bd *pTopAsicBd, *pBotAsicBd, *pTenGigBd;
					unsigned numRxTop = 0;
					unsigned numRxBot = 0;
					unsigned numTx = 0;
					unsigned totalRx = 0;
					unsigned short done = 0;
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
							status = XLlDma_BdRingFree(pRxTopAsicRing, 1, pTopAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Failed to free RXed BD from top ASIC, error code %d\r\n.", status);
							}
							if (!(sts&0xFF000000)&LL_STSCTRL_RX_OK)
							{
								// NOTE: Even if code passes this check there can be no DMA transfer received :(
								printf("[ERROR] STS/CTRL field for top ASIC RX did not show successful completion!  STS/CTRL=0x%08x\r\n", (unsigned)sts);
								// TODO: Handle error
							}
							totalRx++;
						}

						if (numRxBot != 0 )
						{
							sts = (unsigned)XLlDma_BdGetStsCtrl(pBotAsicBd);
							addr = (unsigned)XLlDma_BdGetBufAddr(pBotAsicBd);
							printf("[INFO ] Got data from bottom ASIC. (%d BD(s), STS/CTRL=0x%08x, ADDR=0x%08x)\r\n", numRxBot, (unsigned)sts, (unsigned)addr);
							status = XLlDma_BdRingFree(pRxBotAsicRing, 1, pBotAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Failed to free RXed BD from bottom ASIC, error code %d\r\n.", status);
							}
							if (!(sts&0xFF000000)&LL_STSCTRL_RX_OK)
							{
								// NOTE: Even if code passes this check there can be no DMA transfer received :(
								printf("[ERROR] STS/CTRL field for bottom ASIC RX did not show successful completion!  STS/CTRL=0x%08x\r\n", (unsigned)sts);
								// TODO: Handle error
							}
							totalRx++;
						}

						// Original code, sends data to 10GBe but doesn't free RX BDs...
						/*
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
						*/

						// New code, use this for developing RX
						if (totalRx==2)
						{
							// Pretend here that we sent to TX!
							print("[DEBUG] Not sending to TX, but pretending we did...\r\n");

							// Re-alloc RX BDs into ring
							status = XLlDma_BdRingAlloc(pRxTopAsicRing, 1, &pTopAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Can't re-alloc top ASIC BD!  Error code %d\r\n", status);
							}
							status = XLlDma_BdRingAlloc(pRxBotAsicRing, 1, &pBotAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Can't re-alloc bottom ASIC BD!  Error code %d\r\n", status);
							}

							// Not sure if we need to but best to reset STS/CTRL fields on BDs!
							XLlDma_BdSetStsCtrl(*pBotAsicBd, LL_STSCTRL_RX_BD);
							XLlDma_BdSetStsCtrl(*pTopAsicBd, LL_STSCTRL_RX_BD);

							// Return RX BDs to hardware control
							status = XLlDma_BdRingToHw(pRxTopAsicRing, 1, pTopAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Can't re-assign top ASIC BD!  Error code %d\r\n", status);
							}
							status = XLlDma_BdRingToHw(pRxBotAsicRing, 1, pBotAsicBd);
							if (status!=XST_SUCCESS)
							{
								printf("[ERROR] Can't re-assign bottom ASIC BD!  Error code %d\r\n", status);
							}

							// All finished, flag complete
							done=1;
						}

						// This code is the template for checking TX status and then freeing it's BD.
						// Note it will need sts/ctrl resetting and then ToHw() as for RXes...
						/*
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
						*/

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
				printf("[ERROR] Upload command not yet implemented.\r\n");
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
		printf("[ERROR] Cannot allocate %d x x %d x 0x%08x buffers, exceeds BD storage capacity!\r\n", (int)segmentCnt, (int)segmentMultiplier, (unsigned)totalSegmentSz);
		return XST_FAILURE;
	}

	printf("[DEBUG] Requested %d buffers of 2 x 0x%08x bytes...\r\n", (unsigned)totalNumSegments, (unsigned)segmentSz);



	// Create BD rings of appropriate size
	/*
	 * topAsicRXBd
	 * botAsicRXBd
	 * TXBd
	 */
	// TODO: Give these better names... (hell give ALL the bd stuff better names...)
	u32 bdChunkSize =			XLLDMA_BD_MINIMUM_ALIGNMENT * totalNumSegments;
	u32 topAsicRXBdOffset =		LL_BD_BADDR;
	u32 botAsicRXBdOffset =		topAsicRXBdOffset + bdChunkSize;
	u32 tenGigTXBdOffset =		botAsicRXBdOffset + bdChunkSize;
	printf("[INFO ] BDs: \r\n");
	printf("[INFO ] TopASIC      0x%08x\r\n", (unsigned)topAsicRXBdOffset);
	printf("[INFO ] Bottom ASIC  0x%08x\r\n", (unsigned)botAsicRXBdOffset);
	printf("[INFO ] TenGig       0x%08x\r\n", (unsigned)tenGigTXBdOffset);

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

	printf("[INFO ] Created BD rings w/%d buffers each.\r\n", (int)totalNumSegments);



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
	//printf("[DEBUG] Top ASIC RX BD template: STS/CTRL=0x%08x, len=0x%08x\r\n", (unsigned)LL_STSCTRL_RX_BD, (unsigned)segmentSz);
	XLlDma_BdSetLength(*pTopRXBd, segmentSz);
	XLlDma_BdSetStsCtrl(*pTopRXBd, LL_STSCTRL_RX_BD);

	status = XLlDma_BdRingAlloc(pRingAsicBot, totalNumSegments, &pBotRXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate bottom ASIC RX BD!\r\n");
		return status;
	}
	//printf("[DEBUG] Bottom ASIC RX BD template: STS/CTRL=0x%08x, len=0x%08x\r\n", (unsigned)LL_STSCTRL_RX_BD, (unsigned)segmentSz);
	XLlDma_BdSetLength(*pBotRXBd, segmentSz);
	XLlDma_BdSetStsCtrl(*pBotRXBd, LL_STSCTRL_RX_BD);

	status = XLlDma_BdRingAlloc(pRingTenGig, totalNumSegments, &pTXBd);
	if (status!=XST_SUCCESS) {
		print ("[ERROR] Failed to allocate tengig TX BD!\r\n");
		return status;
	}
	//printf("[DEBUG] TenGig TX BD template: STS/CTRL=0x%08x, len=0x%08x\r\n", (unsigned)LL_STSCTRL_TX_BD, (unsigned)segmentSz);
	XLlDma_BdSetLength(*pTXBd, segmentSz);
	XLlDma_BdSetStsCtrl(*pTXBd, LL_STSCTRL_TX_BD);

	// TODO: Why do the Clone commands fail with XST_DMA_SG_LIST_ERROR?
	// 'if some of the BDs in this channel are under hardware or application control.' - but are not under hw/app control??
	/*
	// Clone the master BD to all BDs in ring
	status = XLlDma_BdRingClone(pRingAsicTop, pTopRXBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to clone master BD (Top ASIC ring), error code %d\r\n", (unsigned)status);
		return status;
	}
	status = XLlDma_BdRingClone(pRingAsicBot, pBotRXBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to clone master BD (Bottom ASIC ring), error code %d\r\n", (unsigned)status);
		return status;
	}
	status = XLlDma_BdRingClone(pRingTenGig, pTXBd);
	if (status!=XST_SUCCESS)
	{
		printf("[ERROR] Failed to clone master BD (TenGig ring), error code %d\r\n", (unsigned)status);
		return status;
	}
	*/



	// Update address field in every BD
	int i=0;
	//u32 currentAddr = DDR2_BADDR;
	// Snapshot pointer to first BDs
	XLlDma_Bd *pTopFirstBd = pTopRXBd;
	XLlDma_Bd *pBotFirstBd = pBotRXBd;
	XLlDma_Bd *pTenGigFirstBd = pTXBd;

	// TODO: Fix this dirty hack!
	// Again these addresses can cause the DMA engine to misbehave!  e.g.:
	// 0x8000000, 0x4000000 = OK! (as is 0)
	// 0x800000,  0x400000  = FAIL (first RX only gets bottomASIC, second topASIC, then repeats :( )
	u32 currentAddr = 0;
	u32 topAsicBufferAddress = 0x4000000;
	u32 botAsicBufferAddress = 0x8000000;

	// RX rings
	for (i=0; i<totalNumSegments; i++)
	{

		// Dummy (testing) buffer allocation (each ASIC gets a memory chunk)

		XLlDma_BdSetBufAddr(*pTopRXBd, topAsicBufferAddress + currentAddr);
		XLlDma_BdSetBufAddr(*pBotRXBd, botAsicBufferAddress + currentAddr);
		currentAddr += segmentSz;

		// Proper buffer allocation
		/*
		XLlDma_BdSetBufAddr(*pTopRXBd, currentAddr);
		currentAddr+=segmentSz;
		XLlDma_BdSetBufAddr(*pBotRXBd, currentAddr);
		currentAddr += segmentSz;
		*/

		// Because clone doesn't seem to work?
		XLlDma_BdSetLength(*pTopRXBd, segmentSz);
		XLlDma_BdSetLength(*pBotRXBd, segmentSz);
		XLlDma_BdSetStsCtrl(*pTopRXBd, LL_STSCTRL_RX_BD);
		XLlDma_BdSetStsCtrl(*pBotRXBd, LL_STSCTRL_RX_BD);

		//printf("[INFO ] TopASIC BD %d: addr=0x%08x, len=0x%08x, sts=0x%08x\r\n", i, (unsigned)(topAsicBufferAddress + currentAddr), (unsigned)segmentSz, (unsigned)LL_STSCTRL_RX_BD);

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



	// Commit RX BDs to DMA engines
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

	print("[INFO ] Committed BDs to HW and started DMA RX engines!\r\n");

	// Everything OK!
	return XST_SUCCESS;
}
