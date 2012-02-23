/*
 * Test PPC1 application
 *
 * Developed to test Xilinx mailbox and LLDMA engine functionality
 *
 */

// Todo list, in order of priority
// TODO: Implement mailbox messaging
// TODO: Implement RX/10GBE TX BdRings
// TODO: Complete event loop with mailbox/DMA
// TODO: Implement shared bram status flags
// TODO: Implement pixmem upload (base on armTenGigTx)

#include <stdio.h>
#include "xmbox.h"
#include "xparameters.h"
#include "platform.h"
#include "xlldma.h"

// Device Control Register (DCR) offsets for PPC DMA engine (See Xilinx UG200, chapter 13)
#define LL_DMA_BASE_ASIC_BOT		0x80	// dma0:rx <- Bottom ASIC
#define LL_DMA_BASE_PIXMEM			0x98	// dma1:tx -> pixel configuration memory
#define LL_DMA_BASE_ASIC_TOP		0xB0	// dma2:rx <- Top ASIC
#define LL_DMA_BASE_TENGIG			0xC8	// dma3:tx -> 10GBE

// BD Alignment, set to minimum
#define LL_DMA_ALIGNMENT			XLLDMA_BD_MINIMUM_ALIGNMENT

//#define LL_BD_BADDR					0x00000000	// Base address for BDs (Start of DDR2)
#define LL_BD_BADDR					0x8D300000	// Bass address for BDs (Top quarter of SRAM)
#define LL_TOP_ASIC_OFFSET			0x00002000	// Offset at which top ASIC BDs start, from LL_BD_BADDR (space for 128 BDs)
#define LL_BOT_ASIC_OFFSET			0x00004000	// Offset at which bottom ASIC BDs start, from LL_BD_BADDR (space for 128 BDs)
#define LL_TENGIG_OFFSET			0x00006000	// Offset at which 10G BDs start, from LL_BD_BADDR (space for 128 BDs)
#define LL_PIXMEM_OFFSET			0x00008000	// Offset at which pixel configuration memory BDs start, from LL_BD_BADDR (space for 128 BDs)

#define LL_STSCTRL_RX_OK			0x1D000000	// STS/CTRL field in BD should be 0x1D------ when successfully RX (COMPLETE | SOP | EOP)

// FUNCTION PROTOTYPES
// TODO: Move to header
int armAsicRX(XLlDma_BdRing *pRingAsicTop, XLlDma_BdRing *pRingAsicBot, u32 topAddr, u32 botAddr, unsigned int len, u32 sts);
int armTenGigTX(XLlDma_BdRing *pRingTenGig, u32 addr1, u32 addr2, unsigned int len);


// Pixel read data should be


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
    u32 mailboxBuffer[2] =	{0,0};		// RX buffer for mailbox
    u32 mailboxSentBytes = 	0;
    u32 topAsicAddr =		0x08000000;
    u32 botAsicAddr =		0x04000000;

    // Initialise DMA engines
    XLlDma dmaAsicTop, dmaAsicBot, dmaTenGig, dmaPixMem;

    XLlDma_BdRing *pRxTopAsicRing = &XLlDma_GetRxRing(&dmaAsicTop);
    XLlDma_BdRing *pRxBotAsicRing = &XLlDma_GetRxRing(&dmaAsicBot);
    XLlDma_BdRing *pTxTenGigRing = &XLlDma_GetTxRing(&dmaTenGig);
    XLlDma_BdRing *pTxPixMemRing = &XLlDma_GetTxRing(&dmaPixMem);

    XLlDma_Initialize(&dmaAsicTop, LL_DMA_BASE_ASIC_TOP);
    XLlDma_Initialize(&dmaAsicBot, LL_DMA_BASE_ASIC_BOT);
    XLlDma_Initialize(&dmaTenGig, LL_DMA_BASE_TENGIG);
    XLlDma_Initialize(&dmaPixMem, LL_DMA_BASE_PIXMEM);

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

    /*
    // **************** START Mailbox event loop **************************************************************************************************************
    print("[INFO ] Entering PPC1 mailbox event loop...\r\n");
    while(1)
    {

    	print("[INFO ] Waiting for mailbox message...\r\n");

    	// Blocking read of 2x 32bit words
    	XMbox_ReadBlocking(&mbox, &mailboxBuffer[0], 4);
    	printf("[INFO ] Got message!  numFrames=%d (0x%08x), frame size=%d (%08x)\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[1], (unsigned)mailboxBuffer[1]);



    } // END while
    // **************** END Mailbox event loop **************************************************************************************************************
	*/

    u32 topAddr, botAddr;

    // Enter mailbox-driven outer loop
    while(1)
    {
    	unsigned short acquireRunning = 0;
    	print("[INFO ] Waiting for mailbox message...\r\n");

    	// Blocking read of 1x 32bit word
    	XMbox_ReadBlocking(&mbox, &mailboxBuffer[0], 4);
    	printf("[INFO ] Got message!  cmd=%d (0x%08x)\r\n", (unsigned)mailboxBuffer[0], (unsigned)mailboxBuffer[0]);

    	switch (mailboxBuffer[0])
    	{

    	case 1:  // START_ACQUIRE
    		printf("[INFO ] Entering acquire DMA event loop\r\n");
    		acquireRunning = 1;
    	    while (acquireRunning)
    	    {

    	    	print ("\r\n");

    	    	// Arm RX engines for ASICs
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
    	    	XLlDma_Bd *pTopAsicBd, *pBotAsicBd;
    	    	unsigned numRxTop = 0;
    	    	unsigned numRxBot = 0;
    	    	unsigned totalRx = 0;
    	    	unsigned short done=0;
    	    	u32 sts;

    	    	print("[INFO ] Waiting for ASIC RX...\r\n");

    	    	// This is a very quick and dirty hacked up event loop
    	    	while(done==0)
    	    	{

    	    		numRxTop = XLlDma_BdRingFromHw(pRxTopAsicRing, 1, &pTopAsicBd);
    	    		numRxBot = XLlDma_BdRingFromHw(pRxBotAsicRing, 1, &pBotAsicBd);

    	    		if (numRxTop !=0 )
    	    		{
    	    			sts = (unsigned)XLlDma_BdGetStsCtrl(pTopAsicBd);
    	    			printf("[INFO ] Got data from top ASIC.    (%d BD(s), STS/CTRL=0x%08x)\r\n", numRxTop, (unsigned)sts);
    	    			if (!(sts&0xFF000000)&LL_STSCTRL_RX_OK)
    	    			{
    	    				// NOTE: Even if code passes this check there can be no DMA transfer received :(
    	    				print("[ERROR] STS/CTRL field for top ASIC RX did not show successful completion!\r\n");
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
    	    			printf("[INFO ] Got data from bottom ASIC. (%d BD(s), STS/CTRL=0x%08x)\r\n", numRxBot, (unsigned)sts);
    	    			status = XLlDma_BdRingFree(pRxBotAsicRing, 1, pBotAsicBd);
    	    			if (!(sts&0xFF000000)&LL_STSCTRL_RX_OK)
    	    			{
    	    				// NOTE: Even if code passes this check there can be no DMA transfer received :(
    	    				print("[ERROR] STS/CTRL field for bottom ASIC RX did not show successful completion!\r\n");
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
    	    	    	//status = armTenGigTX(pTxTenGigRing, topAsicAddr, botAsicAddr, 0x18000);
    	    	    	status = armTenGigTX(pTxTenGigRing, topAddr, botAddr, 0x18000);
    	    	    	if (status!=XST_SUCCESS)
    	    	    	{
    	    	    		printf("[ERROR] Failed to arm DMA engine for 10GBE send!  Error code %d\r\n", status);
    	    	    		print("[ERROR] Fatal error, terminating.\r\n");
    	    	    		return 0;
    	    	    	}
    	    			done=1;
    	    		}

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
    		printf("[INFO ] No doing anything with stop acquire cmd\r\n");
    		break;

    	case 3: // DO_UPLOAD
    		printf("[INFO ] Upload command not yet implemented\r\n");
    		break;

    	default:
    		printf("[ERROR] Unrecognised mailbox command %ld\r\n", mailboxBuffer[0]);
    		break;
    	}

    }

    // **************** START DMA event loop **************************************************************************************************************
    print("[INFO ] Entering PPC1 DMA event loop...\r\n");
    // **************** END DMA event loop **************************************************************************************************************

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
			addr = addr1;
		}
		else if (i==1)
		{
			addr = addr2;
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
