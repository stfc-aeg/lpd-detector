/*
 * femApiTest.c
 *
 *  Created on: 2 Dec 2011
 *      Author: tcn
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#include "femApi.h"

// Forward declaration of functions
int testGetSetInt(void* femHandle);
int testGetSetShort(void* femHandle);
int testCommand(void* femHandle);
int testSetLargeShortArray(void* femHandle);
int testSlowControl(void* femHandle);
int testDacs(void* femHandle);
int testPixelConfig(void* femHandle);
int testReadEfuseIds(void* femHandle);
int testAcquisitionLoop(void* femHandle, unsigned int numFrames);
int testAcquireStatus(void* femHandle);

// Forward declaration of callback functions to simulate WP5 callbacks
static CtlFrame* allocateCallback(void* ctlHandle);
static void      freeCallback(void* ctlHandle, CtlFrame* buffer);
static void      receiveCallback(void* ctlHandle, CtlFrame* buffer);
static void      signalCallback(void* ctlHandle, int id);

int acquiring = 0;
int framesReceived = 0;
int totalDataReceived = 0;

FILE* outputFile = 0;
struct timespec startTime, endTime;

int main(int argc, char* argv[]) {

	void* femHandle = 0;
	int numPassed = 0;
	unsigned int numFrames = 1;

	if (argc < 3)
	{
		printf("Usage: femApiTest <host> <port> <nFrames>\n");
		return 1;
	}

	if (argc >= 4)
	{
		numFrames = atoi(argv[3]);
	}

	printf("Connecting to FEM at IP address %s port %s ... ", argv[1], argv[2]);

	// Create a config structure to pass to the FEM client
	CtlConfig femConfig;
	femConfig.femAddress = argv[1];
	femConfig.femPort = atoi(argv[2]);
	femConfig.femNumber = 1;

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
//	numPassed += testGetSetInt(femHandle);
//	numPassed += testGetSetShort(femHandle);
//	numPassed += testCommand(femHandle);
//	numPassed += testSetLargeShortArray(femHandle);
//	numPassed += testSlowControl(femHandle);
//	numPassed += testDacs(femHandle);
//	numPassed += testPixelConfig(femHandle);
//	numPassed += testReadEfuseIds(femHandle);
//	numPassed += testAcquisitionLoop(femHandle, numFrames);
	numPassed += testAcquireStatus(femHandle);

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

int testSetLargeShortArray(void* femHandle)
{
	int rc;
	int passed = 1;

	const size_t arrayLen = 65536;
	short* shortVals;
	int loop;

	printf("Writing array of length %d of short values to FEM ... ", (int)arrayLen);

	shortVals = (short*)calloc(arrayLen, sizeof(short));
	for (loop = 0; loop < arrayLen; loop++) {
		shortVals[loop] = loop;
	}

	rc = femSetShort(femHandle, 1, 1, arrayLen, shortVals);
	if (rc != FEM_RTN_OK) {
		printf("Gor error on calling femSetShort(): %d\n", rc);
		passed = 0;
	}

	printf("%s\n", passed ? "passed" : "failed");

	return passed;
}

int testSlowControl(void* femHandle)
{

	int rc;
	int passed = 1;
	int chip;
	int pwrStatusId[] = { FEM_OP_P1V5_AVDD_1_POK,
			              FEM_OP_P1V5_AVDD_2_POK,
			              FEM_OP_P1V5_AVDD_3_POK,
			              FEM_OP_P1V5_AVDD_4_POK,
			              FEM_OP_P1V5_VDD_1_POK,
			              FEM_OP_P2V5_DVDD_1_POK,
			              -1
	};
	char *pwrStatusName[] = { "P1V5_AVDD_1",
                              "P1V5_AVDD_2",
                              "P1V5_AVDD_3",
                              "P1V5_AVDD_4",
                              "P1V5_VDD_1",
                              "P2V5_DVDD_1",
                             "END"
	};

	int id, pwrStatus;;

	double remoteTemp, localTemp, molyTemp, molyHumidity, dacValue = -100.0;

	printf("Reading FPGA (remote) diode temperature from FEM ... ");
	rc = femGetFloat(femHandle, 1, FEM_OP_REMOTE_DIODE_TEMP, 1, &remoteTemp);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on call: %d\n", rc);
		passed = 0;
	}
	else
	{
		printf("OK (%.0fC)\n", remoteTemp);
	}

	printf("Reading board (local) diode temperature from FEM ... ");
	rc = femGetFloat(femHandle, 1, FEM_OP_LOCAL_TEMP, 1, &localTemp);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on call: %d\n", rc);
		passed = 0;
	}
	else
	{
		printf("OK (%.0fC)\n", localTemp);
	}

	printf("Reading front-end moly temperature from FEM      ... ");
	rc = femGetFloat(femHandle, 1, FEM_OP_MOLY_TEMPERATURE, 1,&molyTemp);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on call: %d\n", rc);
		passed = 0;
	}
	else
	{
		printf("OK (%.1fC)\n", molyTemp);
	}

	printf("Reading front-end moly humidity from FEM         ... ");
	rc = femGetFloat(femHandle, 1, FEM_OP_MOLY_HUMIDITY, 1,&molyHumidity);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on call: %d\n", rc);
		passed = 0;
	}
	else
	{
		printf("OK (%.1f%%)\n", molyHumidity);
	}

	printf("Reading front-end DAC channels from FEM          ... ");
	for (chip = 1; chip <= 8; chip++)
	{
		rc = femGetFloat(femHandle, chip, FEM_OP_DAC_OUT_FROM_MEDIPIX, 1, &dacValue);
		if (rc != FEM_RTN_OK)
		{
			printf("\nGot error on call for chip ID %d: %d ", chip, rc);
			passed = 0;
		}
		else
		{
			printf("%d : OK (%.3f) ", chip, dacValue);
			if (chip == 3) {
				printf("\n                                                     ");
			}
		}
	}
	printf("\n");

	printf("Reading front-end power status from FEM          ... ");
	id = 0;
	while (pwrStatusId[id] != -1)
	{
		rc = femGetInt(femHandle, 0, pwrStatusId[id], 1, &pwrStatus);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on call for pwr status id %d: %d ", pwrStatusId[id], rc);
			passed = 0;
		}
		else
		{
			printf("%-11s : OK (%d) ", pwrStatusName[id], pwrStatus);
			if (id == 3) {
				printf("\n                                                     ");
			}
		}

		id++;
	}
	printf("\n");

	printf("Testing write to MPX DAC inputs                  ... ");
	for (chip = 0; chip < 8; chip++)
	{
		int value = chip * 100;
		rc = femSetInt(femHandle, chip, FEM_OP_DAC_IN_TO_MEDIPIX, 1, &value);
		if (rc != FEM_RTN_OK)
		{
			printf("\nGot error on call for chip ID %d: %d", chip, rc);
			passed = 0;
		}
		else
		{
			printf("%d: OK ", chip);
		}
	}
	printf("\n");

	printf("Slow control tests %s\n", passed ? "passed" : "failed");

	return passed;
}

int testDacs(void* femHandle)
{
	int rc;
	int passed = 1;

	int value = 123;

	printf("Testing set of THRESHOLD0 DAC                      ...");
	rc = femSetInt(femHandle, 0, FEM_OP_MPXIII_THRESHOLD0DAC, 1, &value);
	if (rc != FEM_RTN_OK)
	{
		printf("\nGot error on call: %d",  rc);
		passed = 0;
	}
	else
	{
		printf("OK\n");
	}
	value = 77;
	printf("Testing set of THRESHOLD1 DAC                      ...");
	rc = femSetInt(femHandle, 1, FEM_OP_MPXIII_THRESHOLD1DAC, 1, &value);
	if (rc != FEM_RTN_OK)
	{
		printf("\nGot error on call: %d",  rc);
		passed = 0;
	}
	else
	{
		printf("OK\n");
	}
	value = 511;
	printf("Testing set of TPREFB DAC                          ...");
	rc = femSetInt(femHandle, 1, FEM_OP_MPXIII_TPREFBDAC, 1, &value);
	if (rc != FEM_RTN_OK)
	{
		printf("\nGot error on call: %d",  rc);
		passed = 0;
	}
	else
	{
		printf("OK\n");
	}

	printf("Testing DAC write command                          ...\n");
	rc = femCmd(femHandle, 1, FEM_OP_LOADDACCONFIG);
	return passed;


}

int testPixelConfig(void* femHandle)
{
	int rc;
	int passed = 1;
	int chip;
	int pixel;
	const unsigned int kNumPixels = FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y;

	// Arrays to contain test pixel config values
	short pixelMask[kNumPixels];
	short pixelThresholdA[kNumPixels];
	short pixelThresholdB[kNumPixels];
	short pixelGainMode[kNumPixels];
	short pixelTestMode[kNumPixels];

	printf("Testing setup of pixel configuration               ... ");

	for (chip = 1; chip <= 1; chip++) {

		// Initialize values with alernating patterns of 0 and 1
		for (pixel = 0; pixel < kNumPixels; pixel++)
		{
//			pixelMask[pixel]       = (chip + pixel) & 1;
//			pixelThresholdA[pixel] = (chip + pixel + 1) & 1;
//			pixelThresholdB[pixel] = (chip + pixel) & 1;
//			pixelGainMode[pixel]   = (chip + pixel + 1) & 1;
//			pixelTestMode[pixel]   = (chip + pixel) & 1;
			pixelMask[pixel]       = 0;
			pixelThresholdA[pixel] = 0;
			pixelThresholdB[pixel] = 0;
			pixelGainMode[pixel]   = 0;
			pixelTestMode[pixel]   = 0;
		}
//		pixelTestMode[0] = 1;

		rc = femSetShort(femHandle, chip, FEM_OP_MPXIII_PIXELMASK, (size_t)(kNumPixels), (short *)&pixelMask);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on set of pixel mask config command for chip %d: %d ", chip, rc);
			passed = 0;
		}

		rc = femSetShort(femHandle, chip, FEM_OP_MPXIII_PIXELTHRESHOLDA, (size_t)(kNumPixels), (short *)&pixelThresholdA);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on set of pixel thresholdA config command for chip %d: %d ", chip, rc);
			passed = 0;
		}

		rc = femSetShort(femHandle, chip, FEM_OP_MPXIII_PIXELTHRESHOLDB, (size_t)(kNumPixels), (short *)&pixelThresholdB);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on set of pixel thresholdB config command for chip %d: %d ", chip, rc);
			passed = 0;
		}

		rc = femSetShort(femHandle, chip, FEM_OP_MPXIII_PIXELGAINMODE, (size_t)(kNumPixels), (short *)&pixelGainMode);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on set of pixel gain mode config command for chip %d: %d ", chip, rc);
			passed = 0;
		}

		rc = femSetShort(femHandle, chip, FEM_OP_MPXIII_PIXELTEST, (size_t)(kNumPixels), (short *)&pixelTestMode);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on set of pixel test mode config command for chip %d: %d ", chip, rc);
			passed = 0;
		}

		// Send command to load pixel configuration
		rc = femCmd(femHandle, chip, FEM_OP_LOADPIXELCONFIG);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on load pixel config command for chip %d: %d ", chip, rc);
			passed = 0;
		}


	}

	printf("%s\n", passed ? "passed" : "failed");

	return passed;

}
int testReadEfuseIds(void* femHandle)
{
	int rc;
	int passed = 1;
	int chip;

	printf("Testing read of eFuseIDs from chips                ...\n");
	for (chip = 1; chip <= 8; chip++)
	{
		int value;
		rc = femGetInt(femHandle, chip, FEM_OP_MPXIII_EFUSEID, 1, &value);
		if (rc != FEM_RTN_OK) {
			printf("\nGot error on call for eFuseID %d: %d ", chip, rc);
			passed = 0;
		}
		else
		{
			printf("%d: OK (0x%08x) ", chip, value);
			if (chip == 3) {
				printf("\n");
			}
		}
	}
	printf("\n");
	printf("eFuseID read test %s\n", passed ? "passed" : "failed");

	return passed;

}

int testAcquisitionLoop(void* femHandle, unsigned int numFrames)
{

	int rc;
	int passed = 1;
	double startSecs, endSecs, elapsedSecs, frameRate, dataRate;

	acquiring = 1;

//	printf("Opening output file... ");
//	outputFile = fopen("/tmp/test.dat", "w+b");
//	if (outputFile == 0)
//	{
//		perror("Failed to open output file");
//		passed = 0;
//	}

	printf("done.\nSending num frames to FEM... ");
	rc = femSetInt(femHandle, 0, FEM_OP_NUMFRAMESTOACQUIRE, sizeof(numFrames), (int*)&numFrames);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on setting number of frames: %d'n", rc);
		passed = 0;
	}

	unsigned int acqPeriodMs = 10;
	printf("done.\nSending acquisition period of %dms to FEM... ", acqPeriodMs);
	rc = femSetInt(femHandle, 0, FEM_OP_ACQUISITIONPERIOD, sizeof(acqPeriodMs), (int*)&acqPeriodMs);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on setting acq period: %d'n", rc);
		passed = 0;
	}

	unsigned int acqTimeMs = 4;
	printf("done.\nSending acquisition time of %dms to FEM... ", acqTimeMs);
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

	printf("Waiting for acquisition to complete ...\n");
	do
	{
		usleep(10000);
	}
	while (acquiring);


	printf("Sending stop acquisition to FEM... ");
	rc = femCmd(femHandle, 0, FEM_OP_STOPACQUISITION);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on calling femCmd(FEM_OP_STOPACQUISITION): %d'n", rc);
		passed = 0;
	}
	printf("done.\n");

	sleep(1);

	acquiring = 1;
	printf("done.\nSending start acquisition to FEM... ");
	rc = femCmd(femHandle, 0, FEM_OP_STARTACQUISITION);
	if (rc != FEM_RTN_OK)
	{
		printf("Got error on calling femCmd(): %d'n", rc);
		passed = 0;
	}

	printf("Waiting for acquisition to complete ...\n");
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

	startSecs = startTime.tv_sec  + ((double)startTime.tv_nsec / 1.0E9);
	endSecs   = endTime.tv_sec  + ((double)endTime.tv_nsec / 1.0E9);

	elapsedSecs = endSecs - startSecs;
	frameRate = (double)framesReceived / elapsedSecs;
	dataRate = (double)totalDataReceived / (elapsedSecs * 1024 * 1024);

	printf("Acquisition completed, received %d frames, %d bytes in %.2fs, rate %.2f Hz, %.2f MB/s\n",
			framesReceived, totalDataReceived, elapsedSecs, frameRate, dataRate);

	if (outputFile != 0)
	{
		fclose(outputFile);
		outputFile = 0;
	}

	return passed;

}

int testAcquireStatus(void* femHandle)
{
	int rc;
	rc = femCmd(femHandle, 0, 10);

	return 1;
}

CtlFrame* allocateCallback(void* ctlHandle)
{
	//printf("In allocateCallback\n");
	CtlFrame* allocFrame = malloc(sizeof(CtlFrame));
	if (allocFrame != 0) {
		allocFrame->sizeX = 256 * 8;
		allocFrame->sizeY = 256;
		allocFrame->sizeZ = 1;
		allocFrame->bitsPerPixel = 16;
		allocFrame->bufferLength = allocFrame->sizeX * allocFrame->sizeY * allocFrame->sizeZ * (allocFrame->bitsPerPixel / 8); // + 16;
//		allocFrame->bufferLength = 393216 * 2;
		allocFrame->buffer = (char *)malloc(allocFrame->bufferLength);
	}
//	printf("In allocateCallback, allocated frame is at 0x%lx buffer at 0x%lx size %ld\n", (unsigned long)allocFrame,
//			(unsigned long)allocFrame->buffer, allocFrame->bufferLength);
	return allocFrame;
}

void freeCallback(void* ctlHandle, CtlFrame* buffer)
{
	//printf("In freeCallback, freeing frame at 0x%lx\n", (unsigned long)buffer);
	if (buffer != 0) {
		if (buffer->buffer != 0) {
			free(buffer->buffer);
		}
		free(buffer);
	}
}

void receiveCallback(void* ctlHandle, CtlFrame* buffer)
{
//	int i;
//	printf("In receive callback, start of data in buffer: ");
//
//	 //Do something with the frame
//	 //...
//
//	char* bufPtr = (char *)(buffer->buffer + buffer->bufferLength - 16);
//	for (i = 0; i < 16; i++) {
//		printf("%x ", (unsigned char)*(bufPtr + i));
//	}
//	printf("\n");
//
//	unsigned int* u32Ptr = (unsigned int *)(buffer->buffer);
//	printf("Data at start of buffer: %x %x\n", *u32Ptr, *(u32Ptr+1));

	// Write data to output file
	if (outputFile != 0)
	{
		fwrite(buffer->buffer, sizeof(char), buffer->bufferLength, outputFile);
	}

	if (framesReceived == 0)
	{
		clock_gettime(CLOCK_REALTIME, &startTime);
	}
	framesReceived++;
	totalDataReceived += buffer->bufferLength;

	if ((framesReceived % 100) == 0)
	{
		printf("Received %d frames\n", framesReceived);
	}
	// Free the frame up
	freeCallback(ctlHandle, buffer);
}

void signalCallback(void* ctlHandle, int id)
{

	switch (id)
	{
	case FEM_OP_ACQUISITIONCOMPLETE:
		clock_gettime(CLOCK_REALTIME, &endTime);
		acquiring = 0;
		printf("Acquisition complete!\n");
		break;

	default:
		break;
	}
}
