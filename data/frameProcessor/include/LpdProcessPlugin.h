/*
x * LpdProcessPlugin.h
 *
 *  Created on: July 9th 2018,
 *      Author: Jack Haydock, STFC Application Engineering Group
 */

#ifndef TOOLS_FILEWRITER_LPDREORDERPLUGIN_H_
#define TOOLS_FILEWRITER_LPDREORDERPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
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
        
    int get_version_major();
    int get_version_minor();
    int get_version_patch();
    std::string get_version_short();
    std::string get_version_long();
 
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for clearing out dropped packet counters **/
    static const std::string CONFIG_DROPPED_PACKETS;
    /** Configuration constant for output image width **/
    static const std::string CONFIG_DIMS_X;
    /** Configuration constant for output image height **/
    static const std::string CONFIG_DIMS_Y;
    /** Configuration constant for live view divisor **/
    static const std::string CONFIG_DIVISOR;
    /** Configuration constant for live view offset **/
    static const std::string CONFIG_OFFSET;

    void process_lost_packets(boost::shared_ptr<Frame> frame);
    void process_frame(boost::shared_ptr<Frame> frame);

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Dimensions of output images **/
    int dims_x;
    int dims_y;
    /** Packet loss counter **/
    int packets_lost_;
    /** Image counter **/
    int image_counter_;
    /** Data received counter **/
    unsigned int data_received_;
    /** frames processed counter **/
    int frames_processed_;
    /** divisor value for live viewer **/
    int divisor_;
    /** offset value for live viewer **/
    int offset_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, LpdProcessPlugin, "LpdProcessPlugin");

} /* namespace FrameProcessor */

#endif /* TOOLS_FILEWRITER_LPDREORDERPLUGIN_H_ */
