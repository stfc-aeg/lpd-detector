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
const u32 kExcaliburAsicControlAddr    = 0x48000000;
const u32 kExcaliburAsicMuxSelect      = kExcaliburAsicControlAddr + 0;
const u32 kExcaliburAsicControlReg     = kExcaliburAsicControlAddr + 1;
const u32 kExcaliburAsicOmrBottom      = kExcaliburAsicControlAddr + 2;
const u32 kExcaliburAsicOmrTop         = kExcaliburAsicControlAddr + 3;
const u32 kExcaliburAsicCtrlState1     = kExcaliburAsicControlAddr + 17;
const u32 kExcaliburAsicDpmRdmaAddress = 0x50000000;

typedef enum
{
	unknownCommandExecute = -1,
	asicCommandWrite      = 0x23,
	asicCommandRead       = 0x25,
	asicPixelConfigLoad   = 0x2b

} asicControlCommand;

#endif /* EXCALIBURFEMRDMAADDRESSES_H_ */
