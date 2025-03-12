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
#from other_functions import freq

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

def create_all_custom_figures(df_cards: pd.DataFrame) -> None:
    df = df_cards[ df_cards.c_type != 0 ]
    stacked_bar(df, var='due_days', group='c_CardType',
                outfile='output/hist_due_num.png')

    # Here, we show how to merge notes that are exported by the companion
    # exporter. We have renamed the output notes file (default name is:
    # [NoteType]___[NoteTypeId].csv) to notes.csv. 'nid' will always be
    # present, as this is from the Anki database. The field `n_exprs` is
    # the field in our notes that we want to merge. Multiple merges may
    # be required if the cards data frame contains more than one type of
    # note.

    #df_notes = pd.read_csv('input/notes.csv', sep='\t', quotechar='"',
    #                 index_col=False)
    #df_cards = df_cards.merge(df_notes[['nid','n_exprs']], how='left',
    #              left_on='c_nid', right_on='nid')
    #freq(df_cards, 'n_exprs', title='Number of expressions', dropna=False)

    #etc...
    #df.hist(column = 'c_ivl')
    #plt.hist(df.due_days, bins=np.linspace(0, 30, 31), rwidth=.90)

