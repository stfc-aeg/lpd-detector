/*
 * LpdDefinitions.h
 *
 *  Created on: Jan 16th, 2017
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef INCLUDE_LPDDEFINITIONS_H_
#define INCLUDE_LPDDEFINITIONS_H_

namespace Lpd {

typedef struct
{
  uint32_t frame_number;
  uint32_t packet_number_flags;
} PacketTrailer;

// NOTE: this typedef does not include the packet states due to it's variable size
typedef struct
{
  uint32_t frame_number;
  uint32_t frame_state;
  struct timespec frame_start_time;
  uint32_t total_packets_received;
  uint8_t total_sof_marker_count;
  uint8_t total_eof_marker_count;
  uint16_t num_images;
  uint16_t num_packets;
} FrameHeader;

  static const size_t num_asic_cols = 16;
  static const size_t num_pixel_cols_per_asic = 16;

  static const size_t num_asic_rows = 8;
  static const size_t num_pixel_rows_per_asic = 32;

  static const size_t image_width = num_asic_cols * num_pixel_rows_per_asic;
  static const size_t image_height = num_asic_rows * num_pixel_cols_per_asic;

  static const size_t image_pixel_size = 2;
  static const size_t image_size = (image_width * image_height * image_pixel_size);

  static const size_t primary_packet_size = 8192;
  static const size_t primary_payload_size = primary_packet_size - sizeof(Lpd::PacketTrailer);
  static const size_t num_trail_packets = 1;

  static const size_t xtdf_alignmnent_size = 32;
  static const size_t xtdf_header_size = 64;
  static const size_t xtdf_num_descriptor_arrays = 4;
  static const size_t xtdf_descriptor_array_size[] = {2, 8, 2, 4};
  static const size_t xtdf_detector_specific_size = 416;
  static const size_t xtdf_tb_specific_size = 0;
  static const size_t xtdf_trailer_size = 32;

  static const uint32_t start_of_frame_mask = 1 << 31;
  static const uint32_t end_of_frame_mask   = 1 << 30;
  static const uint32_t packet_number_mask  = 0x3FFFFFFF;

  static const uint32_t default_frame_number = -1;
  static const uint16_t pkt_missing_flag = 65535;
}

#endif /* INCLUDE_LPDDEFINITIONS_H_ */
