''' Extracts data from various places
'''
from __future__ import print_function

import h5py
import numpy as np
import xml.etree.ElementTree as ET
import os
from datetime import datetime
import sys

#Remove: potentially not used after code move
'''def get_lpd_filename(file_path, filename):
    '''''' Returns absolute path of data file
    ''''''
    return file_path + filename'''


def get_lpd_file(filename):
    ''' Gets hdf file based on filename
    '''
    lpd_file = h5py.File(filename, 'r')
    return lpd_file


def get_lpd_data(lpd_file):
    ''' Get all data from a hdf file. The overall process inside get_lpd_file() and this function
        has been separated so the metadata can be accessed without the need of two h5py file
        objects in the code
    '''
    try:
        lpd_data = lpd_file['data'][()]
    except KeyError:
        lpd_data = lpd_file['lpd/data/image'][()]
    return lpd_data


def get_first_image(lpd_data):
    ''' Get first image from lpd_data
    '''
    single_image = lpd_data[:1, :, :]
    single_image = np.reshape(single_image, (256, 256))
    return single_image


def get_single_tile(lpd_data, tile_position, image_num):
    ''' Get a single tile (left or right) from lpd_data from any image in the file
    '''
    single_tile = lpd_data[image_num:image_num + 1, tile_position[0]:tile_position[0] + 32,
                           tile_position[1]:tile_position[1] + 128]
    single_tile = np.reshape(single_tile, (32, 128))
    return single_tile


def get_mean_tile(lpd_data, tile_position):
    ''' Get a mean tile of all the tiles in the file
    '''
    tile_data = get_total_tile(lpd_data, tile_position)
    mean_tile = np.mean(tile_data, axis=0)
    return mean_tile


def get_total_tile(lpd_data, tile_position):
    ''' Return a 32 x 128 tile that contains the aggregate of all the images in the file
        Used in get_stdev_tile()
    '''
    total_tile_data = lpd_data[:lpd_data.shape[0], tile_position[0]:tile_position[0] + 32,
                               tile_position[1]:tile_position[1] + 128]
    return total_tile_data


def get_stdev_image(lpd_data):
    ''' Get an image that contains the standard deviation of all data in the file
    '''
    stdev_image = np.std(lpd_data, axis=0)
    return stdev_image


def get_stdev_tile(lpd_data, tile_position):
    ''' Get a tile that contains the standard deviation of the data in the file
    '''
    tile_data = get_total_tile(lpd_data, tile_position)
    stdev_tile = np.std(tile_data, axis=0)
    return stdev_tile


def get_single_chip(tile, chip_position):
    ''' Get single chip from a single tile
        chip_position - int from 0 to 7
    '''
    chip_position = chip_position * 16
    single_chip = tile[:, chip_position:chip_position + 16]
    return single_chip


def get_single_column(tile, col_position):
    ''' Get a single column within a tile
    '''
    single_column = tile[:, col_position:col_position + 1]
    return single_column

def get_single_row(tile, row_position): 
    ''' Get a single row within the tile 
    '''
    single_row = tile[row_position :]
    return single_row 

def set_tile_position(tile_orientation, mini_connector):
    ''' Used to set variables defining where to get the data from lpd_data
    '''
    tile_position = []

    # Tiles have a 32 pixel height
    if mini_connector > 1:
        tile_position.append(32 * (mini_connector - 1))
    else:
        tile_position.append(0)

    # Left or right tile
    if tile_orientation == "LHS":
        # Left tiles are on the RHS of the image, and vice versa
        tile_position.append(128)
    else:
        tile_position.append(0)

    return tile_position


def get_file_metadata(file):
    ''' Gets metadata groups from open h5 file
    '''
    try:
        metadata = file['metadata']
    except KeyError:
        metadata = file['lpd/metadata']
    return metadata


def get_num_images_per_train(metadata):
    ''' Gets value for the number of images per train, which is then used in the analysis details
        and when plotting the trigger images
    '''
    # Get contents of readoutParamFile
    readout = metadata['readoutParamFile'][0]

    # Pass contents of readout (of type bytes) into an XML parser and find relevant parameter
    tree = ET.fromstring(readout)
    img_param = tree.find('numberImages')

    return int(img_param.get('val'))


def get_num_trains(metadata):
    ''' Returns the number of trains in the data file's metadata
    '''
    return int(metadata.attrs['numTrains'])


def get_file_date_created(file_path, metadata):
    ''' Gets the timestamp when file was created, either from the metadata or timestamp of the file
    '''
    metadata_key = 'runDate'
    if metadata_key in metadata.attrs.keys():
        date_str = metadata.attrs[metadata_key]
    else:
        date_created = os.path.getmtime(file_path)
        date_str = datetime.fromtimestamp(date_created).strftime('%d-%m-%Y %H:%M:%S')
    return date_str


def get_total_num_images(metadata):
    ''' Calculates total number of images in the data file
    '''
    return get_num_images_per_train(metadata) * get_num_trains(metadata)


def get_cmd_seq_filename(metadata):
    ''' Gets the filename of the command sequence file
    '''
    filename = str(metadata.attrs['cmdSequenceFile']).split('/')[-1]
    if filename.endswith('\''):
        filename = filename[:-len('\'')]
    return filename
