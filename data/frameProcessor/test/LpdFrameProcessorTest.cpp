#define BOOST_TEST_MODULE "LpdFrameProcessorTests"
#define BOOST_TEST_MAIN
#include <boost/test/unit_test.hpp>
#include <boost/shared_ptr.hpp>

#include <iostream>

#include "LpdProcessPlugin.h"

class LpdProcessPluginTestFixture
{
public:
	LpdProcessPluginTestFixture()
	{
		std::cout << "LpdProcessPluginTestFixture constructor" << std::endl;
	}

	~LpdProcessPluginTestFixture()
	{
		std::cout << "LpdProcessPluginTestFixture destructor" << std::endl;
	}
};

BOOST_FIXTURE_TEST_SUITE(LpdProcessPluginUnitTest, LpdProcessPluginTestFixture);

BOOST_AUTO_TEST_CASE(LpdProcessPluginTestFixture)
{
	std::cout << "LpdProcessPluginTestFixture test case" << std::endl;
}

BOOST_AUTO_TEST_SUITE_END();
