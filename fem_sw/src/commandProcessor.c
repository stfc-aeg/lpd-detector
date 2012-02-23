/*
 * commandProcessor.c
 *
 * Manages the decoding of received packets and generation
 * of response packets using LwIP library
 *
 */

#include "commandProcessor.h"

/* Manages the connection of clients to the FEM and
 * the reception / validation / response generation of
 * packets.
 *
 */
void commandProcessorThread()
{
	int listenerSocket, clientSocket, newFd, addrSize, numFds, numBytesRead, numBytesToRead, i, j;
	struct sockaddr_in serverAddress, clientAddress;
	fd_set readSet, masterSet;
	struct timeval tv;
	u8 numConnectedClients = 0;

	// Setup and initialise client statuses to idle
	struct clientStatus state[NET_MAX_CLIENTS];
	j=0;
	do
	{
		state[j].state = STATE_COMPLETE;
		state[j].size = 0;
		state[j].timeoutCount = 0;
		state[j].payloadBufferSz = 0;
		j++;
	} while (j<NET_MAX_CLIENTS);

	// RX and TX packet buffers
	// TODO: Tidy these and change signature of commandHandler()!
	u8* pTxBuffer = (u8*)malloc(sizeof(struct protocol_header)+MAX_PAYLOAD_SIZE);
	struct protocol_header* pTxHeader = (struct protocol_header*)pTxBuffer;

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
		DBGOUT("CmdProc: Can't open socket, aborting...\r\n");
		DBGOUT("Terminating thread...\r\n");
		// TODO: Failing to open a socket is a critical failure!  We could put a retry loop here though...?
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
		DBGOUT("CmdProc: Can't bind to socket %d!\r\n", NET_CMD_PORT);
		DBGOUT("Terminating thread...\r\n");
		// TODO: Failing to bind to a socket is a critical failure!  Should we exit?
		return;
	}

	// Begin listening, register listener as FD of interest to read
	if (lwip_listen(listenerSocket, NET_SOCK_BACKLOG) < 0)
	{
		DBGOUT("CmdProc: Can't listen on socket %d!\r\n", NET_CMD_PORT);
		DBGOUT("Terminating thread...\r\n");
		// TODO: Failing to listen on a socket is a critical failure!  Should we exit?
		return;
	}
	FD_SET(listenerSocket, &masterSet);
	numFds = listenerSocket;

	DBGOUT("CmdProc: Socket on port %d ready, awaiting clients (max. clients = %d).\r\n", NET_CMD_PORT, NET_MAX_CLIENTS);

	// ************************************************** MAIN SERVER LOOP ********************************************************
	while (1) {

		// Show our tick over
		//DBGOUT(".");

		// Copy master set over as readSet will be modified
		memcpy(&readSet, &masterSet, (size_t)sizeof(fd_set));

		if (lwip_select(numFds + 1, &readSet, NULL, NULL, &tv) == -1)
		{
			DBGOUT("CmdProc: ERROR - Select failed!\r\n");
			// TODO: What to do here?
		}

		// Check file descriptors, see which one needs servicing
		for (i=0; i<=numFds; i++)
		{
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
						DBGOUT("CmdProc: Error accepting connection!");
						// TODO: Do we need further error handling here?
					}
					else
					{

						DBGOUT("CmdProc: Received new connection! (Client #%d), fd is %d\r\n", numConnectedClients+1, newFd);

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

							state[newFd-1].state = STATE_COMPLETE;		// This causes reset at beginning of receive from existing client loop!

						}
					}

				}
				else
				// ----------------------------------------------------------------------------------------------------
				// Existing client is communicating with us
				{

					clientSocket = i;

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Determine if the last packet was received from client, if so reset client status
					if (state[i-1].state == STATE_COMPLETE)
					{

						//DBGOUT("***** STATE_COMPLETE ****\r\n");

						// Check if previous transaction had an increased payload buffer size and free it if necessary
						if (state[i-1].payloadBufferSz > NET_NOMINAL_RX_BUFFER_SZ)
						{
							free(state[i-1].pPayload);
							state[i-1].pPayload = malloc(NET_NOMINAL_RX_BUFFER_SZ);
							if (state[i-1].pPayload == NULL)
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
						state[i-1].state = STATE_START;
						state[i-1].payloadBufferSz = NET_NOMINAL_RX_BUFFER_SZ;
						state[i-1].size = 0;
						state[i-1].timeoutCount = 0;
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
					if (state[i-1].state == STATE_START)
					{
						numBytesToRead = sizeof(struct protocol_header) - state[i-1].size;

						PRTDBG("CmdProc: Trying to get %d bytes of header...\r\n", numBytesToRead);

						numBytesRead = lwip_read(i, state[i-1].pHdr + state[i-1].size, numBytesToRead);
						//PRTDBG("Read %d bytes\r\n", numBytesRead);
						if (numBytesRead == 0)
						{
							// Client has disconnected
							disconnectClient(&state[i-1], &i, &masterSet, &numConnectedClients);
						}
						else if (numBytesRead < numBytesToRead)
						{
							state[i-1].timeoutCount++;
						}

						state[i-1].size += numBytesRead;

						// If we have full header move to next state
						if (state[i-1].size == sizeof(struct protocol_header))
						{
							state[i-1].state = STATE_GOT_HEADER;
							// We don't want to allow this loop to continue trying to read data as there might not be any left!
							// Drop out and let select re-enter if there is payload to read...
							//PRTDBG("Got header OK\r\n");
							if (state[i-1].pHdr->payload_sz != 0) {
								break;
							}
						}

					} // END if state == STATE_START

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Validate header
					if (state[i-1].state == STATE_GOT_HEADER)
					{

						//PRTDBG("IN STATE_GOT_HEADER\r\n");
						// Validate
						if(validateHeaderContents(state[i-1].pHdr)==0)
						{
							// Header is valid!
							state[i-1].state = STATE_HDR_VALID;
							PRTDBG("CmdProc: Header is valid.\r\n");
						}
						else
						{
							// Header NOT valid
							DBGOUT("CmdProc: Header received but is invalid.\r\n");
							state[i-1].state = STATE_COMPLETE;
						}

					} // END if state == STATE_GOT_HEADER

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

					// Header is OK so try to get payload for packet
					if (state[i-1].state == STATE_HDR_VALID)
					{

						//DUMPHDR(state[i-1].pHdr);

						// TODO: Check address is in valid range FEM_DDR2_START => addr => (FEM_DDR2_END-payload_sz)
						// TODO: We also need to reject an address of 0 as lwip sees this as a NULL pointer and doesn't do the rxbuf->appbuff copy!

						// Check if this is a direct memory receive, if so handle it
						if (	(state[i-1].pHdr->bus_target==BUS_DIRECT) &&
								(state[i-1].pHdr->command==CMD_ACCESS) &&
								(state[i-1].pHdr->state==STATE_WRITE)
							)
						{
							DBGOUT("CmdProc: Got a BUS_DIRECT, CMD_ACCESS STATE_WRITE!\r\n");


							DBGOUT("CmdProc: Trying to read %d bytes to 0x%08x...\r\n", state[i-1].pHdr->payload_sz, state[i-1].pHdr->address);
							// Read payload directly to DDR at specified address
							numBytesRead = lwip_read(i, (void*)(state[i-1].pHdr->address), state[i-1].pHdr->payload_sz);

							DBGOUT("CmdProc: Read %d bytes...\r\n", numBytesRead);
							if (numBytesRead!=state[i-1].pHdr->payload_sz)
							{
								DBGOUT("CmdProc: Only managed to read %d of %d bytes :(\r\n", numBytesRead, state[i-1].pHdr->payload_sz);
								state[i-1].state = STATE_COMPLETE;
								break;
							}
							else
							{
								// Bypass normal reception of payload as we already have it
								state[i-1].state = STATE_GOT_PYLD;
							}

						}
						else
						{

							if (state[i-1].pHdr->payload_sz > NET_MAX_PAYLOAD_SZ)
							{
								DBGOUT("CmdProc: payload_sz %d exceeds maximum (%d), stopping processing packet.\r\n", state[i-1].pHdr->payload_sz, NET_MAX_PAYLOAD_SZ);
								// TODO: Send NACK here!
								state[i-1].state = STATE_COMPLETE;
							}
							else
							{

								if (state[i-1].pHdr->payload_sz > state[i-1].payloadBufferSz)
								{
									// Payload exceeds buffer, increase it by one chunk
									if (state[i-1].payloadBufferSz == NET_NOMINAL_RX_BUFFER_SZ)
									{
										// If we only have nominal buffer, resize to single chunk (saves having n*chunk + nominal at end...)
										state[i-1].pPayload = realloc(state[i-1].pPayload, NET_LRG_PKT_INCREMENT_SZ);
										state[i-1].payloadBufferSz = NET_LRG_PKT_INCREMENT_SZ;
										if (state[i-1].pPayload == NULL)
										{
											DBGOUT("CmdProc: Fatal error - can't realloc rx buffer!\r\n");
											DBGOUT("Terminating thread...\r\n");
											// TODO: Send NACK here!
											return;
										}
									}
									else
									{
										state[i-1].pPayload = realloc(state[i-1].pPayload, state[i-1].payloadBufferSz + NET_LRG_PKT_INCREMENT_SZ);
										state[i-1].payloadBufferSz += NET_LRG_PKT_INCREMENT_SZ;
										if (state[i-1].pPayload == NULL)
										{
											DBGOUT("CmdProc: Fatal error - can't realloc rx buffer!\r\n");
											DBGOUT("Terminating thread...\r\n");
											// TODO: Send NACK here!
											return;
										}
									}

									// Make sure to not read off the end of this packet - this might not be required as all comms will be synchronous...
									if ( state[i-1].pHdr->payload_sz - (state[i-1].size - sizeof(struct protocol_header)) < NET_LRG_PKT_INCREMENT_SZ )
									{
										numBytesToRead = state[i-1].pHdr->payload_sz - (state[i-1].size - sizeof(struct protocol_header));
									}
									else
									{
										numBytesToRead = NET_LRG_PKT_INCREMENT_SZ;
									}

									DBGOUT("CmdProc: Resized payload buffer to %d\r\n", state[i-1].payloadBufferSz);

								}
								else
								{
									// Payload will fit in existing buffer
									numBytesToRead = state[i-1].pHdr->payload_sz;
								}

								if (numBytesToRead != 0)
								{
									//DBGOUT("CmdProc: Trying to get %d bytes of payload (payload_sz=%d)\r\n", numBytesToRead, state[i-1].pHdr->payload_sz);
									numBytesRead = lwip_read(i, state[i-1].pPayload + (state[i-1].size - sizeof(struct protocol_header)), numBytesToRead);

									if (numBytesRead == 0)
									{
										// Client has disconnected
										disconnectClient(&state[i-1], &i, &masterSet, &numConnectedClients);
									}
									else
									{
										PRTDBG("CmdProc: Read %d bytes of %d as payload.\r\n", numBytesRead, numBytesToRead);
									}

									state[i-1].size += numBytesRead;
								}

								// Check if this is the entire payload received
								if (state[i-1].size == state[i-1].pHdr->payload_sz + sizeof(struct protocol_header))
								{
									state[i-1].state = STATE_GOT_PYLD;
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

					if (state[i-1].state == STATE_GOT_PYLD)
					{

						PRTDBG("CmdProc: Received entire packet...\r\n");

						// Generate response
						if (state[i-1].pHdr->command == CMD_PERSONALITY)
						{
							// Hand off to personality module
							handlePersonalityCommand(state[i-1].pHdr, pTxHeader, state[i-1].pPayload, pTxBuffer+sizeof(struct protocol_header));
						}
						else
						{
							// Process request ourselves
							commandHandler(state[i-1].pHdr, pTxHeader, state[i-1].pPayload, pTxBuffer+sizeof(struct protocol_header));
						}

						PRTDBG("CmdProc: Packet decoded, sending response...\r\n");

						if (lwip_send(clientSocket, pTxBuffer, sizeof(struct protocol_header) + pTxHeader->payload_sz, 0) == -1)
						{
							// Error occured during response
							DBGOUT("CmdProc: Error sending response packet! (has client disconnected?)\r\n");
							// TODO: Set FEM error state
						}
						else
						{
							// Everything OK!
							PRTDBG("CmdProc: Sent response OK.\r\n");
							state[i-1].state = STATE_COMPLETE;
						}

					} // END if state == STATE_GOT_PYLD

					// -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

				}	// END else clause

			}	// END FD_ISSET(i)

		}	// END for (fd)



		// ********************************* START IDLE TICK *********************************

		// Scan all clients and see if they are active, in which case increase the timeoutCount tick on them
		j=0;
		do
		{
			//DBGOUT("!");

			if (state[j].state!=STATE_COMPLETE)
			{

				// Show timeout tick
				//DBGOUT("T");

				state[j].timeoutCount++;
				if (state[j].timeoutCount > NET_DEFAULT_TIMEOUT_LIMIT)
				{
					// Client has timed out :(
					DBGOUT("CmdProc: Client #%d - timed out on operation.\r\n", j+1);
					state[j].state = STATE_COMPLETE;
				}
			}
			j++;
		} while (j<NET_MAX_CLIENTS);

		// ********************************* END IDLE TICK *********************************



	}	// END while(1)
	// ************************************************ END MAIN SERVER LOOP ******************************************************

	// Code below here will never run...  but just in case output debug message
	DBGOUT("CmdProc: Exiting thread! [SHOULD NEVER EXECUTE!]\r\n");

}



/*
 * Cleanly disconnects a client and frees any payload buffers > NET_NOMINAL_RX_BUFFER_SZ
 *
 * @param pState pointer to client state struct of client that has disconnected
 * @param pIndex pointer to fd of client that is disconnecting
 * @param pFdSet pointer to fd_set of read file descriptors
 * @param pNumConnectedClients pointer to number of connected clients
 */
void disconnectClient(struct clientStatus* pState, int *pIndex, fd_set* pFdSet, u8 *pNumConnectedClients)
{

	DBGOUT("DiscClient: Client #%d disconnected.\r\n", *pIndex);
	lwip_close(*pIndex);
	FD_CLR(*pIndex, pFdSet);
	(*pNumConnectedClients)--;

	// If payload buffer exceeds nominal size, reduce it
	// TODO: Move this to a new method?
	if (pState->payloadBufferSz > NET_NOMINAL_RX_BUFFER_SZ)
	{
		free(pState->pPayload);
		pState->pPayload = malloc(NET_NOMINAL_RX_BUFFER_SZ);
		if (pState->pPayload == NULL)
		{
			// Can't allocate payload space
			DBGOUT("DiscClient: Can't re-malloc payload buffer for client after large packet!\r\n");
		}
		else
		{
			DBGOUT("DiscClient: Resized payload buffer to %d\r\n", NET_NOMINAL_RX_BUFFER_SZ);
		}
	}

	pState->state = STATE_COMPLETE;
}


/*
 * Processes received commands over LWIP.  It is assumed that packets are well formed
 * and have been checked before passing to this function.
 *
 * @param pRxHeader pointer to protocol_header for received packet
 * @param pTxHeader pointer to protocol_header for outbound packet
 * @param pRxPayload pointer to payload buffer of received packet
 * @param pTxPayload pointer to payload buffer for outbound packet
 */
void commandHandler(struct protocol_header* pRxHeader,
                        struct protocol_header* pTxHeader,
                        u8* pRxPayload,
                        u8* pTxPayload)
{

	int i;					// General use variable
	int dataWidth = 0;		// Width of data type for operation in bytes
	int responseSize = 0;	// Payload size for response packet in bytes
	u32 numOps = 0;			// Number of requested operations performed
	u8 state = 0;			// Status byte

	// Native size pointers for various data widths
	u32* pTxPayload_32  = NULL;
	u32* pRxPayload_32  = NULL;

	// Copy original header to response packet, take a local copy of the status byte to update
	memcpy(pTxHeader, pRxHeader, sizeof(struct protocol_header));
	state = pRxHeader->state;

	// Verify operation mode is sane, exit if not
	if (!CMPBIT(state, STATE_READ) && !CMPBIT(state, STATE_WRITE))
	{
		// Neither write nor read requested, can't process so just return error response
		DBGOUT("CmdDisp: Invalid operation\r\n");
		SBIT(state, STATE_NACK);
		// TODO: Set FEM error state
		pTxHeader->state = state;
		pTxHeader->payload_sz = 0;
		return;
	}

	// Pointers to received and outgoing packet payloads
	pRxPayload_32 = (u32*)pRxPayload;
	pTxPayload_32 = (u32*)pTxPayload;
	pTxPayload_32 += 1;		// Nudge outgoing packet payload pointer by 1 so as to skip first u32 which will be populated with #ops

	u32 numRequestedReads = *pRxPayload_32;		// Number of REQUESTED ops (only valid for read operations)

	// Increment response size to include #ops as first entry
	responseSize += sizeof(u32);

	u32 mboxBytesSent = 0;

	int status;

	// Determine operation type
	switch(pRxHeader->command)
	{

		case CMD_INTERNAL:
			// TODO: Process internal state request here!
			/*
			 * What will we support eventually?
			 * - Remote reset command (w/payload, bitmask for components to reset?)
			 * - Get # connected clients (+ IPs?) - no payload?
			 * - Current software build (remove from EEPROM?) - no payload?
			 * - Current firmware build (remove from EEPROM?) - no payload?
			 *
			 */
			//DBGOUT("CmdDisp: Internal state requests not yet implemented!  Nag Matt...\r\n");

			DBGOUT("CmdDisp: CMD_INTERNAL addr=0x%08x\r\n", (pRxHeader->address));
			numOps = 0;
			SBIT(state, STATE_ACK);

			// send
			mboxBytesSent = dummySend(pRxHeader->address);

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
							// EEPROM read failed, set NACK
							SBIT(state, STATE_NACK);
							// TODO: Set FEM error state
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
							SBIT(state, STATE_NACK);
							// TODO: Set FEM error state
						} else
						{
							SBIT(state, STATE_ACK);
							numOps = i;
						}

					}
					else
					{
						// Neither R or W bits set, can't process request
						DBGOUT("CmdDisp: Error, can't determine BUS_EEPROM operation mode, status was 0x%x\r\n", state);
						// TODO: Set FEM error state
					}
					break; // BUS_EEPROM

				// --------------------------------------------------------------------
				case BUS_I2C:

					dataWidth = sizeof(u8);	// All I2C operations are byte level

					/*
					 * Decode address field
					 * Least significant word (lower byte) = I2C slave address
					 * Most significant word (lower byte)  = Bus index (0=LM82, 1=EEPROM, 2=SP3_TOP, 3=SP3_BOT)
					 */
					u8 slaveAddress = (pRxHeader->address & 0xFF);
					u8 busIndex = (pRxHeader->address & 0xFF00) >> 8;
					u32 baseAddr = 0;

					// Map of I2C bus base addresses
					u32 i2cAddr[] =			{
												BADDR_I2C_LM82,
												BADDR_I2C_EEPROM,
												BADDR_I2C_SP3_TOP,
												BADDR_I2C_SP3_BOT
											};
					u8 i2cMaxAddr = (sizeof(i2cAddr)/sizeof(u32));

					// Verify bus index is valid, if so lookup associated base address
					if (busIndex >= i2cMaxAddr )
					{
						// I2C bus index invalid, set NACK
						//DBGOUT("CmdDisp: Invalid I2C bus index %d (maximum index is %d)\r\n", busIndex, i2cMaxAddr);
						SBIT(state, STATE_NACK);
						// TODO: Set FEM error state
						break;
					}
					else
					{
						baseAddr = i2cAddr[busIndex];
					}

					//DBGOUT("CmdDisp: Processing I2C operation...\r\n");

					if (CMPBIT(state, STATE_READ))
					{
						i = readI2C(baseAddr, slaveAddress, (u8*)pTxPayload_32, *pRxPayload_32);
						if (i != *pRxPayload_32)
						{
							// I2C operation failed, set NACK
							//DBGOUT("I2C_R - only got %d bytes instead of %d!\r\n", i, *pRxPayload_32);
							SBIT(state, STATE_NACK);
							// TODO: Set FEM error state
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
						i = writeI2C(baseAddr, slaveAddress, pRxPayload, pRxHeader->payload_sz);
						if (i != pRxHeader->payload_sz)
						{
							// I2C operation failed, set NACK
							//DBGOUT("I2C_W - only sent %d bytes instead of %d!\r\n", i, pRxHeader->payload_sz);
							SBIT(state, STATE_NACK);
							// TODO: Set FEM error state
						}
						else
						{
							// Set ACK
							SBIT(state, STATE_ACK);
							numOps = i;
						}
					}
					else
					{
						// Neither R or W bits set, can't process request
						DBGOUT("CmdDisp: Error, can't determine BUS_I2C operation mode, status was 0x%x\r\n", state);
						// TODO: Set FEM error state
					}

					break; // BUS_I2C

				// --------------------------------------------------------------------
				case BUS_RAW_REG:

					dataWidth = sizeof(u32);

					// Make sure return packet will not violate MAX_PAYLOAD_SIZE (write operations should never be too long if MAX_PAYLOAD_SIZE => 4!)
					if (CMPBIT(state, STATE_READ)) {
						if ( (sizeof(u32) + (dataWidth * numRequestedReads)) > MAX_PAYLOAD_SIZE )
						{
							DBGOUT("CmdDisp: Response would be too large! (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->state, pRxHeader->payload_sz);
							SBIT(state, STATE_NACK);
							// TODO: Set FEM error state
							break;
						}
					}

					if (CMPBIT(state, STATE_READ)) // READ OPERATION
					{
						for (i=0; i<*pRxPayload_32; i++)
						{
							//DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*dataWidth));
							*(pTxPayload_32+i) = readRegister_32(pRxHeader->address + (i*dataWidth));
							//DBGOUT(" VALUE 0x%x\r\n", readRegister_32(pRxHeader->address + (i*dataWidth)));
							responseSize += dataWidth;
							numOps++;
						}
						SBIT(state, STATE_ACK);

					}
					else if (CMPBIT(state, STATE_WRITE)) // WRITE OPERATION
					{
						for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
						{
							pRxPayload_32 = (u32*)pRxPayload;
							//DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + (i*dataWidth), *(pRxPayload_32+i));
							writeRegister_32( pRxHeader->address + (i*dataWidth), *(pRxPayload_32+i) );
							numOps++;
						}
						SBIT(state, STATE_ACK);
					}
					else
					{
						// Neither R or W bits set, can't process request
						DBGOUT("CmdDisp: Error, can't determine BUS_RAW_REG operation mode, status was 0x%x\r\n", state);

						SBIT(state, STATE_NACK);
						// TODO: Set FEM error state
					}

					break; // BUS_RAW_REG

				// --------------------------------------------------------------------
				case BUS_RDMA:

					dataWidth = sizeof(u32);
					pTxPayload_32 = (u32*)(pTxPayload+responseSize);

					if (CMPBIT(state, STATE_READ)) // READ OPERATION
					{

						pRxPayload_32 = (u32*)pRxPayload;
						for (i=0; i<*pRxPayload_32; i++)
						{
							//DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*dataWidth));
							//*(pTxPayload_32+i) = readRdma(pRxHeader->address + i);
							status = readRdma( (pRxHeader->address+i) , (pTxPayload_32+i) );
							if (status==XST_FAILURE)
							{
								// TODO: Proper error handling!
								DBGOUT("CmdDisp: Error reading RDMA, aborting!\r\n");
							}
							//DBGOUT(" VALUE 0x%x\r\n", readRdma(pRxHeader->address + i));
							responseSize += dataWidth;
							numOps++;
						}
						SBIT(state, STATE_ACK);

					}
					else if (CMPBIT(state, STATE_WRITE)) // WRITE OPERATION
					{
						for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
						{
							pRxPayload_32 = (u32*)pRxPayload;
							//DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + i, *(pRxPayload_32+i));
							//writeRdma(pRxHeader->address + i, *(pRxPayload_32+i));
							status = writeRdma(pRxHeader->address + i, *(pRxPayload_32+i));
							if (status==XST_FAILURE)
							{
								// TODO: Proper error handling!
								DBGOUT("CmdDisp: Error writing RDMA, aborting!\r\n");
							}
							numOps++;
						}
						SBIT(state, STATE_ACK);
					}
					else
					{
						// Neither R or W bits set, can't process request
						DBGOUT("CmdDisp: Error, can't determine BUS_RDMA operation mode, status was 0x%x\r\n", state);

						SBIT(state, STATE_NACK);
						// TODO: Set FEM error state
					}
					break; // BUS_RDMA

				// --------------------------------------------------------------------
				case BUS_DIRECT:
					numOps = pRxHeader->payload_sz;
					SBIT(state, STATE_ACK);
					break;

				case BUS_UNSUPPORTED:
				default:
					SBIT(state, STATE_NACK);
					// TODO: Set FEM error state
					break;

			} // END switch(bus)

	} // END switch(command)

	// Build response header (all fields other status byte stay same as received packet)
	pTxHeader->state = state;
	pTxHeader->payload_sz = responseSize;

	// Update number of operations in payload
	pTxPayload_32 = (u32*)pTxPayload;
	*pTxPayload_32 = numOps;

}



/*
 * Validates the fields of a header for consistency
 * @param pHeader pointer to header
 *
 * @return 0 if header logically correct, -1 if not
 */
int validateHeaderContents(struct protocol_header *pHeader)
{

	// Verify magic
	if (pHeader->magic != PROTOCOL_MAGIC_WORD)
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
					DBGOUT("validateHeader: No R/W operation specified for CMD_ACCESS!\r\n");
					return -1;
				}

				// CMD_ACCESS + STATE_READ must always have a payload_sz of sizeof(u32)
				if ( (pHeader->state == STATE_READ) && (pHeader->payload_sz!=sizeof(u32)) )
				{
					DBGOUT("validateHeader: payload_sz must always equal 4 on CMD_ACCESS READ operation!\r\n");
					return -1;
				}

				case BUS_EEPROM:
					// Data width must always be 8bit
					if (pHeader->data_width!=WIDTH_BYTE)
					{
						DBGOUT("validateHeader: Data width must always be 8bit for EEPROM access!\r\n");
						return -1;
					}
					break;

				case BUS_I2C:
					// Data width must always be 8bit
					if (pHeader->data_width!=WIDTH_BYTE)
					{
						DBGOUT("validateHeader: Data width must always be 8bit for I2C access!\r\n");
						return -1;
					}
					// Address most significant byte must be 0-4 only
					if ( (((pHeader->address & 0xF00) >> 16)<0) && (((pHeader->address & 0xF00) >> 16)>4) )
					{
						DBGOUT("validateHeader: Address most significant byte must be 0-4 only for I2C access!\r\n");
						return -1;
					}
					break;

				case BUS_RAW_REG:
				case BUS_RDMA:
					// Data width must always be 32bit
					if (pHeader->data_width!=WIDTH_LONG)
					{
						DBGOUT("validateHeader: Data width should always be 32bit for RAW or RDMA access! (%d)\r\n",pHeader->data_width);
						return -1;
					}
					break;

				case BUS_UNSUPPORTED:
					// Never valid!
					return -1;
					DBGOUT("validateHeader: Unsupported bus target!\r\n");
					break;
			}

			break;

		case CMD_INTERNAL:
			//DBGOUT("validateHeader: CMD_INTERNAL not yet supported!\r\n");
			return 0;
			break;

		case CMD_PERSONALITY:
			// TODO - Implement CMD_PERSONALITY checks!
			return 0;		// For the meantime, pass any old packets to the personality modules...
			break;

		case CMD_UNSUPPORTED:
			DBGOUT("validateHeader: Unsupported command!\r\n");
			return -1;
			break;
	}


	// ...otherwise, header is valid!
	return 0;
}

/* Generates and sends a BADPKT response packet which signals
 * to a client that the last packet received was not
 * well formed or it was not possible to decode it correctly.
 *
 * @param pHeader pointer to header object
 * @param clientSocket socket identifier for client
 */
void generateBadPacketResponse(struct protocol_header *pHeader, int clientSocket)
{
	pHeader->address = 0;
	pHeader->bus_target = 0;
	pHeader->command = 0;
	pHeader->data_width = 0;
	pHeader->magic = PROTOCOL_MAGIC_WORD;
	pHeader->payload_sz = 0;
	pHeader->state = 0xF8;

	if (lwip_send(clientSocket, pHeader, sizeof(struct protocol_header), 0) == -1)
	{
		DBGOUT("gBPR: Error sending BADPKT response packet!\r\n");
	}
}
