'''
Created on 16 Oct 2018

@author: xfu59478
'''

import h5py

<<<<<<< HEAD

class MetadataWriter(object):
    ''' This class writes metadata to open HDF files
=======
class MetadataWriter(object):
    ''' This class writes metadata to open HDF files 
>>>>>>> 98f2aeeeed0859e878719e67abec4c63e8fd1aa5
    '''

    def __init__(self, cached_params):
        self.cached_params = cached_params

    def write_metadata(self, metadata_group):
        print("Adding metadata to file")

        # Build metadata attributes from cached parameters
        for param, val in self.cached_params.items():
            metadata_group.attrs[param] = val
<<<<<<< HEAD

=======
        
>>>>>>> 98f2aeeeed0859e878719e67abec4c63e8fd1aa5
        # Write the XML configuration files into the metadata group
        self.xml_ds = {}
        str_type = h5py.special_dtype(vlen=str)

        for param_file in ('readoutParamFile', 'cmdSequenceFile', 'setupParamFile'):
<<<<<<< HEAD
            self.xml_ds[param_file] = metadata_group.create_dataset(param_file, shape=(1,),
=======
            self.xml_ds[param_file] = metadata_group.create_dataset(param_file, shape=(1,), 
>>>>>>> 98f2aeeeed0859e878719e67abec4c63e8fd1aa5
                                                                    dtype=str_type)
            try:
                with open(self.cached_params[param_file], 'r') as xml_file:
                    self.xml_ds[param_file][:] = xml_file.read()

            except IOError as e:
                print("Failed to read %s XML file %s : %s " (param_file, 
                                                             self.cached_params[param_file], e))
                raise(e)
            except Exception as e:
<<<<<<< HEAD
                print("Got exception trying to create metadata for %s XML file %s : %s " %
                      (param_file, self.cached_params[param_file], e))
=======
                print("Got exception trying to create metadata for %s XML file %s : %s " % 
                     (param_file, self.cached_params[param_file], e))
>>>>>>> 98f2aeeeed0859e878719e67abec4c63e8fd1aa5
                raise(e)
