/*
 * commandProcessor.c
 *
 * Manages the decoding of received packets and generation
 * of response packets using LwIP library
 *
 */

#include "commandProcessor.h"
#ifdef USE_CACHE
#include "xcache_l.h"
#endif

/**
 * Manages the connection of clients to the FEM and
 * the reception / validation / response generation of
 * packets.
 *
 * Flag reloadRequested when non zero causes main event loop to drop out and
 * wait a number of seconds before reloading the requested firmware index from the systemace.
 *
 * @param arg pointer to argument
 *
 */
void commandProcessorThread(void* arg)
{
	int listenerSocket, clientSocket, newFd, addrSize, numFds, numBytesRead, numBytesToRead, i, j;
	struct sockaddr_in serverAddress, clientAddress;
	fd_set readSet, masterSet;
	struct timeval tv;
	u8 numConnectedClients = 0;
	int reloadRequested = -1;

	// Setup and initialise client statuses to idle
	struct clientStatus state[NET_MAX_CLIENTS];
	j=0;
	do
	{
		state[j].state = STATE_COMPLETE;
		state[j].size = 0;
		state[j].timeoutCount = 0;
		state[j].payloadBufferSz = 0;
		state[j].gotData = 0;
		state[j].errorCode = 0;
		state[j].errorString[0] = 0;
		j++;
	} while (j<NET_MAX_CLIENTS);

	// RX and TX packet buffers
	u8* pTxBuffer = (u8*)malloc(sizeof(struct protocol_header)+MAX_PAYLOAD_SIZE);
	struct protocol_header* pTxHeader = (struct protocol_header*)pTxBuffer;
	if(pTxBuffer == NULL)
	{
		// Critical error, cannot continue
		xil_printf("CmdProc: Could not malloc main TX buffer!\r\n");
		xil_printf("Terminating thread...\r\n");
		return;
	}

	// Prepare file descriptor sets
	FD_ZERO(&readSet);
	FD_ZERO(&masterSet);
	numFds = -1;

	// Prepare timeval for select call
	tv.tv_sec =  NET_DEFAULT_TICK_SEC;
	tv.tv_usec = NET_DEFAULT_TICK_USEC;

	DBGOUT("CmdProc: Thread starting...\r\n");

	// Open server socket, stream mode
	if ((listenerSocket = lwip_socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		// Failing to open a socket is a critical failure!
		xil_printf("CmdProc: Can't open socket, aborting...\r\n");
		xil_printf("Terminating thread...\r\n");
		return;
	}

	// Configure socket to receive any incoming connections
	serverAddress.sin_family = AF_INET;
	serverAddress.sin_port = htons(NET_CMD_PORT);
	serverAddress.sin_addr.s_addr = INADDR_ANY;
	memset(&(serverAddress.sin_zero), 0, sizeof(serverAddress.sin_zero));

	// Bind to address
	if (lwip_bind(listenerSocket, (struct sockaddr *)&serverAddress, sizeof (serverAddress)) < 0)
	{
		// Failing to bind to a socket is a critical failure!
		xil_printf("CmdProc: Can't bind to socket %d!\r\n", NET_CMD_PORT);
		xil_printf("Terminating thread...\r\n");
		return;
	}

	// Begin listening, register listener as FD of interest to read
	if (lwip_listen(listenerSocket, NET_SOCK_BACKLOG) < 0)
	{
		// Failing to listen on a socket is a critical failure!
		xil_printf("CmdProc: Can't listen on socket %d!\r\n", NET_CMD_PORT);
		xil_printf("Terminating thread...\r\n");
		return;
	}
	FD_SET(listenerSocket, &masterSet);
	numFds = listenerSocket;

	DBGOUT("CmdProc: Socket on port %d ready, awaiting clients (max. clients = %d).\r\n", NET_CMD_PORT, NET_MAX_CLIENTS);

	// ************************************************** MAIN SERVER LOOP ********************************************************
	while (reloadRequested==-1) {

		// Show our tick over
		//DBGOUT(".");

		// Copy master set over as readSet will be modified
		memcpy(&readSet, &masterSet, (size_t)sizeof(fd_set));

		if (lwip_select(numFds + 1, &readSet, NULL, NULL, &tv) == -1)
		{
			xil_printf("CmdProc: ERROR - Select failed!\r\n");
		}

		// Check file descriptors, see which one needs servicing
		for (i=0; i<=numFds; i++)
		{

			state[i-1].gotData = 0;

			if(FD_ISSET(i, &readSet))
			{

				// ----------------------------------------------------------------------------------------------------
				// This is a new connection
				if (i==listenerSocket)
				{

					// Accept connection
					addrSize = sizeof(clientAddress);
					newFd = lwip_accept(listenerSocket, (struct sockaddr*)&clientAddress, (socklen_t*)&addrSize);
					if (newFd == -1)
					{
						xil_printf("CmdProc: Error accepting connection!");
					}
					else
					{

						//DBGOUT("CmdProc: Received new connection! (Client #%d), fd is %d\r\n", numConnectedClients+1, newFd);

						// Check if we can accept more client connections
						if (numConnectedClients == NET_MAX_CLIENTS)
						{

							// Close connection
							DBGOUT("CmdProc: Client attempted to connect but can't accept any more connections!\r\n");
							lwip_close(newFd);

						}
						else
						{

							// Add to master list of FDs, update count
							FD_SET(newFd, &masterSet);
							if (newFd > numFds)
							{
								numFds = newFd;
							}

							// Add to client status list, malloc header and payload buffers (keep separate, simplifies pointer handling!)
							state[newFd-1].pHdr = malloc(sizeof(struct protocol_header));
							if (state[newFd-1].pHdr == NULL)
							{
								// Can't allocate payload space
								DBGOUT("CmdProc: Can't malloc header buffer for client %d!\r\n", newFd);
								DBGOUT("Terminating thread...\r\n");
								// TODO: Don't return, handle gracefully (NACK + disconnect?)
								return;
							}
							state[newFd-1].pPayload = malloc(NET_NOMINAL_RX_BUFFER_SZ);
							if (state[newFd-1].pPayload == NULL)
							{
								// Can't allocate payload space
								DBGOUT("CmdProc: Can't malloc payload buffer for client %d!\r\n", newFd);
								DBGOUT("Terminating thread...\r\n");
								// TODO: Don't return, handle gracefully (NACK + disconnect?)
								return;
							}

							numConnectedClients++;

							state[newFd-1].state = STATE_COMPLETE;		// This causes reset at beginning of receive from existing client loop

						}
					}

				}
				else
				// ----------------------------------------------------------------------------------------------------
				// Existing client is communicating with us
				{

					clientSocket = i;

					struct clientStatus *pState = &(state[i-1]);

					//pState->gotData = 0;

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Determine if the last packet was received from client, if so reset client status
					if (pState->state == STATE_COMPLETE)
					{

						//DBGOUT("***** STATE_COMPLETE ****\r\n");

						// Check if previous transaction had an increased payload buffer size and free it if necessary
						if (pState->payloadBufferSz > NET_NOMINAL_RX_BUFFER_SZ)
						{
							free(pState->pPayload);
							pState->pPayload = malloc(NET_NOMINAL_RX_BUFFER_SZ);
							if (pState->pPayload == NULL)
							{
								// Can't allocate payload space
								DBGOUT("CmdProc: Can't re-malloc payload buffer for client after large packet!\r\n");
								DBGOUT("Terminating thread...\r\n");
								return;
							}
							else
							{
								DBGOUT("CmdProc: Resized payload buffer to %d\r\n", NET_NOMINAL_RX_BUFFER_SZ);
							}
						}

						// Re-initialise client state
						pState->state = STATE_START;
						pState->payloadBufferSz = NET_NOMINAL_RX_BUFFER_SZ;
						pState->size = 0;
						pState->timeoutCount = 0;
						pState->gotData = 0;
						//DBGOUT("CmdProc: Receiving from client #%d.\r\n", i);
					} // END if state == STATE_COMPLETE



					/* ------------------------------------------------------------------------------------------------
					 *
					 * Packet processing is achieved using a state machine with 5 states:
					 *
					 * 		STATE_START			A client is connected and we are ready to receive a request from it
					 * 			-> Client sends us a header
					 *
					 * 		STATE_GOT_HEADER	A client has begun communicating with us and we have received a header from it
					 * 			-> Header is validated
					 *
					 * 		STATE_HDR_VALID		A client send us a header, which we received, and we have verified it is valid
					 * 			-> Payload of size specified in header is sent
					 *
					 * 		STATE_GOT_PAYLD		A client has sent us a payload for the header we already received
					 * 			-> Command is processed either by commandProcessor, or handed off to the FPM for handling
					 *
					 * 		STATE_COMPLETE		We have finished receiving header + payload from the client, so become idle
					 *
					 * 		If errors are encountered during any state, it is handled and the client put into STATE_COMPLETE.
					 * 		New clients are also put into STATE_COMPLETE.
					 *
					 * ------------------------------------------------------------------------------------------------
					 */

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Manage reception of header
					if (pState->state == STATE_START)
					{
						numBytesToRead = sizeof(struct protocol_header) - pState->size;

						PRTDBG("CmdProc: Trying to get %d bytes of header...\r\n", numBytesToRead);

						numBytesRead = lwip_read(i, pState->pHdr + pState->size, numBytesToRead);
						PRTDBG("Read %d bytes\r\n", numBytesRead);
						if (numBytesRead == 0)
						{
							// Client has disconnected or an error occurred, so disconnect client
							disconnectClient(&state[i-1], &i, &masterSet, &numConnectedClients);
						}
						else if (numBytesRead < numBytesToRead)
						{
							pState->timeoutCount++;
						}

						pState->size += numBytesRead;

						// If we have full header move to next state
						if (pState->size == sizeof(struct protocol_header))
						{
							pState->state = STATE_GOT_HEADER;
							// We don't want to allow this loop to continue trying to read data as there might not be any left!
							// Drop out and let select re-enter if there is payload to read...
							PRTDBG("Got header OK\r\n");
							if (pState->pHdr->payload_sz != 0) {
								break;
							}
						}

					} // END if state == STATE_START

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Validate header
					if (pState->state == STATE_GOT_HEADER)
					{

						// Validate header
						PRTDBG("IN STATE_GOT_HEADER\r\n");

						if(validateRequest(pState->pHdr, pState)==0)
						{
							// Header is valid!

							// If a BUS_DIRECT write operation update pState accordingly
							if (( pState->pHdr->bus_target==BUS_DIRECT) && (pState->pHdr->command==CMD_ACCESS) && (pState->pHdr->state==STATE_WRITE) )
							{
								pState->busDirectSize = pState->pHdr->payload_sz;
								pState->pBusDirect = (u8*)pState->pHdr->address;
								//DBGOUT("CmdProc: Got a BUS_DIRECT, CMD_ACCESS STATE_WRITE!\r\n");
							}

							pState->state = STATE_HDR_VALID;
							PRTDBG("CmdProc: Header is valid.\r\n");
						}
						else
						{
							// Header NOT valid
							DBGOUT("CmdProc: Header received but is invalid.\r\n");
							//DUMPHDR(pState->pHdr);
							generateErrorResponse(pTxBuffer, clientSocket, pState);
							pState->state = STATE_COMPLETE;
						}

					} // END if state == STATE_GOT_HEADER

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Header is OK so try to get payload for packet
					if (pState->state == STATE_HDR_VALID)
					{

						//DUMPHDR(pState->pHdr);

						// Note that lwip will reject addresses of 0 as NULL pointers

						// Check if this is a direct memory receive, if so handle it
						if ( (pState->pHdr->bus_target==BUS_DIRECT) && (pState->pHdr->command==CMD_ACCESS) && (pState->pHdr->state==STATE_WRITE) )
						{
							//DBGOUT("CmdProc: BUS_DIRECT write: Trying to read %d bytes to 0x%08x...\r\n", pState->busDirectSize, pState->pBusDirect);

							// Read payload directly to DDR at specified address
							numBytesRead = lwip_read(i, (void*)(pState->pBusDirect), pState->busDirectSize);

							//DBGOUT("CmdProc: BUS_DIRECT Write: Read %d bytes...\r\n", numBytesRead);

							if (numBytesRead<=0)
							{
								// Client has disconnected or an error occurred
								DBGOUT("CmdProc: Client disconnected during BUS_DIRECT write!\r\n");
								DUMPHDR(pState->pHdr);
								DBGOUT("remaining bus direct size = 0x%x\r\n", pState->busDirectSize);
								disconnectClient(&state[i-1], &i, &masterSet, &numConnectedClients);
								break;
							}

							// Update counters with data received
							pState->pBusDirect += numBytesRead;
							pState->busDirectSize -= numBytesRead;
							pState->gotData = 1;

							if (pState->busDirectSize == 0)
							{
								// Bypass normal reception of payload as we already have it
								//DBGOUT("CmdProc: Finished payload rx on BUS_DIRECT operation!\r\n");
								pState->state = STATE_GOT_PYLD;
							}

						}
						else
						{

							if (pState->pHdr->payload_sz > NET_LRG_RX_BUFFER_SZ)
							{
								// Too big to receive so flush it's data and send the client an error
								DBGOUT("CmdProc: payload_sz %d exceeds maximum (%d), stopping processing packet.\r\n", pState->pHdr->payload_sz, NET_MAX_PAYLOAD_SZ);
								flushSocket(i, (void*)pState->pPayload, pState->payloadBufferSz);
								SETERR(pState, ERR_PAYLOAD_TOO_BIG, "Payload %d exceeds maximum of %d, cannot process.", (int)pState->pHdr->payload_sz, NET_LRG_RX_BUFFER_SZ);
								generateErrorResponse(pTxBuffer, clientSocket, pState);
								pState->state = STATE_COMPLETE;
							}
							else
							{

								if (pState->pHdr->payload_sz > pState->payloadBufferSz)
								{
									// Increase payload buffer from nominal to large
									pState->pPayload = realloc(pState->pPayload, NET_LRG_RX_BUFFER_SZ);
									pState->payloadBufferSz = NET_LRG_RX_BUFFER_SZ;
									if (pState->pPayload == NULL)
									{
										DBGOUT("CmdProc: Error - can't realloc. RX buffer!\r\n");
										flushSocket(i, (void*)pState->pPayload, pState->payloadBufferSz);
										SETERR(pState, ERR_RX_MALLOC_FAILED, "Cannot realloc RX payload buffer to %d.", NET_LRG_RX_BUFFER_SZ);
										generateErrorResponse(pTxBuffer, clientSocket, pState);
										pState->state = STATE_COMPLETE;
									}
									DBGOUT("CmdProc: Resized payload buffer to %d numBytesToRead=%d\r\n", pState->payloadBufferSz, numBytesToRead);

								}

								// Skip processing if the realloc failed
								if (pState->state == STATE_COMPLETE)
								{
									numBytesToRead = 0;
								}
								else
								{
									numBytesToRead = pState->pHdr->payload_sz;
								}

								if (numBytesToRead != 0)
								{
									//DBGOUT("CmdProc: Trying to get %d bytes of payload (payload_sz=%d)\r\n", numBytesToRead, pState->pHdr->payload_sz);
									numBytesRead = lwip_read(i, pState->pPayload + (pState->size - sizeof(struct protocol_header)), numBytesToRead);

									if (numBytesRead <= 0)
									{
										// Client has disconnected or an error occurred
										DBGOUT("CmdProc: Client disconnected during STATE_HDR_VALID.\r\n");
										disconnectClient(&state[i-1], &i, &masterSet, &numConnectedClients);
									}
									else
									{
										PRTDBG("CmdProc: Read %d bytes of %d as payload.\r\n", numBytesRead, numBytesToRead);
										pState->gotData = 1;
									}

									pState->size += numBytesRead;
								}

								// Check if this is the entire payload received
								if (pState->size == pState->pHdr->payload_sz + sizeof(struct protocol_header))
								{
									pState->state = STATE_GOT_PYLD;
									PRTDBG("CmdProc: Finished receiving payload!\r\n");
								}
								else
								{
									// Still more data to receive so re-enter select call
									break;
								}

							}

						}

					} // END if state == STATE_HDR_VALID

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					if (pState->state == STATE_GOT_PYLD)
					{

						PRTDBG("CmdProc: Received entire packet...\r\n");

						// Generate response
						//if (!commandHandler(pState->pHdr, pTxHeader, pState->pPayload, pTxBuffer+sizeof(struct protocol_header), pMux, pGpio, &reloadRequested, pState))
						if (!commandHandler(pState->pHdr, pTxHeader, pState->pPayload, pTxBuffer+sizeof(struct protocol_header), &reloadRequested, pState))
						{

							// An error occured handling request
							generateErrorResponse(pTxBuffer, clientSocket, pState);

						}
						else
						{
							// Send response
							if (lwip_send(clientSocket, pTxBuffer, sizeof(struct protocol_header) + pTxHeader->payload_sz, 0) == -1)
							{
								// Error occurred during response
								DBGOUT("CmdProc: Error sending response packet! (has client disconnected?)\r\n");
							}
							else
							{
								// Everything OK!
								PRTDBG("CmdProc: Sent response OK.\r\n");
							}
						}
						pState->state = STATE_COMPLETE;

					} // END if state == STATE_GOT_PYLD

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

				}	// END else clause

			}	// END FD_ISSET(i)

		}	// END for (fd)



		// ********************************* START IDLE TICK *********************************

		// Scan all clients and see if they are active, in which case increase the timeoutCount tick on them
		// Added gotData flag which inhibits timeout count increment if set (otherwise we get invalid timeouts when receiving large payloads)
		j=0;
		do
		{
			if (state[j].state!=STATE_COMPLETE && !state[j].gotData)
			{
				//DBGOUT("T");
				state[j].timeoutCount++;
				if (state[j].timeoutCount > NET_DEFAULT_TIMEOUT_LIMIT)
				{
					// Client has timed out
					DBGOUT("CmdProc: Client #%d - timed out on operation.\r\n", j+1);
					state[j].state = STATE_COMPLETE;
				}
			}
			j++;
		} while (j<NET_MAX_CLIENTS);

		// ********************************* END IDLE TICK *********************************



	}	// END while(reloadRequested==-1)
	// ************************************************ END MAIN SERVER LOOP ******************************************************

	DBGOUT("CmdProc: Triggering firmware reload to index %d...\r\n", reloadRequested);

	// Cleanly disconnect all clients
	i = 0;
	do
	{
		disconnectClient(&state[i], &i, &masterSet, &numConnectedClients);
		i++;
	} while (numConnectedClients>0);

	// Wait some time
	sleep(10000);

	// Do SysAce reload
	DBGOUT("CmdProc: SystemACE rebooting to image %d...\r\n", reloadRequested);
	reloadChain(&sysace, reloadRequested);

	sleep(10000);

	// Do emergency SysAce reload to image 0, will only execute if above image can't be found
	DBGOUT("CmdProc: SystemACE failsafe boot initiated, booting to image 0...\r\n");
	reloadChain(&sysace, 0);

}



/**
 * Cleanly disconnects a client and frees any payload buffers > NET_NOMINAL_RX_BUFFER_SZ
 *
 * @param pState pointer to client state struct of client that has disconnected
 * @param pIndex pointer to fd of client that is disconnecting
 * @param pFdSet pointer to fd_set of read file descriptors
 * @param pNumConnectedClients pointer to number of connected clients
 */
void disconnectClient(struct clientStatus* pState, int *pIndex, fd_set* pFdSet, u8 *pNumConnectedClients)
{

	//DBGOUT("DiscClient: Client #%d disconnected.\r\n", *pIndex);
	lwip_close(*pIndex);
	FD_CLR(*pIndex, pFdSet);
	(*pNumConnectedClients)--;

	// If payload buffer exceeds nominal size, reduce it
	if (pState->payloadBufferSz > NET_NOMINAL_RX_BUFFER_SZ)
	{
		free(pState->pPayload);
		pState->pPayload = malloc(NET_NOMINAL_RX_BUFFER_SZ);
		if (pState->pPayload == NULL)
		{
			// Can't allocate payload space
			DBGOUT("DiscClient: Can't re-malloc payload buffer for client after large packet!\r\n");
			// TODO: HANDLE THIS ERROR
		}
		else
		{
			DBGOUT("DiscClient: Resized payload buffer to %d\r\n", NET_NOMINAL_RX_BUFFER_SZ);
		}
	}

	pState->state = STATE_COMPLETE;
}


/**
 * Processes received commands over LWIP.  It is assumed that packets are well formed
 * and have been checked before passing to this function.
 *
 * @param pRxHeader pointer to protocol_header for received packet
 * @param pTxHeader pointer to protocol_header for outbound packet
 * @param pRxPayload pointer to payload buffer of received packet
 * @param pTxPayload pointer to payload buffer for outbound packet
 * @param pReloadRequested pointer to firmware reload index in main event loop
 * @param pClient pointer to client status
 *
 * @return 0 if request completed successfully, -1 if an error occured.
 */
int commandHandler(struct protocol_header* pRxHeader,
                        struct protocol_header* pTxHeader,
                        u8* pRxPayload,
                        u8* pTxPayload,
                        int* pReloadRequested,
                        struct clientStatus *pClient)
{

	int i;					// General use variable
	int dataWidth = 0;		// Width of data type for operation in bytes
	int responseSize = 0;	// Payload size for response packet in bytes
	u32 numOps = 0;			// Number of requested operations performed
	u8 state = 0;			// Status byte
	int i2cError = 0;		// Flag used to tell if I2C error handler routine needs to run, non 0 represents error code
	u8 slaveAddress = 0;
	u8 busIndex = 0;

	// Native size pointers for various data widths
	u32* pRxPayload_32  = NULL;
	u16* pRxPayload_16	= NULL;
	u8*  pRxPayload_8	= NULL;
	void *pRxPld;
	u32* pTxPayload_32  = NULL;
	u16* pTxPayload_16	= NULL;
	u8*  pTxPayload_8	= NULL;
	void *pTxPld;

	// Copy original header to response packet, take a local copy of the status byte to update
	memcpy(pTxHeader, pRxHeader, sizeof(struct protocol_header));
	state = pRxHeader->state;

	// Pointers to received and outgoing packet payloads
	pRxPayload_32 = (u32*)pRxPayload;
	pRxPayload_16 = (u16*)pRxPayload;
	pRxPayload_8  = (u8*)pRxPayload;
	pTxPayload_32 = (u32*)pTxPayload;
	pTxPayload_16 = (u16*)pTxPayload;
	pTxPayload_8  = (u8*)pTxPayload;

	// Nudge outgoing packet payload pointer by 1 so as to skip first u32 which will be populated with numOps
	pTxPayload_32 += 1;

	// Number of REQUESTED ops (only valid for read operations)
	u32 numRequestedReads = *pRxPayload_32;

	// Increment response size to include numOps as first entry
	responseSize += sizeof(u32);

	// Reset flags
	u32 dmaControllerAck = 0;
	int status;
	int configAck = 0;

	// Make sure response payload doesn't exceed maximum
	if (CMPBIT(state, STATE_READ))
	{
		if ((sizeof(u32) + (dataWidth * numRequestedReads)) > MAX_PAYLOAD_SIZE)
		{
			DBGOUT("Response packet too large\r\n");
			SETERR(pClient, ERR_CLIENT_RESPONSE_TOO_BIG, "Response to read request would exceed maximum payload size (%d > %d).", (int)(sizeof(u32) + (dataWidth * numRequestedReads)), MAX_PAYLOAD_SIZE);
			pRxHeader->command = 0;		// Hack to bypass packet processing
		}
	}

	// Determine operation type
	switch(pRxHeader->command)
	{

		case CMD_PERSONALITY:

			if(handlePersonalityCommand(pRxHeader, pTxHeader, pRxPayload, pTxPayload, &responseSize))
			{
				SBIT(state, STATE_ACK);
			}
			else
			{
				SBIT(state, STATE_NACK);
				// TODO: Set FEM error state
			}
			break;

		case CMD_INTERNAL:
			// Determine operation type
			switch(pRxHeader->address)
			{
			case CMD_INT_FIRMWARE:
				//DBGOUT("CmdDisp: Requested systemACE firmware reload, image %d\r\n", pRxHeader->bus_target);
				SBIT(state, STATE_ACK);
				*pReloadRequested = pRxHeader->bus_target;
				break;
			case CMD_INT_GET_HW_INIT_STATE:
				SBIT(state, STATE_ACK);
				responseSize = 4;
				*(pTxPayload_32) = femErrorState;
				break;
			case CMD_INT_WRITE_TO_SYSACE:
				DBGOUT("CmdDisp: Requested SystemACE file write, doing dummy write of 8 bytes from 0x40000000...\r\n");
				writeImage(1, 0x40000000, 8);
				SBIT(state, STATE_ACK);
				break;
			case CMD_INT_GET_FPM_ID:
				responseSize = 4;
				*(pTxPayload_32) = (u32)getFpmId();
				SBIT(state, STATE_ACK);
				break;
			}
			break;

		case CMD_ACQUIRE:

			numOps = 0;

			/*
			 * Packet structure:
			 *
			 * magic = 0xDEADBEEF
			 * command = CMD_ACQUIRE
			 * bus_target = 0 (ignored)
			 * data_width = WIDTH_LONG
			 * state = 0 (ignored)
			 * address = protocol_acq_command [enum: config/start/stop/status]
			 * payload = struct protocol_acq_config [acqMode, bufferSz, bufferCnt, numAcq]
			 *
			 */

			// Cast payload to struct
			protocol_acq_config* pAcqConfig =(protocol_acq_config*)pRxPayload_32;

			switch(pRxHeader->address)
			{

				case CMD_ACQ_CONFIG:
					// Send config. request (does not block for CMD_ACQ_CONFIG)
					dmaControllerAck = acquireConfigMsgSend(pRxHeader->address, pAcqConfig->bufferSz, pAcqConfig->bufferCnt, pAcqConfig->numAcq, pAcqConfig->acqMode, pAcqConfig->bdCoalesceCount, 10000);

					// Wait for response
					configAck = acquireConfigAckReceive();
					if (configAck==1)
					{
						SBIT(state, STATE_ACK);
					}
					else if (configAck==0)
					{
						SBIT(state, STATE_NACK);
						SETERR(pClient, ERR_ACQ_CONFIG_NACK, "NACK from PPC1 for acquire configure request.");
					}
					else
					{
						SBIT(state, STATE_NACK);
						SETERR(pClient, ERR_ACQ_CONFIG_BAD_ACK, "ACK from PPC1 for acquire configure request had error or timeout.");
					}

					break;

				case CMD_ACQ_START:
				case CMD_ACQ_STOP:
					dmaControllerAck = acquireConfigMsgSend(pRxHeader->address, 0, 0, 0, 0, 0, 10000);
					if (dmaControllerAck==1)
					{
						SBIT(state, STATE_ACK);
					}
					else if (dmaControllerAck==0)
					{
						SBIT(state, STATE_NACK);
						SETERR(pClient, ERR_ACQ_OP_NACK, "NACK from PPC1 for acquire start / stop request.");
					}
					else
					{
						SBIT(state, STATE_NACK);
						SETERR(pClient, ERR_ACQ_OP_BAD_ACK, "ACK from PPC1 for acquire start / stop request had error or timeout.");
					}
					break;

				case CMD_ACQ_STATUS:
					memcpy(pTxPayload_32, (u32*)BADDR_BRAM, (12*4));			// TODO: Change to sizeof(acqStatusBlock) from fem_common.h
					responseSize += (12*4);										// TODO: Change to sizeof(acqStatusBlock) from fem_common.h
					SBIT(state, STATE_ACK);
					break;

				default:
					DBGOUT("CmdDisp: Unrecognised CMD_ACQUIRE! (%d)\r\n", pRxHeader->address);
					break;

			} // END switch(pRxHeader->address)

			break;

		case CMD_ACCESS:

			switch(pRxHeader->bus_target)
			{

				// --------------------------------------------------------------------
				case BUS_EEPROM:

					dataWidth = sizeof(u8); // All EEPROM operations are byte level

					if (CMPBIT(state, STATE_READ))
					{

						i = readFromEEPROM(pRxHeader->address, pTxPayload + 4, *pRxPayload_32);
						if (i != *pRxPayload_32)
						{
							// EEPROM read failed
							i2cError = i;
						}
						else
						{
							SBIT(state, STATE_ACK);
							responseSize += i;
							numOps = i;
						}
					}
					else if (CMPBIT(state, STATE_WRITE))
					{

						i = writeToEEPROM(pRxHeader->address, pRxPayload, pRxHeader->payload_sz);
						if (i != pRxHeader->payload_sz)
						{
							// EEPROM write failed
							i2cError = i;
						} else
						{
							SBIT(state, STATE_ACK);
							numOps = i;
						}

					}
					break; // BUS_EEPROM

				// --------------------------------------------------------------------
				case BUS_I2C:

					dataWidth = sizeof(u8);	// All I2C operations are byte level

					/*
					 * Decode address field
					 * Least significant word (lower byte) = I2C slave address
					 * Most significant word (lower byte)  = Bus index (0=LM82, 1=EEPROM, 2=PWR_RHS, 3=PWR_LHS)
					 */
					slaveAddress = (pRxHeader->address & 0xFF);
					busIndex = (pRxHeader->address & 0xFF00) >> 8;

					if (CMPBIT(state, STATE_READ))
					{
						i = readI2C(busIndex, slaveAddress, (u8*)pTxPayload_32, *pRxPayload_32);
						if (i != *pRxPayload_32)
						{
							// I2C operation failed
							i2cError = i;
						}
						else
						{
							// Set ACK, payload size
							SBIT(state, STATE_ACK);
							responseSize += i;
							numOps = i;
						}

					}
					else if (CMPBIT(state, STATE_WRITE))
					{
						i = writeI2C(busIndex, slaveAddress, pRxPayload, pRxHeader->payload_sz);
						if (i != pRxHeader->payload_sz)
						{
							// I2C operation failed
							i2cError = i;
						}
						else
						{
							// Set ACK
							SBIT(state, STATE_ACK);
							numOps = i;
						}
					}
					break; // BUS_I2C

				// --------------------------------------------------------------------
				case BUS_RAW_REG:

					// Supports BYTE, WORD and LONG operations

					if (CMPBIT(state, STATE_READ)) // READ OPERATION
					{

						switch(pRxHeader->data_width)
						{
						case WIDTH_BYTE:
							dataWidth = 1;
							for (i=0; i<*pRxPayload_32; i++)
							{
								*(pTxPayload_8 + i) = readRegister_8(pRxHeader->address + (i*dataWidth));
								responseSize += dataWidth;
								numOps++;
							}
							SBIT(state, STATE_ACK);
							break;

						case WIDTH_WORD:
							dataWidth = 2;
							for (i=0; i<*pRxPayload_32; i++)
							{
								*(pTxPayload_16 + i) = readRegister_16(pRxHeader->address + (i*dataWidth));
								responseSize += dataWidth;
								numOps++;
							}
							SBIT(state, STATE_ACK);
							break;

						case WIDTH_LONG:
							dataWidth = 4;
							for (i=0; i<*pRxPayload_32; i++)
							{
								*(pTxPayload_32+i) = readRegister_32(pRxHeader->address + (i*dataWidth));
								responseSize += dataWidth;
								numOps++;
							}
							SBIT(state, STATE_ACK);
							break;

						default:
							SBIT(state, STATE_NACK);

						} // END (switch(pRxHeader->data_width))

					}
					else if (CMPBIT(state, STATE_WRITE)) // WRITE OPERATION
					{

						switch(pRxHeader->data_width)
						{
						case WIDTH_BYTE:
							dataWidth = 1;
							for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
							{
								pRxPayload_8 = (u8*)pRxPayload;
								writeRegister_8( pRxHeader->address + (i*dataWidth), *(pRxPayload_8+i) );
								numOps++;
							}
							SBIT(state, STATE_ACK);
							break;

						case WIDTH_WORD:
							dataWidth = 2;
							for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
							{
								pRxPayload_16 = (u16*)pRxPayload;
								writeRegister_16( pRxHeader->address + (i*dataWidth), *(pRxPayload_16+i) );
								numOps++;
							}
							SBIT(state, STATE_ACK);
							break;

						case WIDTH_LONG:
							dataWidth = 4;
							for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
							{
								pRxPayload_32 = (u32*)pRxPayload;
								writeRegister_32( pRxHeader->address + (i*dataWidth), *(pRxPayload_32+i) );
								numOps++;
							}
							SBIT(state, STATE_ACK);
							break;

						default:
							SBIT(state, STATE_NACK);

						} // END (switch(pRxHeader->data_width))
					}

					break; // BUS_RAW_REG

				// --------------------------------------------------------------------
				case BUS_RDMA:

					dataWidth = sizeof(u32);
					pTxPayload_32 = (u32*)(pTxPayload+responseSize);

					// RDMA READ operation
					if (CMPBIT(state, STATE_READ))
					{
						pRxPayload_32 = (u32*)pRxPayload;
						SBIT(state, STATE_ACK);
						for (i=0; i<*pRxPayload_32; i++)
						{
							//DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*dataWidth));
							//status = readRdma( (rdmaAddrNew+i) , (pTxPayload_32+i) );
							status = readRdma( (pRxHeader->address + i) , (pTxPayload_32+i) );
							if (status==XST_FAILURE)
							{
								//DBGOUT("CmdDisp: Error reading RDMA, aborting!\r\n");
								numOps = 0;
								SBIT(state, STATE_NACK);
								SETERR(pClient, ERR_RDMA_READ, "Error occurred during RDMA read.");
								i = *pRxPayload_32;						// Skip any further processing in this loop
							}
							else
							{
								//DBGOUT(" VALUE 0x%x\r\n", readRdma(pRxHeader->address + i));
								responseSize += dataWidth;
								numOps++;
							}
						}

					}

					// RDMA WRITE operation
					else if (CMPBIT(state, STATE_WRITE))
					{
						SBIT(state, STATE_ACK);
						for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
						{
							pRxPayload_32 = (u32*)pRxPayload;
							//DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + i, *(pRxPayload_32+i));
							//status = writeRdma(rdmaAddrNew + i, *(pRxPayload_32+i));
							status = writeRdma(pRxHeader->address + i, *(pRxPayload_32+i));
							if (status==XST_FAILURE)
							{
								//DBGOUT("CmdDisp: Error writing RDMA, aborting!\r\n");
								numOps = 0;
								SBIT(state, STATE_NACK);
								SETERR(pClient, ERR_RDMA_WRITE, "Error occurred during RDMA write.");
								i = ((pRxHeader->payload_sz)/dataWidth);	// Skip any further processing
							}
							else
							{
								numOps++;
							}
						}

					}
					break; // BUS_RDMA

				// --------------------------------------------------------------------
				case BUS_DIRECT:
					switch(pRxHeader->data_width)
					{
					case WIDTH_BYTE: dataWidth = 1; break;
					case WIDTH_WORD: dataWidth = 2; break;
					case WIDTH_LONG: dataWidth = 4; break;
					}
					numOps = pRxHeader->payload_sz/dataWidth;
					SBIT(state, STATE_ACK);
					break;

#ifdef USE_CACHE
					if (CMPBIT(state, STATE_WRITE))
					{
						XCache_FlushDCacheRange((unsigned int)(pRxHeader->address), pRxHeader->payload_sz);
					}
#endif

					if (CMPBIT(state, STATE_ACK))
					{
						// Update number of operations in payload
						pTxPayload_32 = (u32*)pTxPayload;
						*pTxPayload_32 = numOps;
					}

			} // END switch(bus)

	} // END switch(command)

	// Error handler for I2C (common to BUS_I2C and BUS_EEPROM)
	if (i2cError<0)
	{
		SBIT(state, STATE_NACK);

		switch(i2cError)
		{
		case IIC_ERR_INVALID_INDEX:
			SETERR(pClient, ERR_I2C_INVALID_BUS_INDEX, "Invalid I2C bus index %d.", busIndex);
			break;
		case IIC_ERR_SLAVE_NACK:
			SETERR(pClient, ERR_I2C_SLAVE_NACK, "I2C slave 0x%08x on bus %d NACKed.", slaveAddress, busIndex);
			break;
		case IIC_ERR_TIMEOUT:
			SETERR(pClient, ERR_I2C_TIMEOUT, "I2C operation timed for slave address 0x%08x.", slaveAddress);
			break;
		case IIC_ERR_BUS_BUSY:
			SETERR(pClient, ERR_I2C_BUSY, "I2C bus index %d is busy.", busIndex);
			break;
		case IIC_ERR_SET_ADDR:
			SETERR(pClient, ERR_I2C_ADDRESS_ERROR, "Can't assert I2C address 0x%08x on bus index %d.", slaveAddress, busIndex);
			break;
		case IIC_ERR_INVALID_OP_MODE:
			SETERR(pClient, ERR_I2C_INVALID_OPMODE, "Invalid operation mode (internal error).");
			break;
		case IIC_ERR_GENERAL_CALL_ADDR:
			SETERR(pClient, ERR_I2C_GENERAL_CALL, "I2C controller reported general call address (internal error).");
			break;
		default:
			SETERR(pClient, ERR_I2C_UNKNOWN_ERROR, "An unknown I2C error occurred.");
			break;
		}

	}

	// If ACK bit is set update the response packet header
	if (CMPBIT(state, STATE_ACK))
	{
		// Build response header (all fields other status byte stay same as received packet)
		pTxHeader->state = state;
		pTxHeader->payload_sz = responseSize;

		// Update number of operations in payload
		pTxPayload_32 = (u32*)pTxPayload;
		*pTxPayload_32 = numOps;

		return 1;
	}

	return 0;
}



/**
 * Validates the fields of a header for consistency
 * @param pHeader pointer to header
 * @param pClient pointer to client status
 *
 * @return 0 if header logically correct, -1 and sets errorString / errorCode in pClient if incorrect
 */
int validateRequest(struct protocol_header *pHeader, struct clientStatus *pClient)
{

	// Common checks

	// Verify magic is correct
	if (pHeader->magic != PROTOCOL_MAGIC_WORD)
	{
		SETERR(pClient, ERR_HDR_INVALID_MAGIC, "Header magic word 0x%08x is invalid.", (unsigned int)pHeader->magic)
		return -1;
	}

	// Data width should never be 0
	if (pHeader->data_width==0)
	{
		SETERR(pClient, ERR_HDR_INVALID_DATA_WIDTH, "Data width should never be 0.");
		return -1;
	}

	// Ensure response payload size does not exceed maximum
	int numRequestedOps = 0;
	int responseSize = (sizeof(u32) + (pHeader->data_width * numRequestedOps));
	if ( responseSize > MAX_PAYLOAD_SIZE )
	{
		return -1;
	}

	// Logical checks
	switch(pHeader->command)
	{
		case CMD_ACCESS:
			// A normal command, so make sure the options are valid
			switch(pHeader->bus_target)
			{

				// CMD_ACCESS must always specify an operation type, read/write...
				if ( (pHeader->state!=STATE_READ) && (pHeader->state=STATE_WRITE) )
				{
					SETERR(pClient, ERR_HDR_INVALID_RW_STATE, "Neither R or W bit (0x%02x) specified for command %d.", pHeader->state, pHeader->command);
					return -1;
				}

				// CMD_ACCESS + STATE_READ must always have a payload_sz of sizeof(u32)
				if ( (pHeader->state == STATE_READ) && (pHeader->payload_sz!=sizeof(u32)) )
				{
					SETERR(pClient, ERR_HDR_INVALID_PAYLOAD_SZ, "Payload size must always be 4 (got %d) for CMD_ACCESS read operation.", (unsigned int)pHeader->payload_sz);
					return -1;
				}

				case BUS_EEPROM:
					// Data width must always be 8bit
					if (pHeader->data_width!=WIDTH_BYTE)
					{
						SETERR(pClient, ERR_HDR_INVALID_DATA_WIDTH, "Invalid data width of %d for CMD_ACCESS, BUS_EEPROM (should be 1).", pHeader->data_width);
						return -1;
					}
					break;

				case BUS_I2C:
					// Data width must always be 8bit
					if (pHeader->data_width!=WIDTH_BYTE)
					{
						SETERR(pClient, ERR_HDR_INVALID_DATA_WIDTH, "Invalid data width of %d for CMD_ACCESS, BUS_I2C (should be 1).", pHeader->data_width);
						return -1;
					}
					// Address most significant byte must be 0-3 only
					if ( (((pHeader->address & 0xF00) >> 16)<0) && (((pHeader->address & 0xF00) >> 16)>3) )
					{
						SETERR(pClient, ERR_HDR_INVALID_ADDRESS, "Invalid address for BUS_I2C, MSB should be in the range 0-3 (got %d).", (int)((pHeader->address & 0xF00) >> 16));
						return -1;
					}
					break;

				case BUS_RAW_REG:
					// Everything valid!
					break;

				case BUS_RDMA:
					// Data width must always be 32bit
					if (pHeader->data_width!=WIDTH_LONG)
					{
						SETERR(pClient, ERR_HDR_INVALID_DATA_WIDTH, "Invalid data witdh of %d for CMD_ACCESS, BUS_RDMA (should be 3).", pHeader->data_width);
						return -1;
					}
					break;

				case BUS_DIRECT:
					// Only write operations make sense here
					if (pHeader->state!=STATE_WRITE)
					{
						SETERR(pClient, ERR_HDR_INVALID_RW_STATE, "Only W bit should be set on CMD_ACCESS, BUS_DIRECT (got 0x%02x).", pHeader->state);
						return -1;
					}
					break;

				case BUS_UNSUPPORTED:
					SETERR(pClient, ERR_HDR_INVALID_BUS, "Invalid bus for CMD_ACCESS (%d).", pHeader->bus_target);
					return -1;
					break;
			}

			break;

		case CMD_INTERNAL:
			switch(pHeader->address)
			{
			case CMD_INT_FIRMWARE:		// address = CMD_INT_FIRMWARE, bus_target = 0-7 (firmware ID for systemAce)
				if (pHeader->bus_target > 7)
				{
					SETERR(pClient, ERR_HDR_INVALID_COMMAND, "CMD_INTERNAL to reboot to systemAce image must have bus_target value of 0-7 (got %d).", pHeader->bus_target);
					return -1;
				}
				break;
			case CMD_INT_GET_HW_INIT_STATE:
				// Rest of header is ignored, this case only here to avoid running the default case!
				break;
			case CMD_INT_WRITE_TO_SYSACE:
				// TODO: Header check?
				break;
			default:
				// For CMD_INTERNAL the address field holds the command type...
				SETERR(pClient, ERR_HDR_INVALID_COMMAND, "Invalid CMD_INTERNAL command %d.", (int)pHeader->address);
				return -1;
			}
			break;

		case CMD_PERSONALITY:
			return validatePersonalityHeaderContents(pHeader);
			break;

		case CMD_UNSUPPORTED:
			SETERR(pClient, ERR_HDR_INVALID_COMMAND, "Unsupported command %d.", pHeader->command);
			return -1;
			break;
	}

	// ...otherwise, header is valid!
	return 0;
}



/**
 * Flushes data on given socket.  Generally used after malformed packet or
 * packet exceeding maximum payload size received.
 * Will read in chunks to the specified buffer, overwriting the contents.
 *
 * @param sock socket
 * @param mem pointer to memory buffer
 * @param len size of memory buffer
 */
void flushSocket(int sock, void *mem, int len)
{
	int numBytesRead = len;
	int totalBytes = 0;
	while (len==numBytesRead)
	{
		numBytesRead = lwip_read(sock, mem, len);
		totalBytes+=numBytesRead;
	}
	//DBGOUT("flushSocket: Flush complete, flushed %d bytes.\r\n", totalBytes);
}



/**
 * Generates and an error packet to the provided client socket
 *
 * @param pTxPayload pointer to payload to send (assumed to have a protocol_header struct at this pointer!)
 * @param clientSocket socket identifier for client
 * @param pClient pointer to clientStatus struct for client
 */
void generateErrorResponse(u8* pTxPayload, int clientSocket, struct clientStatus *pClient)
{
	DBGOUT("ERROR: ");
	DBGOUT(pClient->errorString);
	DBGOUT("\r\n");

	int payload_sz = 0;
	int slen = 0;
	struct protocol_header *pHeader = (struct protocol_header*)pTxPayload;

	// First byte in payload is the error code
	*(pTxPayload + sizeof(struct protocol_header)) = pClient->errorCode;
	payload_sz++;

	// Copy original header to TX header
	memcpy(pTxPayload, pClient->pHdr, sizeof(struct protocol_header));

	// Set NACK bit, reset the data width field to WIDTH_BYTE
	SBIT(pHeader->state, STATE_NACK);
	pHeader->data_width = WIDTH_BYTE;

	// Get length of error string
	slen = strlen(pClient->errorString);

	// Copy errorString to payload
	memcpy(pTxPayload + sizeof(struct protocol_header) + payload_sz, pClient->errorString, slen);
	payload_sz += slen;

	pHeader->payload_sz = payload_sz;

	if (lwip_send(clientSocket, pTxPayload, sizeof(struct protocol_header) + payload_sz, 0) == -1)
	{
		xil_printf("GenErrResponse: Error sending packet to client!\r\n");
	}
}
