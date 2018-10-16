import h5py

'''
Created on 16 Oct 2018

@author: xfu59478
'''

class MetadataWriter(object):
    '''
    This class writes metadata to closed HDF files 
    '''


    def __init__(self, cachedParams):
        self.cachedParams = cachedParams 
        
    def write_metadata(self, metadata_group):
        print("Adding metadata to file")
        
        # Build metadata attributes from cached parameters
        for param, val in self.cachedParams.items():
            metadata_group.attrs[param] = val
        
        # Write the XML configuration files into the metadata group        
        self.xmlDs = {}
        str_type = h5py.special_dtype(vlen=str)
        
        for paramFile in ('readoutParamFile', 'cmdSequenceFile', 'setupParamFile'):
            self.xmlDs[paramFile] = metadata_group.create_dataset(paramFile, shape=(1,), dtype=str_type)
            try:
                with open(self.cachedParams[paramFile], 'r') as xmlFile:
                    self.xmlDs[paramFile][:] = xmlFile.read()
                    
            except IOError as e:
                print("Failed to read %s XML file %s : %s " (paramFile, self.cachedParams[paramFile], e))
                raise(e)
            except Exception as e:
                print("Got exception trying to create metadata for %s XML file %s : %s " % (paramFile, self.cachedParams[paramFile], e))
                raise(e)
            
        print(metadata_group)