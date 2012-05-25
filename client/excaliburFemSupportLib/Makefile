BUILD_TARGET := libexcaliburFemSupport.a

LIB_FEMAPI_DIR           = ${CURDIR}/../femApi
LIB_FEMAPI_PATH          = ${LIB_FEMAPI_DIR}/${BUILD_CONFIG}
LIB_FEMAPI               = ${LIB_FEMAPI_PATH}/libfemApi.a

LIB_FEMCLIENT_DIR        = ${CURDIR}/../femClient
LIB_FEMCLIENT_PATH       = ${LIB_FEMCLIENT_DIR}/${BUILD_CONFIG}
LIB_FEMCLIENT            = ${LIB_FEMCLIENT_PATH}/libfemClient.a

LIB_EXCAL_FEMCLIENT_DIR  = ${CURDIR}/../excaliburFemClient
LIB_EXCAL_FEMCLIENT_PATH = ${LIB_EXCAL_FEMCLIENT_DIR}/${BUILD_CONFIG}
LIB_EXCAL_FEMCLIENT      = ${LIB_EXCAL_FEMCLIENT_PATH}/libexcaliburFemClient.a

LIB_BOOST_DIR            = ${CURDIR}/boost
LIB_BOOST_SYSTEM         = ${LIB_BOOST_DIR}/libboost_system.a
LIB_BOOST_THREAD         = ${LIB_BOOST_DIR}/libboost_thread.a

LIBS  = ${LIB_FEMAPI} ${LIB_FEMCLIENT} ${LIB_EXCAL_FEMCLIENT} ${LIB_BOOST_SYSTEM} ${LIB_BOOST_THREAD}

all: debug release

debug: BUILD_CONFIG = Debug
debug: ${BUILD_TARGET}

release: BUILD_CONFIG = Release
release: ${BUILD_TARGET}
	
${BUILD_TARGET}:
	rm -f ${BUILD_CONFIG}/obj/*.o 
	rm -f ${BUILD_CONFIG}/${BUILD_TARGET}
	cd ${BUILD_CONFIG}/obj; \
	   for lib in ${LIBS}; do ar -x $$lib; done 
	ar -cr ${BUILD_CONFIG}/${BUILD_TARGET} ${BUILD_CONFIG}/obj/*.o
	
