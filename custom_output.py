# Functions for creating custom tables and figures
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

"""Functions for creating custom tables and figures.
"""

import numpy as np
import matplotlib.pyplot as plt

from parameters import INPUT_MODE
from consts import INPUT_MODE_TEXT

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def stacked_bar(df, var, group, outfile):
    """Create and save a stacked bar chart with bins 0, 1, ..., 30."""
    df = df[df[var].notna()]
    groups = df[group].unique()
    for_hist = []
    for val in groups:
        for_hist.append(df[ df[group] == val][var])
    plt.hist(for_hist, histtype='barstacked', bins=np.linspace(0, 30, 31),
             rwidth=.90, label=groups)
    plt.legend()
    plt.savefig(outfile)

def create_all_custom_figures(df_cards):
    df = df_cards[ df_cards.c_type != 0 ]
    # TODO: remove condition when `due_days` implemented for INPUT_MODE_SQLITE
    if INPUT_MODE == INPUT_MODE_TEXT:
        stacked_bar(df, var='due_days', group='c_CardType',
                    outfile='output/hist_due_num.png')

    #etc...
    #df.hist(column = 'c_ivl')
    #plt.hist(df.due_days, bins=np.linspace(0, 30, 31), rwidth=.90)
