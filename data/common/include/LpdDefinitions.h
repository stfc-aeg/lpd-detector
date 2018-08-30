/*
 * LpdDefinitions.h
 *
 *  Created on: Jan 16th, 2017
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef INCLUDE_LPDDEFINITIONS_H_
#define INCLUDE_LPDDEFINITIONS_H_

namespace Lpd {

    static const size_t num_bit_depths = 4;
    typedef enum {
      bitDepthUnknown = -1,
      bitDepth1  = 0,
      bitDepth6  = 1,
      bitDepth12 = 2,
      bitDepth24 = 3
    } AsicCounterBitDepth;

    //---TODO: Change values for bitdepth levels if needed
    static const size_t primary_packet_size    = 8184;

    static const size_t num_primary_packets[num_bit_depths] = { 320, 320, 320, 320 };
    static const size_t max_primary_packets = 320;
    static const size_t tail_packet_size[num_bit_depths] = { 3464, 3464, 3464, 3464 };
    static const size_t num_tail_packets = 1;

    static const size_t max_num_fems = 1;

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

    typedef struct
    {
    	uint32_t frame_number;
    	uint32_t packet_number_flags;
    } PacketTrailer;

    typedef struct
    {
      uint32_t packets_received;
      uint8_t  sof_marker_count;
      uint8_t  eof_marker_count;
      uint16_t  packet_state[1][max_primary_packets + num_tail_packets];
    } FemReceiveState;

    typedef struct
    {
        uint32_t frame_number;
        uint32_t frame_state;
        struct timespec frame_start_time;
        uint32_t total_packets_received;
        uint8_t total_sof_marker_count;
        uint8_t total_eof_marker_count;
        uint8_t num_active_fems;
        uint8_t active_fem_idx[max_num_fems];
        FemReceiveState fem_rx_state[max_num_fems];
    } FrameHeader;

    inline const std::size_t max_frame_size()
    {
      std::size_t max_frame_size = (sizeof(FrameHeader) + (primary_packet_size * (num_primary_packets[0] + num_tail_packets)));
      return max_frame_size;
    }

    inline const std::size_t num_fem_frame_packets(const AsicCounterBitDepth bit_depth)
    {
      std::size_t num_fem_frame_packets = num_primary_packets[bit_depth] + num_tail_packets;
      return num_fem_frame_packets;
    }
}

#endif /* INCLUDE_LPDDEFINITIONS_H_ */
