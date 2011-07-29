/*
 * rs232_rdma.h
 *
 * Provides access to ESDG group FPGA blocks via
 * RS232-RDMA link
 *
 */

#include "xil_types.h"
#include "xuartlite_l.h"
#include "xtmrctr.h"
#include "profile.h"

#ifndef RS232_RDMA_H_
#define RS232_RDMA_H_

#define RDMA_CMD_READ			0
#define RDMA_CMD_WRITE			1

u32 readRdma(u32 base, u32 addr, XTmrCtr* pTmr, struct profiling_results* pRes);
void writeRdma(u32 base, u32 addr, u32 value, XTmrCtr* pTmr, struct profiling_results* pRes);

#endif /* RS232_RDMA_H_ */
