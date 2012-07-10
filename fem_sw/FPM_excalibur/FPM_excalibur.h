/*
 * FPM_excalibur.h
 *
 * Application specific functions for Excalibur FEM
 *
 */

#ifndef FPM_EXCALIBUR_H_
#define FPM_EXCALIBUR_H_

#include <stdlib.h>
#include <string.h>
#include "personality.h"
#include "xmk.h"
#include "pthread.h"
#include "rdma.h"

// TODO: Remove
#include "sleep.h"

enum personality_commands
{
	FPM_DACSCAN		= 1,
	FPM_GET_STATUS	= 20,
	FPM_GET_RESULT	= 21
};

// DAQ scan
int prepareDACScan(u8 *pRxPayload);
void* doDACScanThread(void *pArg);

#endif /* FPM_EXCALIBUR_H_ */
