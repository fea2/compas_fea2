
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.backends._core import MiscBase
from compas_fea2.backends._core import AmplitudeBase
from compas_fea2.backends._core import TemperaturesBase

# Author(s): Francesco Ranaudo (github.com/franaudo)


__all__ = [
    'Misc',
    'Amplitude',
    'Temperatures'
]


class Misc(MiscBase):

    """ Initialises base Misc object.

    Parameters
    ----------
    name : str
        Misc object name.

    Returns
    -------
    None

    """
    pass
    # def __init__(self, name):
    #     super(Misc, self).__init__(name)


class Amplitude(AmplitudeBase):

    """ Initialises an Amplitude object to act as a discretised function f(x).

    Parameters
    ----------
    name : str
        Amplitude object name.
    values : list
        Amplitude function value pairs [[x0, y0], [x1, y1], ..].

    Returns
    -------
    None

    """
    pass
    # def __init__(self, name, values):
    #     super(Amplitude, self).__init__(name, values)


class Temperatures(TemperaturesBase):

    """ Define nodal temperatures data.

    Parameters
    ----------
    name : str
        Temperature object name.
    file : str
        Path of nodal temperatures file to extract data from.
    values : list
        List of [[node, temperature, time], ...] data.
    tend : float
        End time in seconds to read data till.

    Returns
    -------
    None

    """
    pass
    # def __init__(self, name, file, values, tend):
    #     super(Temperatures, self).__init__(name, file, values, tend)