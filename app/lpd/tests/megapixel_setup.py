'''
Created on Feb 9, 2017

@author: tcn45
'''

from __future__ import print_function
import logging
import os
import time
import argparse
import sys

from lpd.device import LpdDevice
from lpd.gui.readout_config import LpdReadoutConfig, LpdReadoutConfigError

fem_addr_list = [
    '192.168.2.2',
    '192.168.2.3',
    '192.168.2.4',
    '192.168.2.5',
    '192.168.2.6',
    '192.168.2.7',
    '192.168.2.8',
    '192.168.2.9',
    '192.168.2.10',
    '192.168.2.11',
    '192.168.2.12',
    '192.168.2.13',
    '192.168.2.14',
    '192.168.2.15',
    '192.168.2.16',
    '192.168.2.17',
]

fem_port = 6969
fem_timeout = 5.0
num_powercards = 2
sensor_bias = 50.0
config_dir='./megapixel_config'
readout_param_file = 'readoutParam.xml'
asic_setup_param_file = 'slowParam.xml'
asic_cmd_sequence_file='cmdSequence.xml'

def lpdMegapixelSetup(disable):
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)1.1s %(asctime)s %(message)s', datefmt='%y/%m/%d %H:%M:%S')

    if not disable:
        action = 'Enabling'
        powercard_params = [
            ('asicPowerEnable', 1),
            ('sensorBiasEnable', 1),
            ('sensorBias', sensor_bias),
        ]
    else:
        action = 'Disabling'
        powercard_params = [
            ('sensorBiasEnable', 0),
            ('asicPowerEnable', 0),
        ]
        
    
    readout_param_file_path = os.path.join(config_dir, readout_param_file)
    logging.info("Loading readout parameters from file {}".format(readout_param_file_path))
    try:
        readout_config = LpdReadoutConfig(readout_param_file_path, fromFile=True)
    except LpdReadoutConfigError as e:
        logging.error("Error loading readout parameters: {}".format(e))
        return 
    
    asic_setup_param_file_path = os.path.join(config_dir, asic_setup_param_file)
    logging.info("Loading ASIC setup parameters from file {}".format(asic_setup_param_file_path))

    asic_cmd_sequence_file_path = os.path.join(config_dir, asic_cmd_sequence_file)
    logging.info("Loading ASIC command sequence from file {}".format(asic_cmd_sequence_file_path))
 
    num_fems = len(fem_addr_list)
    
    fem_idx = [-1]*num_fems
    fem_device = [None]*num_fems
    fem_connected = [False]*num_fems
    
    
    for idx in range(num_fems):
        
        fem_addr = fem_addr_list[idx]
 
        fem_device[idx] = LpdDevice()
        
        rc = fem_device[idx].open(fem_addr, fem_port, timeout=fem_timeout)
            
        if rc != LpdDevice.ERROR_OK:
            logging.error("Failed to open FEM {} device at addr {} : {}".format(idx, fem_addr, fem_device[idx].errorStringGet()))
            continue
        else:
            fem_connected[idx] = True
            
            
    for idx in range(num_fems):
        
        if not fem_connected[idx]:
            continue
        
        logging.info("{} ASIC power and sensor bias on FEM {}".format(action, idx))
        
        for (param, target) in powercard_params:
            for power_card in range(num_powercards):
                param_name = param + str(power_card)
                
                param_set_verify(idx, fem_device[idx], param_name, target)

    
    if not disable:
                   
        logging.info("Pausing to allow all ASICs to power up...")        
        time.sleep(4.0)
        
        for idx in range(num_fems):
            
            fem_addr = fem_addr_list[idx]
    
            if not fem_connected[idx]:
                continue
            
            logging.info("Setting readout parameters on FEM {}".format(idx))
            
            for (param, target) in readout_config.parameters():
                param_set_verify(idx, fem_device[idx], param, target)
                
            logging.info("Setting ASIC setup parameter file on FEM {}".format(idx))
            param_set_verify(idx, fem_device[idx], 'femAsicSetupParams', asic_setup_param_file_path)
            
            logging.info("Setting ASIC command sequence file on FEM {}".format(idx))
            param_set_verify(idx, fem_device[idx], 'femAsicCmdSequence', asic_cmd_sequence_file_path)
            
            logging.info("Uploading configuration to FEM {}".format(idx))
            rc = fem_device[idx].configure()
            if rc != LpdDevice.ERROR_OK:
                logging.error("Configuration upload to FEM {} failed: rc={}: {}".format(idx, rc, fem_device[idx].errorStringGet()))
        
        for idx in range(num_fems):
            
            if not fem_connected[idx]:
                continue
                                            
            fem_device[idx].close()
            fem_connected[idx] = False

def param_set_verify(fem_idx, the_device, param_name, target):
    
    rc = the_device.paramSet(param_name, target)

    if rc != LpdDevice.ERROR_OK:
        logging.error("Failed to set FEM {} parameter {} to value {}: {}".format(fem_idx, param_name, target, the_device.errorStringGet()))                    
    else:

        (rc, val) = the_device.paramGet(param_name)
        logging.debug("FEM {} parameter {} set to value {}".format(fem_idx, param_name, val))
        
        if type(target) == float:
            target_error = (abs(target - val) / target) > 0.01
        else:
            target_error = val != target
        
        if target_error:
            logging.error("FEM {} parameter {} not correctly set: target {}, actual {}".format(fem_idx, param_name, target, val))
  
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="LpdMegapixelSetup.py - configure the megapixel system")
    group = parser.add_mutually_exclusive_group()

    group.add_argument('--enable', help="Disable all ASIC HV and LV outputs", action='store_true')
    group.add_argument("--disable", help="Disable all ASIC HV and LV outputs", action='store_true')
    args = parser.parse_args()
    
    lpdMegapixelSetup(args.disable)
