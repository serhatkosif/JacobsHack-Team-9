# SPDX-FileCopyrightText: 2022 Earth System Data Exploration (ESDE), Jülich Supercomputing Center (JSC)
#
# SPDX-License-Identifier: MIT

"""
Just some small helper routines taht are used in the demo.
"""

__author__ = "Otoniel Campos"
__date__ = "05-10-2022"

# import modules
import os
from typing import List
import numpy as np
import xarray as xr
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from helper_utils import provide_default, to_list


def plot_cdf(x, y, plot_dict: dict = {}):
    """
    Plot cumulative density function in a x-y plot.
    :param x: the value of the data corresponding to the CDF-values y
    :param y: the CDF-values
    :param plot_dict: dictionary to control x-/y-axis title etc.
    """
    method = plot_cdf.__name__

    assert len(x) == len(y), "%{0}: x and y-data do not have the same length.".format(method)
    data_min, data_max = np.amin(x), np.amax(x)

    fig, ax = plt.subplots(1, figsize=(9, 6))
    # get arguments from plot_dict
    plt_title = provide_default(plot_dict, "plot_title", default="")
    xtitle, ytitle = provide_default(plot_dict, "xtitle", required=True), provide_default(plot_dict, "ytitle",
                                                                                          default="CDF")
    xlim = provide_default(plot_dict, "xlim", default=[data_min, data_max])
    ylim = provide_default(plot_dict, "ylim", default=[0., 1.])
    fs_title = provide_default(plot_dict, "fs_axistitle", default=16)
    fs_label = provide_default(plot_dict, "fs_axislabel", default=14)
    plot_file = provide_default(plot_dict, "plot_file", default=os.path.join(os.getcwd(), "plots", "cdf_plot.png"))
    lw = provide_default(plot_dict, "lw", default=2.)
    col = provide_default(plot_dict, "colour", default="b")

    # plot the data
    ax.plot(x, y, lw=lw, c=col)
    # modify appearance
    ax.set_xlabel(xtitle, fontsize=fs_title)
    ax.set_ylabel(ytitle, fontsize=fs_title)
    ax.tick_params(axis='both', which='major', labelsize=fs_label)
    # modify ticks on x-axis to ensure that the lower bound of the data is ticked
    locs = (ax.get_xticks()).tolist()
    if not data_min in locs:
        locs.insert(0, data_min)
    ax.set_xticks(locs)

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    ax.set_title(plt_title, size=fs_title)

    # save plot
    print("%{0}: Save plot to file '{1}'".format(method, plot_file))
    fig.savefig(plot_file)

    return fig, ax


def plot_histogram(data, bins, plot_dict):
    """
    Creates a histogram of the data accoring to bins.
    :param data: the data for which the histogram should be created.
    :param bins: the bins for the histogram
    :param plot_dict: dictionary to control histogram appearance.
    """
    method = plot_histogram.__name__

    nvalid = np.count_nonzero(~np.isnan(data))

    nbars = len(bins) - 1
    bin_freq, _ = np.histogram(data, bins=bins)
    bin_freq = bin_freq / nvalid * 100.

    # get arguments from plot_dict
    plt_title = provide_default(plot_dict, "plot_title", default="")
    xtitle, ytitle = provide_default(plot_dict, "xtitle", required=True), provide_default(plot_dict, "ytitle",
                                                                                          default="Frequency [%]")
    leg_str = provide_default(plot_dict, "legend", required=True)
    width = provide_default(plot_dict, "bar_width", default=0.8)
    bcol = provide_default(plot_dict, "bar_colour", default="blue")
    plot_first = provide_default(plot_dict, "plot_first", default=False)
    fs_title = provide_default(plot_dict, "fs_axistitle", default=16)
    fs_label = provide_default(plot_dict, "fs_axislabel", default=14)
    ylim = provide_default(plot_dict, "ylim", default=[0., 100.])
    plot_file = provide_default(plot_dict, "plot_file", default=os.path.join(os.getcwd(), "plots",
                                                                             "3h_precipitation_histogram.png"))

    xticks = []
    for i in range(nbars):
        xticks.append("[{0:3.1f},{1:3.1f})".format(bins[i], bins[i + 1]))

    if plot_first:
        ist = 0
    else:
        ist = 1
        print("%{0}: Frequency of events in bin [{1:3.1f}, {2:3.1f}): {3:5.3}%"
              .format(method, bins[0], bins[1], bin_freq[0]))

    # create the plot-object
    fig, ax = plt.subplots(1, figsize=(9, 6))
    ax.bar(np.arange(nbars - ist), bin_freq[ist::], width=width, color=bcol)

    # decorate plot
    ax.set_xlabel(xtitle, fontsize=fs_title)
    ax.set_ylabel(ytitle, fontsize=fs_title)
    ax.set_ylim(*ylim)
    ax.set_xticks(np.arange(nbars - ist))
    ax.set_xticklabels(xticks[ist::])
    ax.tick_params(axis="both", which="both", direction="out", labelsize=fs_label)
    ax.legend([leg_str], prop={'size': fs_label})

    ax.set_title(plt_title, size=fs_title)

    # save plot
    print("%{0}: Save plot to file '{1}'".format(method, plot_file))
    fig.savefig(plot_file)

    return fig, ax


def plot_precip_lead_time(mean_precip, init_hour, plot_dict: dict = {}):
    """
    Plots the temporally (and spatially) averaged precipitation against lead time.
    :param mean_precip: The precipitation data array with dimensions [forecast_hour, Lat, Long]
    :param init_hour: the initialization hour of the model run.
    :param plot_dict: dictionary to control x-/y-axis title etc.
    """
    method = plot_precip_lead_time.__name__

    # process data
    quantiles = provide_default(plot_dict, "quantiles", [0.25, 0.75])
    xy_coords = provide_default(plot_dict, "xy_coords", ["Lat", "Long"])

    data_min, data_max = np.amin(mean_precip), np.amax(mean_precip)

    daytimes = [(init_hour + fcst) % 24 for fcst in mean_precip["forecast_hour.hour"].values]
    nhours = len(daytimes)

    if nhours > 24:
        mean_precip = mean_precip[dict(forecast_hour=slice(-24, None))]
        daytimes = daytimes[-24::]
        nhours = 24

    try:
        mean_precip_davg = mean_precip.mean(dim=xy_coords)
        mean_precip_q1 = mean_precip.quantile(quantiles[0], dim=xy_coords)
        mean_precip_q2 = mean_precip.quantile(quantiles[1], dim=xy_coords)
    except ValueError as err:
        print("%{0}: Check if data has dimensions {1}.".format(method, " and ".join(xy_coords)))
        raise err
    except Exception as err:
        print("%{0}: Something unexpected happened. See error-message below.".format(method))
        raise err

    # plotting
    fig, ax = plt.subplots(1, figsize=(9, 6))
    # get arguments from plot_dict for plot appearance
    xtitle, ytitle = "daytime [UTC]", "mean precipitation [mm/h]"
    plt_title = provide_default(plot_dict, "plot_title", default="")
    ylim = provide_default(plot_dict, "ylim", default=[data_min, data_max])
    fs_title = provide_default(plot_dict, "fs_axistitle", default=16)
    fs_label = provide_default(plot_dict, "fs_axislabel", default=14)
    leg_str = provide_default(plot_dict, "legend", required=True)
    plot_file = provide_default(plot_dict, "plot_file", default=os.path.join(os.getcwd(), "plots",
                                                                             "mean_precipitation_leadtime.png"))
    lw = provide_default(plot_dict, "lw", default=2.)
    col = provide_default(plot_dict, "colour", default="red")

    # plot the data
    ax.plot(np.arange(nhours), mean_precip_davg, lw=lw, c=col, label=leg_str)
    ax.fill_between(np.arange(nhours), mean_precip_q1, mean_precip_q2, facecolor=col, alpha=0.25)

    # modify appearance
    ax.set_title(plt_title, fontsize=fs_title)
    ax.set_xlabel(xtitle, fontsize=fs_title)
    ax.set_ylabel(ytitle, fontsize=fs_title)
    ax.set_xticks(np.arange(nhours))
    ax.set_xticklabels(["{0:d}".format(hh) for hh in daytimes])
    ax.tick_params(axis='both', which='major', labelsize=fs_label)

    ax.set_ylim(*ylim)
    ax.legend([leg_str], prop={'size': fs_label})

    # save plot
    print("%{0}: Save plot to file '{1}'".format(method, plot_file))
    fig.savefig(plot_file)

    return fig, ax


def create_mapplot(data: xr.DataArray, init_hour: int, plot_dict: dict = {}):
    """
    Plot a colormap of data on a PlateCarrer. The borders of the German states are plotted as well.
    :param data: data-array with coordinates ["forecast_hour", "Lat", "Long"] where the former must be one element only.
    :param init_hour: the initialization hour of the model run.
    :param plot_dict: dictionary to control x-/y-axis title etc.
    """
    method = create_mapplot.__name__

    # get coordinate data
    try:
        lat, lon = data["Lat"].values, data["Long"].values
        if init_hour is not None:
            fcst_hour = data["forecast_hour.hour"].values[0],
            fcst_hour = (init_hour + fcst_hour[0]) % 24
    except Exception as err:
        print("Failed to retrieve coordinates from data.".format(method))
        raise err
    # construct array for edges of grid points
    dy, dx = np.round((lat[1] - lat[0]), 4), np.round((lon[1] - lon[0]), 4)
    lat_e, lon_e = np.arange(lat[0] - dy / 2, lat[-1] + dy, dy), np.arange(lon[0] - dx / 2, lon[-1] + dx, dx)

    fs_title = provide_default(plot_dict, "fs_axistitle", default=16)
    fs_label = provide_default(plot_dict, "fs_axislabel", default=14)
    title = provide_default(plot_dict, "title", "data")
    if init_hour is not None:
        title = "{0}, {1:02d} UTC".format(title, fcst_hour)
    levels = provide_default(plot_dict, "levels",
                             [0., 0.01, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1., 1.25, 1.5,
                              2.])
    extent = provide_default(plot_dict, "plot_extent", [5.75, 9.25, 49.75, 52.75])
    colmap = provide_default(plot_dict, "col_map", default="seismic_r")
    plot_file = provide_default(plot_dict, "plot_file", default=os.path.join(os.getcwd(), "plots", "mapdata.png"))

    # get colormap
    cmap_temp, norm_temp, lvl = get_colormap(levels, cmap_name=colmap, fracs=[0.5, 1.])
    # create plot object
    fig, ax = plt.subplots(1, figsize=(9, 6), subplot_kw={"projection": ccrs.PlateCarree()})

    # perform plotting
    data = ax.pcolormesh(lon_e, lat_e, np.squeeze(data.values), cmap=cmap_temp, norm=norm_temp)

    # add nice coast- and borderlines
    ax.coastlines(linewidth=2.5)
    ax.add_feature(cfeature.BORDERS, linewidth=2.5)
    # add borderlines for German states
    fname = os.path.join(os.getcwd(), "shp/vg2500_geo84/vg2500_bld.shp")
    shp_ger_states = list(shpreader.Reader(fname).geometries())
    ax.add_geometries(shp_ger_states, ccrs.PlateCarree(), edgecolor="black", facecolor="none",
                      linewidth=2.5)

    # adjust extent and ticks as well as axis-label
    ax.set_xticks(np.arange(0., 360. + 0.1, 0.5))  # ,crs=projection_crs)
    ax.set_yticks(np.arange(-90., 90. + 0.1, 0.5))  # ,crs=projection_crs)

    ax.set_extent(extent)
    ax.minorticks_on()
    ax.tick_params(axis="both", which="both", direction="out", labelsize=fs_label)

    ax.set_xlabel("Longitude [°E]", fontsize=fs_title)
    ax.set_ylabel("Latitude [°N]", fontsize=fs_title)

    ax.set_title(title, size=fs_title)

    # add colorbar
    cax = fig.add_axes([0.85, 0.25, 0.02, 0.5])
    cbar = fig.colorbar(data, cax=cax, orientation="vertical", ticks=lvl[1::2])
    cbar.ax.tick_params(labelsize=fs_label)

    # save plot
    print("%{0}: Save plot to file '{1}'".format(method, plot_file))
    fig.savefig(plot_file)

    return fig, ax


def get_colormap(levels, cmap_name: str = None, fracs: List = (0., 1.), name: str = "my_colmap"):
    """
    Get a nice colormap for plotting topographic height
    :param levels: level boundaries
    :param cmap_name: name of colormap to be used from matplotlib
    :param fracs: list with start and end fraction of colors from colormap to construct customized color map
    :param name: name of the customized color map
    :return cmap: colormap-object
    :return norm: normalization object corresponding to colormap and levels
    """
    bounds = np.asarray(levels)

    nbounds = len(bounds)

    if cmap_name is None:
        cmap_name = "seismic_r"

    cmap_all = plt.get_cmap(cmap_name)
    col_obj = cmap_all(np.linspace(fracs[0], fracs[1], nbounds))

    # create colormap and corresponding norm
    cmap = mpl.colors.ListedColormap(col_obj, name)
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    return cmap, norm, bounds
