/*
 * mailbox.h
 *
 *  Created on: Feb 22, 2012
 *      Author: mt47
 */

#include "xmbox.h"
#include "fem.h"

#ifndef MAILBOX_H_
#define MAILBOX_H_

int initMailbox(void);
int acquireConfigMsgSend(u32 cmd, u32 bufferSz, u32 bufferCnt, u32 numAcq, u32 mode, u32 coalesceCnt, int timeoutUs);
int acquireConfigAckReceive(void);

#endif /* MAILBOX_H_ */
