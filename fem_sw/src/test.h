/*
 * test.h
 *
 *  Created on: Aug 3, 2011
 *      Author: mt47
 */

#ifndef TEST_H_
#define TEST_H_

// TODO: Why do I need stdio include here, other files pick up from main.c OK??
#include "stdio.h"
#include "fem.h"
#include "xil_types.h"

// Test bits
#define TEST_BIT_EEPROM			(1<<0)
#define TEST_BIT_CONFIG			(1<<1)
#define TEST_BIT_SYSMON			(1<<2)
#define TEST_BIT_RDMA			(1<<3)
#define TEST_BIT_RAW			(1<<4)

int testThread(u8 bitmask);

#endif /* TEST_H_ */
