/*
 * sysace.h
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
int deleteImage(unsigned int idx);
int writeImage(unsigned int idx);

void testCF(void);

int mySelfTest(XSysAce *pAce);

#endif /* SYSACE_H_ */
