/*
 * femClientBusses.cpp - FemClient high level bus transaction methods
 *
 *  Created on: Mar 13, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "FemClient.h"

/** i2cRead - perform an I2C read transaction from the FEM
 *
 * This function performs a I2C read transaction from the FEM, at an address
 * and of the length specified in the arguments. The result is returned as
 * a vector of bytes to the user
 *
 * @param aAddress I2C address to read (including upper byte as FEM bus select)
 * @param aLength number of bytes to read
 * @return vector of u8 byte data read from FEM
 */
std::vector<u8> FemClient::i2cRead(unsigned int aAddress, unsigned int aLength)
{
	unsigned int bus   = BUS_I2C;
	unsigned int width = WIDTH_BYTE;
	std::vector<u8> values = this->read(bus, width, aAddress, aLength);

	return values;
}

/** i2cWrite - perform an I2C write transaction to the FEM
 *
 * This function peforms an I2C write transaction to the FEM, at an address
 * specified in the arguments and of a length determined from the u8 byte
 * values passed. The number of writes completed (which should match the
 * expected length) is returned.
 *
 * @param aAdddress I2C address to read (including upper byte as FEM bus select)
 * @param aValues reference to u8 byte vector containing values to write
 * @return number of bytes written
 */
u32 FemClient::i2cWrite(unsigned int aAddress, std::vector<u8>&aValues)
{
	unsigned int bus   = BUS_I2C;
	unsigned int width = WIDTH_BYTE;

	u32 numWrites = this->write(bus, width, aAddress, aValues);

	return numWrites;
}

/** rdmaRead - perform an RDMA read transaction from the FEM
 *
 * This function performs a RDMA read transaction from the FEM, at an address
 * and of the length specified in the arguments. The result is returned as
 * a vector of bytes to the user
 *
 * @param aAddress RDMA address to read (including upper byte as FEM bus select)
 * @param aLength number of bytes to read
 * @return vector of u8 byte data read from FEM
 */
std::vector<u8> FemClient::rdmaRead(unsigned int aAddress, unsigned int aLength) {

	unsigned int bus = BUS_RDMA;
	unsigned int width = WIDTH_LONG;
	std::vector<u8> values = this->read(bus, width, aAddress, aLength);
    return values;
}

/** rdmaWrite - perform an RDMA write transaction to the FEM
 *
 * This function performs an RDMA write transaction to the FEM, at an address
 * specified in the arguments and of a length determined from the u8 byte
 * values passed. The number of writes completed (which should match the
 * expected length) is returned.
 *
 * @param aAdddress RDMA address to write (including upper byte as FEM bus select)
 * @param aPayload reference to u8 byte vector containing values to write
 * @return number of bytes written
 */
u32 FemClient::rdmaWrite(unsigned int aAddress, std::vector<u8>& aPayload) {

	unsigned int bus   = BUS_RDMA;
	unsigned int width = WIDTH_LONG;
	u32 ack = this->write(bus, width, aAddress, aPayload);
    return ack;
}
/** rdmaWrite - perform an RDMA write transaction to the FEM
 *
 * This function performs an RDMA write transaction to the FEM, at an address
 * specified in the arguments and of a length determined from the u8 byte
 * values passed. The number of writes completed (which should match the
 * expected length) is returned.
 *
 * @param aAdddress RDMA address to write (including upper byte as FEM bus select)
 * @param aPayload reference to u32 word vector containing values to write
 * @return number of bytes written
 */
u32 FemClient::rdmaWrite(unsigned int aAddress, std::vector<u32>& aPayload) {

	unsigned int bus   = BUS_RDMA;
	unsigned int width = WIDTH_LONG;
	std::vector<u8>* payloadPtr = (std::vector<u8>*)&aPayload;
	u32 ack = this->write(bus, width, aAddress, *payloadPtr);

    return ack;
}

/** rdmaWrite - perform a single integer RDMA write transaction to the FEM
 *
 * This function performs an RDMA write transaction to the FEM, at an address
 * specified in the arguments and of a length determined from the u8 byte
 * values passed. The number of writes completed (which should match the
 * expected length) is returned.
 *
 * @param aAdddress RDMA address to write (including upper byte as FEM bus select)
 * @param value a single 32 bit integer value to write
 * @return number of bytes written
 */
void FemClient::rdmaWrite(u_int32_t address, u_int32_t value) {
	std::vector < u32 > payload(1);
	payload[0] = value;
	std::vector < u8 > *payloadPtr = (std::vector<u8>*)(void*) &payload;
	this->rdmaWrite(address, *payloadPtr);
}

/** spiWrite - perform an SPI write transaction to the FEM
 *
 * This function performs an SPI bus transaction to the FEM,,at an address
 * specified in the arguments and of a length determined from the u8 byte
 * values passed. The number of writes completed (which should match the
 * expected length) is returned.
 *
 * @param aAdddress SPI address to read
 * @param aValues reference to u8 byte vector containing values to write
 * @return number of bytes written
 */

u32 FemClient::spiWrite(unsigned int aAddress, std::vector<u8>& aPayload) {

	unsigned int bus   = BUS_SPI;
	unsigned int width = WIDTH_LONG;
	u32 ack = this->write(bus, width, aAddress, aPayload);
    return ack;
}

/** i2cRead - perform an SPI read transaction from the FEM
 *
 * This function performs a SPI read transaction from the FEM, at an address
 * and of the length specified in the arguments. The result is returned as
 * a vector of bytes to the user
 *
 * @param aAddress SPI address to read
 * @param aLength number of bytes to read
 * @return vector of u8 byte data read from FEM
 */
std::vector<u8> FemClient::spiRead(unsigned int aAddress, unsigned int aLength) {

	unsigned int bus = BUS_SPI;
	unsigned int width = WIDTH_LONG;
	std::vector<u8> values = this->read(bus, width, aAddress, aLength);
    return values;
}










