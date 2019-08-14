''' Creates plots based on input data
'''

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import matplotlib.colors as colors
import test_results

def setup_title_plot(filename , tile_position, mini_connector):
    ''' Create an area showing the pdf title and test information
    '''
    fig_title = plt.figure(figsize=(8,2) , num='Title Plot')
    gs1 = gridspec.GridSpec(1, 2, width_ratios=[16, 1], wspace=0.5)

    title_plot = fig_title.add_subplot(gs1[0, 0])
    title_plot.axis('off')

    if(tile_position[1] == 128):
        tile_location = "LHS"
    else: 
        tile_location = "RHS"

    title_plot.set_title("Analysis of: %s, tile from: %s, mini connector number:%i" %(filename, tile_location, mini_connector))

    return(fig_title,title_plot)


def setup_test_plots(test_type):
    ''' Creates a figure with plots for either mean data or stdev data - determined by test_type
    '''
    gs1 = gridspec.GridSpec(2, 1, hspace=0.3)
    # GridSpec inside subplot - used for plot of tile with colorbar
    gs1_tile = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs1[0], wspace=0.05,
                                                width_ratios=[16, 1])

    # Create figure and all subplots
    fig_titles = ('Mean Data Plots', 'Standard Deviation Plots')
    fig = plt.figure(figsize=(8, 4), num=fig_titles[test_type - 1])
    tile_plot = fig.add_subplot(gs1_tile[0, 0])
    tile_colorbar = fig.add_subplot(gs1_tile[0, 1])
    histogram = fig.add_subplot(gs1[1, 0])

    return (fig, tile_plot, tile_colorbar, histogram)


def setup_fault_plots():
    ''' Create figure & plot for fault image
    '''
    fig_fault = plt.figure(figsize=(8, 2), num='Fault Plot')
    gs1 = gridspec.GridSpec(1, 2, width_ratios=[16, 1], wspace=0.5)

    fault_tile_plot = fig_fault.add_subplot(gs1[0, 0])
    fault_legend = fig_fault.add_subplot(gs1[0, 1])

    # Disabling axes for legend - works permanently so no need to be put into set_plot_titles()
    fault_legend.axis('off')

    # Getting range of colour values used in colormap - reverse map used so 'no fault' is white
    # (more readable)
    cmap = cm.get_cmap('CMRmap_r')
    colorbar_range = colors.Normalize(vmin=0, vmax=2)

    # Creating legend
    no_fault_patch = mpatches.Patch(color=cmap(colorbar_range(0)), label='No Fault')
    mean_patch = mpatches.Patch(color=cmap(colorbar_range(1)), label='Mean Fault')
    stdev_patch = mpatches.Patch(color=cmap(colorbar_range(2)), label='Stdev Fault')
    fault_legend.legend(handles=[no_fault_patch, mean_patch, stdev_patch], loc='right')

    return (fig_fault, fault_tile_plot, fault_legend)


def setup_trigger_plots():
    ''' Create figure & plots for first 4 trigger tiles. Currently hardcoded to assume each frame
        contains 10 images
    '''
    fig_trigger = plt.figure(figsize=(8, 3), num='Trigger Plots')
    gs_trigger = gridspec.GridSpec(2, 3, width_ratios=[9, 9, 1])

    # List containing each subplot containing each trigger plot
    trigger_plots = []

    # Coords. of subplots GridSpec positioning
    plot_pos_x = (0, 0, 1, 1)
    plot_pos_y = (0, 1, 0, 1)

    # Create each trigger image
    for trigger_pos in range(0, 4):
        trigger_plots.append(fig_trigger.add_subplot(gs_trigger[plot_pos_x[trigger_pos],
                                                                plot_pos_y[trigger_pos]]))
        trigger_plots[trigger_pos].set_title("Trigger {}".format(trigger_pos + 1))

    trigger_colorbar = fig_trigger.add_subplot(gs_trigger[:, 2])
    fig_trigger.suptitle("First {} Trigger Images".format(len(trigger_plots)), fontsize=16)

    return (fig_trigger, trigger_plots, trigger_colorbar)


def setup_first_image_plot():
    ''' Create figure and plot for very first image
    '''
    fig_first_image = plt.figure(figsize=(8, 6), num='First Full Image Plot')
    gs_first_image = gridspec.GridSpec(1, 2, width_ratios=[12, 1], wspace=0.05)

    # Create subplots for image and respective colorbar
    first_image_plot = fig_first_image.add_subplot(gs_first_image[0, 0])
    first_image_colorbar = fig_first_image.add_subplot(gs_first_image[0, 1])

    return (fig_first_image, first_image_plot, first_image_colorbar)


def disable_ticks(ax):
    ''' Disable ticks on both x & y axis - used to remove them from colorbars and image/tile plots
    '''
    ax.ticklabel_format(useOffset=False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axes.get_xaxis().set_ticks([])
    ax.axes.get_yaxis().set_ticks([])


def set_plot_titles(mean_tile_plot, mean_histogram, stdev_tile_plot, stdev_histogram,
                    fault_tile_plot, trigger_plots, first_image_plot):
    ''' Set titles of all plots and remove ticks on images
        Titles are removed on each gca() call so must be re-set for every analysis done
    '''
    mean_tile_plot.set_title("Plot of Tile Using Mean Data", fontsize=16)
    mean_histogram.set_title("Histogram of Mean Tile Data", fontsize=16)
    disable_ticks(mean_tile_plot)

    stdev_tile_plot.set_title("Plot of Tile Using Standard Deviation Data", fontsize=16)
    stdev_histogram.set_title("Histogram of Standard Deviation Tile Data", fontsize=16)
    disable_ticks(stdev_tile_plot)

    fault_tile_plot.set_title("Plot of Tile's Faults", fontsize=16)
    first_image_plot.set_title("First Image of Data", fontsize=16)
    '''disable_ticks(fault_tile_plot)
    disable_ticks(first_image_plot)

    for trigger_pos in range(0, 4):
        trigger_plots[trigger_pos].set_title("Trigger {}".format(trigger_pos + 1))
        disable_ticks(trigger_plots[trigger_pos])'''


def display_data_plot(ax, data, colorbar=None, colorbar_type=0):
    ''' Displays plot of entire images and tiles
        Colorbar isn't required so trigger images can share one colorbar
        colorbar_type - int value representing type of colorbar being passed
            0 - Colorbar for image plot using raw or mean data
            1 - Colorbar for image using standard deviation data
            2 - Colorbar for showing tile's faults
    '''
    # Use jet unless displaying fault plot
    cmap_name = 'jet'

    # Specify colorbar ticks and determine max value of data
    if colorbar_type == 0:
        c_ticks = [0, 511, 1023, 1535, 2047, 2559, 3071, 3583, 4095]
        # Raw/mean data will always have max of 4095
        data_max = 4095
    elif colorbar_type == 1:
        c_ticks = [0, 20, 40, 60, 80, 100]
        data_max = 100
    elif colorbar_type == 2:
        c_ticks = [0, 1, 2]
        # Constant value set for consistency between multiple fault images
        data_max = 2
        cmap_name = 'CMRmap_r'

    image = ax.imshow(data, cmap=cmap_name, vmin=0, vmax=data_max)

    if colorbar is not None:
        # Create and add colorbar
        cbar = plt.colorbar(image, cax=colorbar)
        cbar.set_ticks(ticks=c_ticks)

        if colorbar_type == 2:
            # Change ticks to strings to make them more understandable to user
            string_ticks = ['No Fault', 'Fault in mean data', 'Fault in stdev. data']
            # set_ticks() is executed before to get 3 ticks, instead of more
            cbar.ax.set_yticklabels(string_ticks)

    rows = data.shape[0]
    cols = data.shape[1]
    # Add vertical and horizontal lines to differentiate between chips and tiles
    for i in range(16, cols, 16):
        # Separate chips
        ax.vlines(i - 0.5, 0, rows - 1, color='k', linestyles='solid', linewidth=0.4)
        # Add vertical lines to differentiate between tiles
        ax.vlines(128 - 0.5, 0, rows - 1, color='k', linestyle='solid')
    for i in range(32, rows, 32):
        ax.hlines(i - 0.5, 0, rows - 1, color='k', linestyles='solid')


def display_histogram(ax, data):
    ''' Displays histograms
    '''
    ax.hist(data.flatten(), bins=250)