# Other functions
# Copyright (C) 2025 Ray Griner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#------------------------------------------------------------------------------

"""Other functions.
"""

import datetime
import math
import time
import json

import numpy as np
import pandas as pd

from consts import SECS_IN_DAY

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def strip_last5(x):
    """Convert input to str and remove last five characters."""
    x = str(x)
    len_x = len(x)
    if len_x>5: return x[0:(len_x - 5)]

# bins are [x, x+5) and [95%, 100%]
#def make_bin(x):
#    if x in ['NaN','(new)']: return ''
#    val_int = x.replace('%','')
#    bin_num = math.floor(int(val_int) / 5)
#    if bin_num in [19, 20]: bin_label = '[95%, 100%]'
#    else: bin_label = f'[{5*(bin_num)}%, {5*(bin_num+1)}%)'
#    return bin_label

def print_time(val):
    """Print input time (in hours) as hours, minutes, or seconds."""
    if val > 1:
        return f'{val:.2f} hours'
    elif val * 60 > 1:
        return f'{(val*60):.2f} minutes'
    else:
        return f'{(val*3600):.2f} seconds'

def bin_label_from_index(val):
    """Given index of bin (0-19) or 20, return the bin label."""
    if np.isnan(val):
        return ''
    if val == 19 or val == 20:
        return '[95%, 100%]'
    else:
        return f'[{int(val*5)}%, {int(val+1)*5}%)'

def str_or_num_to_int_or_nan(val):
    if isinstance(val, str):
        if val:
            return int(val)
        else:
            return np.nan
    else:
        return int(val)

def freq(df_, var, title=None, where=None, percent=False,
         weight=None, format_val=None, dropna=True):
    """Print table giving frequencies or weighted sums."""
    if isinstance(var, str):
        row_vars = [var]
    else:
        row_vars = var

    print()

    if where is not None:
        df_ = df_[where]

    if weight is None:
        freq_ = df_[row_vars].value_counts(dropna=dropna).sort_index()
        freq_ = freq_.to_frame(name='Count')
        if percent:
            freq_['Percent'] = round(100 * freq_.Count
                                     / np.sum(freq_.Count), 1)
        freq_['Cum Count'] = freq_.Count.cumsum()
        if percent:
            freq_['Cum Percent'] = round(100 * freq_['Cum Count']
                                         / np.sum(freq_.Count), 1)
    else:
        vars_to_keep = row_vars.copy()
        vars_to_keep.append(weight)
        df_ = df_[vars_to_keep]
        freq_ = df_.groupby(row_vars, dropna=dropna).sum()

        if format_val is not None:
            freq_[weight] = freq_[weight].map(format_val)

    if title:
        print(title)
    print(f'{freq_}')

def get_days_round_to_zero(x):
    """Convert seconds to days, rounding towards zero."""
    if x < 0:
        return -1 * (-x // SECS_IN_DAY)
    else:
        return x // SECS_IN_DAY

def make_diff_bin(x):
    if not x:
        return ''
    else:
        if math.isnan(x):
            return ''
        bin_num = math.floor(x / 5)
        if bin_num in [19, 20]:
            return '[95%, 100%]'
        else:
            return f'[{5*(bin_num)}%, {5*(bin_num+1)}%)'

def make_ease_bin(x):
    if not x:
        return ''
    elif math.isnan(x):
        return ''
    else:
        ease = x // 10
        return f'[{10*(ease // 10)}%, {10*((ease // 10)+1)}%)'

# internet suggests default round in rust is round-to-even, but testing
# Anki suggests it is using round-away from zero. Default in Python is
# round-to-even, so a custom round function is written.
def round_away(x):
    """Round x away from zero."""
    if math.isnan(x):
        return x
    elif x < 0:
        raise ValueError('non-negative number expected')
    elif abs(x - np.round(x)) > .49999:
        return math.floor(x)+1
    else:
        return np.round(x)

def get_next_day_start(rollover_hour):
    """Return date/time of the next start day (i.e., today or tomorrow)."""
    if rollover_hour == 0:
        return (pd.Timestamp(datetime.date.today())
                + datetime.timedelta(days = 1, hours = rollover_hour))
    elif datetime.datetime.now().hour < rollover_hour:
        return (pd.Timestamp(datetime.date.today())
                + datetime.timedelta(days = 0, hours = rollover_hour))
    else:
        return (pd.Timestamp(datetime.date.today())
                + datetime.timedelta(days = 1, hours = rollover_hour))

def get_local_offset():
    """Return local timezone offset."""
    if time.localtime().tm_isdst:
        return time.altzone
    else:
        return time.timezone

def get_json_val(x, key):
    if not x:
        return np.nan
    else:
        return float(json.loads(x).get(key, np.nan))

