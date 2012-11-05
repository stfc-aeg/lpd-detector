/**
 * @file rdma.h
 *
 * Provides access RDMA endpoints via an internal RS232 UART
 *
 */

#include "xil_types.h"
#include "xparameters.h"
#include "fem.h"
#include <stdio.h>
#ifdef HW_PLATFORM_DEVBOARD
#include "xuartlite_l.h"
#include "xstatus.h"
#else
#include "xuartns550.h"
#include "xgpio.h"
#endif

#ifndef RDMA2_H_
#define RDMA2_H_

// Commands for RDMA block
#define RDMA_CMD_READ			0			//!< RDMA command for read operation (issued as first byte to RDMA channel)
#define RDMA_CMD_WRITE			1			//!< RDMA command for write operation (issued as first byte to RDMA channel)

// Serial settings for RDMA block
#define RDMA_DEF_BAUDRATE		9600						//!< RDMA / RS232 controller default baudrate, probably not needed!
#define RDMA_BAUDRATE			115200						//!< RDMA / RS232 controller baudrate (must match firmware!)
#define RDMA_DATABITS			XUN_FORMAT_8_BITS			//!< RDMA / RS232 databits, always 8
#define RDMA_PARITY				XUN_FORMAT_NO_PARITY		//!< RDMA / RS232 parity, always no parity
#define RDMA_STOPBITS			XUN_FORMAT_1_STOP_BIT		//!< RDMA / RS232 stop bits, always 1

#define RDMA_SELFTEST_REG		1							//!< RDMA register to use for readback self test

#define RDMA_MAX_RETRIES		1000						//!< Number of retries before UART gives up trying to complete an RDMA command

//! Timeout check macro used in read/write functions
#define RDMA_CHECK_TIMEOUT(n)	if (n==RDMA_MAX_RETRIES) { return XST_FAILURE; }

int initRdma(void);
int rdmaSelftest(void);
int readRdma(u32 addr, u32 *pVal);
int writeRdma(u32 addr, u32 value);
void setMux(u32 *pAddr);

#endif /* RDMA2_H_ */
