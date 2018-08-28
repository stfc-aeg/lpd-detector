/*
 * LpdFrameDecoder.cpp
 *
 * ODIN data frame decoder plugin for LPD detector UDP frame data.
 *
 *  Created on: Jan 16th, 2017
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "LpdFrameDecoder.h"
#include "gettime.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <arpa/inet.h>
#include <boost/algorithm/string.hpp>

using namespace FrameReceiver;

const std::string LpdFrameDecoder::asic_bit_depth_str_[Lpd::num_bit_depths] =
    {"1-bit", "6-bit", "12-bit", "24-bit"};

const std::string LpdFrameDecoder::CONFIG_FEM_PORT_MAP = "fem_port_map";
const std::string LpdFrameDecoder::CONFIG_BITDEPTH = "bitdepth";

#define MAX_IGNORED_PACKET_REPORTS 10

//! Constructor for LpdFrameDecoder
//!
//! This constructor sets up the decoder, setting default values of frame tracking information
//! and allocating buffers for packet trailer, dropped frames and scratched packets
//!
LpdFrameDecoder::LpdFrameDecoder() :
    FrameDecoderUDP(),
    asic_counter_bit_depth_(Lpd::bitDepth12),
    current_frame_seen_(Lpd::default_frame_number),
    current_frame_buffer_id_(Lpd::default_frame_number),
    current_frame_buffer_(0),
    current_frame_header_(0),
    num_active_fems_(0),
    dropping_frame_data_(false),
    packets_ignored_(0),
    packets_lost_(0)
{

  // Allocate buffers for packet trailer, dropped frames and scratched packets
  current_packet_trailer_.reset(new uint8_t[Lpd::primary_packet_size + sizeof(Lpd::PacketTrailer)]);
  dropped_frame_buffer_.reset(new uint8_t[Lpd::max_frame_size()]);
  ignored_packet_buffer_.reset(new uint8_t[Lpd::primary_packet_size]);
}

//! Destructor for LpdFrameDecoder
//!
LpdFrameDecoder::~LpdFrameDecoder()
{
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

  // Extract the FEM to port map from the config message and pass to the parser. If no map is
  // present, use the default. If the map cannot be parsed correctly, thrown an exception to signal
  // an error to the app controller. Set the current number of active FEMs based on the output
  // of the map parsing.
  if (config_msg.has_param(CONFIG_FEM_PORT_MAP))
  {
      fem_port_map_str_ = config_msg.get_param<std::string>(CONFIG_FEM_PORT_MAP);
      LOG4CXX_DEBUG_LEVEL(1, logger_, "Parsing FEM to port map found in config: "
                          << fem_port_map_str_);
  }
  else
  {
      LOG4CXX_DEBUG_LEVEL(1,logger_, "No FEM to port map found in config, using default: "
                          << default_fem_port_map);
      fem_port_map_str_ = default_fem_port_map;
  }

  num_active_fems_ = parse_fem_port_map(fem_port_map_str_);
  if (num_active_fems_)  {
      LOG4CXX_DEBUG_LEVEL(1, logger_, "Parsed " << num_active_fems_
                          << " entries from port map configuration");
  }
  else
  {
      throw OdinData::OdinDataException("Failed to parse FEM to port map entries from configuration");
  }

  // Extract the ASIC counter bit depth from the config message
  if (config_msg.has_param(CONFIG_BITDEPTH))
  {
    std::string bit_depth_str = config_msg.get_param<std::string>(CONFIG_BITDEPTH);

    Lpd::AsicCounterBitDepth bit_depth =
        parse_bit_depth(bit_depth_str);

    if (bit_depth == Lpd::bitDepthUnknown)
    {
      LOG4CXX_ERROR(logger_, "Unknown bit depth configuration parameter specified: "
                    << bit_depth_str << ", defaulting to "
                    << asic_bit_depth_str_[asic_counter_bit_depth_]);
    }
    else
    {
      asic_counter_bit_depth_ = bit_depth;
    }
  }
  LOG4CXX_DEBUG_LEVEL(1, logger_, "Setting ASIC counter bit depth to "
      << asic_bit_depth_str_[asic_counter_bit_depth_]);

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
  for (int fem = 0; fem < Lpd::max_num_fems; fem++)
  {
    fem_packets_lost_[fem] = 0;
  }

  // Create buffer for first packet
  current_frame_buffer_ = dropped_frame_buffer_.get();
  LOG4CXX_DEBUG_LEVEL(2, logger_, "Creating first frame buffer");
  current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
  current_frame_seen_ = 1;
  initialise_frame_header(current_frame_header_);
}

void LpdFrameDecoder::request_configuration(const std::string param_prefix,
    OdinData::IpcMessage& config_reply)
{

  // Call the base class method to populate parameters
  FrameDecoder::request_configuration(param_prefix, config_reply);

  // Add current configuration parameters to reply
  config_reply.set_param(param_prefix + CONFIG_FEM_PORT_MAP, fem_port_map_str_);
  config_reply.set_param(param_prefix + CONFIG_BITDEPTH, asic_bit_depth_str_[asic_counter_bit_depth_]);

}

//! Get the size of the frame buffers required for current operation mode.
//!
//! This method returns the frame buffer size required for the current operation mode, which is
//! determined by frame size based on bit depth and number of active FEMs.
//!
//! \return size of frame buffer in bytes
//!
const size_t LpdFrameDecoder::get_frame_buffer_size(void) const
{
  size_t frame_buffer_size = (Lpd::max_frame_size() * num_active_fems_);
  return frame_buffer_size;
}

const size_t LpdFrameDecoder::get_frame_header_size(void) const
{

  return sizeof(Lpd::FrameHeader);
}

//! Initialise a frame header
//!
//! This method initialises the frame header specified by the pointer argument, setting
//! fields to their default values, clearing packet counters and setting the active FEM
//! fields as appropriate.
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

  header_ptr->num_active_fems = num_active_fems_;
  for (LpdDecoderFemMap::iterator it = fem_port_map_.begin();
        it != fem_port_map_.end(); ++it)
  {
    header_ptr->active_fem_idx[(it->second).buf_idx_] = (it->second).fem_idx_;
  }
  memset(header_ptr->fem_rx_state, UINT_MAX,
      sizeof(Lpd::FemReceiveState) * Lpd::max_num_fems);

  gettime(reinterpret_cast<struct timespec*>(&(header_ptr->frame_start_time)));

}

//---TODO: Remove/replace when feasable---------------------------------------------
const size_t LpdFrameDecoder::get_packet_header_size(void) const
{}
void* LpdFrameDecoder::get_packet_header_buffer(void)
{}
void LpdFrameDecoder::process_packet_header(size_t bytes_received, int port, struct sockaddr_in* from_addr)
{}
//---------------------------------------------------------------------------------

// Get a pointer to the next payload buffer.
//
// This method returns a pointer to the next packet payload buffer within the appropriate frame.
// The location of this is determined by state information set during the processing of the packet
// trailer. If thepacket is not from a recognised FEM, a pointer to the ignored packet buffer will
// be returned instead.
//
// \return pointer to the next payload buffer

void* LpdFrameDecoder::get_next_payload_buffer(void) const
{
	uint8_t* next_receive_location;
    int trailer_size = 0;

	next_receive_location =
			reinterpret_cast<uint8_t*>(current_frame_buffer_)
			+ get_frame_header_size()
			+ (Lpd::primary_packet_size * current_frame_header_->total_packets_received);

	return reinterpret_cast<void*>(next_receive_location);
}

//! Get the next packet payload size to receive.
//!
//! This method returns the payload size to receive for the next incoming packet, based on state
//! information set during processing of the trailer. The receive size may vary depending on
//! whether a primary or tail packet is being received, the size of both of which is dependent
//! on the current bit depth.
//!
//! \return size of next packet payload in bytes
//!
size_t LpdFrameDecoder::get_next_payload_size(void) const
{
    return (Lpd::primary_packet_size + sizeof(Lpd::PacketTrailer));
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


  // Resolve the FEM index from the port the packet arrived on
  if (fem_port_map_.count(port)) {
    current_packet_fem_map_ =  fem_port_map_[port];

  }


  // Only process the packet if it is not being ignored due to an illegal port to FEM index mapping
  if (current_packet_fem_map_.fem_idx_ != ILLEGAL_FEM_IDX)
  {

	  LOG4CXX_DEBUG_LEVEL(3, logger_, "Got packet trailer:"
	      << " frame number: " << frame_number
	      << " packet number: " << packet_number
	      << " EOF: " << (int) end_of_frame_marker
	      << " port: " << port
		  << " fem idx: " << current_packet_fem_map_.fem_idx_
	  );

	  if (frame_number != current_frame_seen_)
	  {
		  LOG4CXX_DEBUG_LEVEL(2, logger_, "Packet from frame " << frame_number << " does not match current frame " << current_frame_seen_);
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
	        }
	        else
	        {
	          current_frame_buffer_id_ = frame_buffer_map_[current_frame_seen_];
	          current_frame_buffer_id_ = empty_buffer_queue_.front();
	          current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);
	          current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
	        }

	      }
	  Lpd::FemReceiveState* fem_rx_state =
	      &(current_frame_header_->fem_rx_state[current_packet_fem_map_.buf_idx_]);
	  // If SOF or EOF markers seen in packet trailer, increment appropriate field in frame header
	  if (start_of_frame_marker)
	  {
		  (fem_rx_state->sof_marker_count)++;
	      (current_frame_header_->total_sof_marker_count)++;
	  }
	  if (end_of_frame_marker)
	  {
		  (fem_rx_state->eof_marker_count)++;
	      (current_frame_header_->total_eof_marker_count)++;
	  }

	  // Update packet_number state map in frame header
	  fem_rx_state->packet_state[0][packet_number] = current_frame_header_->total_packets_received;

      // Increment the total and per-FEM packet received counters
      (fem_rx_state->packets_received)++;
      current_frame_header_->total_packets_received++;


      // If we have received the expected number of packets, perform end of frame processing
      // and hand off the frame for downstream processing.
      if (current_frame_header_->total_packets_received ==
        (Lpd::num_fem_frame_packets(asic_counter_bit_depth_) * num_active_fems_))
      {
    	 LOG4CXX_DEBUG_LEVEL(2, logger_,(Lpd::num_fem_frame_packets(asic_counter_bit_depth_) * num_active_fems_));

      // Check that the appropriate number of SOF and EOF markers (one each per frame) have
      // been seen, otherwise log a warning

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

//---DEBUG CODE: Print out frame header
      std::stringstream ss;
      for (unsigned int i = 0; i < sizeof(Lpd::FrameHeader); i++)
      {
        if ((i) % 32 == 0) {ss << "\n" << std::dec << i << std::hex << ": ";}

        uint8_t* pkt_ptr = reinterpret_cast<uint8_t*>(current_frame_buffer_ + i);

        ss << std::hex << std::setw (2) << std::setfill ('0') << (unsigned int) *pkt_ptr << " ";
        if ((i+1) % 8 == 0) {ss << " ";}
      }
      LOG4CXX_DEBUG_LEVEL(2, logger_, ss.str ());
//---

      if (!dropping_frame_data_)
      {
        // Erase frame from buffer map
        frame_buffer_map_.erase(current_frame_seen_);

        // Notify main thread that frame is ready
        ready_callback_(current_frame_buffer_id_, current_frame_header_->frame_number);

        // Initialise frame header
        current_frame_buffer_id_ = empty_buffer_queue_.front();
        empty_buffer_queue_.pop();
        current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);
        current_frame_seen_ += 1;
	    frame_buffer_map_[current_frame_seen_] = current_frame_buffer_id_;

        LOG4CXX_DEBUG_LEVEL(2, logger_, "Creating new buffer for frame "
        		<< current_frame_seen_ << " in buffer " << current_frame_buffer_id_);
        current_frame_header_ = reinterpret_cast<Lpd::FrameHeader*>(current_frame_buffer_);
        initialise_frame_header(current_frame_header_);
      }
    }

  }
  else {
	  LOG4CXX_DEBUG_LEVEL(3, logger_, "Illegal FEM IDX: " << current_packet_fem_map_.fem_idx_);
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

      const std::size_t num_fem_frame_packets =
          Lpd::num_fem_frame_packets(asic_counter_bit_depth_);

      // Calculate packets lost on this frame and add to total
      uint32_t packets_lost = (num_fem_frame_packets * num_active_fems_) -
          frame_header->total_packets_received;
      packets_lost_ += packets_lost;
      if (packets_lost)
      {
        for (LpdDecoderFemMap::iterator iter = fem_port_map_.begin();
            iter != fem_port_map_.end(); ++iter)
        {
          fem_packets_lost_[(iter->second).fem_idx_] += num_fem_frame_packets -
              (frame_header->fem_rx_state[(iter->second).buf_idx_].packets_received);
        }
      }


      if (frame_header->total_packets_received >= 1)
      {
    	  LOG4CXX_DEBUG_LEVEL(1, logger_, "Frame " << frame_num << " in buffer " << buffer_id
    	            << " addr 0x" << std::hex
    	            << buffer_addr << std::dec << " timed out with " << frame_header->total_packets_received
    	            << " packets received, " << packets_lost << " packets lost");

    	  frame_header->frame_state = FrameReceiveStateTimedout;
    	  ready_callback_(buffer_id, frame_num);
      }
      else
      {
    	  LOG4CXX_DEBUG_LEVEL(1, logger_, "Frame " << frame_num << " in buffer " << buffer_id
    	      	    << " addr 0x" << std::hex
    	      	    << buffer_addr << std::dec
					<< " timed out with no packets received. Dropping frame");
    	  // drop frame
    	  dropping_frame_data_ = true;
      }
      frames_timedout++;

      frame_buffer_map_.erase(buffer_map_iter++);
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

  // Workaround for lack of array setters in IpcMessage
  rapidjson::Value fem_packets_lost_array(rapidjson::kArrayType);
  rapidjson::Value::AllocatorType allocator;

  for (int fem = 0; fem < Lpd::max_num_fems; fem++)
  {
    fem_packets_lost_array.PushBack(fem_packets_lost_[fem], allocator);
  }
  status_msg.set_param(param_prefix + "fem_packets_lost", fem_packets_lost_array);

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

//! Parse the port to FEM index map configuration string.
//!
//! This method parses a configuration string containing port to FEM index mapping information,
//! which is expected to be of the format "port:idx,port:idx" etc. The map is saved in a member
//! variable for use in packet handling.
//!
//! \param[in] fem_port_map_str - string of port to FEM index mapping configuration
//! \return number of valid map entries parsed from string
//!
std::size_t LpdFrameDecoder::parse_fem_port_map(const std::string fem_port_map_str)
{
    // Clear the current map
    fem_port_map_.clear();

    // Define entry and port:idx delimiters
    const std::string entry_delimiter(",");
    const std::string elem_delimiter(":");

    // Vector to hold entries split from map
    std::vector<std::string> map_entries;

    // Split into entries
    boost::split(map_entries, fem_port_map_str, boost::is_any_of(entry_delimiter));

    unsigned int buf_idx = 0;
    // Loop over entries, further splitting into port / fem index pairs
    for (std::vector<std::string>::iterator it = map_entries.begin(); it != map_entries.end(); ++it)
    {
        if (buf_idx >= Lpd::max_num_fems) {
          LOG4CXX_WARN(logger_, "Decoder FEM port map configuration contains too many elements, "
                        << "truncating to maximium number of FEMs allowed ("
                        << Lpd::max_num_fems << ")");
          break;
        }

        std::vector<std::string> entry_elems;
        boost::split(entry_elems, *it, boost::is_any_of(elem_delimiter));

        // If a valid entry is found, save into the map
        if (entry_elems.size() == 2) {
            int port = static_cast<int>(strtol(entry_elems[0].c_str(), NULL, 10));
            int fem_idx = static_cast<int>(strtol(entry_elems[1].c_str(), NULL, 10));
            fem_port_map_[port] = LpdDecoderFemMapEntry(fem_idx, buf_idx);
            buf_idx++;
        }
    }

    // Return the number of valid entries parsed
    return fem_port_map_.size();
}

//! Parse the ASIC counter bit depth configuration string.
//!
//! This method parses a configuration string specifying the LPD ASIC counter bit
//! depth currently in use, returning an enumerated constant for use in the decoder.
//!
//! \param[in] bit_depth_str - string of the bit depth
//! \return enumerated constant defining bit depth, or unknown if the string is not recognised
//!
Lpd::AsicCounterBitDepth LpdFrameDecoder::parse_bit_depth(
    const std::string bit_depth_str)
{

  //! Set the default bit depth to return to unknown
  Lpd::AsicCounterBitDepth bit_depth = Lpd::bitDepthUnknown;

  // Initialise a mapping of string to bit depth
  static std::map<std::string, Lpd::AsicCounterBitDepth>bit_depth_map;
  if (bit_depth_map.empty())
  {
    bit_depth_map[asic_bit_depth_str_[Lpd::bitDepth1]]  = Lpd::bitDepth1;
    bit_depth_map[asic_bit_depth_str_[Lpd::bitDepth6]]  = Lpd::bitDepth6;
    bit_depth_map[asic_bit_depth_str_[Lpd::bitDepth12]] = Lpd::bitDepth12;
    bit_depth_map[asic_bit_depth_str_[Lpd::bitDepth24]] = Lpd::bitDepth24;
  }

  // Set the bit depth value if present in the map
  if (bit_depth_map.count(bit_depth_str))
  {
    bit_depth = bit_depth_map[bit_depth_str];
  }

  return bit_depth;
}
