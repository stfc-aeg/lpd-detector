/*
 * calib_sleep.c
 *
 * Provides a calibrated sleep loop for MicroBlaze architecture and implements a usleep()
 * function as found on PowerPC. It requires the presence of an XPS timer core in the
 * design, which has already been initialised.  The calibrateSleep function MUST be called during
 * hardware initialisation and before xilkernel_init() sets the timer up as a down-counting
 * interval timer.
 *
 * WARNING: the sleep function is implemented and calibrated using a simple empty loop
 * function, which therefore assumes that any optimisation level set at compile time
 * will not unroll the loop!
 *
 *  Created on: Aug 2, 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "xmk.h"
#include "fem.h"
#include "stdio.h"
#include "xparameters.h"
#include "platform.h"
#include "platform_config.h"
#include "xtmrctr.h"
#include <string.h>
#include <stdio.h>

#define TIMER_UNIT 0

#ifdef __MICROBLAZE__

static double loopsPerUsec = 0;  // Loop calibration constant

int calibrateSleep_uBlaze(XTmrCtr* pTimer);
unsigned int usleep(unsigned int useconds);

#endif

/*
 * calibrateSleep - calibrates the sleep loop. This is a wrapper
 * function that has no effect except on MicroBlaze, where it calls
 * the specific calibration routine
 *
 * @param pTimer is a pointer to initialised XTmrCtr object
 * @return return code from specific routine or XST_SUCCESS
 */
int calibrateSleep(XTmrCtr* pTimer) {

	int retVal;
#ifdef __MICROBLAZE__
	retVal = calibrateSleep_uBlaze(pTimer);
#else
	retVal = XST_SUCCESS;
#endif

	return retVal;

}

#ifdef __MICROBLAZE__
/*
 * calibrateSleep_uBlaze - calibrates the sleep loop on MicroBlaze. This
 * is implemented by running empty loops (calling usleep with unity constant)
 * over a range of values and performing a least-squares linear fit to the
 * result, allowing the timer call overhead to be factored out. The resulting
 * calibration constant, in units of loops per usec, is stored in a static
 * variable subsequently used by usleep.
 *
 * @param pTimer is a pointer to initialised XTmrCtr timer object
 * @return return code indicating success or failer
 *
 * TODO: sanity check fit result to ensure sensible calibration
 */
int calibrateSleep_uBlaze(XTmrCtr* pTimer) {

	u32 timerValue1, timerValue2, deltaT;
	int timerLoops[] = {0, 1, 10, 100, 1000, 10000, 100000, -1};
	int timerPoint = 0;
	double s1, s2, s3, s4, denom, anum, bnum, slope, intercept;

	s1 = s2 = s3 = s4 = 0.0;

	DBGOUT("Calibrating sleep loop for MicroBlaze using timer ...");

	// Set calibration constant to unity for calibration calls of usleep
	loopsPerUsec = 1.0;

	// Iterate over defined loop lengths, calling usleep for each, wrapped in timers
	while (timerLoops[timerPoint] != -1) {

		// Start timer
		XTmrCtr_Start(pTimer, TIMER_UNIT);

		// Time the usleep call
		timerValue1 = XTmrCtr_GetValue(pTimer, TIMER_UNIT);
		usleep((unsigned int)timerLoops[timerPoint]);
		timerValue2 = XTmrCtr_GetValue(pTimer, TIMER_UNIT);

		deltaT = timerValue2 - timerValue1;

		// Stop and reset timer
		XTmrCtr_Stop(pTimer, TIMER_UNIT);
		XTmrCtr_Reset(pTimer, TIMER_UNIT);

		// Add result to running sums for fits
		s1 += (double)timerLoops[timerPoint];
		s2 += (double)timerLoops[timerPoint] * (double)timerLoops[timerPoint];
		s3 += (double)timerLoops[timerPoint] * (deltaT);
		s4 += (double)(deltaT);

		//DBGOUT("Point %d loop: %6d Ticks : %ld %ld %ld\r\n", timerPoint, timerLoops[timerPoint], timerValue1, timerValue2, (deltaT));
		timerPoint++;
	}

	// Calculate slope and intercept of loop times by linear least-squared fit
	denom = ((double)timerPoint * s2) - (s1 * s1);
	anum = (s2*s4) - (s1 * s3);
	bnum = ((double)timerPoint * s3) - (s1 * s4);

	intercept = anum / denom;
	slope = bnum / denom;

	// Calculate loops per microsecond and store in calibration constant, based on
	// canonical bus frequency timer runs at

	loopsPerUsec = ((double)(XPAR_PROC_BUS_0_FREQ_HZ)/1000000)/slope;

	DBGOUT(" OK (%d.%03d loops per us)\r\n", (int)loopsPerUsec, (int)((loopsPerUsec-(int)loopsPerUsec)*1000));

	return XST_SUCCESS;
}

/*
 * usleep - sleep for a number of microseconds
 *
 * This function replicates the usleep function available on PPC systems. The sleep
 * duration is achieved by running an empty loop for the calibrated duration
 *
 * @param useconds is number of microseconds to sleep for
 * @return always zero, like PPC usleep (!)
 */
unsigned int usleep(unsigned int useconds) {

	int loop, numLoops;

	// Calculate number of loops based on calibration constant
	numLoops = (int)((double)useconds * loopsPerUsec);

	// Run loop for neccessary duration
	for (loop = 0; loop < numLoops; loop++) {
		;
	}

	return 0;
}
#endif
