/*
 * FemClientAcquisition.h
 *
 *  Created on: 21 Jun 2012
 *      Author: tcn45
 */

#ifndef FEMCLIENTACQUISITION_H_
#define FEMCLIENTACQUISITION_H_

typedef enum
{
	acquireIdle = 0,
	acquireConfigBusy,
	acquireConfigNormal,
	acquireConfigUpload,
	acquireConfigStopping

} FemAcquireState;

typedef struct
{
	u32 acquireState;

} FemAcquireStatus;


#endif /* FEMCLIENTACQUISITION_H_ */
