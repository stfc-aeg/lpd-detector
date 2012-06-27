/*
 * rdma.h
 *
 * Provides access to ESDG group FPGA blocks via
 * RS232-RDMA link register set
 *
 * Only compatible with 16550 UART
 *
 */

#include "xil_types.h"
#include "xparameters.h"
#include "fem.h"
#ifdef HW_PLATFORM_DEVBOARD
#include "xuartlite_l.h"
#include "xstatus.h"
#else
#include "xuartns550.h"
#endif

#ifndef RDMA2_H_
#define RDMA2_H_

// Commands for RDMA block
#define RDMA_CMD_READ			0
#define RDMA_CMD_WRITE			1

// Serial settings for RDMA block
#define RDMA_DEF_BAUDRATE		9600						// Probably not needed!
#define RDMA_BAUDRATE			9600
#define RDMA_DATABITS			XUN_FORMAT_8_BITS
#define RDMA_PARITY				XUN_FORMAT_NO_PARITY
#define RDMA_STOPBITS			XUN_FORMAT_1_STOP_BIT

// Register to use for readback self test
#define RDMA_SELFTEST_REG		1

// Maximum number of retries before UART gives up
#define RDMA_MAX_RETRIES		1000

// Timeout check macro used in read/write functions
#define RDMA_CHECK_TIMEOUT(n)	if (n==RDMA_MAX_RETRIES) { return XST_FAILURE; }

int initRdma(void);
int rdmaSelftest(void);
int readRdma(u32 addr, u32 *pVal);
int writeRdma(u32 addr, u32 value);

#endif /* RDMA2_H_ */
