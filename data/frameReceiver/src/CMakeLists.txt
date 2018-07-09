
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBUILD_DIR="${CMAKE_BINARY_DIR}")

include_directories(${FRAMERECEIVER_DIR}/include ${ODINDATA_INCLUDE_DIRS} 
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for Lpd frame decoder
add_library(LpdFrameDecoder SHARED LpdFrameDecoder.cpp LpdFrameDecoderLib.cpp)

install(TARGETS LpdFrameDecoder LIBRARY DESTINATION lib)