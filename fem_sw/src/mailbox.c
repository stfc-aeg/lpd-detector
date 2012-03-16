/*
 * mailbox.c
 *
 *  Created on: Feb 22, 2012
 *      Author: mt47
 */

#include "mailbox.h"

XMbox mbox;

/* Initialises intra-PPC mailbox
 * @return XST_SUCCESS on success, else XST_? on failure
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
