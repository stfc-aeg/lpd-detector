/*
 * LpdFrameDecoderLib.cpp
 *
 *  Created on: 7 Mar 2017
 *      Author: gnx91527
 */

#include "LpdFrameDecoder.h"
#include "ClassLoader.h"

namespace FrameReceiver
{
  /**
   * Registration of this decoder through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameDecoder, LpdFrameDecoder, "LpdFrameDecoder");

}
// namespace FrameReceiver

