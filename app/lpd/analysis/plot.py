''' Creates plots based on input data
'''
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import matplotlib.colors as colors
import test_results


def setup_test_plots(test_type, gs, fig):
    ''' Creates a figure with plots for either mean data or stdev data - determined by test_type
    '''
    if (test_type == 2):
        subplot_spec = 0
        #Create Page 2 layout 
        fig, gs = setup_second_page()
    else:
        subplot_spec = 2

    # GridSpec inside subplot - used for plot of tile with colorbar
    gs1_tile = gridspec.GridSpecFromSubplotSpec(ncols =2, nrows=2, subplot_spec=gs[subplot_spec], width_ratios=[16,1],
                                                height_ratios=[1,1], hspace=0.3)

    # Create figure and all subplots
    fig_titles = ('Mean Data Plots', 'Standard Deviation Plots')
    tile_plot = fig.add_subplot(gs1_tile[0, 0])
    tile_plot.set_title("%s"% fig_titles[test_type - 1])
    tile_colorbar = fig.add_subplot(gs1_tile[0, 1])
    histogram = fig.add_subplot(gs1_tile[1, 0])
    histogram.set_title("Histogram of standard deviation tile data")


    return (fig, gs, tile_plot, tile_colorbar, histogram)

def setup_second_page(testAll=False):
    fig = plt.figure(figsize=(8.27,11.69))
    if testAll:
        gs = gridspec.GridSpec(2, 1, hspace=0.4)
    else:
        gs = gridspec.GridSpec(3, 1, hspace=0.4)
    return (fig, gs)


def setup_fault_plots(fig, gs, test_type):
    ''' Create figure & plot for fault image
    '''
    #Creating the subplots for the fault 
    if test_type == "All":
        gs1_tile = gridspec.GridSpecFromSubplotSpec(ncols =2, nrows=1, subplot_spec=gs[0],
                                                width_ratios=[16,1], hspace=0.1)
    else:
        gs1_tile = gridspec.GridSpecFromSubplotSpec(ncols =2, nrows=1, subplot_spec=gs[1],
                                                width_ratios=[16,1], hspace=0.1)
    fault_tile_plot = fig.add_subplot(gs1_tile[0, 0])
    fault_legend = fig.add_subplot(gs1_tile[0, 1])

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
    fault_legend.legend(handles=[no_fault_patch, mean_patch, stdev_patch],bbox_to_anchor=[2,0.5], loc='right')

    return (fig, fault_tile_plot, fault_legend)


def setup_trigger_plots(fig , gs):
    ''' Create figure & plots for first 4 trigger tiles. Currently hardcoded to assume each frame
        contains 10 images
    '''
    gs_trigger = gridspec.GridSpecFromSubplotSpec(ncols =3, nrows=2, subplot_spec=gs[1], width_ratios=[8,8,1])

    # List containing each subplot containing each trigger plot
    trigger_plots = []

    # Coords. of subplots GridSpec positioning
    plot_pos_x = (0, 0, 1, 1)
    plot_pos_y = (0, 1, 0, 1)

    # Create each trigger image
    for trigger_pos in range(0, 4):
        trigger_plots.append(fig.add_subplot(gs_trigger[plot_pos_x[trigger_pos],
                                                                plot_pos_y[trigger_pos]]))
        trigger_plots[trigger_pos].set_title("Trigger {}".format(trigger_pos + 1))

    trigger_colorbar = fig.add_subplot(gs_trigger[:, 2])
    #gs_trigger.set_title("First {} Trigger Images".format(len(trigger_plots)), fontsize=16)

    return (fig, trigger_plots, trigger_colorbar)


def setup_first_image_plot(fig, gs, test_type):
    ''' Create figure and plot for very first image
    '''
    if test_type=="All":
        gs_first_image = gridspec.GridSpecFromSubplotSpec(ncols =2, nrows=1, subplot_spec=gs[1], width_ratios=[16,1])
    else:
        gs_first_image = gridspec.GridSpecFromSubplotSpec(ncols =2, nrows=1, subplot_spec=gs[2], width_ratios=[16,1])

    # Create subplots for image and respective colorbar
    first_image_plot = fig.add_subplot(gs_first_image[0, 0])
    first_image_colorbar = fig.add_subplot(gs_first_image[0, 1])

    return (fig, first_image_plot, first_image_colorbar)


def disable_ticks(ax):
    ''' Disable ticks on both x & y axis - used to remove them from colorbars and image/tile plots
    '''
    ax.ticklabel_format(useOffset=False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axes.get_xaxis().set_ticks([])
    ax.axes.get_yaxis().set_ticks([])


def set_plot_titles(test_type, fault_tile_plot, first_image_plot, trigger_plots=None,
                     mean_tile_plot=None, mean_histogram=None,
                     stdev_tile_plot=None, stdev_histogram=None):
    ''' Set titles of all plots and remove ticks on images
        Titles are removed on each gca() call so must be re-set for every analysis done
    '''
    if (test_type != "All") :
        mean_tile_plot.set_title("Plot of Tile Using Mean Data", fontsize=16)
        mean_histogram.set_title("Histogram of Mean Tile Data", fontsize=16)
        disable_ticks(mean_tile_plot)

        stdev_tile_plot.set_title("Plot of Tile Using Standard Deviation Data", fontsize=16)
        stdev_histogram.set_title("Histogram of Standard Deviation Tile Data", fontsize=16)
        disable_ticks(stdev_tile_plot)

    fault_tile_plot.set_title("Plot of Tile's Faults", fontsize=16)
    first_image_plot.set_title("First Image of Data", fontsize=16)


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