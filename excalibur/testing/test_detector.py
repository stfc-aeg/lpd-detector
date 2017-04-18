"""
Test cases for the ExcaliburDetector class of the ODIN server EXCALIBUR plugin

Tim Nicholls, STFC Application Engineering Group
"""

from nose.tools import *
import logging

from excalibur.detector import ExcaliburDetector, ExcaliburDetectorError
from excalibur.fem import ExcaliburFem

class TestExcaliburDetector():

    @classmethod
    def setup_class(cls):
        
        ExcaliburFem.use_stub_api = True
        cls.detector_fems = [
                             ('192.168.0.1', 6969, '10.0.2.1'), 
                             ('192.168.0.2', 6969, '10.0.2.1'), 
                             ('192.168.0.3', 6969, '10.0.2.1')
                            ]
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

    def test_detector_simple_init(self):

        detector = ExcaliburDetector(self.detector_fems)
        assert_equal(len(detector.fems), len(self.detector_fems))

    def test_detector_single_fem(self):

        detector = ExcaliburDetector(self.detector_fems[0])
        assert_equal(len(detector.fems), 1)

    def test_detector_bad_fem_spec(self):

        with assert_raises_regexp(ExcaliburDetectorError, "Failed to initialise detector FEM list"):
            detector = ExcaliburDetector([1, 2, 3])

        with assert_raises_regexp(ExcaliburDetectorError, "Failed to initialise detector FEM list"):
            detector = ExcaliburDetector('nonsense')

    def test_detector_bad_fem_port(self):
        bad_detector_fems = self.detector_fems[:]
        bad_detector_fems[0] = ('192.168.0.1', 'bad_port', '10.0.2.1')

        with assert_raises_regexp(ExcaliburDetectorError, "Failed to initialise detector FEM list"):
            detector = ExcaliburDetector(bad_detector_fems)

    def test_detector_connect_fems(self):

        detector = ExcaliburDetector(self.detector_fems)
        connect_params = {'state': True}
        detector.connect(connect_params)

    def test_detector_powercard_idx(self):
        
        detector = ExcaliburDetector(self.detector_fems)
        powercard_idx = 1
        detector.set_powercard_fem_idx(powercard_idx)
        assert_equal(detector.powercard_fem_idx, powercard_idx)
        
    def test_detector_bad_powercard_idx(self):
        
        detector = ExcaliburDetector(self.detector_fems)
        powercard_idx = 4
        with assert_raises_regexp(
            ExcaliburDetectorError, "Illegal FEM index {} specified for power card".format(powercard_idx)
        ):
            detector.set_powercard_fem_idx(powercard_idx)

    def test_detector_set_chip_enable_mask(self):
        
        detector = ExcaliburDetector(self.detector_fems)
        chip_enable_mask = [0xff, 0x3f, 0x7f]
        detector.set_chip_enable_mask(chip_enable_mask)
        assert_equal(chip_enable_mask, detector.chip_enable_mask)
        
    def test_detector_set_chip_enable_mask_single(self):
        
        detector = ExcaliburDetector(('192.168.0.1', 6969, '10.0.2.1'))
        chip_enable_mask = 0xff
        detector.set_chip_enable_mask(chip_enable_mask)
        assert_equal([chip_enable_mask], detector.chip_enable_mask)
        
    def test_detector_set_chip_enable_length_mistmatch(self):
        
        detector = ExcaliburDetector(self.detector_fems)
        chip_enable_mask = [0xff, 0x3f]
        with assert_raises_regexp(ExcaliburDetectorError, 'Mismatch in length of asic enable mask'):
            detector.set_chip_enable_mask(chip_enable_mask)
