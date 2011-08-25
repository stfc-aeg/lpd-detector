/*
 * commandProcessor.c
 *
 *  Created on: Aug 4, 2011
 *      Author: mt47
 */

#include "commandProcessor.h"

// Communicates with PC via TCP/IP socket (SOCK_STREAM) to receive packets
// and display them to stdout (RS232)
//
// TODO: Adhere to MAX_CONNECTIONS, MAX_PAYLOAD_SIZE
// TODO: Replace return statements, make sure to close any open FDs too
void commandProcessorThread()
{
	// Socket stuff
	int listenerSocket, clientSocket, newFd, addrSize, numFds, numBytesRead, isValid, i;
	struct sockaddr_in serverAddress, clientAddress;
	fd_set readSet, masterSet;
	struct timeval tv;

	// RX and TX packet buffers
	u8* pRxBuffer = (u8*)malloc(sizeof(struct protocol_header)+MAX_PAYLOAD_SIZE);
	u8* pTxBuffer = (u8*)malloc(sizeof(struct protocol_header)+MAX_PAYLOAD_SIZE);
	struct protocol_header* pRxHeader = (struct protocol_header*)pRxBuffer;
	struct protocol_header* pTxHeader = (struct protocol_header*)pTxBuffer;

	// Client count
	u8 numConnectedClients = 0;

	// Prepare file descriptor sets
	FD_ZERO(&readSet);
	FD_ZERO(&masterSet);
	numFds = -1;

	// Prepare timeval
	tv.tv_sec = 1;
	tv.tv_usec = 0;

	DBGOUT("CmdProc: Thread starting...\r\n");

	// Open server socket, stream mode
	if ((listenerSocket = lwip_socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		DBGOUT("CmdProc: Can't open socket, aborting...\r\n");
		return;
	}

	// Configure socket to receive any incoming connections
	serverAddress.sin_family = AF_INET;
	serverAddress.sin_port = htons(CMD_PORT);
	serverAddress.sin_addr.s_addr = INADDR_ANY;
	memset(&(serverAddress.sin_zero), 0, sizeof(serverAddress.sin_zero));

	// Bind to address
	if (lwip_bind(listenerSocket, (struct sockaddr *)&serverAddress, sizeof (serverAddress)) < 0)
	{
		DBGOUT("CmdProc: Can't bind to socket %d, aborting...\r\n", CMD_PORT);
		return;
	}

	// Begin listening, register listener as FD of interest to read
	// Second parameter (backlog) is number of queued connection requests to handle, NOT the maximum permitted socket connections :(
	if (lwip_listen(listenerSocket, SOCK_BACKLOG) < 0)
	{
		DBGOUT("CmdProc: Can't listen on socket %d, aborting...\r\n", CMD_PORT);
		return;
	}
	FD_SET(listenerSocket, &masterSet);
	numFds = listenerSocket;

	// ************************* MAIN SERVER LOOP *******************************
	while (1) {

		// Copy master set over as readSet will be modified
		memcpy(&readSet, &masterSet, (size_t)sizeof(fd_set));

		isValid = 1;

		// TODO: Use timeval?  (using NULL here means the thread will wait forever without timing out)
		if (lwip_select(numFds + 1, &readSet, NULL, NULL, NULL) == -1)
		{
			// Unrecoverable error
			DBGOUT("CmdProc: Select failed, aborting...\r\n");
			return;
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

					//if (numConnectedClients < MAX_CONNECTIONS) {

						DBGOUT("CmdProc: Received new connection! (Client %d of a possible %d)\r\n", numConnectedClients+1, MAX_CONNECTIONS);
						numConnectedClients++;

						// Accept connection
						addrSize = sizeof(clientAddress);
						newFd = lwip_accept(listenerSocket, (struct sockaddr*)&clientAddress, (socklen_t*)&addrSize);
						if (newFd == -1)
						{
							// Unrecoverable error
							DBGOUT("CmdProc: Accept error\r\n");
							return;
						}

						// Add to master list of FDs, update count
						FD_SET(newFd, &masterSet);
						if (newFd > numFds)
						{
							numFds = newFd;
						}

					/*
					}
					else		// Reached client limit, so don't accept connection
					{
						DBGOUT("CmdProc: Received new connection request, but rejecting due to connection limit.\r\n");
						lwip_close(i);
						FD_CLR(i, &masterSet);
					}
					*/

				}
				else
				// ----------------------------------------------------------------------------------------------------
				// Existing client is communicating with us
				{

					clientSocket = i;

					// Read header if we can
					numBytesRead = socketRead(i, pRxBuffer, sizeof(struct protocol_header), 0);

					if (numBytesRead < sizeof(struct protocol_header))
					{
						isValid = 0;	// Prevent any further reading of this socket

						if (numBytesRead == 0)
						{
							// Client closed connection, so drop our side
							DBGOUT("CmdProc: Client closed connection.\r\n");
							lwip_close(i);
							FD_CLR(i, &masterSet);
							numConnectedClients--;
						}
						else if (numBytesRead == -1)
						{
							// Error occurred
							// TODO: get errno?
							DBGOUT("CmdProc: Error encountered during lwip_read(), closing connection.\r\n");
							lwip_close(i);
							FD_CLR(i, &masterSet);
							numConnectedClients--;
						}
						else
						{
							DBGOUT("CmdProc: Header is smaller than expected (expected %d, got %d)\r\n", sizeof(struct protocol_header), numBytesRead);
						}
					} // END if (numBytesRead < sizeof(struct protocol_header))

					// Everything OK so far, validate magic...
					if ((pRxHeader->magic != PROTOCOL_MAGIC_WORD) && (isValid==1))
					{
						DBGOUT("CmdProc: Got bad packet, ignoring... (magic=%x)\r\n", pRxHeader->magic);
						isValid = 0;
					}

					// If header looks to be well formed, process it's contents
					if (isValid==1) {

						// DEBUG - dump out header
						/*
						DBGOUT("------------------------\r\n");
						DBGOUT("HEADER:\r\n");
						DUMPHDR(pRxHeader);
						DBGOUT("------------------------\r\n");
						*/

						// --------------------- BEGIN READING VALID PACKET ----------------------

						if (pRxHeader->command == CMD_ACCESS) {

							// TODO: Verify payload_sz%data_width == 0!

							if (pRxHeader->payload_sz>0 && pRxHeader->payload_sz <= MAX_PAYLOAD_SIZE)
							{
								numBytesRead = socketRead(i, pRxBuffer+sizeof(struct protocol_header), pRxHeader->payload_sz, 0);
								if (numBytesRead < pRxHeader->payload_sz)
								{
									// Prevent further processing because payload is smaller than expected
									isValid = 0;

									if (numBytesRead == 0)
									{
										// TODO: Fix this, drops connection if we receive a header but no payload.  What should we do in that case?
										// Client closed connection, so drop our side
										DBGOUT("CmdProc: Client closed connection (payload processing stage).\r\n");
										lwip_close(i);
										FD_CLR(i, &masterSet);
										numConnectedClients--;
									}
									else if (numBytesRead == -1)
									{
										// Error occurred
										// TODO: get errno?
										DBGOUT("CmdProc: Error encountered during lwip_read(), closing connection.\r\n");
										lwip_close(i);
										FD_CLR(i, &masterSet);
										numConnectedClients--;
									}
									else
									{
										// Got less data than expected
										DBGOUT("CmdProc: Payload is smaller than expected (expected %d, got %d)\r\n", pRxHeader->payload_sz, numBytesRead);
									}

								} else {

									// Received payload OK, correct size
									/*
									DBGOUT("PAYLOAD:\r\n");
									DBGOUT("[sz=%d] = ", pRxHeader->payload_sz);
									for(i=0; i<pRxHeader->payload_sz; i++)
									{
										DBGOUT("%x ",pRxBuffer[i+sizeof(struct protocol_header)]);
									}
									DBGOUT("\r\n");
									DBGOUT("------------------------\r\n");
									*/
								}
							}
							else
							{
								DBGOUT("CmdProc: No payload to recover...\r\n");
							} // END if (header.payloadSize>0))

						} // END if (rx_header.command == CMD_ACCESS)

						// ------------------- END READING VALID PACKET ----------------------

					} // END if isValid==1)

					// Process command if we encountered no errors
					if (isValid==1)
					{

						// Kludge new vars into old prototype!
						// TODO: Update command_dispatcher function prototype
						commandHandler(pRxHeader, pTxHeader, pRxBuffer+sizeof(struct protocol_header), pTxBuffer+sizeof(struct protocol_header));

						if (lwip_send(clientSocket, pTxBuffer, sizeof(struct protocol_header) + pTxHeader->payload_sz, 0) == -1)
						{
							DBGOUT("CmdProc: Error sending response packet!\r\n");
						}

					}

				}	// END else clause

			}	// END FD_ISSET(i)

		}	// END for (fd)

	}	// END while(1)
	// *********************** END MAIN SERVER LOOP *****************************

	// Code below here will never run...  but just in case output debug message
	DBGOUT("CmdProc: Exiting thread! [SHOULD NEVER EXECUTE!]\r\n");

}



/*
 * Processes received commands over LWIP.  It is assumed that packets are well formed
 * and have been checked before passing to this function.
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
	u8 status = 0;			// Status byte

	// Native size pointers for various data widths
	u32* pTxPayload_32  = NULL;
	u32* pRxPayload_32  = NULL;

	// Copy original header to response packet, take a local copy of the status byte to update
	memcpy(pTxHeader, pRxHeader, sizeof(struct protocol_header));
	status = pRxHeader->status;

	// Verify operation mode is sane, exit if not
	if (!CMPBIT(status, STATE_READ) && !CMPBIT(status, STATE_WRITE))
	{
		// Neither write nor read requested, can't process so just return error response
		DBGOUT("CmdDisp: Invalid operation\r\n");
		SBIT(status, STATE_NACK);
		// TODO: Set error bits
		pTxHeader->status = status;
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

	// Process packet based on target
	switch(pRxHeader->bus_target)
	{

		// --------------------------------------------------------------------
		case BUS_EEPROM:

			// Verify request parameters are sane
			if ( (pRxHeader->data_width != WIDTH_BYTE) || (pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid EEPROM request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: set error bits
				break;
			}

			dataWidth = sizeof(u8); // All EEPROM operations are byte level

			if (CMPBIT(status, STATE_READ))
			{

				i = readFromEEPROM(pRxHeader->address, pTxPayload + 4, *pRxPayload_32);
				if (i != *pRxPayload_32)
				{
					// EEPROM read failed, set NACK
					SBIT(status, STATE_NACK);
					// TODO: set error bits?
				}
				else
				{
					SBIT(status, STATE_ACK);
					responseSize += i;
					numOps++;
				}
			}
			else if (CMPBIT(status, STATE_WRITE))
			{

				i = writeToEEPROM(pRxHeader->address, pRxPayload, pRxHeader->payload_sz);
				if (i != pRxHeader->payload_sz)
				{
					SBIT(status, STATE_NACK);
					// TODO: Set error bits?
				} else
				{
					SBIT(status, STATE_ACK);
					numOps++;
				}

			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_EEPROM operation mode, status was 0x%x\r\n", status);
				// TODO: Set error bits
			}
			break; // BUS_EEPROM

		// --------------------------------------------------------------------
		case BUS_I2C:

			// Verify request parameters are sane
			if ( (pRxHeader->data_width != WIDTH_BYTE) || ( pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
				break;
			}
			dataWidth = sizeof(u8);	// All I2C operations are byte level

			/*
			 * Decode address field
			 * Least significant word (lower byte) = I2C slave address
			 * Most significant word (lower byte)  = Bus index (0=LM82, 1=EEPROM, 2=SP3_TOP, 3=SP3_BOT)
			 */
			u8 slaveAddress = (pRxHeader->address & 0xF);
			u8 busIndex = (pRxHeader->address & 0xF00) >> 16;
			u32 baseAddr = 0;

			// Map of I2C bus base addresses
			u32 i2cAddr[] =			{
										BADDR_I2C_LM82,
										BADDR_I2C_EEPROM,
										BADDR_I2C_SP3_TOP,
										BADDR_I2C_SP3_BOT
									};
			u8 i2cMaxAddr = ((sizeof(i2cAddr)/sizeof(u32)) +1);

			// Verify bus index is valid, if so lookup associated base address
			if (busIndex >= i2cMaxAddr )
			{
				DBGOUT("CmdDisp: Invalid I2C bus index %d (maximum index is %d)\r\n", busIndex, i2cMaxAddr);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
			}
			else
			{
				baseAddr = i2cAddr[busIndex];
			}

			if (CMPBIT(status, STATE_READ))
			{
				i = readI2C(baseAddr, slaveAddress, pTxPayload + 1, (u32)pRxPayload[0]);
				if (i != (u32)pRxPayload[0])
				{
					// I2C operation failed, set NACK
					SBIT(status, STATE_NACK);
					// TODO: Set error bits?
				}
				else
				{
					// Set ACK, payload size
					SBIT(status, STATE_ACK);
					responseSize += i;
					numOps++;
				}

			}
			else if (CMPBIT(status, STATE_WRITE))
			{
				i = writeI2C(baseAddr, slaveAddress, pRxPayload, pRxHeader->payload_sz);
				if (i != pRxHeader->payload_sz)
				{
					// I2C operation failed, set NACK
					SBIT(status, STATE_NACK);
					// TODO: Set error bits?
				}
				else
				{
					// Set ACK
					SBIT(status, STATE_ACK);
					numOps++;
				}
			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_I2C operation mode, status was 0x%x\r\n", status);
				// TODO: Set error bits
			}

			break; // BUS_I2C

		// --------------------------------------------------------------------
		case BUS_RAW_REG:

			// Verify request parameters are sane
			// We don't support anything other than 32-bit operations for RAW_REG as all Xilinx registers are 32bit.
			if ( (pRxHeader->data_width != WIDTH_LONG) || ( pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid raw reg request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
				break;
			}

			dataWidth = sizeof(u32);

			// Make sure return packet will not violate MAX_PAYLOAD_SIZE (write operations should never be too long if MAX_PAYLOAD_SIZE => 4!)
			if (CMPBIT(status, STATE_READ)) {
				if ( (sizeof(u32) + (dataWidth * numRequestedReads)) > MAX_PAYLOAD_SIZE )
				{
					DBGOUT("CmdDisp: Response would be too large! (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
					SBIT(status, STATE_NACK);
					// TODO: set error bits
					break;
				}
			}

			if (CMPBIT(status, STATE_READ)) // READ OPERATION
			{
				for (i=0; i<*pRxPayload_32; i++)
				{
					DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*dataWidth));
					*(pTxPayload_32+i) = readRegister_32(pRxHeader->address + (i*dataWidth));
					DBGOUT(" VALUE 0x%x\r\n", readRegister_32(pRxHeader->address + (i*dataWidth)));
					responseSize += dataWidth;
					numOps++;
				}
				SBIT(status, STATE_ACK);

			}
			else if (CMPBIT(status, STATE_WRITE)) // WRITE OPERATION
			{
				for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
				{
					pRxPayload_32 = (u32*)pRxPayload;
					DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + (i*dataWidth), *(pRxPayload_32+i));
					writeRegister_32( pRxHeader->address + (i*dataWidth), *(pRxPayload_32+i) );
					numOps++;
				}
				SBIT(status, STATE_ACK);
			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_RAW_REG operation mode, status was 0x%x\r\n", status);

				SBIT(status, STATE_NACK);
				// TODO: Set error bits
			}

			break; // BUS_RDMA

		// --------------------------------------------------------------------
		case BUS_RDMA:

			// Verify request parameters are sane
			// We don't support anything other than 32-bit operations for RAW_REG as all RDMA registers are 32bit.
			if ( (pRxHeader->data_width != WIDTH_LONG) || ( pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
				break;
			}

			dataWidth = sizeof(u32);
			pTxPayload_32 = (u32*)(pTxPayload+responseSize);

			if (CMPBIT(status, STATE_READ)) // READ OPERATION
			{

				pRxPayload_32 = (u32*)pRxPayload;
				for (i=0; i<*pRxPayload_32; i++)
				{
					DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*dataWidth));
					*(pTxPayload_32+i) = readRdma(BADDR_RDMA, pRxHeader->address + i);
					//DBGOUT(" VALUE 0x%x\r\n", readRegister_32(pRxHeader->address + i));
					DBGOUT(" VALUE 0x%x\r\n", readRdma(BADDR_RDMA, pRxHeader->address + i));
					responseSize += dataWidth;
					numOps++;
				}
				SBIT(status, STATE_ACK);

			}
			else if (CMPBIT(status, STATE_WRITE)) // WRITE OPERATION
			{
				for (i=0; i<((pRxHeader->payload_sz)/dataWidth); i++)
				{
					pRxPayload_32 = (u32*)pRxPayload;
					DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + i, *(pRxPayload_32+i));
					writeRdma(BADDR_RDMA, pRxHeader->address + i, *(pRxPayload_32+i));
					numOps++;
				}
				SBIT(status, STATE_ACK);
			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_RDMA operation mode, status was 0x%x\r\n", status);

				SBIT(status, STATE_NACK);
				// TODO: Set error bits
			}

			break; // BUS_RAW_REG

		case BUS_UNSUPPORTED:
		default:
			SBIT(status, STATE_NACK);
			// TODO: Set error bits
			break;

	}

	// Build response header (all fields other status byte stay same as received packet)
	pTxHeader->status = status;
	pTxHeader->payload_sz = responseSize;

	// Update number of operations in payload
	pTxPayload_32 = (u32*)pTxPayload;
	*pTxPayload_32 = numOps;

}

/*
 * Reads the specified number of bytes from the given socket within the timeout period
 * @param sock socket identifier
 * @param pBuffer data buffer to write received data to
 * @param numBytes number of bytes to try to read
 * @param timeoutMs timeout in milliseconds
 *
 * @return 0 on success, -1 on failure
 */
int socketRead(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs)
{
	// TODO: Use timeoutMs, remove maxloops
	int totalBytes = 0;
	int read = 0;

	int tempNumLoops = 0;
	int tempMaxLoops = 100;

	while (totalBytes < numBytes)
	{
		read = lwip_read(sock, (void*)pBuffer, numBytes-read);
		if (read==0) {
			// Client closed connection
			return 0;
		}
		else if (read!=-1)
		{
			totalBytes += read;
		}
		if (tempNumLoops++ == tempMaxLoops)
		{
			// Break out
			DBGOUT("socketRead: Hit maximum retries, bailing out...\r\n");
			return -1;
		}

	}

	return totalBytes;
}
