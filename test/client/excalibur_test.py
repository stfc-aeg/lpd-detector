from excalibur import ExcaliburClient, ExcaliburParameter, ExcaliburDefinitions
from config_parser import *
import logging
import argparse
import os
import time

class ExcaliburTestAppDefaults(object):
    
    def __init__(self):
        
        self.ip_addr = 'localhost'
        self.port = 8888
        self.tengig_addr = '10.0.2.1'
        self.log_level = 'info'
        
        self.log_levels = {
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'info': logging.INFO,
            'debug': logging.DEBUG,
        }
             
        self.asic_readout_mode = 0
        self.asic_counter_select = 0
        self.asic_counter_depth = 2
        
        self.num_frames = 1
        self.acquisition_time = 100
        self.tp_count = 0
        self.trigger_mode = ExcaliburDefinitions.FEM_TRIGMODE_INTERNAL
        self.readout_mode = ExcaliburDefinitions.FEM_READOUT_MODE_SEQUENTIAL
        self.colour_mode = ExcaliburDefinitions.FEM_COLOUR_MODE_FINEPITCH
        self.csmspm_mode = ExcaliburDefinitions.FEM_CSMSPM_MODE_SINGLE
        self.disccsmspm = ExcaliburDefinitions.FEM_DISCCSMSPM_DISCL
        self.equalization_mode = ExcaliburDefinitions.FEM_EQUALIZATION_MODE_OFF
        self.gain_mode = ExcaliburDefinitions.FEM_GAIN_MODE_SLGM
        self.counter_select = 0
        self.counter_depth = 12
        self.operation_mode = ExcaliburDefinitions.FEM_OPERATION_MODE_NORMAL
        
        self.sense_dac = 0
        
        
class ExcaliburTestApp(object):
    
    def __init__(self):
        
        self.defaults = ExcaliburTestAppDefaults()
        
        try:
            term_columns = int(os.environ['COLUMNS']) - 2
        except:
            term_columns = 100
            
        parser = argparse.ArgumentParser(
            prog='excalibur_test.py', description='EXCALIBUR test application',
            formatter_class=lambda prog : argparse.ArgumentDefaultsHelpFormatter(
                prog, max_help_position=40, width=term_columns)
        )
        
        config_group = parser.add_argument_group('Configuration')
        config_group.add_argument('--ipaddress', '-i', type=str, dest='ip_addr', 
            default=self.defaults.ip_addr, metavar='ADDR',
            help='Hostname or IP address of EXCALIBUR control server to connect to')
        config_group.add_argument('--port', '-p', type=int, dest='port',
            default=self.defaults.port, 
            help='Port number of EXCALIBUBR control server to connect to')
        config_group.add_argument('--tengigaddress', '-g', type=str, dest='tengig_addr',
            default=self.defaults.tengig_addr,  metavar='ADDR',
            help='Destination IP address for 10G UDP data stream')
        config_group.add_argument('--logging', type=str, dest='log_level',
            default=self.defaults.log_level,
            choices=['error', 'warning', 'info', 'debug'],
            help='Setting logging output level')
        
        cmd_group = parser.add_argument_group('Commands')
        cmd_group.add_argument('--dump', action='store_true',
            help="Dump the state of the control server")
        cmd_group.add_argument('--reset', '-r', action='store_true', 
            help='Issue front-end reset/init')
        cmd_group.add_argument('--efuse', '-e', action='store_true',
            help="Read and diplay MPX3 eFuse IDs")
        cmd_group.add_argument('--slow', '-s', action='store_true',
            help='Display front-end slow control parameters')
        cmd_group.add_argument('--acquire', '-a', action='store_true',
            help="Execute image acquisition sequence")
        cmd_group.add_argument('--stop', action='store_true',
            help='Stop acquisition execution')
        cmd_group.add_argument('--disconnect', action='store_true',
            help='Disconnect server from detector system')
        cmd_group.add_argument('--dacs', nargs='*', metavar='FILE',
            help='Load MPX3 DAC values from a filename if given, otherwise use default values')
        
        config_group = parser.add_argument_group('Configuration mode parameters')
        config_group.add_argument('--fem', metavar='FEM', dest='config_fem',
            nargs='+', type=int, default=[ExcaliburDefinitions.ALL_FEMS],
            help='Specify FEM(s) for configuration loading (0=all)')
        config_group.add_argument('--chip', metavar='CHIP', dest='config_chip',
            nargs='+', type=int, default=[ExcaliburDefinitions.ALL_CHIPS],
            help='Specified chip(s) for configuration loading (0=all)')
        config_group.add_argument('--sensedac', metavar='DAC', dest='sense_dac',
            type=int, default=self.defaults.sense_dac,
            help='Set MPX3 sense DAC id. NB Requires DAC load command to take effect')
       
        acq_group = parser.add_argument_group("Acquisition parameters")
        acq_group.add_argument('--nowait', action='store_true', dest='no_wait',
            help='Do not wait for acqusition to complete before returning')
        acq_group.add_argument('--burst', action='store_true', dest='burst_mode',
            help='Select burst mode for image acquisition')
        acq_group.add_argument('--matrixread', action='store_true',
            help='During acquisition, perform matrix read only (i.e. no shutter for config read or digital test')
        acq_group.add_argument('--frames', '-n', type=int, dest='num_frames',
            default=self.defaults.num_frames, metavar='FRAMES',
            help='Set number of frames to acquire')
        acq_group.add_argument('--acqtime', '-t', type=int, dest='acquisition_time',
            default=self.defaults.acquisition_time, metavar='TIME',
            help='Set acquisition time (shutter duration) in ms')
        acq_group.add_argument('--readmode', type=int, dest='readout_mode',
            choices=[0,1],
            default=self.defaults.readout_mode,
            help='Set readout mode: 0=sequential, 1=continuous')
        acq_group.add_argument('--trigmode', type=int, dest='trigger_mode',
           choices = [0, 1, 2],
           default=self.defaults.trigger_mode,
           help='Set trigger mode: 0=internal, 1=external shutter, 2=external sync')
        acq_group.add_argument('--colourmode', type=int, dest='colour_mode',
            choices=[0, 1],
            default=self.defaults.colour_mode,
            help='Set MPX3 colour mode: 0=finepitch, 1=spectroscopic')
        acq_group.add_argument('--csmspm', type=int, dest='csmspm_mode',
            choices=[0, 1],
            default=self.defaults.csmspm_mode,
            help='Set MPX3 pixel mode: 0=single pixel, 1=charge summing')
        acq_group.add_argument('--disccsmspm', type=int, dest='disccsmspm',
            choices=[0, 1],
            default=self.defaults.disccsmspm,
            help='Set MPX3 discriminator output mode: 0=DiscL, 1=DiscH')
        acq_group.add_argument('--equalization', type=int, dest='equalization_mode',
            choices=[0, 1],
            default=self.defaults.equalization_mode,
            help='Set MPX3 equalization mode: 0=off, 1=on')
        acq_group.add_argument('--gainmode', type=int, dest='gain_mode',
            choices=[0, 1, 2, 3],
            default=self.defaults.gain_mode,
            help='Set MPX3 gain mode: 0=SHGM, 1=HGM, 2=LGM, 3=SLGM')
        acq_group.add_argument('--counter', type=int, dest='counter_select',
            choices=[0, 1],
            default=self.defaults.counter_select,
            help='Set MPX counter to read: 0 or 1')
        acq_group.add_argument('--depth', type=int, dest='counter_depth',
            choices=[1, 6, 12, 24],
            default=self.defaults.counter_depth,
            help='Set MPX counter bit depth: 1, 6, 12, or 24')
        acq_group.add_argument('--tpcount', type=int, dest='tp_count',
            default=self.defaults.tp_count, metavar='COUNT',
            help='Set MPX3 test pulse count')
        
        self.args = parser.parse_args()
        if self.args.log_level in self.defaults.log_levels:
            log_level = self.defaults.log_levels[self.args.log_level]
        else:
            log_level = self.defaults.log_levels[self.defaults.log_level]
            
        logging.basicConfig(level=log_level, format='%(levelname)1.1s %(asctime)s.%(msecs)03d %(message)s', datefmt='%y%m%d %H:%M:%S')
        self.client = ExcaliburClient(address=self.args.ip_addr, port=self.args.port, log_level=log_level)
    
    def run(self):
        
        if self.args.dump:
            logging.info("Dumping state of control server:")
            self.client.print_all(logging.INFO)
            return
        
        self.client.connect()

        (self.fem_ids, self.chip_ids) = self.client.get_fem_chip_ids()
        self.num_fems = len(self.fem_ids)
        logging.info('Detector has {} FEM{} with ID {}'.format(
            self.num_fems, ('' if self.num_fems == 1 else 's'), 
            ','.join([str(fem_id) for fem_id in self.fem_ids])
        ))
                    
        if self.args.reset:
            self.do_frontend_init()
            
        if self.args.efuse:
            self.do_efuseid_read()
            
        if self.args.slow:
            self.do_slow_control_read()
        
        if self.args.dacs is not None:
            self.do_dac_load()
               
        if self.args.acquire:
            self.do_acquisition()
            
        if self.args.stop:
            self.do_stop()
        
        if self.args.disconnect:    
            self.client.disconnect()
    
    def do_frontend_init(self):
        
        self.client.fe_init()
        
    def do_efuseid_read(self):
        
        (read_ok, response) = self.client.fe_param_read('efuseid')
        if read_ok:
            efuse_ids = response['efuseid']          
            for fem_idx in range(len(efuse_ids)):
                fem_efuse_ids = efuse_ids[fem_idx]
                if not isinstance(fem_efuse_ids, list):
                    fem_efuse_ids = [fem_efuse_ids]
                logging.info('FEM {} : efuse IDs: {}'.format(fem_idx, ' '.join([hex(efuse_id) for efuse_id in fem_efuse_ids])))
        else:
            logging.error("eFuse ID read command failed")
    
    def do_slow_control_read(self):

        fem_params = ['fem_local_temp','fem_remote_temp', 'moly_temp', 'moly_humidity']
        supply_params = ['supply_p1v5_avdd1', 'supply_p1v5_avdd2', 'supply_p1v5_avdd3', 'supply_p1v5_avdd4', 
                     'supply_p1v5_vdd1', 'supply_p2v5_dvdd1']
      
        fe_params = fem_params + supply_params + ['mpx3_dac_out']
         
        (read_ok, param_vals) = self.client.fe_param_read(fe_params)

        if read_ok:
            for fem_idx in range(self.num_fems):
                logging.info('FEM {} : FPGA temp: {:.1f}C PCB temp: {:.1f}C FE temp: {:.1f}C FE humidity: {:.1f}%'.format(
                    fem_idx, param_vals['fem_remote_temp'][fem_idx], param_vals['fem_local_temp'][fem_idx],
                    param_vals['moly_temp'][fem_idx], param_vals['moly_humidity'][fem_idx]
                ))
                 
                supply_vals = ['ON' if val == 1 else 'OFF' for val in [param_vals[key][fem_idx] for key in supply_params]]
                 
                logging.info('FEM {} : Supply status: P1V5_AVDD: {}/{}/{}/{} P1V5_VDD1: {} P2V5_DVDD1: {}'.format(
                    fem_idx, *supply_vals
                ))
                 
                fe_dacs = ' '.join(['{}: {:.3f}V'.format(idx, val) for (idx, val) in enumerate(param_vals['mpx3_dac_out'][fem_idx])])
                 
                logging.info("FEM {} : Front-end DAC channels: {}".format(fem_idx, fe_dacs))
        else:
            logging.error("Slow control read command failed")
    
    def do_dac_load(self):

        try:
            fem_ids = self.args.config_fem
            if fem_ids == [ExcaliburDefinitions.ALL_FEMS]:
                fem_ids = self.fem_ids
            fem_idxs = [self.fem_ids.index(fem_id) for fem_id in fem_ids]
        except ValueError as e:
            logging.error('Error in FEM IDs specified for DAC loading: {}'.format(e))
            return
        
        
        self.dac_config = ExcaliburDacConfigParser(
            self.args.dacs, fem_ids, self.args.config_chip)
 
        dac_params = []
        
        for (dac_name, dac_param) in self.dac_config.dac_api_params():

            dac_vals = []
            for (fem_id, fem_idx) in zip(fem_ids, fem_idxs):
    
                chip_ids = self.args.config_chip
                if chip_ids == [ExcaliburDefinitions.ALL_CHIPS]:
                    chip_ids = self.chip_ids[fem_idx]
                try:                        
                    [self.chip_ids[fem_idx].index(chip_id) for chip_id in chip_ids]
                except ValueError as e:
                    logging.error('Error in FEM {} chip IDs specified for DAC loading: {}'.format(fem_id, e))
                    return
                
                fem_vals = [self.dac_config.dacs(fem_id, chip_id)[dac_name] for chip_id in chip_ids]
                dac_vals.append(fem_vals)
            
            dac_params.append(ExcaliburParameter(dac_param, dac_vals, 
                              fem=self.args.config_fem, chip=self.args.config_chip))
        
        dac_params.append(ExcaliburParameter('mpx3_dacsense', [[self.args.sense_dac]],
                          fem=self.args.config_fem, chip=self.args.config_chip))
        
        write_ok = self.client.fe_param_write(dac_params)
        if not write_ok:
            logging.error("Failed to write DAC parameters for FEM ID {}, chip ID {}".format(fem_id, chip_id))
            return
        
        load_ok = self.client.do_command('load_dacconfig', self.args.config_fem, self.args.config_chip)
        if load_ok:
            logging.info("DAC load completed OK")
        else:
            logging.error('Failed to execute DAC load command: {}'.format(self.client.error_msg))
                           
    def do_acquisition(self):
        
        # Resolve the acquisition operating mode appropriately, handling burst and matrix read if necessary
        operation_mode = self.defaults.operation_mode
        
        if self.args.burst_mode:
            operation_mode = ExcaliburDefinitions.FEM_OPERATION_MODE_BURST
        
        if self.args.matrixread:
            if self.args.burst_mode:
                logging.warning("Cannot select burst mode and matrix read simultaneously, ignoring burst option")
            operation_mode =  ExcaliburDefinitions.FEM_OPERATION_MODE_MAXTRIXREAD
           
        # TODO - handle 24 bit readout here - needs to check frame count etc and execute C0 read 
        
        logging.info("Executing acquisition ...")
        
        # Build a list of parameters to be written to the system to set up acquisition
        write_params = []
                
        logging.info('  Setting test pulse count to {}'.format(self.args.tp_count))
        write_params.append(ExcaliburParameter('mpx3_numtestpulses', [[self.args.tp_count]]))
        tp_enable = 1 if self.args.tp_count != 0 else 0
        write_params.append(ExcaliburParameter('testpulse_enable', [[tp_enable]]))
        
        logging.info('  Setting number of frames to {}'.format(self.args.num_frames))
        write_params.append(ExcaliburParameter('num_frames_to_acquire', [[self.args.num_frames]]))
        
        logging.info('  Setting acquisition time to {} ms'.format(self.args.acquisition_time))
        write_params.append(ExcaliburParameter('acquisition_time', [[self.args.acquisition_time]]))
        
        logging.info('  Setting trigger mode to {}'.format(
            ExcaliburDefinitions.trigmode_name(self.args.trigger_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_externaltrigger', [[self.args.trigger_mode]]))
        
        logging.info('  Setting ASIC readout mode to {}'.format(
            ExcaliburDefinitions.readout_mode_name(self.args.readout_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_readwritemode', [[self.args.readout_mode]]))

        logging.info('  Setting ASIC colour mode to {} '.format(
            ExcaliburDefinitions.colour_mode_name(self.args.colour_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_colourmode', [[self.args.colour_mode]]))

        logging.info('  Setting ASIC pixel mode to {} '.format(
            ExcaliburDefinitions.csmspm_mode_name(self.args.csmspm_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_csmspmmode', [[self.args.csmspm_mode]]))

        logging.info('  Setting ASIC discriminator output mode to {} '.format(
            ExcaliburDefinitions.disccsmspm_name(self.args.disccsmspm)
        ))
        write_params.append(ExcaliburParameter('mpx3_disccsmspm', [[self.args.disccsmspm]]))

        logging.info('  Setting ASIC equalization mode to {} '.format(
            ExcaliburDefinitions.equalisation_mode_name(self.args.equalization_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_equalizationmode', [[self.args.equalization_mode]]))
        
        logging.info('  Setting ASIC gain mode to {} '.format(
            ExcaliburDefinitions.gain_mode_name(self.args.gain_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_gainmode', [[self.args.gain_mode]]))

        logging.info('  Setting ASIC counter select to {} '.format(self.args.counter_select))
        write_params.append(ExcaliburParameter('mpx3_counterselect', [[self.args.counter_select]]))
        
        logging.info('  Setting ASIC counter depth to {} bits'.format(self.args.counter_depth))
        counter_depth_val = ExcaliburDefinitions.counter_depth(self.args.counter_depth)
        write_params.append(ExcaliburParameter('mpx3_counterdepth', [[counter_depth_val]]))
        
        logging.info('  Setting operation mode to {}'.format(
            ExcaliburDefinitions.operation_mode_name(operation_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_operationmode', [[operation_mode]]))
        
        if self.args.matrixread:
            lfsr_bypass_mode = ExcaliburDefinitions.FEM_LFSR_BYPASS_MODE_ENABLED
        else:
            lfsr_bypass_mode = ExcaliburDefinitions.FEM_LFSR_BYPASS_MODE_DISABLED
        logging.info('  Setting LFSR bypass mode to {}'.format(
            ExcaliburDefinitions.lfsr_bypass_mode_name(lfsr_bypass_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_lfsrbypass', [[lfsr_bypass_mode]]))
        
        logging.info('  Disabling local data receiver thread')
        write_params.append(ExcaliburParameter('datareceiver_enable', [[0]]))
        
        # Write all the parameters to system
        logging.info("Writing configuration parameters to system")
        write_ok = self.client.fe_param_write(write_params)
        if not write_ok:
            logging.error("Failed to write configuration parameters to system: {}".format(self.client.error_msg))
            return
        
        # Send start acquisition command
        logging.info('Sending start acquisition command')
        cmd_ok = self.client.do_command('start_acquisition')
        if not cmd_ok:
            logging.error('start_acquisition command failed: {}'.format(self.client.error_msg))
            return
        
        # If the nowait arguments wasn't given, monitor the acquisition state until all requested frames
        # have been read out by the system
        if not self.args.no_wait:

            wait_count = 0
            acq_completion_state_mask = 0x40000000
            frames_acquired = 0
                    
            while True:
                
                (read_ok, vals) = self.client.fe_param_read(['frames_acquired','control_state'])
                frames_acquired = min(vals['frames_acquired'])                
                acq_completed = all(
                    [((state & acq_completion_state_mask) == acq_completion_state_mask) for state in vals['control_state']]
                )
                if acq_completed:
                    break
                
                wait_count += 1
                if wait_count % 5 == 0:
                    logging.info('  {:d} frames read out  ...'.format(frames_acquired))
            
            logging.info("Completed readout of {} frames".format(frames_acquired))
            self.do_stop()    
            logging.info("Acquisition complete")
        else:
            logging.info("Acquisition started, not waiting for completion, will not send stop command")
        
    def do_stop(self):
        
        logging.info('Sending stop acquisition command')
        self.client.do_command('stop_acquisition')
        
if __name__ == '__main__':
    
    ExcaliburTestApp().run()
