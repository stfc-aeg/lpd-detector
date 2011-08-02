/*
 * calib_sleep.h
 *
 * Header file for calibrated sleep functions replicating usleep available on PPC
 *
 *  Created on: Aug 2, 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef CALIB_TIMER_H_
#define CALIB_TIMER_H_

#include "xtmrctr.h"

int calibrateSleep(XTmrCtr* pTimer);

#ifdef __MICROBLAZE__
inline unsigned int usleep(unsigned int useconds);
#endif
#endif /* CALIB_TIMER_H_ */
