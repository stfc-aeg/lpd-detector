/**
 * @file mailbox.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * Wrapper for Xilinx mailbox functions, used to provide inter-PPC communications.
 *
 */

#include "xmbox.h"
#include "fem.h"

#ifndef MAILBOX_H_
#define MAILBOX_H_

#define MBOX_ACK_LOOP_MAX		50000		//!< Maximum number of loops to wait for an ACK

int initMailbox(void);
int acquireConfigMsgSend(u32 cmd, u32 bufferSz, u32 bufferCnt, u32 numAcq, u32 mode, u32 coalesceCnt, int timeoutUs);
int acquireConfigAckReceive(void);

#endif /* MAILBOX_H_ */
