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
      image_pixels_(image_width_ * image_height_),
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

    image_pixels_ = image_width_ * image_height_;

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
    LOG4CXX_TRACE(logger_, "Frame state: " << hdr_ptr->frame_state);
    LOG4CXX_TRACE(logger_, "Packets received: " << hdr_ptr->total_packets_received
        << " SOF markers: "<< (int)hdr_ptr->total_sof_marker_count
        << " EOF markers: "<< (int)hdr_ptr->total_eof_marker_count);

    // Loop over the active FEM list to determine the maximum active FEM index

    unsigned int max_active_fem_idx = 0;
    {
      std::stringstream msg;
      msg << "Number of active FEMs: " << static_cast<int>(hdr_ptr->num_active_fems) << " ids:";
      for (uint8_t idx = 0; idx < hdr_ptr->num_active_fems; idx++)
      {
        if (hdr_ptr->active_fem_idx[idx] > max_active_fem_idx)
        {
          max_active_fem_idx = hdr_ptr->active_fem_idx[idx];
        }
        msg << " " << static_cast<int>(hdr_ptr->active_fem_idx[idx]);
      }
      LOG4CXX_TRACE(logger_, msg.str());
    }

    // Determine the size of the output reordered image based on current bit depth
    const std::size_t output_image_size = reordered_image_size(asic_counter_depth_);
    LOG4CXX_TRACE(logger_, "Output image size: " << output_image_size);

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()) + sizeof(Excalibur::FrameHeader)
    );

    // Pointers to full and partial reordered images - will be allocated on demand

    void * reordered_image = NULL;
    void* reordered_part_image_c0 = NULL;
    static void* reordered_part_image_c1 = NULL;

    try
    {

      // Check that the pixels from all active FEMs are contained within the dimensions of the
      // specified output image, otherwise throw an error
      if (((max_active_fem_idx +1) * FEM_TOTAL_PIXELS) > image_pixels_)
      {
        std::stringstream msg;
        msg << "Pixel count inferred from active FEMs ("
            << ((max_active_fem_idx + 1) * FEM_TOTAL_PIXELS)
            << ", max FEM idx: " << max_active_fem_idx
            << ") will exceed dimensions of output image (" << image_pixels_ << ")";
        throw std::runtime_error(msg.str());
      }

      // Allocate buffer to receive reordered image. In 24 bit mode only do this once the second
      // frame containing C0 data has been received
      if ((asic_counter_depth_ != DEPTH_24_BIT) || (frames_received_ == 1))
      {
        reordered_image = (void*)malloc(output_image_size);
        if (reordered_image == NULL)
        {
          throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
        }
      }

      // Calculate the FEM frame size once so it can be used in the following loop
      // repeatedly
      std::size_t fem_frame_size = (
          Excalibur::num_subframes *
          Excalibur::subframe_size(static_cast<Excalibur::AsicCounterBitDepth>(asic_counter_depth_))
      );

      // Loop over active FEMs in the input frame image data, reordering pixels into the output
      // images

      for (uint8_t idx = 0; idx < hdr_ptr->num_active_fems; idx++)
      {
        uint8_t fem_idx = hdr_ptr->active_fem_idx[idx];

        // Calculate pointer into the input image data based on loop index
        void* input_ptr = static_cast<void *>(
            static_cast<char *>(const_cast<void *>(data_ptr)) + (fem_frame_size * idx)
        );

        // Calculate output image pixel offset based on active FEM index
        std::size_t output_offset = fem_idx * FEM_TOTAL_PIXELS;

        std::cout << "*** idx: " << (int)idx << " fem_idx: " << (int)fem_idx
            << " data_ptr: " << data_ptr << " input_ptr: " << input_ptr
            << " output offset: " << output_offset << std::endl;

        // Determine stripe orientation based on FEM index
        bool stripe_is_even = ((fem_idx & 1) == 0);
        LOG4CXX_TRACE(logger_, "Active FEM idx=" << static_cast<int>(fem_idx)
            << ": stripe orientation is " << (stripe_is_even ? "even" : "odd"));

        // Reorder strip according to counter depth
        switch (asic_counter_depth_)
        {
          case DEPTH_1_BIT: // 1-bit counter depth
            reorder_1bit_stripe(static_cast<unsigned int *>(input_ptr),
                                static_cast<unsigned char *>(reordered_image) + output_offset,
                                stripe_is_even);
            break;

          case DEPTH_6_BIT: // 6-bit counter depth
            reorder_6bit_stripe(static_cast<unsigned char *>(input_ptr),
                                static_cast<unsigned char *>(reordered_image) + output_offset,
                                stripe_is_even);
            break;

          case DEPTH_12_BIT: // 12-bit counter depth
            reorder_12bit_stripe(static_cast<unsigned short *>(input_ptr),
                                 static_cast<unsigned short *>(reordered_image) + output_offset,
                                 stripe_is_even);
            break;

          case DEPTH_24_BIT: // 24-bit counter depth needs special handling to merge partial frames

            std::size_t partial_image_size = reordered_image_size(DEPTH_12_BIT);

            if (frames_received_ == 0)
            {
              // First frame contains C1 data, so allocate space if not already done, reorder and
              // store the partial image for later use
              if (reordered_part_image_c1 == NULL)
              {
                reordered_part_image_c1 = (void *)malloc(partial_image_size);
                if (reordered_part_image_c1 == NULL)
                {
                  throw std::runtime_error(
                      "Failed to allocate temporary buffer for 24-bit partial C1 image"
                      );
                }
              }

              std::cout << "About to reorder C1: addr: "
                  << reordered_part_image_c1 << " offset: " << output_offset
                  << " partial size " << partial_image_size << std::endl;

              reorder_12bit_stripe(static_cast<unsigned short *>(input_ptr),
                  static_cast<unsigned short *>(reordered_part_image_c1) + output_offset,
                  stripe_is_even);

            }
            else
            {
              // Second frame contains C0 data, allocate space for this if not already done,
              // reorder and then build the full-depth output image
              if (reordered_part_image_c0 == NULL)
              {
                std::cout << "Doing C0 malloc" << std::endl;
                reordered_part_image_c0 = (void *)malloc(partial_image_size);
                if (reordered_part_image_c0 == NULL)
                {
                  throw std::runtime_error(
                      "Failed to allocate temporary buffer for 24-bit partial C0 image"
                      );
                }
              }

              std::cout << "About to reorder C0: addr: "
                  << reordered_part_image_c0 << " offset: " << output_offset
                  << " partial size " << partial_image_size << std::endl;

              // Reorder received buffer into C0
              reorder_12bit_stripe(static_cast<unsigned short *>(input_ptr),
                  static_cast<unsigned short *>(reordered_part_image_c0) + output_offset,
                  stripe_is_even);

            }
            break;
        }
      }

      // Handle 24-bit switching of partial images outside the active FEM loop, building the full
      // 24-bit image into the reordered image buffer when both partial images have been received.
      if (asic_counter_depth_ == DEPTH_24_BIT)
      {
        if (frames_received_ == 0)
        {
          // Set the frames switch ready for the second frame
          frames_received_ = 1;
        }
        else
        {
          // Build 24 bit image into output buffer
          build_24bit_image((unsigned short *)reordered_part_image_c0,
                            (unsigned short *)reordered_part_image_c1,
                            (unsigned int*)reordered_image, image_pixels_);

          // Free the partial image buffers as no longer needed
          free(reordered_part_image_c0);
          reordered_part_image_c0 = NULL;
          free(reordered_part_image_c1);
          reordered_part_image_c1 = NULL;

          // Reset the frames switch
          frames_received_ = 0;
        }
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
        data_frame->copy_data(reordered_image, output_image_size);

        LOG4CXX_TRACE(logger_, "Pushing data frame.");
        this->push(data_frame);

        free(reordered_image);
        reordered_image = NULL;
      }
    }
    catch (const std::exception& e)
    {
      LOG4CXX_ERROR(logger_, "EXCALIBUR frame decode failed: " << e.what());
    }
  }

  /**
   * Reorder an image stripe using 1 bit re-ordering.
   * 1 bit images are captured in raw data mode, i.e. without reordering. In this mode, each
   * 32-bit word contains the current pixel being output on each data line of the group of
   * 4 ASICs, i.e. a supercolumn
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   */
  void ExcaliburProcessPlugin::reorder_1bit_stripe(unsigned int* in, unsigned char* out,
      bool stripe_is_even)
  {
    int block, y, x, x2, chip, pixel_x, pixel_y, pixel_addr, bit_posn;
    int raw_addr = 0;

    // Loop over two blocks of data
    for (block = 0; block < FEM_BLOCKS_PER_STRIPE_X; block++)
    {
      // Loop over Y axis (rows)
      for (y = 0; y < FEM_PIXELS_PER_CHIP_Y; y++)
      {
        pixel_y = stripe_is_even ? (255 - y) : y;

        // Loop over pixels in a supercolumn
        for (x = 0; x < FEM_PIXELS_PER_SUPERCOLUMN_X; x++)
        {
          // Loop over chips in x per block
          for (chip = 0; chip < FEM_CHIPS_PER_BLOCK_X; chip++)
          {
            // Loop over supercolumns per chip
            for (x2 = 0; x2 < FEM_SUPERCOLUMNS_PER_CHIP; x2++)
            {
              if (stripe_is_even)
              {
                pixel_x = (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2)) +
                     (chip * FEM_PIXELS_PER_CHIP_X) +
                     (255 - ((x2 * FEM_PIXELS_PER_SUPERCOLUMN_X) + x));
              }
              else
              {
                pixel_x = (FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X - 1) -
                    ((block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2)) +
                     (chip * FEM_PIXELS_PER_CHIP_X) +
                     (255 - ((x2 * FEM_PIXELS_PER_SUPERCOLUMN_X) + x)));
              }
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
   * Reorder an image stripe using 6 bit re-ordering.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   */
  void ExcaliburProcessPlugin::reorder_6bit_stripe(unsigned char* in, unsigned char* out,
      bool stripe_is_even)
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
              if (stripe_is_even)
              {
                pixel_x = (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2) +
                    chip*FEM_PIXELS_PER_CHIP_X + (255-(x2 + x*FEM_PIXELS_IN_GROUP_6BIT)));
             }
              else
              {
                pixel_x = (FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X - 1) -
                    ((block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2) +
                     chip*FEM_PIXELS_PER_CHIP_X + (255-(x2 + x*FEM_PIXELS_IN_GROUP_6BIT))));
              }
              pixel_y = stripe_is_even ? (254 - y) : (y+1);
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              out[pixel_addr] = in[raw_addr];
              raw_addr++;

              pixel_y = stripe_is_even ? (255 - y) : y;
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              out[pixel_addr] = in[raw_addr];
              raw_addr++;
            }
          }
        }
      }
      // Skip over the subframe trailer in the last 8 bytes (4 words) at the end of each block
      raw_addr += 8;
    }
  }

  /**
   * Reorder an image stripe using 12 bit re-ordering.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   */
  void ExcaliburProcessPlugin::reorder_12bit_stripe(unsigned short* in, unsigned short* out,
      bool stripe_is_even)
  {
    int block, y, x, chip, x2, pixel_x, pixel_y, pixel_addr;
    int raw_addr = 0;

    for (block=0; block<FEM_BLOCKS_PER_STRIPE_X; block++)
    {
      for (y=0; y<FEM_PIXELS_PER_CHIP_Y; y++)
      {
        pixel_y = stripe_is_even ? (255 - y) : y;

        for (x=0; x<FEM_PIXELS_PER_CHIP_X/FEM_PIXELS_IN_GROUP_12BIT; x++)
        {
          for (chip=0; chip<FEM_CHIPS_PER_BLOCK_X; chip++)
          {
            for (x2=0; x2<FEM_PIXELS_IN_GROUP_12BIT; x2++)
            {
              if (stripe_is_even)
              {
                pixel_x = (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2) +
                       chip*FEM_PIXELS_PER_CHIP_X + (255-(x2 + x*FEM_PIXELS_IN_GROUP_12BIT)));
              }
              else
              {
                pixel_x = (FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X - 1) -
                    (block*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X/2) +
                     chip*FEM_PIXELS_PER_CHIP_X + (255-(x2 + x*FEM_PIXELS_IN_GROUP_12BIT)));
              }
              pixel_addr = pixel_x + pixel_y*(FEM_PIXELS_PER_CHIP_X*FEM_CHIPS_PER_STRIPE_X);
              out[pixel_addr] = in[raw_addr];
              raw_addr++;
            }
          }
        }
      }
      // Skip over the subframe trailer in the last 8 bytes (4 words) at the end of each block
      raw_addr += 4;
    }
  }

  /**
   * Build a 24bit image from two partial images.
   *
   * \param[in] inC0 - Pointer to the incoming first image data.
   * \param[in] inC1 - Pointer to the incoming second image data.
   * \param[out] out - Pointer to the allocated memory where the combined image is written.
   */
  void ExcaliburProcessPlugin::build_24bit_image(
      unsigned short* inC0, unsigned short* inC1, unsigned int* out, int num_pixels)
  {
    int addr;
    for (addr = 0; addr < num_pixels; addr++)
    {
      out[addr] = (((unsigned int)(inC1[addr] & 0xFFF)) << 12) | (inC0[addr] & 0xFFF);
    }
  }

  std::size_t ExcaliburProcessPlugin::reordered_image_size(int asic_counter_depth) {

    std::size_t slice_size = 0;

    switch (asic_counter_depth)
    {
      case DEPTH_1_BIT:
      case DEPTH_6_BIT:
        slice_size = image_width_ * image_height_ * sizeof(unsigned char);
        break;

      case DEPTH_12_BIT:
        slice_size = image_width_ * image_height_ * sizeof(unsigned short);
        break;

      case DEPTH_24_BIT:
        slice_size = image_width_ * image_height_ * sizeof(unsigned int);
        break;

      default:
      {
        std::stringstream msg;
        msg << "Invalid bit depth specified for reordered slice size: " << asic_counter_depth;
        throw std::runtime_error(msg.str());
      }
      break;
    }

    return slice_size;

  }
} /* namespace filewriter */

