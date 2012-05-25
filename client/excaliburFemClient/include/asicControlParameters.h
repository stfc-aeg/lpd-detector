/*
 * asicControlParameters.h - addresses, settings & parameters for
 * the EXCALIBUR FEM ASIC control firmware block
 *
 *  Created on: Mar 21, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef EXCALIBURFEMRDMAADDRESSES_H_
#define EXCALIBURFEMRDMAADDRESSES_H_

#include "dataTypes.h"

// RDMA address of the ASIC control block and its registers
const u32 kExcaliburAsicControlAddr       = 0x48000000;
const u32 kExcaliburAsicMuxSelect         = kExcaliburAsicControlAddr + 0;
const u32 kExcaliburAsicControlReg        = kExcaliburAsicControlAddr + 1;
const u32 kExcaliburAsicOmrBottom         = kExcaliburAsicControlAddr + 2;
const u32 kExcaliburAsicOmrTop            = kExcaliburAsicControlAddr + 3;
const u32 kExcaliburAsicShutter0Counter   = kExcaliburAsicControlAddr + 6;
const u32 kExcaliburAsicShutter1Counter   = kExcaliburAsicControlAddr + 7;
const u32 kExcaliburAsicFrameCounter      = kExcaliburAsicControlAddr + 8;
const u32 kExcaliburAsicPixelCounterDepth = kExcaliburAsicControlAddr + 9;
const u32 kExcaliburAsicShutterResolution = kExcaliburAsicControlAddr + 10;
const u32 kExcaliburAsicReadoutLength     = kExcaliburAsicControlAddr + 11;
const u32 kExcaliburAsicCtrlState1        = kExcaliburAsicControlAddr + 17;

const u32 kExcaliburAsicDpmRdmaAddress    = 0x50000000;

typedef enum
{
	unknownCommandExecute = -1,
	asicCommandWrite      = 0x23,
	asicCommandRead       = 0x25,
	asicPixelConfigLoad   = 0x2b,
	asicRunSequentialC0   = 0xa41,

} asicControlCommand;

typedef enum
{
	unknownMode        = -1,
	reorderedDataMode  = 0,
	rawDataMode        = 1

} asicDataReorderMode;

#endif /* EXCALIBURFEMRDMAADDRESSES_H_ */
