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

const unsigned int kNumAsicsPerFem = 8;
const unsigned int kNumExcaliburDacs = 25;
const unsigned int kNumAsicDpmWords = 8;

// RDMA address
// TODO: these have top nibble tweaked to avoid MUX select 'feature'
#define ASIC_DPM_RDMA_ADDR 0xA0000000
#define ASIC_CONTROL_ADDR 0x90000000

const u32 kExcaliburAsicDpmRdmaAddress = ASIC_DPM_RDMA_ADDR;
const u32 kExcaliburAsicControlAddr    = ASIC_CONTROL_ADDR;
const u32 kExcaliburAsicMuxSelect      = ASIC_CONTROL_ADDR + 0;
const u32 kExcaliburAsicControlReg     = ASIC_CONTROL_ADDR + 1;
const u32 kExcaliburAsicOmrBottom      = ASIC_CONTROL_ADDR + 2;
const u32 kExcaliburAsicOmrTop         = ASIC_CONTROL_ADDR + 3;
const u32 kExcaliburAsicCtrlState1     = ASIC_CONTROL_ADDR + 17;

typedef struct
{
	u32 bottom;
	u32 top;
} alignedOmr;

typedef struct
{
	u32        scanDac;
	u32        dacStart;
	u32        dacStop;
	u32        dacStep;
	u32        dacCache[8][25];
	u32        asicMask;
	alignedOmr omrDacSet;
	alignedOmr omrAcquire;
	u32        executeCommand;
} dacScanParams;

typedef enum
{
	unknownDacId = -1,
	threshold0Dac = 0,
	threshold1Dac,
	threshold2Dac,
	threshold3Dac,
	threshold4Dac,
	threshold5Dac,
	threshold6Dac,
	threshold7Dac,
	preampDac,
	ikrumDac,
	shaperDac,
	discDac,
	discLsDac,
	thresholdNDac,
	dacPixelDac,
	delayDac,
	tpBufferInDac,
	tpBufferOutDac,
	rpzDac,
	gndDac,
	tpRefDac,
	fbkDac,
	casDac,
	tpRefADac,
	tpRefBDac,
	numExcaliburDacs
} mpx3Dac;

// DAQ scan
int prepareDACScan(u8 *pRxPayload);
void* doDACScanThread(void *pArg);
int loadDacs(unsigned int iAsic, dacScanParams* scanParams);
int setOmr(alignedOmr omr);

#endif /* FPM_EXCALIBUR_H_ */
