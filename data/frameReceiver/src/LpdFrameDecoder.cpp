/*
 * LpdFrameDecoder.cpp
 *
 * ODIN data frame decoder plugin for LPD detector UDP frame data.
 *
 *  Created on: July 9th, 2018
 *      Author: Jack Haydock, STFC Application Engineering Group
 */

#include "LpdFrameDecoder.h"
#include "logging.h"
#include "version.h"
#include "gettime.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <arpa/inet.h>
#include <boost/algorithm/string.hpp>

using namespace FrameReceiver;

const std::string LpdFrameDecoder::CONFIG_NUM_IMAGES = "numimages";

#define MAX_IGNORED_PACKET_REPORTS 10

//! Constructor for LpdFrameDecoder
//!
//! This constructor sets up the decoder, setting default values of frame tracking information
//! and allocating buffers for packet trailer, dropped frames and scratched packets
//!
LpdFrameDecoder::LpdFrameDecoder() :
    FrameDecoderUDP(),
    current_frame_seen_(Lpd::default_frame_number),
    current_frame_buffer_id_(Lpd::default_frame_number),
    current_frame_buffer_(0),
    current_frame_header_(0),
    dropping_frame_data_(false),
    packets_ignored_(0),
    packets_lost_(0),
    num_images_(Lpd::default_num_images),
    incoming_frame_size_(calculate_frame_size()),
    num_packets_(0)
{
  // Allocate buffers for packet trailer, dropped frames and scratched packets
  dropped_frame_buffer_.reset(new uint8_t[incoming_frame_size_]);

  this->logger_ = Logger::getLogger("FR.LpdDecoderPlugin");
  LOG4CXX_INFO(logger_, "LpdFrameDecoder version " << this->get_version_long() << " loaded");

}

//! Destructor for LpdFrameDecoder
//!
LpdFrameDecoder::~LpdFrameDecoder()
{
}

int LpdFrameDecoder::get_version_major()
{
  return ODIN_DATA_VERSION_MAJOR;
}

int LpdFrameDecoder::get_version_minor()
{
  return ODIN_DATA_VERSION_MINOR;
}

int LpdFrameDecoder::get_version_patch()
{
  return ODIN_DATA_VERSION_PATCH;
}

std::string LpdFrameDecoder::get_version_short()
{
  return ODIN_DATA_VERSION_STR_SHORT;
}

std::string LpdFrameDecoder::get_version_long()
{
  return ODIN_DATA_VERSION_STR;
}


//! Initialise the frame decoder.
//!
//! This method initialises the decoder based on a configuration message passed by the
//! application controller. Parameters found in the decoder configuraiton are parsed and stored
//! in the decoder as appropriate.
//!
//! \param[in] logger - pointer to the message logger
//! \param[in] config_msg - configuration message
//!
void LpdFrameDecoder::init(LoggerPtr& logger, OdinData::IpcMessage& config_msg)
{

  // Pass the configuration message to the base class decoder
  FrameDecoder::init(logger, config_msg);

  LOG4CXX_DEBUG_LEVEL(2, logger_, "Got decoder config message: " << config_msg.encode());

  // Number of Images
  if (config_msg.has_param(CONFIG_NUM_IMAGES))
  {
    num_images_ = config_msg.get_param<int>(CONFIG_NUM_IMAGES);

    // Calculate incoming frame size based on configured number of images
    incoming_frame_size_ = calculate_frame_size();
    dropped_frame_buffer_.reset(new uint8_t[incoming_frame_size_]);
  }

  // Calculate expected number of packets based on frame size
  num_packets_ = (incoming_frame_size_ / Lpd::primary_packet_size) + Lpd::num_trail_packets;

  // Print a packet logger trailer to the appropriate logger if enabled
  if (enable_packet_logging_)
  {
    LOG4CXX_INFO(packet_logger_, "PktTrlr: SourceAddress");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |               SourcePort");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |               |     DestinationPort");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |               |     |     Bytes Received");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |               |     |     |     FrameCounter  [4 Bytes]");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |               |     |     |     |           PacketCounter&Flags [4 Bytes]");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |               |     |     |     |           |");
    LOG4CXX_INFO(packet_logger_, "PktTrlr: |-------------- |---- |---- |---- |---------- |----------");
  }

  // Reset the scratched and lost packet counters
  packets_ignored_ = 0;
  packets_lost_ = 0 ;

  // Create buffer for first packet
  current_frame_seen_ = Lpd::default_frame_number;
  current_frame_buffer_ = dropped_frame_buffer_.get();
  LOG4CXX_DEBUG_LEVEL(2, logger_, "Creating first frame buffer");
  current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
  initialise_frame_header(current_frame_header_);
}

void LpdFrameDecoder::request_configuration(const std::string param_prefix,
    OdinData::IpcMessage& config_reply)
{
  // Call the base class method to populate parameters
  FrameDecoder::request_configuration(param_prefix, config_reply);
}

const size_t LpdFrameDecoder::calculate_frame_size(void) const
{
  size_t frame_size = 0;

  // Image Data Header
  frame_size += Lpd::xtdf_header_size;

  // Pixel Data
  size_t pixel_data_size = Lpd::image_size * num_images_;
  frame_size += pixel_data_size;

  // Image Descriptor Arrays
  size_t descriptor_array_size = 0;
  for (unsigned int descriptor = 0; descriptor < Lpd::xtdf_num_descriptor_arrays; descriptor++)
  {
    size_t descriptor_size = Lpd::xtdf_alignmnent_size *
        (1 + (unsigned int)((num_images_ * Lpd::xtdf_descriptor_array_size[descriptor] - 1) / 32));
    descriptor_array_size += descriptor_size;
  }
  frame_size += descriptor_array_size;

  // LPD specific size
  frame_size += Lpd::xtdf_detector_specific_size;

  // TB-specific size
  frame_size += Lpd::xtdf_tb_specific_size;

  // Image Data Trailer
  frame_size += Lpd::xtdf_trailer_size;

  return frame_size;
}

// Get the size of the frame buffers required for current operation mode.
const size_t LpdFrameDecoder::get_frame_buffer_size(void) const
{
  size_t frame_buffer_size =
      get_frame_header_size()
      + num_packets_ * Lpd::primary_payload_size;

  return frame_buffer_size;
}

// Get the size of the frame header
const size_t LpdFrameDecoder::get_frame_header_size(void) const
{
  size_t frame_header_size =
      sizeof(Lpd::FrameHeader)
      + (num_packets_ * 2);

  return frame_header_size;
}

//! Initialise a frame header
//!
//! This method initialises the frame header specified by the pointer argument, setting
//! fields to their default values, clearing packet counters
//!
//! \param[in] header_ptr - pointer to frame header to initialise.
//!
void LpdFrameDecoder::initialise_frame_header(Lpd::FrameHeader* header_ptr)
{

  header_ptr->frame_number = current_frame_seen_;
  header_ptr->frame_state = FrameDecoder::FrameReceiveStateIncomplete;
  header_ptr->total_packets_received = 0;
  header_ptr->total_sof_marker_count = 0;
  header_ptr->total_eof_marker_count = 0;
  header_ptr->num_images = num_images_;
  header_ptr->num_packets = num_packets_;

  // Packet State Flags
  void* packet_state_ptr = reinterpret_cast<void*>(header_ptr) + sizeof(Lpd::FrameHeader);
  memset(packet_state_ptr, Lpd::pkt_missing_flag, num_packets_ * 2);

  gettime(reinterpret_cast<struct timespec*>(&(header_ptr->frame_start_time)));
}

//---NOTE: These methods are required by odin-data to avoid errors but do not serve any purpose within Lpd
const size_t LpdFrameDecoder::get_packet_header_size(void) const
{
  return 0;
}
void* LpdFrameDecoder::get_packet_header_buffer(void)
{
  return NULL;
}
void LpdFrameDecoder::process_packet_header(size_t bytes_received, int port, struct sockaddr_in* from_addr)
{}
//---------------------------------------------------------------------------------

// Get a pointer to the next payload buffer.
//
// This method returns a pointer to the next packet payload buffer within the appropriate frame.
// This is 8 bytes before the end of the previous packet, overwriting the previous packet trailer.
//
// \return pointer to the next payload buffer

void* LpdFrameDecoder::get_next_payload_buffer(void) const
{
  uint8_t* next_receive_location;

  next_receive_location =
      reinterpret_cast<uint8_t*>(current_frame_buffer_)
      + get_frame_header_size()
      + (Lpd::primary_payload_size * current_frame_header_->total_packets_received);

    return reinterpret_cast<void*>(next_receive_location);
}

//! Get the next packet payload size to receive.
//!
//! This method returns the payload size to receive for the next incoming packet.
//!
//! \return size of next packet payload in bytes
//!
size_t LpdFrameDecoder::get_next_payload_size(void) const
{
    return (Lpd::primary_packet_size);
}


//! Process a received packet payload.
//!
//! This method processes the payload of a received packet. This is restricted to checking the
//! subframe trailer if appropriate and keeping track of the number of packets, SOF and EOF markers
//! etc received. If this packet is the last required to complete a frame, the number of SOF and EOF
//! markers seen is validated, the frame state is set to complete and the ready callback is called
//! to notify the main thread that the buffer is ready for processing.
//!
//! \param[in] bytes_received - number of packet payload bytes received
//! \return current frame receive state
//!
FrameDecoder::FrameReceiveState LpdFrameDecoder::process_packet(size_t bytes_received, int port, struct sockaddr_in* from_addr)
{
  FrameDecoder::FrameReceiveState frame_state = FrameDecoder::FrameReceiveStateIncomplete;

  // Pointers to packet and trailer
  uint8_t* pkt_ptr = reinterpret_cast<uint8_t*>(get_next_payload_buffer());
  uint8_t* trlr_ptr = reinterpret_cast<uint8_t*>(pkt_ptr + (bytes_received - sizeof(Lpd::PacketTrailer)));

  // Extract fields from packet trailer
  uint32_t frame_number = get_frame_number (trlr_ptr);
  uint32_t packet_number = get_packet_number (trlr_ptr);
  bool start_of_frame_marker = get_start_of_frame_marker (trlr_ptr);
  bool end_of_frame_marker = get_end_of_frame_marker (trlr_ptr);

  // Print packet info to file
  if (enable_packet_logging_){

    std::stringstream ss;

    ss << "PktTrlr:"
        << std::left << " " << std::setw (15) << inet_ntoa (from_addr->sin_addr) // src address
        << std::right << " " << std::setw (5) << ntohs (from_addr->sin_port) // src port
        << " " << std::setw(5) << port // dest port
        << " " << std::setw(4) << bytes_received
        << std::hex;

    // Print packet trailer
    for (unsigned int trlr_byte = 0; trlr_byte < sizeof(Lpd::PacketTrailer); trlr_byte++)
    {
      if (trlr_byte % 8 == 0)
      {
        ss << "  ";
      }
      ss << std::setw (2) << std::setfill ('0') << (unsigned int) *trlr_ptr << " ";
      trlr_ptr++;
    }

    // Verify that system recognises SOF/EOF
    if (start_of_frame_marker){
      ss << "SOF";
    }
    else if (end_of_frame_marker){
      ss << "EOF";
    }
    LOG4CXX_INFO(packet_logger_, ss.str ());
  }

  LOG4CXX_DEBUG_LEVEL(3, logger_, "Got packet trailer:"
      << " frame number: " << frame_number
      << " packet number: " << packet_number
      << " EOF: " << (int) end_of_frame_marker
      << " port: " << port
  );

  if (frame_number != current_frame_seen_)
  {
    LOG4CXX_DEBUG_LEVEL(2, logger_, "Packet from frame " << frame_number << " does not match current frame " << current_frame_seen_);

    // If current frame is left over from previous acquisition, reuse it rather than dumping it
    if ((current_frame_header_->total_packets_received == 0) && (current_frame_buffer_id_ != -1))
    {
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Current frame " << current_frame_seen_ << " has not received any packets, repurposing buffer for frame " << frame_number );
      current_frame_header_->frame_number = frame_number;
      frame_buffer_map_[frame_number] = current_frame_buffer_id_;
      frame_buffer_map_.erase(current_frame_seen_);
      current_frame_seen_ = frame_number;
      gettime(reinterpret_cast<struct timespec*>(&(current_frame_header_->frame_start_time)));
    }
    else
    {
      current_frame_seen_ = frame_number;

      if (frame_buffer_map_.count(current_frame_seen_) == 0)
      {
        if (empty_buffer_queue_.empty())
        {
          current_frame_buffer_ = dropped_frame_buffer_.get();
          if (!dropping_frame_data_)
          {
            LOG4CXX_ERROR(logger_, "First packet from frame " << current_frame_seen_
                << " detected but no free buffers available. Dropping packet data for this frame");
            dropping_frame_data_ = true;
          }
        }
        else
        {
          current_frame_buffer_id_ = empty_buffer_queue_.front();
          empty_buffer_queue_.pop();
          frame_buffer_map_[current_frame_seen_] = current_frame_buffer_id_;
          current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);

          if (!dropping_frame_data_)
          {
            LOG4CXX_DEBUG_LEVEL(2, logger_, "First packet from frame " << current_frame_seen_
                << " detected, allocating frame buffer ID " << current_frame_buffer_id_);
          }
          else
          {
            dropping_frame_data_ = false;
            LOG4CXX_DEBUG_LEVEL(2, logger_, "Free buffer now available for frame "
                << current_frame_seen_ << ", allocating frame buffer ID "
                << current_frame_buffer_id_);
          }
        }
          // Initialise frame header
          LOG4CXX_DEBUG_LEVEL(2, logger_, "Creating new buffer for frame " << current_frame_seen_);
          current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
          initialise_frame_header(current_frame_header_);

          // Copy payload into new frame buffer
          LOG4CXX_DEBUG_LEVEL(2, logger_, "Copying payload from packet "
              << packet_number << " (at " << &pkt_ptr
              << ") into frame " << current_frame_seen_ << " buffer at " << get_next_payload_buffer());

          memcpy (get_next_payload_buffer(), pkt_ptr, (bytes_received - sizeof(Lpd::PacketTrailer)));
          LOG4CXX_DEBUG_LEVEL(2, logger_, "memcopy complete");
      }
      else
      {
        current_frame_buffer_id_ = frame_buffer_map_[current_frame_seen_];
        current_frame_buffer_id_ = empty_buffer_queue_.front();
        current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);
        current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
      }
    }
  }

  // If SOF or EOF markers seen in packet trailer, increment appropriate field in frame header
  if (start_of_frame_marker)
  {
    (current_frame_header_->total_sof_marker_count)++;
  }
  if (end_of_frame_marker)
  {
    (current_frame_header_->total_eof_marker_count)++;
  }

  // Update packet_number state map in frame header
  uint16_t* pkt_state_ptr = reinterpret_cast<uint16_t*>(current_frame_buffer_) + (sizeof(Lpd::FrameHeader)/2) + packet_number;
  *pkt_state_ptr = current_frame_header_->total_packets_received;

  // Increment the total packet received counter
  current_frame_header_->total_packets_received++;

  // If we have received the expected number of packets, perform end of frame processing
  // and hand off the frame for downstream processing.
  if (current_frame_header_->total_packets_received == num_packets_)
  {
    // Check that the appropriate number of SOF and EOF markers (one each per frame) have been seen, otherwise log a warning
    if ((current_frame_header_->total_sof_marker_count != 1) ||
        (current_frame_header_->total_eof_marker_count != 1))
    {
      LOG4CXX_WARN(logger_, "Incorrect number of SOF ("
          << (int)current_frame_header_->total_sof_marker_count << ") or EOF ("
          << (int)current_frame_header_->total_eof_marker_count << ") markers "
          << "seen on completed frame " << current_frame_seen_);
    }

    // Set frame state accordingly
    frame_state = FrameDecoder::FrameReceiveStateComplete;

    // Complete frame header
    current_frame_header_->frame_state = frame_state;

    if (!dropping_frame_data_)
    {
      // Erase frame from buffer map
      frame_buffer_map_.erase(current_frame_seen_);

      // Notify main thread that frame is ready
      ready_callback_(current_frame_buffer_id_, current_frame_header_->frame_number);

      // Initialise frame buffer for next frame
      current_frame_buffer_id_ = empty_buffer_queue_.front();
      empty_buffer_queue_.pop();
      current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);
      current_frame_seen_ += 1;
      frame_buffer_map_[current_frame_seen_] = current_frame_buffer_id_;

      // Initialise next frame header
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Creating new buffer for frame "
          << current_frame_seen_ << " in buffer " << current_frame_buffer_id_);
      current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
      initialise_frame_header(current_frame_header_);
    }
  }

  return frame_state;
}

//! Monitor the state of currently mapped frame buffers.
//!
//! This method, called periodically by a timer in the receive thread reactor, monitors the state
//! of currently mapped frame buffers. In any frame buffers have been mapped for a sufficiently
//! long time that indicates packets have been lost and the frame is incomplete, the frame is
//! flagged as such and notified to the main thread via the ready callback.
//!
void LpdFrameDecoder::monitor_buffers(void)
{

  int frames_timedout = 0;
  struct timespec current_time;

  gettime(&current_time);

  // Loop over frame buffers currently in map and check their state
  std::map<int, int>::iterator buffer_map_iter = frame_buffer_map_.begin();
  while (buffer_map_iter != frame_buffer_map_.end())
  {
    int frame_num = buffer_map_iter->first;
    int buffer_id = buffer_map_iter->second;
    void* buffer_addr = buffer_manager_->get_buffer_address(buffer_id);
    Lpd::FrameHeader* frame_header = reinterpret_cast<Lpd::FrameHeader*>(buffer_addr);

    if (elapsed_ms(frame_header->frame_start_time, current_time) > frame_timeout_ms_)
    {

      if (frame_header->total_packets_received >= 1)
      {
        // Calculate packets lost on this frame and add to total
        uint32_t packets_lost = num_packets_ - frame_header->total_packets_received;
        packets_lost_ += packets_lost;

        LOG4CXX_DEBUG_LEVEL(1, logger_, "Frame " << frame_num << " in buffer " << buffer_id
            << " addr 0x" << std::hex
            << buffer_addr << std::dec << " timed out with " << frame_header->total_packets_received
            << " packets received, " << packets_lost << " packets lost");

        frame_header->frame_state = FrameReceiveStateTimedout;
        ready_callback_(buffer_id, frame_num);
        frames_timedout++;

        frame_buffer_map_.erase(buffer_map_iter++);
      }
      else
      {
        buffer_map_iter++;
      }
    }
    else
    {
      buffer_map_iter++;
    }
  }

  if (frames_timedout)
  {
    LOG4CXX_WARN(logger_, "Released " << frames_timedout << " timed out incomplete frames");
  }
  frames_timedout_ += frames_timedout;

  LOG4CXX_DEBUG_LEVEL(3, logger_,  get_num_mapped_buffers() << " frame buffers in use, "
      << get_num_empty_buffers() << " empty buffers available, "
      << frames_timedout_ << " incomplete frames timed out, "
      << packets_lost_ << " packets lost"
  );

}

//! Get the current status of the frame decoder.
//!
//! This method populates the IpcMessage passed by reference as an argument with decoder-specific
//! status information, e.g. packet loss by source.
//!
//! \param[in] param_prefix - path to be prefixed to each status parameter name
//! \param[in] status_msg - reference to IpcMesssage to be populated with parameters
//!
void LpdFrameDecoder::get_status(const std::string param_prefix,
    OdinData::IpcMessage& status_msg)
{
  status_msg.set_param(param_prefix + "name", std::string("LpdFrameDecoder"));
  status_msg.set_param(param_prefix + "packets_lost", packets_lost_);
}

uint32_t LpdFrameDecoder::get_frame_number(uint8_t* &trlr_ptr) const
{
  return reinterpret_cast<Lpd::PacketTrailer*>(trlr_ptr)->frame_number;
}

//! Get the current packet number.
//!
//! This method extracts and returns the packet number from the current UDP packet trailer.
//!
//! \return current packet number
//!
uint32_t LpdFrameDecoder::get_packet_number(uint8_t* &trlr_ptr) const
{
  return reinterpret_cast<Lpd::PacketTrailer*>(trlr_ptr)->packet_number_flags & Lpd::packet_number_mask;
}

//! Get the current packet start of frame (SOF) marker.
//!
//! This method extracts and returns the start of frame marker from the current UDP packet trailer.
//!
//! \return true is SOF marker set in packet trailer
//!
bool LpdFrameDecoder::get_start_of_frame_marker(uint8_t* &trlr_ptr) const
{
  uint32_t packet_number_flags =
      reinterpret_cast<Lpd::PacketTrailer*>(trlr_ptr)->packet_number_flags;
  return ((packet_number_flags & Lpd::start_of_frame_mask) != 0);
}

//! Get the current packet end of frame (EOF) marker.
//!
//! This method extracts and returns the end of frame marker from the current UDP packet trailer.
//!
//! \return true is EOF marker set in packet trailer
//!
bool LpdFrameDecoder::get_end_of_frame_marker(uint8_t* &trlr_ptr) const
{
  uint32_t packet_number_flags =
      reinterpret_cast<Lpd::PacketTrailer*>(trlr_ptr)->packet_number_flags;
  return ((packet_number_flags & Lpd::end_of_frame_mask) != 0);
}

//! Calculate and return an elapsed time in milliseconds.
//!
//! This method calculates and returns an elapsed time in milliseconds based on the start and
//! end timespec structs passed as arguments.
//!
//! \param[in] start - start time in timespec struct format
//! \param[in] end - end time in timespec struct format
//! \return eclapsed time between start and end in milliseconds
//!
unsigned int LpdFrameDecoder::elapsed_ms(struct timespec& start, struct timespec& end)
{

  double start_ns = ((double) start.tv_sec * 1000000000) + start.tv_nsec;
  double end_ns = ((double) end.tv_sec * 1000000000) + end.tv_nsec;

  return (unsigned int)((end_ns - start_ns) / 1000000);
}
