/**
 * @file calib_sleep.h
 * @author Tim Nicholls, STFC Application Engineering Group
 *
 * Header file for calibrated sleep functions replicating usleep available on PPC
 *
 */

#ifndef CALIB_TIMER_H_
#define CALIB_TIMER_H_

#include "xtmrctr.h"

int calibrateSleep(XTmrCtr* pTimer);

#ifdef __MICROBLAZE__
inline unsigned int usleep(unsigned int useconds);
#endif
#endif /* CALIB_TIMER_H_ */
