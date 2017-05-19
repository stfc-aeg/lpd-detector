#define BOOST_TEST_MODULE "ExcaliburFrameProcessorTests"
#define BOOST_TEST_MAIN
#include <boost/test/unit_test.hpp>
#include <boost/shared_ptr.hpp>

#include <iostream>

#include "ExcaliburReorderPlugin.h"

class ExcaliburReorderPluginTestFixture
{
public:
	ExcaliburReorderPluginTestFixture()
	{
		std::cout << "ExcaliburReorderPluginTestFixture constructor" << std::endl;
	}

	~ExcaliburReorderPluginTestFixture()
	{
		std::cout << "ExcaliburReorderPluginTestFixture destructor" << std::endl;
	}
};

BOOST_FIXTURE_TEST_SUITE(ExcaliburReorderPluginUnitTest, ExcaliburReorderPluginTestFixture);

BOOST_AUTO_TEST_CASE(ExcaliburReorderPluginTestFixture)
{
	std::cout << "ExcaliburReorderPluginTestFixture test case" << std::endl;
}

BOOST_AUTO_TEST_SUITE_END();
