/*
 * femApi.cpp
 *
 *  Created on: 2 Dec 2011
 *      Author: tcn
 */
#include "femApi.h"
#include "ExcaliburFemClient.h"

// Forward declarations of internal functions
static int translateFemErrorCode(FemErrorCode error);

// Internal static variables, which cache the WP5 control handle and callback structures passed
// as arguments during the initialisation
static void* lCtlHandle = NULL;
static const CtlCallbacks* lCallbacks = NULL;

void* femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config)
{

	// Initialise FEM client object, which opens and handles connection with the FEM
	ExcaliburFemClient* theFem = NULL;
	try
	{
		theFem = new ExcaliburFemClient(ctlHandle, callbacks, config);
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught trying to initialise FEM connection: " << e.what() << std::endl;
	}

	// Store the control API handle and callback structures
	lCtlHandle = ctlHandle;
	lCallbacks = callbacks;

	return (void*) theFem;

}

void femClose(void* femHandle)
{
	FemClient* theFem = reinterpret_cast<FemClient*>(femHandle);

	delete theFem;
}

int femSetInt(void* femHandle, int chipId, int id, std::size_t size, int* value)
{
	int rc = FEM_RTN_OK;
	FemClient* theFem = reinterpret_cast<FemClient*>(femHandle);

	// TODO: remove this temporary hack of the address from chip ID and config ID
	unsigned int address = 8000*chipId + id;

	// Build a payload array from the parameters passed
	std::vector<u32> payload(size);
	for (unsigned int i = 0; i < (unsigned int)size; i++) {
		payload[i] = *(value + i);
	}
	std::vector<u8>* payloadPtr = (std::vector<u8>*)&payload;

	// Issue the write transaction
	try {
		std::size_t writeLen = theFem->write(BUS_RAW_REG, WIDTH_LONG, address, *payloadPtr);
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught during femSetInt: " << e.what() << std::endl;
		rc = translateFemErrorCode(e.which());
	}

	return rc;
}

int femSetShort(void* femHandle, int chipId, int id, std::size_t size, short* value)
{
	int rc = FEM_RTN_OK;
	FemClient* theFem = reinterpret_cast<FemClient*>(femHandle);

	// TODO: remove this temporary hack of the address from chip ID and config ID
	unsigned int address = 8000*chipId + id;

	// Build a payload array from the parameters passed
	std::vector<u16> payload(size);
	for (unsigned int i = 0; i < (unsigned int)size; i++) {
		payload[i] = *(value + i);
	}
	std::vector<u8>* payloadPtr = (std::vector<u8>*)&payload;
	// Issue the write transaction
	try {
		std::size_t writeLen = theFem->write(BUS_RAW_REG, WIDTH_WORD, address, *payloadPtr);
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught during femSetShort: " << e.what() << std::endl;
		rc = translateFemErrorCode(e.which());
	}

	return rc;
}

int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value)
{
	int rc = FEM_RTN_OK;

	FemClient* theFem = reinterpret_cast<FemClient*>(femHandle);

	// TODO: remove this temporary hack of the address from chip ID and config ID
	unsigned int address = 8000*chipId + id;

	// Perform the read operation, trapping any exceptions that occur
	try
	{
		std::vector<u8> readResult = theFem->read(BUS_RAW_REG, WIDTH_LONG, address, size);

		// Convert read byte vector into u32 and unpack into result array
		std::vector<u32>* longResult = (std::vector<u32>*)&readResult;
		for (unsigned int i = 0; i < size; i++) {
			*(value + i) = (*longResult)[i];
		}
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught during femGetInt: " << e.what() << std::endl;
		rc = translateFemErrorCode(e.which());
	}

	return rc;
}

int femGetShort(void* femHandle, int chipId, int id, size_t size, short* value)
{
	int rc = FEM_RTN_OK;

	FemClient* theFem = reinterpret_cast<FemClient*>(femHandle);

	// TODO: remove this temporary hack of the address from chip ID and config ID
	unsigned int address = 8000*chipId + id;

	// Perform the read operation, trapping any exceptions that occur
	try
	{
		std::vector<u8> readResult = theFem->read(BUS_RAW_REG, WIDTH_WORD, address, size);

		// Convert read byte vector into u16 and unpack into result array
		std::vector<u16>* shortResult = (std::vector<u16>*)&readResult;
		for (unsigned int i = 0; i < size; i++) {
			*(value + i) = (*shortResult)[i];
		}
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught during femGetShort: " << e.what() << std::endl;
		rc = translateFemErrorCode(e.which());
	}

	return rc;
}

int femCmd(void* femHandle, int chipId, int id)
{
	int rc = FEM_RTN_OK;

	FemClient* theFem = reinterpret_cast<FemClient*>(femHandle);

	// TODO: remove this temporary hack of the command and chip ID
	unsigned int command = (10000 * chipId) + id;

	try
	{
		theFem->command(command);
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught during getCmd: " << e.what() << std::endl;
		rc = translateFemErrorCode(e.which());
	}

	return rc;
}

// Internal functions
int translateFemErrorCode(FemErrorCode error)
{
	// TODO - implement lookup at this point
	return (int)error;
}

