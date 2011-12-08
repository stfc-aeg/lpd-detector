/*
 * FemTransaction.h
 *
 *  Created on: Nov 16, 2011
 *      Author: tcn45
 */

#ifndef FEMTRANSACTION_H_
#define FEMTRANSACTION_H_

#include <vector>
#include "protocol.h"

class FemTransaction
{

public:

	FemTransaction(u8 cmd=CMD_UNSUPPORTED, u8 bus=BUS_UNSUPPORTED, u8 width=WIDTH_UNSUPPORTED,
				   u8 state=STATE_UNSUPPORTED, u32 address=0, u8* payload=0, u32 payloadSize=0);
	FemTransaction(const std::vector<u8>& byteStream);

	virtual ~FemTransaction();

	static const size_t headerLen(void) { return sizeof(struct protocol_header); };

	std::vector<u8> encode();
	void appendPayload(u8* aPayload, u32 aPayloadLen);
	void appendPayloadFromStream(const std::vector<u8>& byteStream, size_t offset=0);
	void clearPayload(void);

	// Getter methods
	u8 getCommand(void);
	u8 getState(void);
	u32 getAddress(void);
	std::vector<u8> getPayload(void);

	bool payloadIncomplete(void);
	size_t payloadRemaining(void);


	friend std::ostream& operator<<(std::ostream& aOut, const FemTransaction& aTrans);

	static std::size_t widthToSize(u8 aWidth);

private:

	struct protocol_header mHeader;
	std::vector<u8> mPayload;

	size_t mPayloadRemaining;

	void u16Encode(std::vector<u8>& aEncoded, u16 aValue);
	void u32Encode(std::vector<u8>& aEncoded, u32 aValue);
	void u16Decode(std::vector<u8>& aDecoded, u16 aValue);
	void u32Decode(std::vector<u8>& aDecoded, u32 aValue);

};

#endif /* FEMTRANSACTION_H_ */
