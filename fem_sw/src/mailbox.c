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
 * @param bufferSz size of segment to receive from *EACH I/O SPARTAN*
 * @param bufferCnt number of segments in capture
 * @param numAcq number of acquisitions
 * @param mode
 * @return number of sent bytes (should always be 20)
 */
// TODO: Merge cmd/mode fields into single u32?
int acquireConfigMsgSend(u32 cmd, u32 bufferSz, u32 bufferCnt, u32 numAcq, u32 mode)
{
	u32 buf[5];
	u32 sentBytes = 0;

	buf[0] = cmd;
	buf[1] = bufferSz;
	buf[2] = bufferCnt;
	buf[3] = numAcq;
	buf[4] = mode;

	XMbox_Write(&mbox, buf, 20, &sentBytes);

	return sentBytes;
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
	u32 countMax = 1000;

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
