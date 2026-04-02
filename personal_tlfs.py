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
from statsmodels.nonparametric.smoothers_lowess import lowess
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

def custom_tlfs(df_cards: pd.DataFrame) -> None:
    #df = df_cards[ df_cards.c_type != 0 ]
    #stacked_bar(df, var='due_days', group='c_CardType',
    #            outfile='output/hist_due_num.png')

    # Here, we show how to merge notes that are exported by the companion
    # exporter. We have renamed the output notes file (default name is:
    # [NoteType]___[NoteTypeId].csv) to notes.csv. 'nid' will always be
    # present, as this is from the Anki database. The field `n_exprs` is
    # the field in our notes that we want to merge. Multiple merges may
    # be required if the cards data frame contains more than one type of
    # note.
    def n_tokens(x):
        ctr = 0
        for char in x:
            if char == ',': ctr = ctr + 1
        return ctr + 1

    def summarize(anal_var, group_var):
        round_dict = {'min': 1, 'max': 1, 'mean': 1}
        df_final = df_cards.groupby(group_var) \
            .agg({anal_var: ["size","count","min","mean","max"]})
        print(df_final)

    df_notes = pd.read_csv('input/notes.csv', sep='\t', quotechar='"',
                     index_col=False, dtype={'de1': 'str'}, keep_default_na=False)

    df_notes['n_de1'] = df_notes.de1.map(n_tokens)
    
    df_cards = df_cards.merge(df_notes[['nid','n_exprs','chapter','n_de1','part_of_speech']], how='left',
                  left_on='c_nid', right_on='nid')
    #freq(df_cards, 'n_exprs', title='Number of expressions', dropna=False)
    summarize('scaled_difficulty', group_var='chapter')
    summarize('scaled_difficulty', group_var='n_de1')
    summarize('scaled_difficulty', group_var='part_of_speech')
    quit()


    subset_df = df_cards[ (df_cards.chapter <= 70) 
                          & (df_cards.c_CardType.isin(['DEEN','ENDE']))
                          & ~pd.isnull(df_cards.scaled_difficulty)]
                        #.sample(n=200, random_state=2394239)
    subset_df.reset_index(inplace=True)
    subset_df.boxplot(column=anal_var, by='chapter')
    plt.savefig('output/difficulty_by_chapter_boxplot.png')
    plt.close()
    subset_df.boxplot(column=anal_var, by='n_exprs')
    plt.savefig('output/difficulty_by_n_exprs_boxplot.png')
    plt.close()

    l_df = pd.DataFrame(lowess(subset_df.scaled_difficulty, subset_df.chapter))
    l_df.rename({0: 'chapter', 1: 'scaled_difficulty'}, axis=1, inplace=True)
    #order = np.argsort(subset_df.chapter)
    #print(subset_df.chapter[order])
    #print(ys[order])
    fig, ax = plt.subplots(figsize=(6,4))
    colors = {'ENDE': 'blue', 'DEEN': 'red'}
    labels = {'ENDE': 'Linear A on front', 'DEEN': 'English on front'}
    print(subset_df.columns)
    for card_type, data in subset_df.groupby('c_CardType'):
        l_df = pd.DataFrame(lowess(data.scaled_difficulty, data.chapter))
        l_df.rename({0: 'chapter', 1: 'scaled_difficulty'}, axis=1, inplace=True)
        plt.plot(l_df.chapter, l_df.scaled_difficulty,
                 label=f'LOWESS {labels[card_type]}', color=colors[card_type])
        plt.scatter(data.chapter, data.scaled_difficulty, s=2,
                    label=f'Observations {labels[card_type]}', color=colors[card_type])
    ax.set(xlabel='Chapter', ylabel='Difficulty', ylim=[0, 100])
    #plt.scatter(subset_df.chapter, subset_df.scaled_difficulty, label='Observations')
    plt.legend(loc='lower center')
    plt.savefig('output/difficulty_by_chapter_loess.png')
    quit()

    #etc...
    #df.hist(column = 'c_ivl')
    #plt.hist(df.due_days, bins=np.linspace(0, 30, 31), rwidth=.90)

