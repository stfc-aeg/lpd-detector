/*
x * LpdProcessPlugin.h
 *
 *  Created on: 6 Jun 2016
 *      Author: gnx91527
 */

#ifndef TOOLS_FILEWRITER_LPDREORDERPLUGIN_H_
#define TOOLS_FILEWRITER_LPDREORDERPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;


#include "FrameProcessorPlugin.h"
#include "LpdDefinitions.h"
#include "ClassLoader.h"

namespace FrameProcessor
{

  /** Processing of Lpd Frame objects.
   *
   * The LpdProcessPlugin class is currently responsible for receiving a raw data
   * Frame object and reordering the data into valid Lpd frames.
   */
  class LpdProcessPlugin : public FrameProcessorPlugin
  {
  public:
    LpdProcessPlugin();
    virtual ~LpdProcessPlugin();
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for clearing out dropped packet counters **/
    static const std::string CONFIG_DROPPED_PACKETS;
    /** Configuration constant for asic counter depth **/
    static const std::string CONFIG_ASIC_COUNTER_DEPTH;
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for number of images in frame **/
    static const std::string CONFIG_NUM_IMAGES;

    void process_lost_packets(boost::shared_ptr<Frame> frame);
    void process_frame(boost::shared_ptr<Frame> frame);

    std::size_t reordered_image_size(int asic_counter_depth_);

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Number of Images **/
    int num_images_;
    /** Image pixel count **/
    int image_pixels_;
    /** Packet loss counter **/
    int packets_lost_;
    /** Image counter **/
    int image_counter_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, LpdProcessPlugin, "LpdProcessPlugin");

} /* namespace FrameProcessor */

#endif /* TOOLS_FILEWRITER_LPDREORDERPLUGIN_H_ */
