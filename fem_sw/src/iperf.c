/*
 * iperf.c
 *
 * This code taken from Xilinx example, not yet tested!
 *
 */

#include "iperf.h"

// iperf server
void iperf_tx_application_thread()
{
	//struct tcp_pcb *pcb;
	struct ip_addr ipaddr;
	int i, sock;
	struct sockaddr_in serv_addr;

	xil_printf("PerfTX: Thread starting...\r\n");

	IP4_ADDR(&ipaddr, 192, 168, 1, 100);		// iperf server address

	// initialise data buffer being sent
	for (i = 0; i < IPERF_SEND_BUFSIZE; i++)
		send_buf[i] = (i % 10) + '0';

	if ((sock = lwip_socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		xil_printf("PerfTX: Error creating socket\n\r");
		return;
	}

	memset((void*)&serv_addr, 0, sizeof serv_addr);
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = IPERF_PORT;
	serv_addr.sin_addr.s_addr = ipaddr.addr;

	print("PerfTX: Connecting to iperf server...");
	if (lwip_connect(sock, (struct sockaddr *)&serv_addr, sizeof (serv_addr)) < 0) {
		xil_printf("PerfTX: Error during connect\n\r");
		return;
	}
	print("PerfTX: Connected to server\n\r");

	while (lwip_write(sock, send_buf, IPERF_SEND_BUFSIZE) >= 0) {
         ;
	}

	print("PerfTX: TX perf stopped\n\r");
}

// iperf RX
void iperf_rx_application_thread()
{
	int sock, new_sd;
	struct sockaddr_in address, remote;
	int size;

	xil_printf("PerfRX: Thread starting...\r\n");

	if ((sock = lwip_socket(AF_INET, SOCK_STREAM, 0)) < 0)
		return;

	address.sin_family = AF_INET;
	address.sin_port = htons(IPERF_PORT);
	address.sin_addr.s_addr = INADDR_ANY;

	if (lwip_bind(sock, (struct sockaddr *)&address, sizeof (address)) < 0)
		return;

	lwip_listen(sock, 5);

	size = sizeof(remote);
	new_sd = lwip_accept(sock, (struct sockaddr *)&remote, (socklen_t*)&size);

	while (1) {
        char recv_buf[1500];
		// keep reading data
		if (lwip_read(new_sd, recv_buf, 1500) <= 0)
			break;
	}

	print("PerfRX: Connection closed, exiting.\r\n");

	lwip_close(new_sd);
}
