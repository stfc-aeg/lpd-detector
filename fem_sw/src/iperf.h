/*
 * iperf.h
 *
* This code taken from Xilinx example, not yet tested!
*
 */

#ifndef IPERF_H_
#define IPERF_H_

#include <string.h>
#include "lwip/init.h"
#include "lwip/inet.h"
#include "lwip/ip_addr.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwipopts.h"
#include "netif/xadapter.h"

#define IPERF_PORT			5001
#define IPERF_SEND_BUFSIZE	1440

static char send_buf[IPERF_SEND_BUFSIZE];

void iperf_tx_application_thread();
void iperf_rx_application_thread();

#endif /* IPERF_H_ */
