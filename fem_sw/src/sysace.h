/**
 * @file sysace.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * Wrapper for SystemACE functionality
 *
 */

#ifndef SYSACE_H_
#define SYSACE_H_

#include "fem.h"
#include "xsysace.h"
#include "sysace_stdio.h"

void reloadChain(XSysAce *pAce, unsigned int idx);
int writeImage(unsigned int idx, u32 addr, u32 len);
int mySelfTest(XSysAce *pAce);

#endif /* SYSACE_H_ */
