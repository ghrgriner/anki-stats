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
import math
import time
import json
#from typing import NewType

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

#------------------------------------------------------------------------------
# Parameters (for modification by user)
#------------------------------------------------------------------------------
CARDS_INPUT_FILE = 'input/cards.csv'
# Path to optional input file if user wants to use additional fields export
# from the browser (see corresponding export program).
CARDS_BROWSER_INPUT_FILE = None
pd.set_option('display.max_rows',500)

#------------------------------------------------------------------------------
# Constants (do not require user modification)
#------------------------------------------------------------------------------
# seconds in a day
SECS_IN_DAY = 24 * 60 * 60

# Queue types
# use same const names and values as pylib/anki/consts.py
#CardQueue = NewType('CardQueue', int)
QUEUE_TYPE_MANUALLY_BURIED = -3
QUEUE_TYPE_SIBLING_BURIED = -2
QUEUE_TYPE_SUSPENDED = -1
QUEUE_TYPE_NEW = 0
QUEUE_TYPE_LRN = 1
QUEUE_TYPE_REV = 2
QUEUE_TYPE_DAY_LEARN_RELEARN = 3
QUEUE_TYPE_PREVIEW = 4

# Card types
#CardType = NewType('CardType', int)
CARD_TYPE_NEW = 0
CARD_TYPE_LRN = 1
CARD_TYPE_REV = 2
CARD_TYPE_RELEARNING = 3

# Review kinds
REVLOG_LRN = 0
REVLOG_REV = 1
REVLOG_RELRN = 2
REVLOG_FILT = 3    # called REVLOG_CRAM in repo
# repo has only REVLOG_RESCHED = 4 in pylib/anki/consts.py. Will wait and see
# how these are eventually defined in consts.py.
# TODO (future): update when consts.py is updated per the above
REVLOG_MANUAL = 4
REVLOG_RESCHED = 5

# Numbers in the labels are to order the labels to match the order the
# categories appear in the `Stats` window. They are not meant to equal the
# value of the 'enum'.
REVLOG_LABELS = {
        REVLOG_LRN:     '1. Learning',
        REVLOG_REV:     '2. Reviewing',
        REVLOG_RELRN:   '3. Relearning',
        REVLOG_FILT:    '4. Filtered',
        REVLOG_MANUAL:  'Manual',
        REVLOG_RESCHED: 'Rescheduled',
        }

# Review kinds
REVLOG_SUBCAT1_LRN = 1
REVLOG_SUBCAT1_YOUNG = 2
REVLOG_SUBCAT1_MATURE = 3
REVLOG_SUBCAT1_OTHER = 9

REVLOG_SUBCAT1_LABELS = {
        REVLOG_SUBCAT1_LRN :   '1. Learning (+ Filtered + Relearning)',
        REVLOG_SUBCAT1_YOUNG:  '2. Young',
        REVLOG_SUBCAT1_MATURE: '3. Mature',
        REVLOG_SUBCAT1_OTHER:  'Other',
        }

# REVLOG_SUBCAT2_ has same values as REVLOG_, except REVLOG_REV is split into
# REVLOG_SUBCAT2_YOUNG and REVLOG_SUBCAT2_MATURE
REVLOG_SUBCAT2_LRN = 0
REVLOG_SUBCAT2_RELRN = 2
REVLOG_SUBCAT2_FILT = 3
REVLOG_SUBCAT2_YOUNG = 4
REVLOG_SUBCAT2_MATURE = 5

REVLOG_SUBCAT2_LABELS = {
        REVLOG_SUBCAT2_FILT:   '1. Filtered',
        REVLOG_SUBCAT2_LRN:    '2. Learning',
        REVLOG_SUBCAT2_RELRN:  '3. Relearning',
        REVLOG_SUBCAT2_YOUNG:  '4. Young',
        REVLOG_SUBCAT2_MATURE: '5. Mature',
        }

TYPE_AND_QUEUE_LABELS = {
        0: '1. New',
        1: '2. Learning',
        3: '3. Relearning',
        5: '4. Young',
        2: '5. Mature',
        -1: '6. Suspended',
        -3: '7. Buried',
        }

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

def get_next_day_start():
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

def get_hour_from_secs(x):
    """Return local hour from seconds in epoch time."""
    return math.floor(((float(x) - offset) / 3600) % 24)

def get_local_offset():
    """Return local timezone offset."""
    if time.localtime().tm_isdst:
        return time.altzone
    else:
        return time.timezone

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

#------------------------------------------------------------------------------
# 1a. Read cards where fields were manually selected (because fields like the
#   review history are not available through the browser).
#------------------------------------------------------------------------------
#rows_to_keep = [0,2]
df_cards_m = pd.read_csv(CARDS_INPUT_FILE, sep='\t', quotechar='"',
                         index_col=False,
                         dtype={'c_nid': str, 'revlog_entries':str,
                                'col_TodayDaysElapsed': int, 'c_due': np.int32,
                                'c_difficulty': float, 'c_stability': float,
                                'c_id': int, 'csd_fsrs_retrievability':float})

rollover_hour=int(df_cards_m.at[0, 'col_RolloverHour'])
next_day_start = get_next_day_start()

df_cards_m['added_millis'] = df_cards_m.c_id
df_cards_m.set_index(['c_id'], verify_integrity=True, inplace=True)
df_cards_m['type_and_queue'] = np.where(df_cards_m.c_queue<0,
        df_cards_m.c_queue,
        np.where(  (df_cards_m.c_ivl < 21)
                 & (df_cards_m.c_type == CARD_TYPE_REV),
                 5, df_cards_m.c_type))
df_cards_m['type_and_queue_label'] = df_cards_m.type_and_queue.map(
        lambda x: TYPE_AND_QUEUE_LABELS[x])
df_cards_m['due_date'] = df_cards_m.c_due.map(datetime.datetime.fromtimestamp)
df_cards_m['odue_date'] = df_cards_m.c_odue.map(
     datetime.datetime.fromtimestamp)
df_cards_m['which_due'] = np.where(df_cards_m.c_odid != 0,
     df_cards_m.odue_date,
     df_cards_m.due_date)
df_cards_m['due_in_unix_epoch'] = df_cards_m.which_due.map(
        lambda x: x.timestamp() > 1000000000 if not pd.isnull(x) else False)
df_cards_m['due_days'] = np.where(df_cards_m.due_in_unix_epoch,
     ((df_cards_m.which_due
         - next_day_start).dt.total_seconds().map(get_days_round_to_zero)),
     np.where(df_cards_m.c_odid == 0,
              df_cards_m.c_due - df_cards_m.col_TodayDaysElapsed,
              df_cards_m.c_odue - df_cards_m.col_TodayDaysElapsed))
df_cards_m['added_days'] = ((
    (df_cards_m.added_millis / 1000).map(datetime.datetime.fromtimestamp)
         - next_day_start).dt.total_seconds() / SECS_IN_DAY).map(math.ceil)
df_cards_m['stability_rounded'] = df_cards_m.c_stability.map(round_away)
df_cards_m['bin_retr'] = df_cards_m.csd_fsrs_retrievability.map(
    lambda x: np.nan if math.isnan(x) else (100*x // 5))
df_cards_m['bin_retr_label'] = df_cards_m.bin_retr.map(bin_label_from_index)
df_cards_m['ease_label'] = df_cards_m.c_factor.map(make_ease_bin)
df_cards_m['scaled_difficulty'] = 100*(df_cards_m.c_difficulty - 1) / 9
df_cards_m['diff_bin_label'] = df_cards_m.scaled_difficulty.map(make_diff_bin)

# we could also get the difficulty and stability ourselves from the JSON string
# in the card.data field
df_cards_m['db_difficulty'] = df_cards_m.c_Data.map(
        lambda x: float(json.loads(x).get('d', np.nan)))
df_cards_m['db_stability'] = df_cards_m.c_Data.map(
        lambda x: float(json.loads(x).get('s', np.nan)))
#print(df_cards_m[['db_difficulty','c_difficulty']][
#    abs(df_cards_m.db_difficulty - df_cards_m.c_difficulty) > 0 ])
#print(df_cards_m[['db_stability','c_stability']][
#    abs(df_cards_m.db_stability - df_cards_m.c_stability) > 0 ])

#------------------------------------------------------------------------------
# 1b. Make a data frame containing the review information from the
# revlog_entries column (records separated by '-----', fields separated by
# '#').
#------------------------------------------------------------------------------
offset = get_local_offset()

df_reviews = pd.DataFrame(df_cards_m.revlog_entries.map(strip_last5).str.split(
                 '-----', expand=True).stack(), columns=['revlog_entries2'])
df_reviews[['date_millis', 'review_kind', 'ease', 'ivl', 'lastivl',
            'taken_millis', 'factor']
          ] = df_reviews.revlog_entries2.str.split('#', expand=True)
df_reviews.index.set_names(['c_id','seq'], inplace=True)

df_reviews['factor'] = df_reviews.factor.map(lambda x: int(x) if x else np.nan)
df_reviews['ease'] = df_reviews.ease.map(lambda x: int(x) if x else np.nan)
df_reviews['date_secs'] = df_reviews.date_millis.map(lambda x: float(x)/1000)
df_reviews['taken'] = df_reviews.taken_millis.map(lambda x: float(x)/1000)
df_reviews = df_reviews.astype({'lastivl': int, 'ivl': int,
                                'review_kind': int, 'taken': float})
df_reviews.drop(columns=['ivl'], inplace=True)
df_reviews['review_hr'] = df_reviews.date_secs.map(get_hour_from_secs)

df_reviews['review_datetime'] = df_reviews.date_secs.map(
      datetime.datetime.fromtimestamp)
df_reviews['review_kind_subcat1'] = np.where(
      df_reviews.review_kind.isin([REVLOG_LRN, REVLOG_RELRN, REVLOG_FILT]),
      REVLOG_SUBCAT1_LRN,
      np.where(df_reviews.review_kind == REVLOG_REV,
               np.where(df_reviews.lastivl < 21,
                        REVLOG_SUBCAT1_YOUNG,
                        REVLOG_SUBCAT1_MATURE),
               REVLOG_SUBCAT1_OTHER))
df_reviews['review_kind_subcat1_label'] = df_reviews.review_kind_subcat1.map(
      lambda x: REVLOG_SUBCAT1_LABELS[x])

df_reviews['review_kind_subcat2'] = np.where(
      df_reviews.review_kind == REVLOG_REV,
      np.where(df_reviews.lastivl < 21,
               REVLOG_SUBCAT2_YOUNG, REVLOG_SUBCAT2_MATURE),
      df_reviews.review_kind)
df_reviews['review_kind_subcat2_label'] = df_reviews.review_kind_subcat2.map(
      lambda x: REVLOG_SUBCAT2_LABELS[x])
df_reviews['taken_hrs'] = df_reviews.taken / (60*60)
df_reviews['review_date_adj'] = (df_reviews.review_datetime
                                 - datetime.timedelta(hours = rollover_hour)
                                ).dt.date
df_reviews['review_relative_days'] = (
          (df_reviews.review_datetime - next_day_start).dt.total_seconds().map(
          get_days_round_to_zero))
df_reviews['review_kind_label'] = df_reviews.review_kind.map(
                                  lambda x: REVLOG_LABELS[x])
df_reviews['retention_pop'] = (
        (df_reviews.ease > 0 )
     & ((df_reviews.review_kind != REVLOG_FILT) | (df_reviews.factor != 0))
     & ((df_reviews.review_kind == REVLOG_REV) | (df_reviews.lastivl <= -86400)
        | (df_reviews.lastivl >= 1))
                              )
# True / False / None
df_reviews['correct_answer'] = (np.where(df_reviews.ease == 0,
                                         None, (df_reviews.ease > 1)))
#df_reviews['correct'] = (np.where(df_reviews.retention_pop,
#                                  (df_reviews.ease > 1).astype(int), np.nan))

#------------------------------------------------------------------------------
# 1c. Read card file that was exported from the browser. This is needed because
#   things like card difficulty, stability, etc...  are not (I think) are not
#   stored in the database directly.
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

# This might not match the `Stats` window exactly. See Limitations section of
# the repository README.
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
stacked_bar(df, var='due_days', group='c_CardType',
            outfile='output/hist_due_num.png')

#etc...
#df.hist(column = 'c_ivl')
#plt.hist(df.due_days, bins=np.linspace(0, 30, 31), rwidth=.90)
