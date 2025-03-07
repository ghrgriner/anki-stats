# Python code to generate statistics similar to those in Anki
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

"""Python code to generate statistics similar to those in Anki v25.02.

The aim is to show at a high-level how to generate the statistics provided
in the Anki Statistics window outside of the Anki application using an export
file that is one record per card. This program does not generate every value
found in the Anki Statistics window. However, for every report it provides the
variables used to define the analysis population as well as the outcome
variable analyzed in the figure/text (if applicable).

The input file should be tab-delimited with '"' as the quote character and
should contain at least the following columns:
   [`c_type`, `c_due`, `c_odue`, `c_odid`, `c_queue`, `c_ivl`, `c_nid`,
    `c_id`, `c_stability`, `c_difficulty`, `csd_fsrs_retrievability`,
    `c_factor`, `c_CardType`, `col_TodayDaysElapsed, `c_Data`,
    `revlog_entries`, `col_RolloverHour`],
where:
  - `c_[var]` (var lowercase) contains the Python `card.var` variable, or,
    in the case of [var] = `difficulty` and `stability`, the Python
    `card.memory_state.[var]` variable.
  - `csd_fsrs_retrievability` contains the FSRS retrievability from
     mw.col.card_stats_data(card.id).fsrs_retrievability
  - `c_CardType` is the card type from `card.template()['name']`
  - `c_Data` is the card.data field from the database
  - `col_TodayDaysElapsed` is the number of days from the collection start
    until today (from `mw.col.sched.today`).
  - `col_RolloverHour` is the hour at which a new day is defined to start
     (from `mw.col.conf.get("rollover", 4)). This should be the same on all
     records, although it isn't checked.
  - `revlog_entries`: is a single string with all the entries from the `revlog`
    table for this card, with '-----' separating each entry and the fields
    within each entry delimited by '#'. The included fields are:
        id, type, ease, ivl, lastivl, time, factor.
"""

import csv
import datetime
#from typing import NewType

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import db
from consts import (
    INPUT_MODE_TEXT, INPUT_MODE_SQLITE,
    QUEUE_TYPE_MANUALLY_BURIED, QUEUE_TYPE_SIBLING_BURIED,
    QUEUE_TYPE_SUSPENDED,
    CARD_TYPE_NEW, CARD_TYPE_REV, CARD_TYPE_RELEARNING,
    REVLOG_FILT, REVLOG_MANUAL,
    REVLOG_RESCHED,
    )
from other_functions import print_time, freq
from prepare_data import create_cards, create_reviews

#------------------------------------------------------------------------------
# Parameters (for modification by user)
#------------------------------------------------------------------------------
INPUT_FILE = 'input/cards.csv'

# We recommend using INPUT_MODE_TEXT. If INPUT_MODE_SQLITE is used, the
# INPUT_FILE must be the path to a collection.anki2 file. We only provide a
# connection function in `db.py` that is meant to open the database read-only,
# but nevertheless, you should not attempt to write to the Anki database as
# this can easily corrupt the collection. Therefore, only use INPUT_MODE_SQLITE# if you have reviewed the code in this package and are satisfied with the
# database operations being performed.
INPUT_MODE = INPUT_MODE_TEXT

# Only used when INPUT_MODE_SQLITE to filter the cards (if desired), since all
# cards in collection retrieved from database
DECK_NAME = None

# Path to optional input file if user wants to use additional fields export
# from the browser (see corresponding export program).
CARDS_BROWSER_INPUT_FILE = None
pd.set_option('display.max_rows',500)

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def print_retention_row(desc, start_day, end_day):
    """Print a row of the retention table."""
    df2_ = df_reviews[ df_reviews.retention_pop
                     & (df_reviews.review_relative_days <= end_day)]
    if start_day is not None:
        df_ = df2_[(df2_.review_relative_days >= start_day)]
    else:
        df_ = df2_

    def get_pct(subset=None):
        if subset is not None:
            df3_ = df_[subset]
        else:
            df3_ = df_
        den = df3_.correct_answer.count()
        if den == 0:
            return 'N/A'
        else:
            pct_series = (df3_.correct_answer.value_counts()/den)*100
            try:
                pct = pct_series.at[True]
            except KeyError:
                return '  0   '
            return f'{pct:6.1f}%'

    total_pct = get_pct()
    young_pct = get_pct(df_.lastivl < 21)
    mature_pct = get_pct(~(df_.lastivl < 21))
    print(f'{desc:<11}{young_pct:>10}{mature_pct:>10}{total_pct:>10}'
          f'{len(df_):>10}')
#------------------------------------------------------------------------------
# End Functions
#------------------------------------------------------------------------------

if INPUT_MODE == INPUT_MODE_SQLITE: db.connect_readonly(INPUT_FILE)

#------------------------------------------------------------------------------
# 1a. Read cards: this is either the export file where fields were manually
# selected or it will read from the SQLite database.
#------------------------------------------------------------------------------
df_cards_m = create_cards(INPUT_FILE, INPUT_MODE)

#------------------------------------------------------------------------------
# 1b. Filter by deck name, if requested (INPUT_MODE_SQLITE only)
#------------------------------------------------------------------------------
if DECK_NAME is not None and INPUT_MODE == INPUT_MODE_SQLITE:
    df_decks = db.read_sql_query('select * from decks')
    deck_id = df_decks.loc[df_decks.name == DECK_NAME, 'id'].values[0]
    df_cards_m = df_cards_m[  (df_cards_m.c_did == deck_id)
                            | (df_cards_m.c_odid == deck_id) ]

#------------------------------------------------------------------------------
# 1c. Get reviews either from df_cards_m.revlog_entries or by querying the
# SQLite database.
#------------------------------------------------------------------------------
df_reviews = create_reviews(INPUT_MODE, df_cards_m)
if INPUT_MODE == INPUT_MODE_SQLITE: db.close()

#------------------------------------------------------------------------------
# 1c. Read card file that was exported from the browser, if the user decided
# to include one.
#------------------------------------------------------------------------------
if CARDS_BROWSER_INPUT_FILE is not None:
    df_cards_b = pd.read_csv(CARDS_BROWSER_INPUT_FILE, sep='\t',
                       quoting=csv.QUOTE_NONE, skiprows=(1), index_col=False,
                       dtype={'Difficulty': str, 'Ease': str})
    df_cards_b.set_index(['cid'], verify_integrity=True, inplace=True)

#------------------------------------------------------------------------------
# 2. Merge above sets as needed
#------------------------------------------------------------------------------
if CARDS_BROWSER_INPUT_FILE is not None:
    df_cards = df_cards_m.merge(df_cards_b, how='left', left_index=True,
                                right_index=True)
else:
    df_cards = df_cards_m
df_r_and_c = df_cards.merge(df_reviews, how='left', on='c_id')

#------------------------------------------------------------------------------
# 3. Create tables matching the text/tables/figures from the Anki `Stats`
# window.
#------------------------------------------------------------------------------
freq(df_reviews, 'review_kind_label', percent=True,
     title='Table 1a: Today',
     where=(  (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)
            & (df_reviews.review_relative_days == 0)))

freq(df_reviews, 'correct_answer', percent=True,
     title='Table 1b: Today (all cards)',
     where=(  (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)
            & (df_reviews.review_relative_days == 0)))

freq(df_reviews, 'correct_answer', percent=True,
     title='Table 1c: Today (mature cards)',
     where=(  (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)
            & (df_reviews.review_relative_days == 0)
            & (df_reviews.lastivl >= 21)))

# TODO: due_days not yet calculated for INPUT_MODE_SQLITE
if INPUT_MODE == INPUT_MODE_TEXT:
    freq(df_cards_m, 'due_days', percent=True,
         title='Table 2: Future Due',
         where=(   (df_cards_m.due_days >= 0)
                 & (df_cards_m.due_days <= 30)
                 & (df_cards_m.c_type != CARD_TYPE_NEW)
                 & (df_cards_m.c_queue != QUEUE_TYPE_SUSPENDED)
                 & ~( ( (df_cards_m.c_queue == QUEUE_TYPE_SIBLING_BURIED)
                      | (df_cards_m.c_queue == QUEUE_TYPE_MANUALLY_BURIED))
                     & (df_cards_m.due_days <= 0))))

freq(df_reviews, 'review_date_adj',
     title='Table 3: Calendar (current year to date)',
     where=((df_reviews.review_date_adj
                >= datetime.date(datetime.date.today().year, 1, 1))
            & (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)
            ))

freq(df_reviews, 'review_relative_days',
     title='Table 4.1: Reviews (counts)',
     where=(  (df_reviews.review_relative_days >= -30)
            & (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)))
#df_prob.to_csv("reviews.txt", sep='\t', quoting=csv.QUOTE_NONE)

freq(df_reviews, 'review_relative_days',
     title='Table 4.2: Reviews (time - overall)',
     weight='taken_hrs', format_val=print_time,
     where=(  (df_reviews.review_relative_days >= -30)
            & (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)))

freq(df_reviews, ['review_relative_days', 'review_kind_subcat2_label'],
     title='Table 4.3: Reviews (time - by type)',
     weight='taken_hrs', format_val=print_time,
     where=(  (df_reviews.review_relative_days >= -30)
            & (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)))

freq(df_cards_m, 'type_and_queue_label', percent=True,
     title='Table 5: Card Counts')

# TODO: Anki `running total` percentage in 'onHover' seems wrong. Research and
# report bug.
freq(df_cards, 'c_ivl',
     title='Table 6: Review Intervals', percent=True,
     where=( (  (df_cards.c_type == CARD_TYPE_REV)
              | (df_cards.c_type == CARD_TYPE_RELEARNING)))
            & (df_cards.c_ivl <= 31))

freq(df_cards_m, ['ease_label'],
     title='Table 7: Card Ease (non-FSRS decks only)',
     where=( (  (df_cards.c_type == CARD_TYPE_REV)
              | (df_cards.c_type == CARD_TYPE_RELEARNING))))

# TODO: Anki `running total` percentage in 'onHover' seems wrong. Research and
# report bug.
freq(df_cards_m, ['stability_rounded'],
     title='Table 8: Card Stability (FSRS decks only)',
     where=df_cards_m.stability_rounded < 31)

freq(df_cards_m, ['diff_bin_label'],
     title='Table 9: Card Difficulty (FSRS desks only)',
     where=~pd.isnull(df_cards.scaled_difficulty))
     #where=(df_cards_m.diff_bin_label != ''))

# When INPUT_MODE_TEXT, this might not match the `Stats` window exactly.
# See Limitations section of the repository README.
# TODO: retrievability not yet calculated for INPUT_MODE_SQLITE
if INPUT_MODE == INPUT_MODE_TEXT:
    freq(df_cards, 'bin_retr_label',
        title='Table 10: Card Retrievability (FSRS desks only)',
        where=~pd.isnull(df_cards.scaled_difficulty))

freq(df_r_and_c, ['review_hr'],
     title='Table 11: Hourly Breakdown (counts)',
     where=(  (df_r_and_c.review_kind != REVLOG_MANUAL)
            & (df_r_and_c.review_kind != REVLOG_RESCHED)
            & (df_r_and_c.review_kind != REVLOG_FILT)))

freq(df_reviews, ['review_kind_subcat1_label','ease'],
     title='Table 12: Answer Buttons',
     where=(  (df_reviews.review_kind != REVLOG_MANUAL)
            & (df_reviews.review_kind != REVLOG_RESCHED)
            & (df_reviews.ease >= 1)
            & (df_reviews.ease <= 4)))

freq(df_cards_m, ['added_days'],
     title='Table 13: Added',
     where=(df_cards_m.added_days >= -31) & (df_cards_m.added_days <= 0))

print('\nTable 14: True Retention')
print('                Young    Mature     Total     Count')
print_retention_row(desc='Today',      start_day=0,    end_day=0)
print_retention_row(desc='Yesterday',  start_day=-1,   end_day=-1)
print_retention_row(desc='Last week',  start_day=-6,   end_day=0)
print_retention_row(desc='Last month', start_day=-29,  end_day=0)
print_retention_row(desc='Last year',  start_day=-364, end_day=0)
print_retention_row(desc='All time',   start_day=None, end_day=0)

#------------------------------------------------------------------------------
# 4. Create custom figure(s) that are not available in the Anki `Stats` window.
# As an example, here we repeat Figure 4 stratified by card type.
#------------------------------------------------------------------------------

def stacked_bar(df_, var, group, outfile):
    """Create and save a stacked bar chart with bins 0, 1, ..., 30."""
    df_ = df_[ df[var].notna() ]
    groups = df_[group].unique()
    for_hist = []
    for val in groups:
        for_hist.append(df_[ df_[group] == val][var])
    plt.hist(for_hist, histtype='barstacked', bins=np.linspace(0, 30, 31),
             rwidth=.90, label=groups)
    plt.legend()
    plt.savefig(outfile)

df = df_cards[ df_cards.c_type != 0 ]
# TODO: remove condition when `due_days` implemented for INPUT_MODE_SQLITE
if INPUT_MODE == INPUT_MODE_TEXT:
    stacked_bar(df, var='due_days', group='c_CardType',
                outfile='output/hist_due_num.png')

#etc...
#df.hist(column = 'c_ivl')
#plt.hist(df.due_days, bins=np.linspace(0, 30, 31), rwidth=.90)
