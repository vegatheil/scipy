"""

A collection of filters for timeseries

:author: Pierre GF Gerard-Marchant & Matt Knox
:contact: pierregm_at_uga_dot_edu - mattknox_ca_at_hotmail_dot_com
:version: $Id$
"""
__author__ = "Pierre GF Gerard-Marchant & Matt Knox ($Author$)"
__version__ = '1.0'
__revision__ = "$Revision$"
__date__     = '$Date$'

import numpy as N
from numpy import bool_, float_
narray = N.array

from scipy.signal import convolve, get_window

import maskedarray as MA
from maskedarray import MaskedArray, nomask, getmask, getmaskarray, masked
marray = MA.array


__all__ = ['expmave'
           'running_window', 'running_mean'           
           ]

#####---------------------------------------------------------------------------
#---- --- Moving average functions ---
#####---------------------------------------------------------------------------
def expmave(data, n, tol=1e-6):
    """Calculate the exponential moving average of a series.

:Parameters:
    - `data` (ndarray, MaskedArray) : data is a valid ndarray or MaskedArray
      or an instance of a subclass of these types. In particular, TimeSeries
      objects are valid here.
    - `n` (int) : time periods. Where the smoothing factor is 2/(n + 1)
    - `tol` (float, *[1e-6]*) : when `data` contains masked values, this
      parameter will determine what points in the result should be masked.
      Values in the result that would not be "significantly" impacted (as
      determined by this parameter) by the masked values are left unmasked.
"""
    if isinstance(data, MaskedArray):
        ismasked = (data._mask is not nomask)
    else:
        ismasked = False
    #
    k = 2./float(n + 1)
    def expmave_sub(a, b):
        return b + k * (a - b)
    #    
    if ismasked:
        data = data.filled(0)
    #
    result = N.frompyfunc(expmave_sub, 2, 1).accumulate(data).astype(data.dtype)
    if ismasked:
        _unmasked = N.logical_not(getmask(data)).astype(float_)
        marker = 1 - N.frompyfunc(expmave_sub, 2, 1).accumulate(_unmasked)
        result[marker > tol] = masked
    #
    return result

#...............................................................................
def running_window(data, window_type, window_size):
    """Applies a running window of type window_type and size window_size on the 
    data.
    
    Returns a (subclass of) MaskedArray. The k first and k last data are always 
    masked (with k=window_size//2). When data has a missing value at position i, 
    the result has missing values in the interval [i-k:i+k+1].
    
    
:Parameters:
    data : ndarray
        Data to process. The array should be at most 2D. On 2D arrays, the window
        is applied recursively on each column.
    window_type : string/tuple/float
        Window type (see Notes)
    window_size : integer
        The width of the window.
        
Notes
-----

The recognized window types are: boxcar, triang, blackman, hamming, hanning, 
bartlett, parzen, bohman, blackmanharris, nuttall, barthann, kaiser (needs beta), 
gaussian (needs std), general_gaussian (needs power, width), slepian (needs width).
If the window requires parameters, the window_type argument should be a tuple
with the first argument the string name of the window, and the next arguments 
the needed parameters. If window_type is a floating point number, it is interpreted 
as the beta parameter of the kaiser window.

Note also that only boxcar has been thoroughly tested.
    """
    #
    data = marray(data, copy=True, subok=True)
    if data._mask is nomask:
        data._mask = N.zeros(data.shape, bool_)
    window = get_window(window_type, window_size, fftbins=False)
    (n, k) = (len(data), window_size//2)
    #
    if data.ndim == 1:
        data._data.flat = convolve(data._data, window)[k:n+k] / float(window_size)
        data._mask[:] = ((convolve(getmaskarray(data), window) > 0)[k:n+k])
    elif data.ndim == 2:
        for i in range(data.shape[-1]):
            _data = data._data[:,i]
            _data.flat = convolve(_data, window)[k:n+k] / float(window_size)
            data._mask[:,i] = (convolve(data._mask[:,i], window) > 0)[k:n+k]
    else:
        raise ValueError, "Data should be at most 2D"
    data._mask[:k] = data._mask[-k:] = True
    return data

def running_mean(data, width):
    """Computes the running mean of size width on the data.
    
    Returns a (subclass of) MaskedArray. The k first and k last data are always 
    masked (with k=window_size//2). When data has a missing value at position i, 
    the result has missing values in the interval [i-k:i+k+1].
    
:Parameters:
    data : ndarray
        Data to process. The array should be at most 2D. On 2D arrays, the window
        is applied recursively on each column.
    window_size : integer
        The width of the window.    
    """
    return running_window(data, 'boxcar', width)

################################################################################
if __name__ == '__main__':
    from maskedarray.testutils import assert_equal, assert_almost_equal
    from timeseries import time_series, thisday
    
