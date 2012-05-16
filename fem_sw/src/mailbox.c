/*
 * mailbox.c
 *
 *  Created on: Feb 22, 2012
 *      Author: mt47
 */

#include "mailbox.h"

XMbox mbox;

/* Initialises intra-PPC mailbox
 * @return XST_SUCCESS on success, or XST_nnn on failure
 */
int initMailbox()
{
	int status;

    XMbox_Config mboxCfg;
    mboxCfg.BaseAddress =	BADDR_MBOX;
    mboxCfg.DeviceId =		MBOX_ID;
    mboxCfg.RecvID =		MBOX_RECV_ID;
    mboxCfg.SendID =		MBOX_SEND_ID;
    mboxCfg.UseFSL =		MBOX_USE_FSL;

    status = XMbox_CfgInitialize(&mbox, &mboxCfg, BADDR_MBOX);
    if (status!=XST_SUCCESS) { return status; }
    status = XMbox_Flush(&mbox);
    return status;
}

/* Sends a configuration message to PPC1 to configure it for acquisition
 * This call will block until it receives a response from PPC1, unless
 * @param bufferSz size of segment to receive from *EACH I/O SPARTAN*
 * @param bufferCnt number of segments in capture
 * @param numAcq number of acquisitions
 * @param mode
 * @return 1 for ACK, 0 for NACK of command by PPC1, -1 on mailbox error
 */
// TODO: Merge cmd/mode fields into single u32?
// TODO: Move msgSize, message structure to common include
// TODO: DO NOT HARDCODE CMD_ACQ_CONFIG!  MOVE TO COMMON HEADER
#define CMD_ACQ_CONFIG 1
int acquireConfigMsgSend(u32 cmd, u32 bufferSz, u32 bufferCnt, u32 numAcq, u32 mode)
{
	u32 buf[5];
	u32 sentBytes = 0;
	u32 msgSize = 20;

	buf[0] = cmd;
	buf[1] = bufferSz;
	buf[2] = bufferCnt;
	buf[3] = numAcq;
	buf[4] = mode;

	// Send to PPC1
	XMbox_Write(&mbox, buf, msgSize, &sentBytes);

	if (sentBytes!=msgSize) { return -1; }	// Trap mailbox errors

	// If it's a config. request, send response immediately because configuring takes a long time
	if(cmd==CMD_ACQ_CONFIG)
	{
		return 1;
	}

	// Wait for response from PPC1
	XMbox_ReadBlocking(&mbox, buf, 4);		// Just 4 bytes, no sense using more
	if (buf[0])
	{
		// ACK
		return 1;
	}
	else
	{
		// NACK
		return 0;
	}

}

/* Receives a confirmation message from PPC1 to confirm that it
 * is processing a config request (NOT that it has finished doing so!)
 * @return 1 if PPC1 confirms request or 0 if no message received before timeout
 */
unsigned short acquireConfigAckReceive(void)
{
	u32 buf;		// Smallest possible message, has to be 4-byte aligned
	u32 recBytes;
	int status = XST_NO_DATA;
	u32 count = 0;
	u32 countMax = 10000;

	while (count<countMax && status==XST_NO_DATA)
	{
		status = XMbox_Read(&mbox, &buf, 4, &recBytes);
		count++;
	}

	if (status==XST_SUCCESS)
	{
		if (buf==0xA5A5FACE)	// TODO: Make constant, put in header
		{
			return 1;
		}
		else
		{
			return 0;
		}

	}
	else
	{
		return 0;
	}
}
