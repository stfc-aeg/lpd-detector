'''
Created on 16 Oct 2018

@author: xfu59478
'''

import h5py
from datetime import datetime


class MetadataWriter(object):
    ''' This class writes metadata to open HDF files
    '''

    def __init__(self, cached_params):
        self.cached_params = cached_params

    def write_metadata(self, metadata_group):
        print("Adding metadata to file")

        # Build metadata attributes from cached parameters
        for param, val in self.cached_params.items():
            metadata_group.attrs[param] = val
        # Add additional attribute to record current date
        metadata_group.attrs['runDate'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        # Write the XML configuration files into the metadata group
        self.xml_ds = {}
        str_type = h5py.special_dtype(vlen=str)

        for param_file in ('readoutParamFile', 'cmdSequenceFile', 'setupParamFile'):
            self.xml_ds[param_file] = metadata_group.create_dataset(param_file, shape=(1,),
                                                                    dtype=str_type)
            try:
                with open(self.cached_params[param_file], 'r') as xml_file:
                    self.xml_ds[param_file][:] = xml_file.read()

            except IOError as e:
                print("Failed to read %s XML file %s : %s " (param_file, 
                                                             self.cached_params[param_file], e))
                raise(e)
            except Exception as e:
                print("Got exception trying to create metadata for %s XML file %s : %s " %
                      (param_file, self.cached_params[param_file], e))
                raise(e)
