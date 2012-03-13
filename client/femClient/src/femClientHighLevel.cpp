/*
 * femClientHighLevel.cpp - FemClient high level transaction methods
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




