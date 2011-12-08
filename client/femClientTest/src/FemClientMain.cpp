/*
 * femClientMain.cpp
 *
 *  Created on: Nov 15, 2011
 *      Author: tcn45
 */

#include <iostream>
#include <vector>
#include "FemClient.h"
#include "FemTransaction.h"

int main(int argc, char* argv[])
{

	if (argc != 3)
	{
		std::cerr << "Usage: femClient <host> <port>" << std::endl;
		return 1;
	}

	try
	{

		std::cout << "Connecting to FEM at IP address " << argv[1] << " port " << argv[2] << " ... ";
		FemClient theFem(argv[1], std::atoi(argv[2]));
		std::cout << "done" << std::endl;

		unsigned int timeout = 5000;
		std::cout << "Setting FEM client transaction timeout to " << timeout << "ms" << std::endl;
		theFem.setTimeout(timeout);

		FemTransaction writeTrans(CMD_ACCESS, BUS_RAW_REG, WIDTH_LONG, STATE_WRITE, 0x81440000);

		u32 payload[] = {0xAA};
		writeTrans.appendPayload((u8*)payload, sizeof(payload));
		std::cout << "Initial write transaction:" << std::endl << writeTrans << std::endl;

		theFem.send(writeTrans);
		std::cout << "Sent write, waiting for response" << std::endl;
		FemTransaction response = theFem.receive();
		std::cout << "Write transaction response:" << std::endl << response << std::endl;

		FemTransaction readTrans(CMD_ACCESS, BUS_RAW_REG, WIDTH_LONG, STATE_READ, 0x81440000);
		u32 payload2[] = { 0x1 };
		readTrans.appendPayload((u8*)payload2, sizeof(payload2));

		theFem.send(readTrans);
		std::cout << "Sent read, waiting for response" << std::endl;
		response = theFem.receive();
		std::cout << "Read transaction response:" << std::endl << response << std::endl;

		std::vector<u8> respByte = response.getPayload();
		for (std::vector<u8>::iterator respByteIter = respByte.begin(); respByteIter != respByte.end(); respByteIter++)
		{
			std::cout << std::hex << (u32)*respByteIter << " ";
		}
		std::cout << std::dec << std::endl;

		std::vector<u32>* respLong = (std::vector<u32>*)&respByte;
		for (std::vector<u32>::iterator respLongIter = respLong->begin(); respLongIter != respLong->end(); respLongIter++)
		{
			std::cout << std::hex << *respLongIter << " ";
		}
		std::cout << std::dec << std::endl;

		// Do a write transaction
		std::cout << "Sending write command" << std::endl;
		std::vector<u8> writePayload(4);
		u32 writeVal = 0x55;
		*((u32*)&(writePayload[0])) = writeVal;

		size_t writeLen = theFem.write((unsigned int)BUS_RAW_REG, (unsigned int)WIDTH_LONG, (unsigned int)0x81440000, writePayload);

		// Repeat the read with a read call this time
		std::cout << "Sending read command" << std::endl;
		std::vector<u8> readVals = theFem.read(BUS_RAW_REG, WIDTH_LONG, 0x81440000, 10);
		std::vector<u32>* readLong = (std::vector<u32>*)&readVals;

		std::cout << "Read command response:" << std::endl;
		for (std::vector<u32>::iterator readLongIter = readLong->begin(); readLongIter != readLong->end(); readLongIter++)
		{
			std::cout << std::hex << *readLongIter << " ";
		}
		std::cout << std::dec << std::endl;

		// Check first read value matches write value
		if ((*readLong)[0] != writeVal) {
			std::cout << "ERROR : read and write values do not match!!" << std::endl;
		}

//		u8 ledVal = 0x55;
//		for (unsigned int i = 0; i < 100; i++) {
//
//			u32 ledPayload[] = { ledVal };
//			writeTrans.clearPayload();
//			writeTrans.appendPayload((u8*)ledPayload, sizeof(ledPayload));
//			theFem.send(writeTrans);
//			response = theFem.receive();
//			ledVal = ~ledVal;
//		}
//
//		for (unsigned int i = 0; i < 256; i++) {
//
//			u32 ledPayload[] = { i };
//			writeTrans.clearPayload();
//			writeTrans.appendPayload((u8*)ledPayload, sizeof(ledPayload));
//			theFem.send(writeTrans);
//			response = theFem.receive();
//		}

//		std::cout << "running io service" << std::endl;
//		theFem.runIoService();

		std::cout << "Hit return to quit ... ";
		std::cin.get();

	}
	catch (FemException& e)
	{
		std::cerr << "Got a FEM exception: " << e.what() << ", error code=" << e.which() << std::endl;
		std::cout << "Hit return to quit ... ";
		std::cin.get();

	}
	catch (std::exception& e)
	{
		std::cerr << "Got a std::exception: " << e.what() << std::endl;
		std::cout << "Hit return to quit ... ";
		std::cin.get();

	}

	return 0;
}

