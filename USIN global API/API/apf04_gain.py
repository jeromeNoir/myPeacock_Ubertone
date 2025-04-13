#!/usr/bin/env python
# -*- coding: UTF_8 -*-

# @copyright  this code is the property of Ubertone.
# You may use this code for your personal, informational, non-commercial purpose.
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Stéphane Fischer, Alexandre Schaeffer, Marie Burckbuchler

from math import pow

APF04_RECEPTION_CHAIN_CONSTANT_GAIN = 11.72 # dB (after DAC+LNA)
         # currently on hardware after 05/2021 the max value is 14.5 and depend on f0 (filter bandwidth)
APF04_GAIN_CODE_RATIO = 4.029E-2  # in the chain (DAC + LNA), where DAC (12bits-->4096, 3.3V) and gain LNA (50dB/V).

APF04_CODE_MAX_APPLIED = 1241
APF04_CODE_MAX_USER = 4095
APF04_CODE_MIN_USER = -4096
APF04_CODE_MIN_APPLIED = 50


def convert_dB_m2code(_gain_dB, _r_dvol):
    """Conversion of gain slope a1 (in dB) to code ca1.
        4 bits shift is used for precision reasons. The code is truncated in the available range.

    Args:
        _gain_dB(float): gain slope in dB/m
        _r_dvol(float): inter-volume size in m

    Returns:
        code (int)
    """
    code = int(round((16. * _gain_dB * _r_dvol) / APF04_GAIN_CODE_RATIO, 1))
    code = _truncate(code, APF04_CODE_MAX_USER, APF04_CODE_MIN_USER)
    return code


def convert_code2dB_m(_code, _r_dvol):
    """Conversion of any code ca1 to gain slope a1 (in dB)
        4 bits shift is used for precision reasons.

    Args:
        _code(int): gain code
        _r_dvol(float): inter-volume size in m

    Returns:
        gain slope in dB/m (float)
    """
    gain_dB = (APF04_GAIN_CODE_RATIO / (16. * _r_dvol)) * _code
    return gain_dB


def convert_dB2code(_gain_dB):
    """Conversion of gain (in dB) to code.
        The code is truncated in the available range.

    Args:
        _gain_dB(float): gain intercept in dB

    Returns:
        gain code (int)
    """
    code = int(round((_gain_dB - APF04_RECEPTION_CHAIN_CONSTANT_GAIN) / APF04_GAIN_CODE_RATIO, 1))
    code = _truncate(code, APF04_CODE_MAX_APPLIED, APF04_CODE_MIN_USER)
    return code


def convert_code2dB(_code):
    """Conversion of any code to a theoretical gain (in dB)

    Args:
        _code(int): gain code

    Returns:
        gain intercept in dB (float)
    """
    gain_dB = (_code * APF04_GAIN_CODE_RATIO) + APF04_RECEPTION_CHAIN_CONSTANT_GAIN
    return gain_dB


def _convert_code2dB_trunc(_code):
    """Conversion of code to the effective (truncated) gain (in dB) applied in a cell
    
    Args :
        _code (int) : gain code

    Returns :
        gain in dB applied in a cell
    """
    _code = _truncate(_code, APF04_CODE_MAX_APPLIED, APF04_CODE_MIN_APPLIED)
    gain_dB = convert_code2dB(_code)
    return gain_dB


def calc_gain(_n_vol, _gain_ca0, _gain_ca1, _gain_max_ca0, _gain_max_ca1):
    """Compute the table of the gains in dB applied to each cell of the profile

    Args:
        _n_vol(int): number of cells in the profile
        _gain_ca0(int): code of the gain intercept
        _gain_ca1(int): code of the gain slope
        _gain_max_ca0(int): code of the blind zone gain limit intercept
        _gain_max_ca1(int): code of the blind zone gain limit slope

    Returns:
        list of gains in dB to apply to each cell of the profile
    
    """
    tab_gain = []
    i = 0
    while i <= (_n_vol - 1):
        G = _convert_code2dB_trunc(_gain_ca0 + (i * _gain_ca1) / 16.)
        G_max = _convert_code2dB_trunc(_gain_max_ca0 + (i * _gain_max_ca1) / 16.)
        if (G >= G_max):
            tab_gain.append(pow(10, G_max / 20.))
        else:
            tab_gain.append(pow(10, G / 20.))
        i = i + 1
    return tab_gain


def _truncate(value, limit_max, limit_min):
    """Troncate value with min/max limit

    Args:
        value: value to troncate
        limit_max: max limit
        limit_min: min limit

    Returns:
        the truncated value
    """
    return max(min(value, limit_max), limit_min)
