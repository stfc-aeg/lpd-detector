from __future__ import print_function
import sys
import numpy as np
from os import listdir, path
from os.path import isfile, join, getmtime
from datetime import timedelta, date, datetime
import warnings
import matplotlib.cbook
import extract_data
import test_data
import test_results
from fpdf import FPDF
import plot
import fault_tiles
import extract_data
import generate_report
import os.path

class DataAnalyser():

    def __init__(self, tile_position , mini_connector, file_name):

        #def analyse_data(self, tile_position , mini_connector, file_name):
        ''' Analysis is performed on the specific tile selected, analysing data by taking mean and standard deviation
            measurements
        '''  

        # Creating components needed for analysis
        self.file_name = file_name
        self.mini_connector = mini_connector
        self.lpd_file = extract_data.get_lpd_file(self.file_name)
        lpd_data = extract_data.get_lpd_data(self.lpd_file)
        self.tile_position = extract_data.set_tile_position(tile_position, self.mini_connector)
        mean_tile = extract_data.get_mean_tile(lpd_data, self.tile_position)
        stdev_tile = extract_data.get_stdev_tile(lpd_data, self.tile_position)
        fault_tile = np.zeros((32, 128), dtype=np.int32)

        self.figure_setup()


        # Mean data test with plots of mean tile and histogram
        bad_chips_mean = test_data.bad_chips(mean_tile, fault_tile, 1)
        bad_cols_mean = test_data.bad_columns(mean_tile, fault_tile, 1)
        bad_pixels_mean = test_data.bad_pixels(mean_tile, fault_tile, 1)
        test_data.manage_figure(mean_tile, self.mean_tile_plot, self.mean_tile_colorbar, self.mean_histogram, 0)
        self.mean_fig.show()

        # Test using standard deviation data
        bad_chips_stdev = test_data.bad_chips(stdev_tile, fault_tile, 2)
        bad_cols_stdev = test_data.bad_columns(stdev_tile, fault_tile, 2)
        bad_pixels_stdev = test_data.bad_pixels(stdev_tile, fault_tile, 2)
        test_data.manage_figure(stdev_tile, self.stdev_tile_plot, self.stdev_tile_colorbar, 
                                self.stdev_histogram, 1)
        self.stdev_fig.show()

        # Plotting fault image
        fault_tiles.plot_faults(self.fault_tile_plot, fault_tile)
        self.fault_fig.show()

        # Display bad components of tile as text
        table_values = test_results.collate_results(bad_chips_mean, bad_chips_stdev, bad_cols_mean, bad_cols_stdev, 
                                                    bad_pixels_mean, bad_pixels_stdev)
        test_results.update_table(table_values, self.results_table)
        
        # Get metadata to be used in analysis details
        lpd_data_metadata = extract_data.get_file_metadata(self.lpd_file)
        test_results.set_analysis_text(self.analysis_textarea, self.analysis_text_list, self.lpd_file,
                                        self.data_file_path, lpd_data_metadata)
        self.results_fig.show()
        

        test_results.display_trigger_images(lpd_data, self.tile_position, self.fig_trigger, self.trigger_plots, self.trigger_colorbar, lpd_data_metadata)
        self.fig_trigger.show()

        test_results.display_first_image(lpd_data, self.first_image_plot, self.first_image_colorbar) 
        self.fig_first_image.show()

        pdf_name = self.generate_analysis_report()

    def figure_setup(self):

        # Setup figures, subplots and results table
        self.mean_fig, self.mean_tile_plot, self.mean_tile_colorbar, self.mean_histogram = plot.setup_test_plots(1)
        self.stdev_fig, self.stdev_tile_plot, self.stdev_tile_colorbar, self.stdev_histogram = plot.setup_test_plots(2)
        self.fault_fig, self.fault_tile_plot, self.fault_legend = plot.setup_fault_plots()
        self.results_fig, self.results_table, self.analysis_textarea, \
        self.analysis_text_list = test_results.setup_results_figure(self.file_name , self.tile_position , self.mini_connector)

        self.fig_trigger, self.trigger_plots, self.trigger_colorbar = plot.setup_trigger_plots()
        self.fig_first_image, self.first_image_plot, self.first_image_colorbar = plot.setup_first_image_plot()

        self.data_file_path = self.lpd_file
        self.date_format = '%d/%m/%Y'
        # CSS classes used to modify styling of each type of widget
        self.title_css_class = 'group-titles'
        self.bold_text_class = 'bold-label'

        # Set titles of all plots - would've been cleared by cla()
        self.title_fig , self.title_plot = plot.setup_title_plot(self.file_name , self.tile_position , self.mini_connector)
        plot.set_plot_titles(self.mean_tile_plot, self.mean_histogram, self.stdev_tile_plot, self.stdev_histogram,
                                self.fault_tile_plot, self.trigger_plots, self.first_image_plot)

    

    def generate_analysis_report(self):
        ''' Event handling for 'Analysis Report' button
        '''
        file_name = str(self.file_name)
        file_name = os.path.basename(file_name)
        # Generate list of figures to be added to pdf
        pdf_fig_list = [self.title_fig, self.results_fig, self.mean_fig, self.stdev_fig, self.fault_fig,  self.fig_trigger, self.fig_first_image]
        pdf_file_name = generate_report.export(pdf_fig_list, file_name, self.data_file_path ,self.tile_position, self.mini_connector )
        return pdf_file_name
 