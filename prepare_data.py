# Functions to create data frames containing cards and reviews.
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

"""Functions to create data frames containing cards and reviews.
"""

import datetime
import math
#from typing import NewType

import numpy as np
import pandas as pd

import db
from consts import (
    INPUT_MODE_TEXT, INPUT_MODE_SQLITE,
    CARD_TYPE_REV,
    REVLOG_LRN, REVLOG_REV, REVLOG_RELRN, REVLOG_FILT,
    REVLOG_LABELS,
    REVLOG_SUBCAT1_LRN, REVLOG_SUBCAT1_YOUNG, REVLOG_SUBCAT1_MATURE,
    REVLOG_SUBCAT1_OTHER, REVLOG_SUBCAT1_LABELS,
    REVLOG_SUBCAT2_YOUNG, REVLOG_SUBCAT2_MATURE, REVLOG_SUBCAT2_LABELS,
    SECS_IN_DAY,
    TYPE_AND_QUEUE_LABELS,
    )
from other_functions import (bin_label_from_index, get_days_round_to_zero,
    make_diff_bin, make_ease_bin, round_away, get_next_day_start,
    get_local_offset, strip_last5, get_json_val, str_or_num_to_int_or_nan)

#------------------------------------------------------------------------------
# Parameters (for modification by user)
#------------------------------------------------------------------------------
CARDS_INPUT_FILE = 'input/cards.csv'
# Path to optional input file if user wants to use additional fields export
# from the browser (see corresponding export program).
CARDS_BROWSER_INPUT_FILE = None
pd.set_option('display.max_rows',500)

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def get_hour_from_secs(x, offset):
    """Return local hour from seconds in epoch time."""
    return math.floor(((float(x) - offset) / 3600) % 24)

def get_rollover_from_cards(df):
    """Get rollover hour from first row and 'col_RolloverHour' col of df.
    """
    return int(df.iloc[0, df.columns.get_loc('col_RolloverHour')])

#------------------------------------------------------------------------------
# End Functions
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# 1a. Read cards where fields were manually selected (because fields like the
#   review history are not available through the browser).
#------------------------------------------------------------------------------
#rows_to_keep = [0,2]
def create_cards(input_file, input_mode):
    """Create data frame that is one record per card.
    """
    if input_mode == INPUT_MODE_TEXT:
        df = pd.read_csv(input_file, sep='\t', quotechar='"',
                         index_col=False,
                         dtype={'c_nid': str, 'revlog_entries':str,
                                'col_TodayDaysElapsed': int, 'c_due': np.int32,
                                'c_difficulty': float, 'c_stability': float,
                                'c_id': int, 'csd_fsrs_retrievability':float})
        rollover_hour = get_rollover_from_cards(df)
    else:
        df = db.read_sql_query('select * from cards')
        df_config = db.read_sql_query('select * from config')
        df_config.set_index(['KEY'], verify_integrity=True, inplace=True)
        rollover_hour = int(df_config.at['rollover','val'].decode('utf-8'))

        rename_dict = {}
        for col_name in df.columns:
            rename_dict[col_name] = 'c_' + col_name
        df.rename(rename_dict, axis=1, inplace=True)

        df['col_RolloverHour'] = rollover_hour

    next_day_start = get_next_day_start(rollover_hour)

    df['added_millis'] = df.c_id
    df.set_index(['c_id'], verify_integrity=True, inplace=True)
    df['type_and_queue'] = np.where(df.c_queue<0,
            df.c_queue,
            np.where((df.c_ivl < 21) & (df.c_type == CARD_TYPE_REV),
                     5, df.c_type))
    df['type_and_queue_label'] = df.type_and_queue.map(
            lambda x: TYPE_AND_QUEUE_LABELS[x])
    df['due_date'] = df.c_due.map(
            datetime.datetime.fromtimestamp)
    df['odue_date'] = df.c_odue.map(
            datetime.datetime.fromtimestamp)
    df['which_due'] = np.where(df.c_odid != 0, df.odue_date, df.due_date)
    df['due_in_unix_epoch'] = df.which_due.map(
        lambda x: x.timestamp() > 1000000000 if not pd.isnull(x) else False)
    df['added_days'] = ((
        (df.added_millis / 1000).map(datetime.datetime.fromtimestamp)
         - next_day_start).dt.total_seconds() / SECS_IN_DAY).map(math.ceil)
    if input_mode == INPUT_MODE_SQLITE:
        df['c_difficulty'] = df.c_data.map(lambda x: get_json_val(x, 'd'))
        df['c_stability'] = df.c_data.map(lambda x: get_json_val(x, 's'))
    else: pass    # pass: in this case, already in data frame
    df['stability_rounded'] = df.c_stability.map(round_away)
    df['ease_label'] = df.c_factor.map(make_ease_bin)
    df['scaled_difficulty'] = 100*(df.c_difficulty - 1) / 9
    df['diff_bin_label'] = df.scaled_difficulty.map(make_diff_bin)

    # TODO: implement logic for INPUT_MODE_SQLITE for due_days
    if input_mode == INPUT_MODE_TEXT:
        df['due_days'] = np.where(df.due_in_unix_epoch,
            ((df.which_due
             - next_day_start).dt.total_seconds().map(get_days_round_to_zero)),
            np.where(df.c_odid == 0,
                     df.c_due - df.col_TodayDaysElapsed,
                     df.c_odue - df.col_TodayDaysElapsed))
        df['bin_retr'] = df.csd_fsrs_retrievability.map(
                lambda x: np.nan if math.isnan(x) else (100*x // 5))
        df['bin_retr_label'] = df.bin_retr.map(bin_label_from_index)

    return df

def create_reviews(input_mode, cards_df=None):
    if input_mode == INPUT_MODE_TEXT:
        df = pd.DataFrame(cards_df.revlog_entries.map(strip_last5).str.split(
                 '-----', expand=True).stack(), columns=['revlog_entries2'])
        df[['date_millis', 'review_kind', 'ease', 'ivl', 'lastivl',
           'taken_millis', 'factor']
          ] = df.revlog_entries2.str.split('#', expand=True)
        df.index.set_names(['c_id','seq'], inplace=True)
    else:
        df = db.read_sql_query('select * from revlog')
        #id cid usn ease ivl lastIvl factor time type
        df = df.rename({'id': 'date_millis',
                        'cid': 'c_id',
                        'type': 'review_kind',
                        'lastIvl': 'lastivl',
                        'time': 'taken_millis'}, axis=1)
        df = df.merge(cards_df[['added_millis']], how='inner', left_on='c_id',
                      right_on='added_millis', suffixes=(None, '_y'))

    rollover_hour = get_rollover_from_cards(cards_df)
    next_day_start = get_next_day_start(rollover_hour)
    offset = get_local_offset()

    # these next two are str from INPUT_MODE_TEXT and num otherwise
    df['factor'] = df.factor.map(str_or_num_to_int_or_nan)
    df['ease'] = df.ease.map(str_or_num_to_int_or_nan)
    df['date_secs'] = df.date_millis.map(lambda x: float(x)/1000)
    df['taken'] = df.taken_millis.map(lambda x: float(x)/1000)
    df = df.astype({'lastivl': int, 'ivl': int,
                    'review_kind': int, 'taken': float})
    df['review_hr'] = df.date_secs.map(lambda x: get_hour_from_secs(x, offset))

    df['review_datetime'] = df.date_secs.map(
          datetime.datetime.fromtimestamp)
    df['review_kind_subcat1'] = np.where(
          df.review_kind.isin([REVLOG_LRN, REVLOG_RELRN, REVLOG_FILT]),
          REVLOG_SUBCAT1_LRN,
          np.where(df.review_kind == REVLOG_REV,
                   np.where(df.lastivl < 21,
                            REVLOG_SUBCAT1_YOUNG,
                            REVLOG_SUBCAT1_MATURE),
                   REVLOG_SUBCAT1_OTHER))
    df['review_kind_subcat1_label'] = df.review_kind_subcat1.map(
          lambda x: REVLOG_SUBCAT1_LABELS[x])

    df['review_kind_subcat2'] = np.where(
          df.review_kind == REVLOG_REV,
          np.where(df.lastivl < 21,
                   REVLOG_SUBCAT2_YOUNG, REVLOG_SUBCAT2_MATURE),
          df.review_kind)
    df['review_kind_subcat2_label'] = df.review_kind_subcat2.map(
          lambda x: REVLOG_SUBCAT2_LABELS[x])
    df['taken_hrs'] = df.taken / (60*60)
    df['review_date_adj'] = (df.review_datetime
                             - datetime.timedelta(hours = rollover_hour)
                            ).dt.date
    df['review_relative_days'] = (
              (df.review_datetime - next_day_start).dt.total_seconds().map(
              get_days_round_to_zero))
    df['review_kind_label'] = df.review_kind.map(
                                      lambda x: REVLOG_LABELS[x])
    df['retention_pop'] = (
            (df.ease > 0 )
         & ((df.review_kind != REVLOG_FILT) | (df.factor != 0))
         & ((df.review_kind == REVLOG_REV) | (df.lastivl <= -86400)
            | (df.lastivl >= 1))
                                  )
    # True / False / None
    df['correct_answer'] = (np.where(df.ease == 0,
                                             None, (df.ease > 1)))
    #df['correct'] = (np.where(df.retention_pop,
    #                                  (df.ease > 1).astype(int), np.nan))

    return df
