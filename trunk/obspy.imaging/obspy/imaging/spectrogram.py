# -*- coding: utf-8 -*-
#-------------------------------------------------------------------
# Filename: spectrogram.py
#  Purpose: Plotting spectrogram of Seismograms.
#   Author: Christian Sippl, Moritz Beyreuther
#    Email: sippl@geophysik.uni-muenchen.de
#
# Copyright (C) 2008-2010 Christian Sippl
#---------------------------------------------------------------------
"""
Plotting Spectrogram of Seismograms.


GNU General Public License (GPL)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
    
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
"""

from matplotlib import mlab
from matplotlib.colors import Normalize
from obspy.core.util import MATPLOTLIB_VERSION
import math as M
import matplotlib.pyplot as plt
import numpy as np


def nearestPow2(x):
    """
    Find power of two nearest to x

    >>> nearestPow2(3)
    2.0
    >>> nearestPow2(15)
    16.0

    :type x: Float
    :param x: Number
    :rtype: Int
    :return: Nearest power of 2 to x
    """
    a = M.pow(2, M.ceil(np.log2(x)))
    b = M.pow(2, M.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return a
    else:
        return b


def spectrogram(data, samp_rate, per_lap=0.9, wlen=None, log=False,
                outfile=None, format=None, axes=None, dbscale=False,
                mult=8.0, cmap=None, zorder=None, title=None, show=True,
                sphinx=False, clip=[0.0, 1.0]):
    """
    Computes and plots logarithmic spectrogram of the input data.
    
    :param data: Input data
    :type samp_rate: float
    :param samp_rate: Samplerate in Hz
    :type per_lap: float
    :param per_lap: Percentage of overlap of sliding window. (Ranging from 0 to 1)
            High overlaps take a long time to compute.
    :type wlen: int or float
    :param wlen: Window length for fft in seconds. If this parameter is too
                 small, the calculation will take forever.
    :type log: bool
    :param log: Logarithmic frequency axis if True, linear frequency axis
            otherwise
    :type outfile: String
    :param outfile: String for the filename of output file, if None
                    interactive plotting is activated.
    :type format: String
    :param format: Format of image to save
    :type axes: :class:`matplotlib.axes.Axes`
    :param axes: Plot into given axes, this deactivates the format and
                 outfile option
    :type dbscale: bool
    :param dbscale: If True 10 * log10 of color values is taken, if False
                    the sqrt is taken
    :type mult: float
    :param mult: Pad zeros to lengh mult * wlen. This will make the
                 spectrogram smoother. Available for matplotlib > 0.99.0
    :type cmap: :class:`matplotlib.colors.Colormap`
    :param cmap: Specify a custom colormap instance
    :type zorder: float
    :param zorder: Specify the zorder of the plot. Only of importance if other
            plots in the same axes are executed.
    :type title: String
    :param title: Set the plot title
    :type show: bool
    :param show: Do not call `plt.show()` at end of routine. That way,
            further modifications can be done to the figure before showing it.
    :type sphinx: bool
    :param sphinx: Internal flag used for API doc generation, default False
    :type clip: [float, float]
    :param clip: adjust colormap to clip at lower and/or upper end. The given
            percentages of the amplitude range (linear or logarithmic depending
            on option `dbscale`) are clipped.
    """
    # enforce float for samp_rate
    samp_rate = float(samp_rate)

    # set wlen from samp_rate if not specified otherwise
    if not wlen:
        wlen = samp_rate / 100.

    npts = len(data)
    # nfft needs to be an integer, otherwise a deprecation will be raised
    #XXX add condition for too many windows => calculation takes for ever
    nfft = int(nearestPow2(wlen * samp_rate))
    if nfft > npts:
        nfft = int(nearestPow2(npts / 8.0))

    if mult != None:
        mult = int(nearestPow2(mult))
        mult = mult * nfft
    nlap = int(nfft * float(per_lap))

    data = data - data.mean()
    end = npts / samp_rate

    # Here we call not plt.specgram as this already produces a plot
    # matplotlib.mlab.specgram should be faster as it computes only the
    # arrays
    # XXX mlab.specgram uses fft, would be better and faster use rfft
    if MATPLOTLIB_VERSION >= [0, 99, 0]:
        spectrogram, freq, time = mlab.specgram(data, Fs=samp_rate, NFFT=nfft,
                                              pad_to=mult, noverlap=nlap)
    else:
        spectrogram, freq, time = mlab.specgram(data, Fs=samp_rate,
                                                NFFT=nfft, noverlap=nlap)
    # db scale and remove zero/offset for amplitude
    if dbscale:
        spectrogram = 10 * np.log10(spectrogram[1:, :])
    else:
        spectrogram = np.sqrt(spectrogram[1:, :])
    freq = freq[1:]

    vmin, vmax = clip
    if vmin < 0 or vmax > 1 or vmin >= vmax:
        msg = "Invalid parameters for clip option."
        raise ValueError(msg)
    range = float(spectrogram.max() - spectrogram.min())
    vmin = spectrogram.min() + vmin * range
    vmax = spectrogram.min() + vmax * range
    norm = Normalize(vmin, vmax, clip=True)

    if not axes:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    else:
        ax = axes

    # calculate half bin width
    halfbin_time = (time[1] - time[0]) / 2.0
    halfbin_freq = (freq[1] - freq[0]) / 2.0

    if log:
        # pcolor expects one bin more at the right end
        freq = np.concatenate((freq, [freq[-1] + 2 * halfbin_freq]))
        time = np.concatenate((time, [time[-1] + 2 * halfbin_time]))
        # center bin
        time -= halfbin_time
        freq -= halfbin_freq
        # pcolormesh issue was fixed in matplotlib r5716 (2008-07-07)
        # inbetween tags 0.98.2 and 0.98.3
        # see:
        #  - http://matplotlib.svn.sourceforge.net/viewvc/...
        #    matplotlib?revision=5716&view=revision
        #  - http://matplotlib.sourceforge.net/_static/CHANGELOG
        if MATPLOTLIB_VERSION >= [0, 98, 3]:
            # Log scaling for frequency values (y-axis)
            ax.set_yscale('log')
            # Plot times
            ax.pcolormesh(time, freq, spectrogram, cmap=cmap, zorder=zorder,
                          norm=norm)
        else:
            X, Y = np.meshgrid(time, freq)
            ax.pcolor(X, Y, spectrogram, cmap=cmap, zorder=zorder, norm=norm)
            ax.semilogy()
    else:
        # this method is much much faster!
        spectrogram = np.flipud(spectrogram)
        # center bin
        extent = (time[0] - halfbin_time, time[-1] + halfbin_time, \
                  freq[0] - halfbin_freq, freq[-1] + halfbin_freq)
        ax.imshow(spectrogram, interpolation="nearest", extent=extent,
                  cmap=cmap, zorder=zorder)

    # set correct way of axis, whitespace before and after with window
    # length
    ax.axis('tight')
    ax.set_xlim(0, end)
    ax.grid(False)

    if axes:
        return ax

    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Frequency [Hz]')
    if title:
        ax.set_title(title)

    if not sphinx:
        # ignoring all NumPy warnings during plot
        temp = np.geterr()
        np.seterr(all='ignore')
        plt.draw()
        np.seterr(**temp)
    if outfile:
        if format:
            fig.savefig(outfile, format=format)
        else:
            fig.savefig(outfile)
    else:
        if show:
            plt.show()
    return fig
