/*
 * mailbox.c
 *
 *  Created on: Feb 22, 2012
 *      Author: mt47
 */

#include "mailbox.h"

XMbox mbox;

/* Initialises intra-PPC mailbox
 *
 * @return XST_SUCCESS on success, or XST_nnn on failure
 */
int initMailbox(void)
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
 * @param coalesceCnt number of RX BDs to process per event cycle of main event loop
 *
 * @return 1 for ACK, 0 for NACK of command by PPC1, -1 on mailbox error
 */
// TODO: Pass pointer to protocol_acq_config instead of parameters?
// TODO: Move msgSize, message structure to common include
#define CMD_ACQ_CONFIG 1	// TODO: Remove this declare and use fem_common.h
int acquireConfigMsgSend(u32 cmd, u32 bufferSz, u32 bufferCnt, u32 numAcq, u32 mode, u32 coalesceCnt, int maxRetries)
{
	u32 buf[6];
	u32 sentBytes = 0;
	u32 msgSize = 24;		// TODO: Set to X + sizeof(protocol_acq_config)

	u32 status;
	int numRetries = 0;

	buf[0] = cmd;
	buf[1] = bufferSz;
	buf[2] = bufferCnt;
	buf[3] = numAcq;
	buf[4] = mode;
	buf[5] = coalesceCnt;

	int tick = 100;

	// Send to PPC1
	XMbox_Write(&mbox, buf, msgSize, &sentBytes);

	if (sentBytes!=msgSize) { return -1; }	// Trap mailbox errors

	// If it's a config. request, send response immediately because configuring takes a long time
	if(cmd==CMD_ACQ_CONFIG)
	{
		return 1;
	}


	while(numRetries < maxRetries)
	{
		status = XMbox_Read(&mbox, buf, 4, &sentBytes);
		if (status == XST_SUCCESS)
		{
			// Got message!
			if (buf[0])
			{
				return 1;
			}
			else
			{
				return 0;
			}

		} else {
			// No message, wait a bit
			usleep(tick);
			numRetries++;
		}
	}

	// Timed out, so NACK
	// TODO: Another return code, -1 for timeout?
	return -1;

}


/* Receives a confirmation message from PPC1 to confirm that it
 * is processing a config request (NOT that it has finished doing so!)
 *
 * @return 1 if PPC1 confirms request or 0 if no message received before timeout.  -1 on error.
 */
int acquireConfigAckReceive(void)
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
		// Timed out or an error occured
		return -1;
	}
}
