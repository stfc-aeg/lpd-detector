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

#define FPM_ID			1

enum personality_commands
{
	FPM_DACSCAN		= 1,
	FPM_GET_STATUS	= 20,
	FPM_GET_RESULT	= 21
};

enum personality_errors
{
	FPM_EXCALIBUR_NO_ERROR         = 0,
	FPM_EXCALIBUR_SETUP_FAILED,
	FPM_EXCALIBUR_DAC_LOAD_FAILED,
	FPM_IMAGE_ACQUIRE_FAILED,
};

const unsigned int kNumAsicsPerFem = 8;
const unsigned int kNumExcaliburDacs = 25;
const unsigned int kNumAsicDpmWords = 8;

// RDMA address
// TODO: these have top nibble tweaked to avoid MUX select 'feature'
#define ASIC_DPM_RDMA_ADDR 0x0A000000
#define ASIC_CONTROL_ADDR 0x09000000

const u32 kExcaliburAsicDpmRdmaAddress    = ASIC_DPM_RDMA_ADDR;
const u32 kExcaliburAsicControlAddr       = ASIC_CONTROL_ADDR;
const u32 kExcaliburAsicMuxSelect         = ASIC_CONTROL_ADDR + 0;
const u32 kExcaliburAsicControlReg        = ASIC_CONTROL_ADDR + 1;
const u32 kExcaliburAsicOmrBottom         = ASIC_CONTROL_ADDR + 2;
const u32 kExcaliburAsicOmrTop            = ASIC_CONTROL_ADDR + 3;
const u32 kExcaliburAsicConfig1Reg        = ASIC_CONTROL_ADDR + 4;
const u32 kExcaliburAsicShutter0Counter   = ASIC_CONTROL_ADDR + 6;
const u32 kExcaliburAsicShutter1Counter   = ASIC_CONTROL_ADDR + 7;
const u32 kExcaliburAsicFrameCounter      = ASIC_CONTROL_ADDR + 8;
const u32 kExcaliburAsicShutterResolution = ASIC_CONTROL_ADDR + 10;
const u32 kExcaliburAsicCtrlState1        = ASIC_CONTROL_ADDR + 17;

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
	u32        acquisitionTimeMs;
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

typedef struct
{
	u32 state;			//! Acquisition state
	u32 bufferCnt;		//! Number of buffers allocated
	u32 bufferSize;		//! Size of buffers
	u32 bufferDirty;	//! If non-zero a problem occurred last run and the buffers / engines need to be reconfigured
	u32 readPtr;		//! Read pointer
	u32 writePtr;		//! Write pointer
	u32 numAcq;			//! Number of acquisitions in this run
	u32 numConfigBds;	//! Number of configuration BDs set
	u32 totalRecvTop;	//! Total number of BDs received from top ASIC
	u32 totalRecvBot;	//! Total number of BDs received from bot ASIC
	u32 totalSent;		//! Total number of BDs sent to 10GBe block
	u32 totalErrors;	//! Total number of DMA errors (do we need to track for each channel?)
} acqStatus;

// DAQ scan
int prepareDACScan(u8 *pRxPayload);
void* doDACScanThread(void *pArg);
int setupScan(dacScanParams *scanParams);
int loadDacs(unsigned int iAsic, dacScanParams* scanParams);
int acquireImage(dacScanParams *scanParams);
int setOmr(alignedOmr omr);
unsigned int getNumImagesTransferred(void);

#endif /* FPM_EXCALIBUR_H_ */
