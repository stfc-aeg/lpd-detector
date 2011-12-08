//============================================================================
// Name        : excaliburPixelDecode.cpp
// Author      : Tim Nicholls
// Version     : 0.1
// Copyright   : STFC Rutherford Appleton Laboratory
// Description : Quick test of EXCALIBUR pixel decoding algorithm
//============================================================================

#include <iostream>
#include <iomanip>
#include <time.h>
#include "dataTypes.h"

const int kRows = 256;
const int kCols = 256;
const int kAsics = 8;
const int kDataLanes = 8;

const int kConsecPixels = 4;
const int kAsicStreams = 2;

const int kPixels = kRows * kCols * kAsics;
const int kColsPerDataLane = kCols / kDataLanes;
const int kPixelGroups = kCols / kConsecPixels;
const int kAsicsPerStream = kAsics / kAsicStreams;
const int kColsPerStream = kCols * kAsicsPerStream;

const int kRepeats = 100;

using namespace std;

double elapsedTime(struct timespec* start, struct timespec* end)
{
	return (((double)(end->tv_sec * 1E9 ) + end->tv_nsec) -
			((double)(start->tv_sec * 1E9) + start->tv_nsec)) / 1E9;
}

int main() {

	struct timespec startTime, endTime;
	// Create a raw pixel data array
	u16 rawPixelData[kPixels];

	// Fill the raw pixel array with data incrementing linearly by column across each row
	int rawPixelCount = 0;

	clock_gettime(CLOCK_REALTIME, &startTime);
	for (int iStream = 0; iStream < kAsicStreams; iStream++)
	{
		for (int iRow = 0; iRow < kRows; iRow++)
		{
			int pixelColNum = 0;
			for (int iPixelGroup = 0; iPixelGroup < kPixelGroups; iPixelGroup++)
			{
				for (int iAsic = 0; iAsic < kAsicsPerStream; iAsic ++)
				{
					for (int iPixel = 0; iPixel < kConsecPixels; iPixel++)
					{
						int pixelAddr = (iStream * kColsPerStream) + (iAsic * kCols) + pixelColNum + iPixel;
						rawPixelData[rawPixelCount] = pixelAddr;
						rawPixelCount++;
//						cout << "Stream " << iStream << " Row " << iRow << " Col " << pixelColNum << " Asic " << iAsic
//							 << " Group " << iPixelGroup << " Pixel " << iPixel << " rawPixelCount " << rawPixelCount << " pixelAddr " << pixelAddr << endl;
					}
				}
				pixelColNum += kConsecPixels;
			}

		}
	}
	clock_gettime(CLOCK_REALTIME, &endTime);
	cout << "Elapsed time for filling raw data buffer pixel was " << elapsedTime(&startTime, &endTime) << endl;

	// Sanity check number of raw pixels filled in stream equals total number of pixels
	if (rawPixelCount != kPixels) {
		cout << "ERROR: mismatched number of pixels in raw array build. Filled " << rawPixelCount << ", expected " << kPixels << endl;
	}
	cout << "There are " << rawPixelCount << " pixels in the array of total size " << sizeof(rawPixelData) << endl;


	// Create a decoded pixel array
	u16 decodedPixelData[kPixels];

	clock_gettime(CLOCK_REALTIME, &startTime);
	for (int repeat = 0; repeat < kRepeats; repeat++) {
		rawPixelCount = 0;
		for (int iStream = 0; iStream < kAsicStreams; iStream++)
		{
			for (int iRow = 0; iRow < kRows; iRow++)
			{
				int pixelColNum = 0;
				for (int iPixelGroup = 0; iPixelGroup < kPixelGroups; iPixelGroup++)
				{
					for (int iAsic = 0; iAsic < kAsicsPerStream; iAsic ++)
					{
#ifdef NAIVE_DECODE
						for (int iPixel = 0; iPixel < kConsecPixels; iPixel++)
						{
							int pixelAddr = (iStream * kColsPerStream) + + (iRow * kCols * kAsics) + (iAsic * kCols) + pixelColNum + iPixel;
							decodedPixelData[pixelAddr] = rawPixelData[rawPixelCount];
							rawPixelCount++;
						}
#else
						int pixelAddr = (iStream * kColsPerStream) + + (iRow * kCols * kAsics) + (iAsic * kCols) + pixelColNum;
						u64* rawAddr = (u64*)&(rawPixelData[rawPixelCount]);
						u64* decodedAddr = (u64*)&(decodedPixelData[pixelAddr]);
						*decodedAddr = *rawAddr;
						rawPixelCount += kConsecPixels;
#endif
					}
					pixelColNum += kConsecPixels;
				}

			}
		}
	}
	clock_gettime(CLOCK_REALTIME, &endTime);
	double timePerDecode = elapsedTime(&startTime, &endTime) / kRepeats;
	cout << "Decode time = " << setprecision(3) << timePerDecode * 1000 << "ms" << endl;

	// Scan decoded data to check it's linear
	int numDecodeErrors = 0;
	int pixelAddr = 0;
	for (int iRow = 0; iRow < kRows; iRow++)
	{
		for (int iCol = 0; iCol < kCols * kAsics; iCol++) {
			if (decodedPixelData[pixelAddr] != iCol) {
				numDecodeErrors++;
				cout << "Error at row " << iRow << " Col " << setw(4) << iCol << " Value " << setw(4) << decodedPixelData[pixelAddr] << endl;
			}
			pixelAddr++;
		}
	}
	cout << "Number of decode errors found: " << numDecodeErrors << endl;

	return 0;
}
