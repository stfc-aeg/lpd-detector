/*
 * LpdDefinitions.h
 *
 *  Created on: Jan 16th, 2017
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef INCLUDE_LPDDEFINITIONS_H_
#define INCLUDE_LPDDEFINITIONS_H_

namespace Lpd {

  static const size_t primary_packet_size = 8184;
  static const size_t num_primary_packets = 320;

  static const size_t tail_packet_size = 3464;
  static const size_t num_tail_packets = 1;

  static const size_t num_packets = num_primary_packets + num_tail_packets;

  static const uint32_t start_of_frame_mask = 1 << 31;
  static const uint32_t end_of_frame_mask   = 1 << 30;
  static const uint32_t packet_number_mask  = 0x3FFFFFFF;

  static const uint32_t default_frame_number = -1;

  static const int num_asic_rows = 8;
  static const int num_asic_cols = 16;

  static const int num_pixel_rows_per_asic = 32;
  static const int num_pixel_cols_per_asic = 16;

  static const int image_data_header = 64;
  static const int image_data_trailer = 32;

  static const uint16_t pkt_missing_flag = 65535;

  typedef struct
  {
    uint32_t frame_number;
    uint32_t packet_number_flags;
  } PacketTrailer;

  typedef struct
  {
    uint32_t frame_number;
    uint32_t frame_state;
    struct timespec frame_start_time;
    uint32_t total_packets_received;
    uint8_t total_sof_marker_count;
    uint8_t total_eof_marker_count;
    uint16_t packet_state[1][num_packets];
  } FrameHeader;

  static const size_t max_frame_size = sizeof(FrameHeader) + (num_packets * primary_packet_size);
}

#endif /* INCLUDE_LPDDEFINITIONS_H_ */
