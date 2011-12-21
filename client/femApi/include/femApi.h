/*
 * femapi.h
 *
 *  Created on: 2 Feb 2011
 *      Author: fgz73762
 */

/* This file defines the API of the library that is used to communicate with the FEM hardware */

#ifndef FEMAPI_H_
#define FEMAPI_H_

#include "string.h"
#include "time.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Image dimension constants
 */
#define FEM_PIXELS_PER_CHIP_X 256
#define FEM_PIXELS_PER_CHIP_Y 256
#define FEM_CHIPS_PER_BLOCK_X 4
#define FEM_BLOCKS_PER_STRIPE_X 2
#define FEM_CHIPS_PER_STRIPE_X 8
#define FEM_CHIPS_PER_STRIPE_Y 1
#define FEM_STRIPES_PER_MODULE 2
#define FEM_STRIPES_PER_IMAGE 6
#define FEM_CHIP_GAP_PIXELS_X 3
#define FEM_CHIP_GAP_PIXELS_Y_LARGE 125
#define FEM_CHIP_GAP_PIXELS_Y_SMALL 3
#define FEM_PIXELS_PER_STRIPE_X ((FEM_PIXELS_PER_CHIP_X+FEM_CHIP_GAP_PIXELS_X)*FEM_CHIPS_PER_STRIPE_X-FEM_CHIP_GAP_PIXELS_X)
#define FEM_TOTAL_PIXELS_Y (FEM_PIXELS_PER_CHIP_Y*FEM_CHIPS_PER_STRIPE_Y*FEM_STRIPES_PER_IMAGE +\
		(FEM_STRIPES_PER_IMAGE/2-1)*FEM_CHIP_GAP_PIXELS_Y_LARGE +\
		(FEM_STRIPES_PER_IMAGE/2)*FEM_CHIP_GAP_PIXELS_Y_SMALL)
#define FEM_TOTAL_PIXELS_X FEM_PIXELS_PER_STRIPE_X

/*
 * Edge pixel ratio (Note: don't put parentheses around this so that integer arithmetic works).
 */
#define FEM_EDGE_PIXEL_RATIO_NUM 2
#define FEM_EDGE_PIXEL_RATIO_DEN 5
#define FEM_EDGE_PIXEL_RATIO 2/5

/*
 * Bits per pixel constants
 */
#define FEM_BITS_PER_PIXEL_1 0
#define FEM_BITS_PER_PIXEL_4 1
#define FEM_BITS_PER_PIXEL_12 2
#define FEM_BITS_PER_PIXEL_24 3

/* The frame buffer structure.  These are used to carry frame pixels and their
 * associated metadata.
 */
typedef struct CtlFrame
{
    void* buffer;
    size_t bufferLength;
    unsigned int sizeX;
    unsigned int sizeY;
    unsigned int sizeZ;
    int bitsPerPixel;
    time_t timeStamp;
    void* internalArray;
    struct CtlFrame* internalNext;
    int referenceCount;
} CtlFrame;

/* A structure used to pass the call back functions to the library by
 * the femInitialise function.
 */
typedef struct CtlCallbacks
{
    CtlFrame* (*ctlAllocate)(void* ctlHandle);
    void (*ctlFree)(void* ctlHandle, CtlFrame* buffer);
    void (*ctlReceive)(void* ctlHandle, CtlFrame* buffer);
    void (*ctlSignal)(void* ctlHandle, int id);
    void (*ctlReserve)(void* ctlHandle, CtlFrame* buffer);
} CtlCallbacks;

/* A structure that contains fem configuration data.
 */
typedef struct CtlConfig
{
    int femNumber;
    const char* femAddress;
    int femPort;
} CtlConfig;

/* The functions provided by the library.
 */
void* femInitialise(void* ctlHandle, const CtlCallbacks* callBacks, const CtlConfig* config);
int femSetInt(void* femHandle, int chipId, int id, size_t size, int* value);
int femSetShort(void* femHandle, int chipId, int id, size_t size, short* value);
int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value);
int femGetShort(void* femHandle, int chipId, int id, size_t size, short* value);
int femCmd(void* femHandle, int chipId, int id);
void femClose(void* femHandle);

/* An identifier that indicates 'all chips'.
 */
#define FEM_CHIP_ALL 0

/* The return codes used by various functions.
 */
#define FEM_RTN_OK 0
#define FEM_RTN_UNKNOWNOPID 1
#define FEM_RTN_ILLEGALCHIP 2
#define FEM_RTN_BADSIZE 3

/* The operation identifiers for the get, set, cmd and signal functions.
 */
/* Commands */
#define FEM_OP_STARTACQUISITION 1
#define FEM_OP_STOPACQUISITION 2
#define FEM_OP_LOADPIXELCONFIG 3
#define FEM_OP_FREEALLFRAMES 4
/* Medipix III global registers */
#define FEM_OP_MPXIII_COLOURMODE 1000
#define FEM_OP_MPXIII_COUNTERDEPTH 1001
/* Medipix III per chip registers */
#define FEM_OP_MPXIII_DACSENSE 2000
#define FEM_OP_MPXIII_DACEXTERNAL 2001
#define FEM_OP_MPXIII_THRESHOLD0DAC 2002
#define FEM_OP_MPXIII_THRESHOLD1DAC 2003
#define FEM_OP_MPXIII_THRESHOLD2DAC 2004
#define FEM_OP_MPXIII_THRESHOLD3DAC 2005
#define FEM_OP_MPXIII_THRESHOLD4DAC 2006
#define FEM_OP_MPXIII_THRESHOLD5DAC 2007
#define FEM_OP_MPXIII_THRESHOLD6DAC 2008
#define FEM_OP_MPXIII_THRESHOLD7DAC 2009
#define FEM_OP_MPXIII_PREAMPDAC 2010
#define FEM_OP_MPXIII_IKRUMDAC 2011
#define FEM_OP_MPXIII_SHAPERDAC 2012
#define FEM_OP_MPXIII_DISCDAC 2013
#define FEM_OP_MPXIII_DISCLSDAC 2014
#define FEM_OP_MPXIII_THRESHOLDNDAC 2015
#define FEM_OP_MPXIII_DACPIXELDAC 2016
#define FEM_OP_MPXIII_DELAYDAC 2017
#define FEM_OP_MPXIII_TPBUFFERINDAC 2018
#define FEM_OP_MPXIII_TPBUFFEROUTDAC 2019
#define FEM_OP_MPXIII_RPZDAC 2020
#define FEM_OP_MPXIII_GNDDAC 2021
#define FEM_OP_MPXIII_TPREFDAC 2022
#define FEM_OP_MPXIII_FBKDAC 2023
#define FEM_OP_MPXIII_CASDAC 2024
#define FEM_OP_MPXIII_TPREFADAC 2025
#define FEM_OP_MPXIII_TPREFBDAC 2026
/* Medipix III per pixel registers */
#define FEM_OP_MPXIII_PIXELMASK 3000
#define FEM_OP_MPXIII_PIXELTHRESHOLDA 3001
#define FEM_OP_MPXIII_PIXELTHRESHOLDB 3002
#define FEM_OP_MPXIII_PIXELGAINMODE 3003
#define FEM_OP_MPXIII_PIXELTEST 3004
/* Ids 4000..4999 are FEM registers */
#define FEM_OP_NUMFRAMESTOACQUIRE 4000
#define FEM_OP_ACQUISITIONTIME 4001
#define FEM_OP_ACQUISITIONPERIOD 4002
/* Ids 5000..5999 are signals */
#define FEM_OP_ACQUISITIONCOMPLETE 5000

#ifdef __cplusplus
}  /* Closing brace for extern "C" */
#endif

#endif /* FEMAPI_H_ */
