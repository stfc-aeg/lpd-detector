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

// DAQ scan
int prepareDACScan(u8 *pRxPayload);
void* doDACScanThread(void *pArg);

#endif /* FPM_EXCALIBUR_H_ */
