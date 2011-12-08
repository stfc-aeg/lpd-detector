/*
 * femApiTest.c
 *
 *  Created on: 2 Dec 2011
 *      Author: tcn
 */

#include <stdio.h>
#include <stdlib.h>

#include "femApi.h"

// Forward declaration of functions
int testGetSetInt(void* femHandle);
int testGetSetShort(void* femHandle);
int testCommand(void* femHandle);

// Forward declaration of callback functions to simulate WP5 callbacks
static CtlFrame* allocateCallback(void* ctlHandle);
static void      freeCallback(void* ctlHandle, CtlFrame* buffer);
static void      receiveCallback(void* ctlHandle, CtlFrame* buffer);
static void      signalCallback(void* ctlHandle, int id);

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

	rc = femCmd(femHandle, 1, FEM_OP_ACQUIRE);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on calling femCmd(): %d\n", rc);
		passed = 0;
	}
	printf("%s\n", passed ? "passed" : "failed");

	return passed;
}

CtlFrame* allocateCallback(void* ctlHandle)
{
	printf("In allocateCallback\n");
	return (CtlFrame*)0;
}

void freeCallback(void* ctlHandle, CtlFrame* buffer)
{
	printf("In freeCallback\n");
}

void receiveCallback(void* ctlHandle, CtlFrame* buffer)
{
	printf("In receive callback now\n");
}

void signalCallback(void* ctlHandle, int id)
{
	printf("In signal callback: %d\n", id);
}
