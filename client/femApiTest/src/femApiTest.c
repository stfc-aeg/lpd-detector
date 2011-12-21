/*
 * femApiTest.c
 *
 *  Created on: 2 Dec 2011
 *      Author: tcn
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "femApi.h"

// Forward declaration of functions
int testGetSetInt(void* femHandle);
int testGetSetShort(void* femHandle);
int testCommand(void* femHandle);
int testAcquisitionLoop(void* femHandle);

// Forward declaration of callback functions to simulate WP5 callbacks
static CtlFrame* allocateCallback(void* ctlHandle);
static void      freeCallback(void* ctlHandle, CtlFrame* buffer);
static void      receiveCallback(void* ctlHandle, CtlFrame* buffer);
static void      signalCallback(void* ctlHandle, int id);

int acquiring = 0;

int main(int argc, char* argv[]) {

	void* femHandle = 0;
	int numPassed = 0;

	if (argc != 3)
	{
		printf("Usage: femApiTest <host> <port>\n");
		return 1;
	}

	printf("Connecting to FEM at IP address %s port %s ... ", argv[1], argv[2]);

	// Create a config structure to pass to the FEM client
	CtlConfig femConfig;
	femConfig.femAddress = argv[1];
	femConfig.femPort = atoi(argv[2]);

	// Create a callback structure to pass to the FEM client
	CtlCallbacks femCallbacks;
	femCallbacks.ctlAllocate = &allocateCallback;
	femCallbacks.ctlFree     = &freeCallback;
	femCallbacks.ctlReceive  = &receiveCallback;
	femCallbacks.ctlSignal   = &signalCallback;

	// Initialise the FEM
	femHandle = femInitialise(0, &femCallbacks, &femConfig);

	// femHandle will return NULL if the initialisation failed
	if (femHandle == NULL) {
		return 1;
	}
	printf("done\n");

	// Run the tests
	numPassed += testGetSetInt(femHandle);
	numPassed += testGetSetShort(femHandle);
	numPassed += testCommand(femHandle);
	numPassed += testAcquisitionLoop(femHandle);

	printf("Hit return to quit ... ");
	getchar();

	femClose(femHandle);
	return 0;
}

int testGetSetInt(void* femHandle)
{

	int rc, i;
	int passed = 1;
	int numVals = 2;

	printf("Write & read back long values from FEM ... ");

	// Write a a set of long integer values to the FEM
	int setInt[] = { 0x01234567, 0x89ABCDEF };
	rc = femSetInt(femHandle, 1, 1, numVals, setInt);
	if (rc != FEM_RTN_OK) {
		printf("Got error on calling femSetInt(): %d\n", rc);
		passed = 0;
	}

	// Read the values back
	int getInt[] = { -1, -1 };
	rc = femGetInt(femHandle, 1, 1, numVals, getInt);
	if (rc != FEM_RTN_OK) {
		printf("Got error on calling femGetInt(): %d\n", rc);
		passed = 0;
	}

	// Check the two agree
	for (i =  0; i < numVals; i++) {
		if (setInt[i] != getInt[i]) {
			printf("Error, set a value of %d at index %d, read the value back as %d\n", setInt[i], i, getInt[i]);
			passed = 0;
		}
	}

	printf("%s\n", passed ? "passed" : "failed");
	return passed;
}

int testGetSetShort(void* femHandle)
{
	int rc, i;
	int passed = 1;
	int numVals = 2;

	printf("Write & read back short values from FEM ... ");

	// Write a set of short values to the FEM
	short setShort[] = { 0xdead, 0xd00f };
	rc = femSetShort(femHandle, 1, 1, numVals, setShort);
	if (rc != FEM_RTN_OK) {
		printf("Got error on calling femSetShort(): %d\n", rc);
	}

	// Read the values back
	short getShort[] = { -1, -1 };
	rc = femGetShort(femHandle, 1, 1, numVals, getShort);
	if (rc != FEM_RTN_OK) {
		printf("Got error on calling femGetShort(): %d\n", rc);
	}

	// Check the two agree
	for (i =  0; i < numVals; i++) {
		if (setShort[i] != getShort[i]) {
			printf("Error, set a value of %d at index %d, read the value back as %d\n", (unsigned short)setShort[i], i, (unsigned short)getShort[i]);
			passed = 0;
		}
	}
	printf("%s\n", passed ? "passed" : "failed");

	return passed;
}

int testCommand(void* femHandle)
{
	int rc;
	int passed = 1;

	printf("Sending command to FEM ... ");

	rc = femCmd(femHandle, 0, FEM_OP_LOADPIXELCONFIG);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on calling femCmd(): %d\n", rc);
		passed = 0;
	}
	printf("%s\n", passed ? "passed" : "failed");

	return passed;
}

int testAcquisitionLoop(void* femHandle)
{

	int rc;
	int passed = 1;

	acquiring = 1;

	printf("Sending num frames to FEM...");
	unsigned int numFrames = 100;
	rc = femSetInt(femHandle, 0, FEM_OP_NUMFRAMESTOACQUIRE, sizeof(numFrames), (int*)&numFrames);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on setting number of frames: %d'n", rc);
		passed = 0;
	}

	printf("done.\nSending acq period to FEM...");
	unsigned int acqPeriodMs = 10;
	rc = femSetInt(femHandle, 0, FEM_OP_ACQUISITIONPERIOD, sizeof(acqPeriodMs), (int*)&acqPeriodMs);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on setting acq period: %d'n", rc);
		passed = 0;
	}

	printf("done.\nSending acq time frames to FEM...");
	unsigned int acqTimeMs = 10;
	rc = femSetInt(femHandle, 0, FEM_OP_ACQUISITIONTIME, sizeof(acqTimeMs), (int*)&acqTimeMs);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on setting acq time: %d'n", rc);
		passed = 0;
	}


	printf("done.\nSending start acquisition to FEM... ");
	rc = femCmd(femHandle, 0, FEM_OP_STARTACQUISITION);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on calling femCmd(): %d'n", rc);
		passed = 0;
	}

	printf("Waiting for acquisition to complete ...");
	do
	{
		usleep(10000);
	}
	while (acquiring);


//	printf("done.\nPress return to stop acquisition...");
//	getchar();

	printf("Sending stop acquisition to FEM... ");
	rc = femCmd(femHandle, 0, FEM_OP_STOPACQUISITION);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on calling femCmd(FEM_OP_STOPACQUISITION): %d'n", rc);
		passed = 0;
	}
	printf("done.\n");

	return passed;

}

CtlFrame* allocateCallback(void* ctlHandle)
{
	printf("In allocateCallback\n");
	CtlFrame* allocFrame = malloc(sizeof(CtlFrame));
	if (allocFrame != 0) {
		allocFrame->sizeX = 512;
		allocFrame->sizeY = 512;
		allocFrame->sizeZ = 1;
		allocFrame->bitsPerPixel = 16;
		allocFrame->bufferLength = allocFrame->sizeX * allocFrame->sizeY * allocFrame->sizeZ * (allocFrame->bitsPerPixel / 8);
		allocFrame->buffer = (char *)malloc(allocFrame->bufferLength);
	}
	printf("In allocateCallback, allocated frame is at 0x%lx buffer at 0x%lx\n", (unsigned long)allocFrame, (unsigned long)allocFrame->buffer);
	return allocFrame;
}

void freeCallback(void* ctlHandle, CtlFrame* buffer)
{
	printf("In freeCallback, freeing frame at 0x%lx\n", (unsigned long)buffer);
	if (buffer != 0) {
		if (buffer->buffer != 0) {
			free(buffer->buffer);
		}
		free(buffer);
	}
}

void receiveCallback(void* ctlHandle, CtlFrame* buffer)
{
	int i;
	printf("In receive callback, start of data in buffer: ");

	// Do something with the frame
	// ...

	char* bufPtr = (char *)(buffer->buffer);
	for (i = 0; i < 10; i++) {
		printf("%x ", *(bufPtr + i));
	}
	printf("\n");

	// Free the frame up
	freeCallback(ctlHandle, buffer);
}

void signalCallback(void* ctlHandle, int id)
{
	printf("In signal callback: %d\n", id);

	switch (id)
	{
	case FEM_OP_ACQUISITIONCOMPLETE:
		printf("Acquisition complete!\n");
		acquiring = 0;
		break;

	default:
		break;
	}
}
