/*
 * FemRdma.cpp
 *
 *  Created on: Mar 13, 2012
 *      Author: gm
 */

#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <ifaddrs.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <netinet/in.h>
#include <string.h>
#include "FemClient.h"

#define IP_IDENT_COUNT 0xDB00
#define IP_PKT_LENGTH_BASE 0x1c
#define UDP_LENGTH_BASE 0x0008
#define PACKET_SPLIT_SIZE 0x3e6
#define INT_PKT_GAP_VAL 0x800

#define INT_PKT_GAP_EN 0x11
#define DEBUG_MODE_EN  0x2
#define DEBUG_MODE_STEP 0x4
#define FXD_PKT_SZE	0x8

const u32 kTenGigUdpRdmaAddr       = 0x00000000;

/** configUDP - configure the RDMA channel on the FEM
 *
 * @param fpgaMACaddress string representation of an IP address in dotted quad format
 * @param fpgaIPaddress string representation of an IP address in dotted quad format
 * @param fpgaPort integer containing the port number of the FEM fpga
 * @param hostIPaddress string representation of an IP address in dotted quad format
 * @param hostPort integer containing the port number of the host PC
 * @return 0 if success else -1
 */
u32 FemClient::configUDP(char* fpgaMACaddress, char* fpgaIPaddress, u32 fpgaPort, char* hostIPaddress, u32 hostPort) {
	int rc = 0;
	u_int32_t value;
	unsigned char* hostMAC = getMacAddressFromIP(hostIPaddress);
	unsigned char fpgaMAC[6];
	unsigned char fpgaIP[4];
	unsigned char hostIP[4];
	if (hostMAC == NULL) {
		return -1;
	}
	try {
		to_bytes(fpgaMACaddress, fpgaMAC, 6, 16);
		to_bytes(fpgaIPaddress, fpgaIP, 4, 10);
		to_bytes(hostIPaddress, hostIP, 4, 10);
		value = (fpgaMAC[3] << 24) + (fpgaMAC[2] << 16) + (fpgaMAC[1] << 8) + fpgaMAC[0];
		this->rdmaWrite(kTenGigUdpRdmaAddr + 0, value); // UDP Block 0 MAC Source Lower 32

		value = (hostMAC[1] << 24) + (hostMAC[0] << 16) + (fpgaMAC[5] << 8) + (fpgaMAC[4]);
		this->rdmaWrite(kTenGigUdpRdmaAddr + 1, value); // UDP Block 0 MAC Source Upper 16/Dest Lower 16

		value = (hostMAC[5] << 24) + (hostMAC[4] << 16) + (hostMAC[3] << 8) + hostMAC[2];
		this->rdmaWrite(kTenGigUdpRdmaAddr + 2, value); // UDP Block 0 MAC Dest Upper 32

		value = (IP_IDENT_COUNT << 16) + IP_PKT_LENGTH_BASE;
		this->rdmaWrite(kTenGigUdpRdmaAddr + 4, value); // UDP Block 0 IP Ident / Header Length

		value = (hostIP[1] << 24) + (hostIP[0] << 16) + (0xDE << 8) + 0xAD;
		this->rdmaWrite(kTenGigUdpRdmaAddr + 6, value); // UDP Block 0 IP Dest Addr / Checksum

		value = (fpgaIP[1] << 24) + (fpgaIP[0] << 16) + (hostIP[3] << 8) + hostIP[2];
		this->rdmaWrite(kTenGigUdpRdmaAddr + 7, value); // UDP Block 0 IP Src Addr / Dest Addr

		value = ((fpgaPort & 0xff) << 24) + ((fpgaPort & 0xff00) << 8) + (fpgaIP[3] << 8) + fpgaIP[2];
		this->rdmaWrite(kTenGigUdpRdmaAddr + 8, value); // UDP Block 0 IP Src Port / Src Addr

		value = (UDP_LENGTH_BASE << 16) + ((hostPort & 0xff) << 8) + (hostPort >> 8);
		this->rdmaWrite(kTenGigUdpRdmaAddr + 9, value); // UDP Block 0 UDP Length / Dest Port

		value = PACKET_SPLIT_SIZE;
		this->rdmaWrite(kTenGigUdpRdmaAddr + 0xC, value); // UDP Block 0 Packet Size

		value = INT_PKT_GAP_VAL;
		this->rdmaWrite(kTenGigUdpRdmaAddr + 0xD, value); // UDP Block 0 IFG Value

		value = INT_PKT_GAP_EN;
		this->rdmaWrite(kTenGigUdpRdmaAddr + 0xF, value); // UDP Block 0 IFG Enable

	} catch (FemClientException& e) {
		std::cerr << "Exception caught during configUDP: " << e.what() << std::endl;
		rc = -1;
	}
	free(hostMAC);
	return rc;
}


void FemClient::to_bytes(char *ipName, unsigned char* b, int n, int base) {
	char *end;
	char* iptr = ipName;
	for (int i=0; i<n; i++) {
		b[i] = (unsigned char) strtol(iptr, &end, base);
		iptr = end + 1;
	}
}

/** getMacAddressFromIP - get the MAC address corresponding to the given IP address
 *
 * @param ipAddress string representation of an IP address in dotted quad format
 * @param ip byte array containing the IP address
 * @return the mac address of the interface as a byte array or NULL if not found
 */
unsigned char* FemClient::getMacAddressFromIP(char *ipName) {

	struct ifaddrs *ifaddr, *ifa;
	int family, s;
	char host[NI_MAXHOST];
	struct sockaddr *sdl;
	unsigned char *ptr;
	char *ifa_name = NULL;
	unsigned char* mac_addr = (unsigned char*) calloc(sizeof(unsigned char), 6);

	if (getifaddrs(&ifaddr) == -1) {
		return NULL;
	}

	//iterate to find interface name for given server_ip
	for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
		if (ifa->ifa_addr != NULL) {
			family = ifa->ifa_addr->sa_family;
			if (family == AF_INET) {
				s = getnameinfo(ifa->ifa_addr,
						(family == AF_INET) ? sizeof(struct sockaddr_in) : sizeof(struct sockaddr_in6), host,
						NI_MAXHOST, NULL, 0, NI_NUMERICHOST);
				if (s != 0) {
					return NULL;
				}
				if (strcmp(host, ipName) == 0) {
					ifa_name = ifa->ifa_name;
				}
			}
		}
	}
	if (ifa_name == NULL) {
		return NULL;
	}

	int i;
	//iterate to find corresponding MAC address
	for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
		family = ifa->ifa_addr->sa_family;
		if (family == PF_PACKET && strcmp(ifa_name, ifa->ifa_name) == 0) {
			sdl = (struct sockaddr *) (ifa->ifa_addr);
			ptr = (unsigned char *) sdl->sa_data;
			ptr += 10;
			for (i=0; i<6; i++) {
				mac_addr[i] = *ptr++;
			}
			break;
		}
	}
	freeifaddrs(ifaddr);
	return mac_addr;
}

char* FemClient::getFpgaIpAddressFromHost(const char *ipAddr)
{

	struct in_addr addr;
	if (inet_aton(ipAddr, &addr) == 0)
	{
		std::cout << "Invalid address: " << ipAddr <<std::endl;
		return NULL;
	}
	addr.s_addr += 1 << 24;
	return inet_ntoa(addr);

}
