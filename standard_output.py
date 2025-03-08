# Print output tables similar to those in the Anki `Stats` window.
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

"""Print output tables similar to those in the Anki `Stats` window.
"""

import datetime

import pandas as pd

from parameters import INPUT_MODE
from consts import (
    INPUT_MODE_TEXT,
    QUEUE_TYPE_MANUALLY_BURIED, QUEUE_TYPE_SIBLING_BURIED,
    QUEUE_TYPE_SUSPENDED,
    CARD_TYPE_NEW, CARD_TYPE_REV, CARD_TYPE_RELEARNING,
    REVLOG_FILT, REVLOG_MANUAL,
    REVLOG_RESCHED,
    )
from other_functions import print_time, freq

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def print_retention_row(df, desc, start_day, end_day):
    """Print a row of the retention table."""
    if start_day is not None:
        df_ = df[  (df.review_relative_days >= start_day)
                 & (df.review_relative_days <= end_day)]
    else:
        df_ = df

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

def print_stats_tables(df_cards=None, df_reviews=None, df_r_and_c=None):
    #--------------------------------------------------------------------------
    # 3. Create tables matching the text/tables/figures from the Anki `Stats`
    # window.
    #--------------------------------------------------------------------------
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
        freq(df_cards, 'due_days', percent=True,
             title='Table 2: Future Due',
             where=(   (df_cards.due_days >= 0)
                     & (df_cards.due_days <= 30)
                     & (df_cards.c_type != CARD_TYPE_NEW)
                     & (df_cards.c_queue != QUEUE_TYPE_SUSPENDED)
                     & ~( ( (df_cards.c_queue == QUEUE_TYPE_SIBLING_BURIED)
                          | (df_cards.c_queue == QUEUE_TYPE_MANUALLY_BURIED))
                         & (df_cards.due_days <= 0))))

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

    freq(df_cards, 'type_and_queue_label', percent=True,
         title='Table 5: Card Counts')

    # TODO: Anki `running total` percentage in 'onHover' seems wrong. Research
    # and report bug.
    freq(df_cards, 'c_ivl',
         title='Table 6: Review Intervals', percent=True,
         where=( (  (df_cards.c_type == CARD_TYPE_REV)
                  | (df_cards.c_type == CARD_TYPE_RELEARNING)))
                & (df_cards.c_ivl <= 31))

    freq(df_cards, ['ease_label'],
         title='Table 7: Card Ease (non-FSRS decks only)',
         where=( (  (df_cards.c_type == CARD_TYPE_REV)
                  | (df_cards.c_type == CARD_TYPE_RELEARNING))))

    # TODO: Anki `running total` percentage in 'onHover' seems wrong.
    # Research and report bug.
    freq(df_cards, ['stability_rounded'],
         title='Table 8: Card Stability (FSRS decks only)',
         where=df_cards.stability_rounded < 31)

    freq(df_cards, ['diff_bin_label'],
         title='Table 9: Card Difficulty (FSRS desks only)',
         where=~pd.isnull(df_cards.scaled_difficulty))
         #where=(df_cards.diff_bin_label != ''))

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

    freq(df_cards, ['added_days'],
         title='Table 13: Added',
         where=(df_cards.added_days >= -31) & (df_cards.added_days <= 0))

    ret_df = df_reviews[ df_reviews.retention_pop ]
    print('\nTable 14: True Retention')
    print('                Young    Mature     Total     Count')
    print_retention_row(ret_df, desc='Today',      start_day=0,    end_day=0)
    print_retention_row(ret_df, desc='Yesterday',  start_day=-1,   end_day=-1)
    print_retention_row(ret_df, desc='Last week',  start_day=-6,   end_day=0)
    print_retention_row(ret_df, desc='Last month', start_day=-29,  end_day=0)
    print_retention_row(ret_df, desc='Last year',  start_day=-364, end_day=0)
    print_retention_row(ret_df, desc='All time',   start_day=None, end_day=0)

