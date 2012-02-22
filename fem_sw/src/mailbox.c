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
