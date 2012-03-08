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

/* Debug routine, sends a single 32-bit word to PPC1
 * @param cmd data to send
 * @return number of sent bytes (should always be 4)
 */
int dummySend(int cmd)
{

	u32 data;
	u32 sentBytes = 0;
	data = (u32)cmd;

	XMbox_Write(&mbox, &data, 4, &sentBytes);

	return sentBytes;

}

/* Sends a configuration message to PPC1 to set up it's DMA rings
 * @param segment_sz size of segment to receive from *EACH I/O SPARTAN*
 * @param segment_cnt number of segments in capture
 * @return number of sent bytes (should always be 12)
 */
int bufferConfigMsgSend(u32 cmd, u32 segment_sz, u32 segment_cnt)
{
	u32 buf[3];
	u32 sentBytes = 0;

	buf[0] = cmd;			// CMD
	buf[1] = segment_sz;	// Segment size
	buf[2] = segment_cnt;	// Segment count

	XMbox_Write(&mbox, buf, 12, &sentBytes);

	return sentBytes;
}
