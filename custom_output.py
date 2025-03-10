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
import pandas as pd
import matplotlib.pyplot as plt
from consts import INPUT_MODE_TEXT

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def stacked_bar(df: pd.DataFrame, var, group, outfile) -> None:
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

def create_all_custom_figures(df_cards: pd.DataFrame, input_mode) -> None:
    if input_mode == INPUT_MODE_TEXT:
        df = df_cards[ df_cards.c_type != 0 ]
        stacked_bar(df, var='due_days', group='c_CardType',
                    outfile='output/hist_due_num.png')

    #etc...
    #df.hist(column = 'c_ivl')
    #plt.hist(df.due_days, bins=np.linspace(0, 30, 31), rwidth=.90)

# Debugging
#def custom_listings(df_cards: pd.DataFrame) -> None:
#    df = pd.read_csv('input/cards.csv', sep='\t', quotechar='"',
#                        index_col=False,
#                        dtype={'c_nid': str, 'revlog_entries':str,
#                               'col_TodayDaysElapsed': int, 'c_due': np.int32,
#                                'c_difficulty': float, 'c_stability': float,
#                                'c_id': int, 'csd_fsrs_retrievability':float})
#    df.set_index(['c_id'], verify_integrity=True, inplace=True)
#
#    df_cards['csd_fsrs_retrievability'] = df.csd_fsrs_retrievability
#    freq(df_cards, ['days_since_last_review'])
#    print(df_cards[['days_since_last_review',
#                     'csd_fsrs_retrievability','fsrs_retrievability']])
