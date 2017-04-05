#include <iostream>
#include <map>
#include <vector>

#include "femApi.h"
#include "FemApiError.h"
#include "ExcaliburFemClient.h"

std::map<int, std::vector<int> > int_params;

const unsigned int kClientTimeoutMsecs = 10000;

typedef struct {
	ExcaliburFemClient* client;
	FemApiError         error;
} FemHandle;

const char* femErrorMsg(void* handle)
{
	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    return (femHandle->error).get_string();
}

int femErrorCode(void* handle)
{
	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    return (femHandle->error).get_code();
}

int femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config, void** handle)
{

	int rc = FEM_RTN_OK;

	// Initialise FEM handle and client objects, which opens and manages the connection with the FEM
	FemHandle* femHandle = new FemHandle;
	femHandle->client = NULL;
	*handle = reinterpret_cast<void*>(femHandle);

	try
	{
		femHandle->client = new ExcaliburFemClient(ctlHandle, callbacks, config, kClientTimeoutMsecs);

	}
	catch (FemClientException& e)
	{
		femHandle->error.set() << "Failed to initialise FEM connection: " << e.what();
		rc = FEM_RTN_INITFAILED;
	}


    return rc;
}

int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value)
{
    int rc = FEM_RTN_OK;

    //ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

    if (int_params.count(id) > 0) {
        for (size_t i = 0; i < size; i++) {
            value[i] = int_params[id][i];
        }
    } else {
        for (size_t i = 0; i < size; i++) {
            value[i] = id + i;
        }
    }

    return rc;
}

int femGetId(void* handle)
{
	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    return (femHandle->client)->get_id();
}

void femClose(void* handle)
{

	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

	if (femHandle->client != NULL) {
		delete femHandle->client;
	}

	delete femHandle;
}

int femSetInt(void* handle, int chipId, int id, size_t size, int* value)
{
    int rc = FEM_RTN_OK;

    int_params[id] = std::vector<int>(value, value + size);

    return rc;
}

int femCmd(void* handle, int chipId, int id)
{
    int rc = FEM_RTN_OK;

    FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    switch (id)
    {
        case FEM_OP_STARTACQUISITION:
        case FEM_OP_STOPACQUISITION:
        case FEM_OP_LOADPIXELCONFIG:
        case FEM_OP_FREEALLFRAMES:
        case FEM_OP_LOADDACCONFIG:
        case FEM_OP_FEINIT:
        case FEM_OP_REBOOT:
            // Do nothing for now
            break;

        default:
            rc = FEM_RTN_UNKNOWNOPID;
            (femHandle->error).set() << "femCmd: illegal command ID: " << id;
    }

    return rc;
}

