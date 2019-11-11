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

    def __init__(self, analysis_pdf, module_num, run_num, test_type, tile_position , mini_connector, file_name, pre_config_current, post_config_current, hvBias):

        #def analyse_data(self, tile_position , mini_connector, file_name):
        ''' Analysis is performed on the specific tile selected, analysing data by taking mean and standard deviation
            measurements
        '''  
        self.pre_config_current = pre_config_current
        self.post_config_current = post_config_current
        self.analysis_pdf = analysis_pdf
        self.hvBias = hvBias
        self.module_num = module_num
        self.run_num = run_num
        self.test_type = test_type

        # Creating components needed for analysis
        self.file_name = file_name
        self.mini_connector = mini_connector
        self.lpd_file = extract_data.get_lpd_file(self.file_name)
        lpd_data = extract_data.get_lpd_data(self.lpd_file)

        if (self.test_type != "All"):
            self.tile_position = extract_data.set_tile_position("tile_position", self.mini_connector)
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
            self.fig_page2.show()
            print(bad_chips_mean, bad_cols_mean, bad_pixels_mean)
            print(bad_chips_stdev, bad_cols_stdev, bad_pixels_stdev)
            
        else:
            self.figure_setup()
            fault_tile_list = [np.zeros((32, 128), dtype=np.int32)] * 16
            bad_chips_mean_list = [None] * 16
            bad_cols_mean_list = [None] * 16
            bad_pixels_mean_list = [None] * 16
            bad_chips_stdev_list = [None] * 16
            bad_cols_stdev_list = [None] * 16
            bad_pixels_stdev_list = [None] * 16
            

            for x in range(16):
                if (x < 8):
                    self.tile_position = extract_data.set_tile_position("RHS", x+1)
                else:
                    self.tile_position = extract_data.set_tile_position("LHS", x-7)
                mean_tile = extract_data.get_mean_tile(lpd_data, self.tile_position)
                stdev_tile = extract_data.get_stdev_tile(lpd_data, self.tile_position)

                # Mean data test with plots of mean tile and histogram
                bad_chips_mean_list[x] = test_data.bad_chips(mean_tile, fault_tile_list[x], 1)
                bad_cols_mean_list[x] = test_data.bad_columns(mean_tile, fault_tile_list[x], 1)
                bad_pixels_mean_list[x] = test_data.bad_pixels(mean_tile, fault_tile_list[x], 1)

                # Test using standard deviation data
                bad_chips_stdev_list[x] = test_data.bad_chips(stdev_tile, fault_tile_list[x], 2)
                bad_cols_stdev_list[x] = test_data.bad_columns(stdev_tile, fault_tile_list[x], 2)
                bad_pixels_stdev_list[x] = test_data.bad_pixels(stdev_tile, fault_tile_list[x], 2)   

            fault_tile = self.collate_list(fault_tile_list)
            bad_chips_mean = self.collate_list(bad_chips_mean_list)
            bad_cols_mean = self.collate_list(bad_cols_mean_list)
            bad_pixels_mean = self.collate_list(bad_pixels_mean_list)
            bad_chips_stdev = self.collate_list(bad_chips_stdev_list)
            bad_cols_stdev = self.collate_list(bad_cols_stdev_list)
            bad_pixels_stdev = self.collate_list(bad_pixels_stdev_list)

        print(fault_tile)
        print(np.sum(fault_tile))
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
                                        self.data_file_path, lpd_data_metadata, self.pre_config_current, self.post_config_current)
        self.fig_page1.show()
        
        if (self.test_type != "All"):
            test_results.display_trigger_images(lpd_data, self.tile_position, self.fig_trigger, self.trigger_plots, self.trigger_colorbar, lpd_data_metadata)
            self.fig_trigger.show()

        test_results.display_first_image(lpd_data, self.first_image_plot, self.first_image_colorbar) 
        self.fig_first_image.show()

        self.generate_analysis_report()

    def figure_setup(self):

        # Setup figures, subplots and results table
        if (self.test_type != "All"):
            self.fig_page1, self.gs1, self.results_table, self.analysis_textarea, self.analysis_text_list = test_results.setup_results_figure(self.file_name, self.module_num, self.hvBias, self.test_type, self.tile_position , self.mini_connector)
            self.fault_fig, self.fault_tile_plot, self.fault_legend = plot.setup_fault_plots(self.fig_page1, self.gs1)
            self.mean_fig, self.gs,  self.mean_tile_plot, self.mean_tile_colorbar, self.mean_histogram = plot.setup_test_plots(1, self.gs1, self.fig_page1)
            self.fig_page2 , self.gs2, self.stdev_tile_plot, self.stdev_tile_colorbar, self.stdev_histogram = plot.setup_test_plots(2, self.gs1, self.fig_page1)
            self.fig_trigger, self.trigger_plots, self.trigger_colorbar = plot.setup_trigger_plots(self.fig_page2 , self.gs2)
            self.fig_first_image, self.first_image_plot, self.first_image_colorbar = plot.setup_first_image_plot(self.fig_page2,self.gs2)
        else:
            self.fig_page1, self.gs1, self.results_table, self.analysis_textarea, self.analysis_text_list = test_results.setup_results_figure(self.file_name, self.module_num, self.hvBias, self.test_type)
            self.fault_fig, self.fault_tile_plot, self.fault_legend = plot.setup_fault_plots(self.fig_page1, self.gs1)
            self.fig_first_image, self.first_image_plot, self.first_image_colorbar = plot.setup_first_image_plot(self.fig_page1,self.gs1)


        self.data_file_path = self.lpd_file
        self.date_format = '%d/%m/%Y'
        # CSS classes used to modify styling of each type of widget
        self.title_css_class = 'group-titles'
        self.bold_text_class = 'bold-label'

        # Set titles of all plots - would've been cleared by cla()
        if (self.test_type != "All"):
            plot.set_plot_titles(self.test_type, self.fault_tile_plot, self.first_image_plot, self.trigger_plots,
                                self.mean_tile_plot, self.mean_histogram, self.stdev_tile_plot, self.stdev_histogram)
        else:
               plot.set_plot_titles(self.test_type, self.fault_tile_plot, self.first_image_plot)         

    

    def generate_analysis_report(self):
        ''' Event handling for 'Analysis Report' button
        '''
        file_name = str(self.file_name)
        file_name = os.path.basename(file_name)
        # Generate list of figures to be added to pdf
        if (self.test_type != "All"):
            pdf_fig_list = [self.fig_page1, self.fig_page2]
        else:
            pdf_fig_list = [self.fig_page1]

        pdf_file_name = generate_report.export(self.analysis_pdf, self.module_num, self.run_num, self.test_type, pdf_fig_list, file_name)
        return pdf_file_name


    def collate_list(self, item_list):
        item = np.concat((item_list[0], item_list[8]), axis=1)
        for i in range(7) :
            newRows = np.concat((item_list[i+1], item_list[i+9]), axis=1)
            item = np.concat((item, newRows))
        return item