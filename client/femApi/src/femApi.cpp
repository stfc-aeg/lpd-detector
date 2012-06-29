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

const unsigned int kClientTimeoutMsecs = 10000;

void* femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config)
{

	// Initialise FEM client object, which opens and handles connection with the FEM
	ExcaliburFemClient* theFem = NULL;
	try
	{
		theFem = new ExcaliburFemClient(ctlHandle, callbacks, config, kClientTimeoutMsecs);

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
	ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

	delete theFem;
}

int femSetInt(void* femHandle, int chipId, int id, std::size_t size, int* value)
{
	int rc = FEM_RTN_OK;

	if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
	{
		rc = FEM_RTN_ILLEGALCHIP;
	}
	else
	{

		ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

		try {

			switch (id)
			{

			case FEM_OP_MPXIII_COLOURMODE:

				if (size == 1)
				{
					theFem->mpx3ColourModeSet((int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MPXIII_COUNTERDEPTH:

				if (size == 1)
				{
					theFem->mpx3CounterDepthSet((int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MPXIII_EXTERNALTRIGGER:

				if (size == 1)
				{
					theFem->externalTriggerSet((int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MPXIII_OPERATIONMODE:

				if (size == 1)
				{
					theFem->operationModeSet((int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MPXIII_COUNTERSELECT:

				if (size == 1)
				{
					theFem->mpx3CounterSelectSet((int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MPXIII_DACSENSE:

				if (size == 1)
				{
					theFem->mpx3DacSenseSet((unsigned int)chipId, (int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MPXIII_DACEXTERNAL:

				if (size == 1)
				{
					theFem->mpx3DacExternalSet((unsigned int)chipId, (int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			// Handle all DAC settings through the femSetDac helper function
			case FEM_OP_MPXIII_THRESHOLD0DAC:
			case FEM_OP_MPXIII_THRESHOLD1DAC:
			case FEM_OP_MPXIII_THRESHOLD2DAC:
			case FEM_OP_MPXIII_THRESHOLD3DAC:
			case FEM_OP_MPXIII_THRESHOLD4DAC:
			case FEM_OP_MPXIII_THRESHOLD5DAC:
			case FEM_OP_MPXIII_THRESHOLD6DAC:
			case FEM_OP_MPXIII_THRESHOLD7DAC:
			case FEM_OP_MPXIII_PREAMPDAC:
			case FEM_OP_MPXIII_IKRUMDAC:
			case FEM_OP_MPXIII_SHAPERDAC:
			case FEM_OP_MPXIII_DISCDAC:
			case FEM_OP_MPXIII_DISCLSDAC:
			case FEM_OP_MPXIII_THRESHOLDNDAC:
			case FEM_OP_MPXIII_DACPIXELDAC:
			case FEM_OP_MPXIII_DELAYDAC:
			case FEM_OP_MPXIII_TPBUFFERINDAC:
			case FEM_OP_MPXIII_TPBUFFEROUTDAC:
			case FEM_OP_MPXIII_RPZDAC:
			case FEM_OP_MPXIII_GNDDAC:
			case FEM_OP_MPXIII_TPREFDAC:
			case FEM_OP_MPXIII_FBKDAC:
			case FEM_OP_MPXIII_CASDAC:
			case FEM_OP_MPXIII_TPREFADAC:
			case FEM_OP_MPXIII_TPREFBDAC:

				if (size == 1)
				{
					theFem->mpx3DacSet(chipId, id, (unsigned int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_NUMFRAMESTOACQUIRE:

				theFem->numFramesSet((unsigned int)*value);
				break;

			case FEM_OP_ACQUISITIONTIME:

				theFem->acquisitionTimeSet((unsigned int)*value);
				break;

			case FEM_OP_ACQUISITIONPERIOD:

				theFem->acquisitionPeriodSet((unsigned int)*value);
				break;

			case FEM_OP_VDD_ON_OFF:

				theFem->frontEndEnableSet((unsigned int)*value);
				break;

//			case FEM_OP_DAC_IN_TO_MEDIPIX:
//
//				theFem->frontEndDacInWrite(chipId, (unsigned int)*value);
//				break;
//
			case FEM_OP_BIAS_ON_OFF:

				// Do nothing for now
				break;

			case FEM_OP_LV_ON_OFF:

				// Do nothing for now
				break;

//			case FEM_OP_BIAS_LEVEL:
//
//				// Do nothing for now
//				break;

			case FEM_OP_MEDIPIX_CHIP_DISABLE:

				if (size == 1)
				{
					theFem->mpx3DisableSet((unsigned int)chipId, (unsigned int)*value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			default:
				rc = FEM_RTN_UNKNOWNOPID;
				break;
			}
		}
		catch (FemClientException& e)
		{
			std::cerr << "Exception caught during femSetInt: " << e.what() << std::endl;
			rc = translateFemErrorCode(e.which());
		}
	}
	return rc;
}

int femSetShort(void* femHandle, int chipId, int id, std::size_t size, short* value)
{
	int rc = FEM_RTN_OK;

	if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
	{
		rc = FEM_RTN_ILLEGALCHIP;
	}
	else
	{

		ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

		try
		{

			switch (id)
			{

			// Handle all pixel settings through single call
			case FEM_OP_MPXIII_PIXELMASK:
			case FEM_OP_MPXIII_PIXELTHRESHOLDA:
			case FEM_OP_MPXIII_PIXELTHRESHOLDB:
			case FEM_OP_MPXIII_PIXELGAINMODE:
			case FEM_OP_MPXIII_PIXELTEST:

				if (size == (FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y))
				{
					theFem->mpx3PixelConfigSet((unsigned int)chipId, id, size, (unsigned short*)value);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			default:
				break;
			}
		}
		catch (FemClientException& e)
		{
			std::cerr << "Exception caught during femSetShort: " << e.what() << std::endl;
			rc = translateFemErrorCode(e.which());
		}
	}
	return rc;
}

int femSetFloat(void* femHandle, int chipId, int id, std::size_t size, double* value)
{
	int rc = FEM_RTN_OK;

	if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
	{
		rc = FEM_RTN_ILLEGALCHIP;
	}
	else
	{
		ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

		try {

			switch (id)
			{

			case FEM_OP_DAC_IN_TO_MEDIPIX:

				theFem->frontEndDacInWrite(chipId, *value);
				break;

			case FEM_OP_BIAS_LEVEL:

				// Do nothing for now
				break;

			default:
				rc = FEM_RTN_UNKNOWNOPID;
				break;
			}
		}
		catch (FemClientException& e)
		{
			std::cerr << "Exception caught during femSetInt: " << e.what() << std::endl;
			rc = translateFemErrorCode(e.which());
		}
	}

	return rc;
}

int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value)
{
	int rc = FEM_RTN_OK;

	if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
	{
		rc = FEM_RTN_ILLEGALCHIP;
	}
	else
	{
		ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

		try
		{
			switch (id)
			{

			case FEM_OP_P1V5_AVDD_1_POK:
				*value = theFem->frontEndSupplyStatusRead(frontEndAVDD1);
				break;

			case FEM_OP_P1V5_AVDD_2_POK:
				*value = theFem->frontEndSupplyStatusRead(frontEndAVDD2);
				break;

			case FEM_OP_P1V5_AVDD_3_POK:
				*value = theFem->frontEndSupplyStatusRead(frontEndAVDD3);
				break;

			case FEM_OP_P1V5_AVDD_4_POK:
				*value = theFem->frontEndSupplyStatusRead(frontEndAVDD4);
				break;

			case FEM_OP_P1V5_VDD_1_POK:
				*value = theFem->frontEndSupplyStatusRead(frontEndVDD);
				break;

			case FEM_OP_P2V5_DVDD_1_POK:
				*value = theFem->frontEndSupplyStatusRead(frontEndDVDD);
				break;

			case FEM_OP_COOLANT_TEMP_STATUS:
				*value = 1;
				break;

			case FEM_OP_HUMIDITY_STATUS:
				*value = 1;
				break;

			case FEM_OP_COOLANT_FLOW_STATUS:
				*value = 1;
				break;

			case FEM_OP_AIR_TEMP_STATUS:
				*value = 1;
				break;

			case FEM_OP_FAN_FAULT:
				*value = 1;
				break;

			case FEM_OP_MPXIII_EFUSEID:
				*value = theFem->mpx3eFuseIdRead(chipId);
				break;

			default:
				rc = FEM_RTN_UNKNOWNOPID;
				break;

			}
		}
		catch (FemClientException& e)
		{
			std::cerr << "Exception caught during femGetInt, chipId: " << chipId << " opId: "
					  << id << " : " << e.what() << std::endl;
			rc = translateFemErrorCode(e.which());
		}

	}

	return rc;
}

int femGetShort(void* femHandle, int chipId, int id, size_t size, short* value)
{
	int rc = FEM_RTN_OK;

	if ((chipId < 0) || (chipId >= (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
	{
		rc = FEM_RTN_ILLEGALCHIP;
	}
	else
	{
		ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

		try
		{
			switch (id)
			{

				*value = (short) id & 0x1;
				break;

			default:
				rc = FEM_RTN_UNKNOWNOPID;
				break;

			}
		}
		catch (FemClientException& e)
		{
			std::cerr << "Exception caught during femGetShort: " << e.what() << std::endl;
			rc = translateFemErrorCode(e.which());
		}

	}

//	ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);
//
//	// TODO: remove this temporary hack of the address from chip ID and config ID
//	unsigned int address = 8000*chipId + id;
//
//	// Perform the read operation, trapping any exceptions that occur
//	try
//	{
//		std::vector<u8> readResult = theFem->read(BUS_RAW_REG, WIDTH_WORD, address, size);
//
//		// Convert read byte vector into u16 and unpack into result array
//		std::vector<u16>* shortResult = (std::vector<u16>*)&readResult;
//		for (unsigned int i = 0; i < size; i++) {
//			*(value + i) = (*shortResult)[i];
//		}
//	}
//	catch (FemClientException& e)
//	{
//		std::cerr << "Exception caught during femGetShort: " << e.what() << std::endl;
//		rc = translateFemErrorCode(e.which());
//	}

	return rc;
}

int femGetFloat(void* femHandle, int chipId, int id, size_t size, double* value)
{

	int rc = FEM_RTN_OK;

	if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
	{
		rc = FEM_RTN_ILLEGALCHIP;
	}
	else
	{
		ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

		try
		{
			switch(id)
			{

			case FEM_OP_P5V_A_VMON:

				if (size == 1)
				{
					*value = 5.03;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P5V_B_VMON:

				if (size == 1)
				{
					*value = 4.97;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P5V_FEMO0_IMON:
			case FEM_OP_P5V_FEMO1_IMON:
			case FEM_OP_P5V_FEMO2_IMON:
			case FEM_OP_P5V_FEMO3_IMON:
			case FEM_OP_P5V_FEMO4_IMON:
			case FEM_OP_P5V_FEMO5_IMON:

				if (size == 1)
				{
					*value = 0.1 * (id - FEM_OP_P5V_FEMO0_IMON);
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;


			case FEM_OP_P48V_VMON:

				if (size == 1)
				{
					*value = 48.43;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P48V_IMON:

				if (size == 1)
				{
					*value = 7.83;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P5VSUP_VMON:

				if (size == 1)
				{
					*value = 5.17;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P5VSUP_IMON:

				if (size == 1)
				{
					*value = 0.63;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_HUMIDITY_MON:

				if (size == 1)
				{
					*value = 37.48;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_AIR_TEMP_MON:

				if (size == 1)
				{
					*value = 28.11;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_COOLANT_TEMP_MON:

				if (size == 1)
				{
					*value = 19.85;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_COOLANT_FLOW_MON:

				if (size == 1)
				{
					*value = 123.45;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P3V3_IMON:

				if (size == 1)
				{
					*value = 0.77;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P1V8_IMON_A:

				if (size == 1)
				{
					*value = 19.44;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_BIAS_IMON:

				if (size == 1)
				{
					*value = 0.0043;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P3V3_VMON:

				if (size == 1)
				{
					*value = 3.37;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P1V8_VMON_A:

				if (size == 1)
				{
					*value = 1.88;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_BIAS_VMON:

				if (size == 1)
				{
					*value = 200.05;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P1V8_IMON_B:

				if (size == 1)
				{
					*value = 18.69;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_P1V8_VMON_B:

				if (size == 1)
				{
					*value = 1.79;
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;


			// -- Real calls below here
			case FEM_OP_REMOTE_DIODE_TEMP:

				if (size == 1)
				{
					*value = theFem->tempSensorRead(femFpgaTemp);
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_LOCAL_TEMP:
				if (size == 1)
				{
					*value = theFem->tempSensorRead(femBoardTemp);
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MOLY_TEMPERATURE:
				if (size == 1)
				{
					*value = theFem->frontEndTemperatureRead();
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_MOLY_HUMIDITY:
				if (size == 1)
				{
					*value = theFem->frontEndHumidityRead();
				}
				else {
					rc = FEM_RTN_BADSIZE;
				}
				break;

			case FEM_OP_DAC_OUT_FROM_MEDIPIX:
				if (size == 1)
				{
					*value = theFem->frontEndDacOutRead(chipId);
				}
				else
				{
					rc = FEM_RTN_BADSIZE;
				}
				break;

			default:
				rc = FEM_RTN_UNKNOWNOPID;
				break;
			}
		}
		catch (FemClientException& e)
		{
			std::cerr << "Exception caught during femGetFloat with id=" << id << " : "<< e.what() << std::endl;
			rc = translateFemErrorCode(e.which());
		}

	}
	return rc;
}

int femCmd(void* femHandle, int chipId, int id)
{
	int rc = FEM_RTN_OK;

	ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

	// TODO: remove this temporary hack of the command and chip ID
	//unsigned int command = (10000 * chipId) + id;

	try
	{
		//theFem->command(command);
		switch (id)
		{

		case FEM_OP_STARTACQUISITION:
		case FEM_OP_STOPACQUISITION:
			theFem->command(id);
			break;

		case FEM_OP_LOADDACCONFIG:
			theFem->mpx3DacsWrite(chipId);
			break;

		case FEM_OP_LOADPIXELCONFIG:
			theFem->mpx3PixelConfigWrite(chipId);
			break;

		case FEM_OP_FREEALLFRAMES:
			theFem->freeAllFrames();
			break;

		case 10:
		{
			FemAcquireStatus acqStatus = theFem->acquireStatus();
			std::cout << "Acquisition status" << std::endl;
			std::cout << "------------------" << std::endl;
			std::cout << "   State            : "   << acqStatus.state << std::endl;
			std::cout << "   Buffer count     : 0x" << std::hex << acqStatus.bufferCnt << std::dec << std::endl;
			std::cout << "   Buffer size      : 0x" << std::hex << acqStatus.bufferSize << std::dec << std::endl;
			std::cout << "   Buffer dirty     : "   << acqStatus.bufferDirty << std::endl;
			std::cout << "   Read pointer     : 0x" << std::hex << acqStatus.readPtr << std::dec << std::endl;
			std::cout << "   Write pointer    : 0x" << std::hex << acqStatus.writePtr << std::dec << std::endl;
			std::cout << "   Number of acqs   : "   << acqStatus.numAcq << std::endl;
			std::cout << "   Configured BDs   : "   << acqStatus.numConfigBds << std::endl;
			std::cout << "   Total RX bottom  : "   << acqStatus.totalRecvBot << std::endl;
			std::cout << "   Total RX top     : "   << acqStatus.totalRecvTop << std::endl;
			std::cout << "   Total TX sent    : "   << acqStatus.totalSent << std::endl;
			std::cout << "   Total errors     : "   << acqStatus.totalErrors << std::endl;

		}
		break;

		default:
			rc = FEM_RTN_UNKNOWNOPID;
			break;
		}
	}
	catch (FemClientException& e)
	{
		std::cerr << "Exception caught during femCmd: " << e.what() << std::endl;
		rc = translateFemErrorCode(e.which());
	}

	return rc;
}

// Internal functions
int translateFemErrorCode(FemErrorCode error)
{
	int rc = -1;

	switch(error)
	{
	case excaliburFemClientIllegalDacId:
		rc = FEM_RTN_ILLEGALCHIP;
		break;

	case excaliburFemClientIllegalChipId:
		rc = FEM_RTN_ILLEGALCHIP;
		break;

	case excaliburFemClientOmrTransactionTimeout:
		rc = FEM_RTN_ILLEGALCHIP;
		break;

	default:
		// Default translation is to just return error code
		rc = (int)error;
		break;
	}

	return rc;
}

