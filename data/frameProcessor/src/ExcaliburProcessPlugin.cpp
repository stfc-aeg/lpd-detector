/*
 * ExcaliburProcessPlugin.cpp
 *
 *  Created on: 6 Jun 2016
 *      Author: gnx91527
 */

#include <ExcaliburProcessPlugin.h>

namespace FrameProcessor
{

  const std::string ExcaliburProcessPlugin::CONFIG_ASIC_COUNTER_DEPTH = "bitdepth";
  const std::string ExcaliburProcessPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string ExcaliburProcessPlugin::CONFIG_IMAGE_HEIGHT = "height";
  const std::string ExcaliburProcessPlugin::CONFIG_RESET_24_BIT = "reset";
  const std::string ExcaliburProcessPlugin::BIT_DEPTH[4] = {"1-bit", "6-bit", "12-bit", "24-bit"};

  /**
   * The constructor sets up logging used within the class.
   */
  ExcaliburProcessPlugin::ExcaliburProcessPlugin() :
      asic_counter_depth_(DEPTH_12_BIT),
      image_width_(2048),
      image_height_(256),
      frames_received_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.ExcaliburProcessPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "ExcaliburProcessPlugin constructor.");
  }

  /**
   * Destructor.
   */
  ExcaliburProcessPlugin::~ExcaliburProcessPlugin()
  {
    LOG4CXX_TRACE(logger_, "ExcaliburProcessPlugin destructor.");
  }

  /**
   * Configure the Excalibur plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - bitdepth
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[out] reply - Reference to the reply IpcMessage object.
   */
  void ExcaliburProcessPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(ExcaliburProcessPlugin::CONFIG_ASIC_COUNTER_DEPTH))
    {
      std::string bit_depth_str =
          config.get_param<std::string>(ExcaliburProcessPlugin::CONFIG_ASIC_COUNTER_DEPTH);

      if (bit_depth_str == BIT_DEPTH[DEPTH_1_BIT])
      {
        asic_counter_depth_ = DEPTH_1_BIT;
      }
      else if (bit_depth_str == BIT_DEPTH[DEPTH_6_BIT])
      {
        asic_counter_depth_ = DEPTH_6_BIT;
      }
      else if (bit_depth_str == BIT_DEPTH[DEPTH_12_BIT])
      {
        asic_counter_depth_ = DEPTH_12_BIT;
      }
      else if (bit_depth_str == BIT_DEPTH[DEPTH_24_BIT])
      {
        asic_counter_depth_ = DEPTH_24_BIT;
      }
      else
      {
        LOG4CXX_ERROR(logger_, "Invalid bit depth requested: " << bit_depth_str);
        throw std::runtime_error("Invalid bit depth requested");
      }
    }

    if (config.has_param(ExcaliburProcessPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(ExcaliburProcessPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(ExcaliburProcessPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(ExcaliburProcessPlugin::CONFIG_IMAGE_HEIGHT);
    }

    if (config.has_param(ExcaliburProcessPlugin::CONFIG_RESET_24_BIT))
    {
      frames_received_ = 0;
    }
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void ExcaliburProcessPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for Excalibur plugin");
    status.set_param(get_name() + "/bitdepth", BIT_DEPTH[asic_counter_depth_]);
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void ExcaliburProcessPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Reordering frame.");
    LOG4CXX_TRACE(logger_, "Frame size: " << frame->get_data_size());

    const Excalibur::FrameHeader* hdr_ptr =
        static_cast<const Excalibur::FrameHeader*>(frame->get_data());

    LOG4CXX_TRACE(logger_, "Raw frame number: " << hdr_ptr->frame_number);
    LOG4CXX_TRACE(logger_, "Packets received: " << hdr_ptr->total_packets_received << " SOF markers: "
        << (int)hdr_ptr->total_sof_marker_count << " EOF markers: "
        << (int)hdr_ptr->total_eof_marker_count);

    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()) + sizeof(Excalibur::FrameHeader)
    );
    const size_t data_size = frame->get_data_size() - sizeof(Excalibur::FrameHeader);
    LOG4CXX_TRACE(logger_, "Frame data size: " << data_size);

    static void* reordered_part_image_c1;

    // Allocate buffer to receive reordered image;
    void* reordered_image = NULL;

    // If incoming frame size is different from outgoing frame size
    // then we need to allocate memory accordingly
    int mem_scale_factor = 1;

    try
    {
      // Reorder image according to counter depth
      switch (asic_counter_depth_)
      {
        case DEPTH_1_BIT: // 1-bit counter depth
          mem_scale_factor = 8;
          reordered_image = (void *)malloc(data_size * mem_scale_factor);
          memcpy(reordered_image, (void*)(data_ptr), data_size);
          reorder_1bit_image((unsigned int*)(data_ptr), (unsigned char *)reordered_image);
          break;

        case DEPTH_6_BIT: // 6-bit counter depth
          reordered_image = (void *)malloc(data_size);
          reorder_6bit_image((unsigned char *)(data_ptr), (unsigned char *)reordered_image);
          break;

        case DEPTH_12_BIT: // 12-bit counter depth
          reordered_image = (void *)malloc(data_size);
          reorder_12bit_image((unsigned short *)(data_ptr), (unsigned short*)reordered_image);
          break;

        case DEPTH_24_BIT: // 24-bit counter depth needs special handling to merge successive frames
          mem_scale_factor = 2;

  #if 1
          if (frames_received_ == 0)
          {
            // First frame contains C1 data, so allocate space, reorder and store for later use
            reordered_part_image_c1 = (void *)malloc(data_size);

            reorder_12bit_image(
                (unsigned short *)(data_ptr), (unsigned short*)reordered_part_image_c1);
            reordered_image = 0;  // No buffer to write to file or release

            // set the frames switch ready for the second frame
            frames_received_ = 1;
          }
          else
          {
            // Second frame contains C0 data, allocate space for this and for output image (32bit)
            void* reordered_part_image_c0 = (void *)malloc(data_size);

            size_t output_image_size = image_width_ * image_height_ * 4;
            reordered_image = (void *)malloc(output_image_size);

            // Reorder received buffer into C0
            reorder_12bit_image(
                (unsigned short *)(data_ptr), (unsigned short*)reordered_part_image_c0);

            // Build 24 bit image into output buffer
            build_24bit_image((unsigned short *)reordered_part_image_c0,
                            (unsigned short *)reordered_part_image_c1,
                            (unsigned int*)reordered_image);

            // Free the partial image buffers as no longer needed
            free(reordered_part_image_c0);
            free(reordered_part_image_c1);

            // Reset the frames switch
            frames_received_ = 0;
          }
  #endif
          break;
      }

      // Set the frame image to the reordered image buffer if appropriate
      if (reordered_image)
      {
        // Setup the frame dimensions
        dimensions_t dims(2);
        dims[0] = image_height_;
        dims[1] = image_width_;

        boost::shared_ptr<Frame> data_frame;
        data_frame = boost::shared_ptr<Frame>(new Frame("data"));

        if (asic_counter_depth_ == DEPTH_24_BIT)
        {
          // Only every other incoming frame results in a new frame
          data_frame->set_frame_number(hdr_ptr->frame_number/2);
        }
        else
        {
          data_frame->set_frame_number(hdr_ptr->frame_number);
        }
        data_frame->set_dimensions("data", dims);
        data_frame->copy_data(reordered_image, frame->get_data_size()*mem_scale_factor);
        LOG4CXX_TRACE(logger_, "Pushing data frame.");
        this->push(data_frame);
        free(reordered_image);
        reordered_image = NULL;
      }
    }
    catch (const std::exception& e)
    {
      LOG4CXX_ERROR(logger_, "Serious error in decoding Excalibur frame: " << e.what());
      LOG4CXX_ERROR(logger_, "Possible incompatible data type");
    }
  }

  /**
   * Reorder the image using 1 bit re-ordering.
   * 1 bit images are captured in raw data mode, i.e. without reordering. In this mode, each
   * 32-bit word contains the current pixel being output on each data line of the group of
   * 4 ASICs, i.e. a supercolumn
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   */
  void ExcaliburProcessPlugin::reorder_1bit_image(unsigned int* in, unsigned char* out)
  {
    int block, y, x, x2, chip, pixel_x, pixel_y, pixel_addr, bit_posn;
    int raw_addr = 0;

    // Loop over two blocks of data
    for (block = 0; block < FEM_BLOCKS_PER_STRIPE_X; block++)
    {
      // Loop over Y axis (rows)
      for (y = 0; y < FEM_PIXELS_PER_CHIP_Y; y++)
      {
        pixel_y = 255 - y;
        // Loop over pixels in a supercolumn
        for (x = 0; x < FEM_PIXELS_PER_SUPERCOLUMN_X; x++)
        {
          // Loop over chips in x per block
          for (chip = 0; chip < FEM_CHIPS_PER_BLOCK_X; chip++)
          {
            // Loop over supercolumns per chip
            for (x2 = 0; x2 < FEM_SUPERCOLUMNS_PER_CHIP; x2++)
            {
              pixel_x = (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2)) +
                   (chip * FEM_PIXELS_PER_CHIP_X) +
                   (255 - ((x2 * FEM_PIXELS_PER_SUPERCOLUMN_X) + x));
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              bit_posn = (chip * 8) + x2;
              out[pixel_addr] = (in[raw_addr] >> bit_posn) & 0x1;
            }
          }
          raw_addr++;
        }
      }
    }
  }

  /**
   * Reorder the image using 6 bit re-ordering.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   */
  void ExcaliburProcessPlugin::reorder_6bit_image(unsigned char* in, unsigned char* out)
  {
    int block, y, x, chip, x2, pixel_x, pixel_y, pixel_addr;
    int raw_addr = 0;

    for (block=0; block<FEM_BLOCKS_PER_STRIPE_X; block++)
    {
      for (y=0; y<FEM_PIXELS_PER_CHIP_Y; y+=2)
      {
        for (x=0; x<FEM_PIXELS_PER_CHIP_X/FEM_PIXELS_IN_GROUP_6BIT; x++)
        {
          for (chip=0; chip<FEM_CHIPS_PER_BLOCK_X; chip++)
          {
            for (x2=0; x2<FEM_PIXELS_IN_GROUP_6BIT; x2++)
            {
              pixel_x = (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2) +
                  chip*FEM_PIXELS_PER_CHIP_X + (255-(x2 + x*FEM_PIXELS_IN_GROUP_6BIT)));
              pixel_y = 254-y;
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              out[pixel_addr] = in[raw_addr];
              raw_addr++;
              pixel_y = 255-y;
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              out[pixel_addr] = in[raw_addr];
              raw_addr++;
            }
          }
        }
      }
    }
  }

  /**
   * Reorder the image using 12 bit re-ordering.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   */
  void ExcaliburProcessPlugin::reorder_12bit_image(unsigned short* in, unsigned short* out)
  {
    int block, y, x, chip, x2, pixel_x, pixel_y, pixel_addr;
    int raw_addr = 0;

    for (block=0; block<FEM_BLOCKS_PER_STRIPE_X; block++)
    {
      for (y=0; y<FEM_PIXELS_PER_CHIP_Y; y++)
      {
        for (x=0; x<FEM_PIXELS_PER_CHIP_X/FEM_PIXELS_IN_GROUP_12BIT; x++)
        {
          for (chip=0; chip<FEM_CHIPS_PER_BLOCK_X; chip++)
          {
            for (x2=0; x2<FEM_PIXELS_IN_GROUP_12BIT; x2++)
            {
              pixel_x = (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2) +
                       chip*FEM_PIXELS_PER_CHIP_X + (255-(x2 + x*FEM_PIXELS_IN_GROUP_12BIT)));
              pixel_y = 255-y;
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              out[pixel_addr] = in[raw_addr];
              raw_addr++;
              //LOG4CXX_TRACE(logger_, "Pixel Address: " << pixel_addr);
              //LOG4CXX_TRACE(logger_, "Raw Address: " << raw_addr);
            }
          }
        }
      }
    }
  }

  /**
   * Build a 24bit image from two images.
   *
   * \param[in] inC0 - Pointer to the incoming first image data.
   * \param[in] inC1 - Pointer to the incoming second image data.
   * \param[out] out - Pointer to the allocated memory where the combined image is written.
   */
  void ExcaliburProcessPlugin::build_24bit_image(
      unsigned short* inC0, unsigned short* inC1, unsigned int* out)
  {
    int addr;
    for (addr = 0; addr < FEM_TOTAL_PIXELS; addr++)
    {
      out[addr] = (((unsigned int)(inC1[addr] & 0xFFF)) << 12) | (inC0[addr] & 0xFFF);
    }
  }

} /* namespace filewriter */
