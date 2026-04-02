# Functions for simple example of adding fields to text notes file
# Copyright (C) 2026 Ray Griner
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

import csv
import datetime
import sys

import pandas as pd

import db

from consts import INPUT_MODE_SQLITE, REVLOG_FILT

from prepare_data import (
    create_cards, create_reviews, add_fsrs_retrievability,
    add_deck_names_and_filter,
                         )

#---------------------
# Constants
#---------------------
C_DF_VARS = ['c_nid','which_due','due_days']
R_DF_VARS = ['c_nid','c_id','ease','date_millis','review_kind','factor']

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def _date_from_timestamp_or_missing(x):
    if not pd.isna(x):
        return datetime.datetime.fromtimestamp(x).date()
    else:
        return np.nan

def _calc_days_since_etal_for_notes(df_cards, df_reviews):
    '''Create df by note with `days_since_last_review`, `days_until_due`, etc.

    Returns
    -------
    Data frame with the following fields:
    - c_nid : Anki internal note id
    - date_secs : Time of last review in seconds (for debugging) for any
        card on the note
    - date_of_last_review : Date of last review (or np.nan)
    - days_since_last_review : Today - `date_of_last_review`
    - days_until_due : Days until earliest due date (across cards)
    '''
    subset_df = df_reviews[  (df_reviews.ease >= 1)
                           & (df_reviews.ease <= 4)
                           & (~pd.isna(df_reviews.date_millis))
                           & (  (df_reviews.review_kind != REVLOG_FILT)
                              | (df_reviews.factor != 0))].copy()
    subset_df['date_secs'] = subset_df.date_millis.astype(int) / 1000
    max_date_secs = subset_df.groupby(['c_nid'],
                                      as_index=False)['date_secs'].max()
    min_due_days = df_cards.groupby(['c_nid'],
                                    as_index=False)['due_days'].min()

    df_notes = df_cards.drop_duplicates(subset=['c_nid']).copy()
    df_notes.drop(['which_due','due_days'], inplace=True, axis=1)

    out_df = df_notes.merge(max_date_secs, left_on='c_nid', right_on='c_nid')
    out_df = out_df.merge(min_due_days, left_on='c_nid', right_on='c_nid')

    out_df['date_of_last_review'] = out_df.date_secs.map(
        _date_from_timestamp_or_missing)
    out_df['days_since_last_review'] = out_df.date_of_last_review.map(
        lambda x: (datetime.date.today() - x).days)

    out_df['days_until_due'] = out_df.due_days

    out_df = out_df[['c_nid','date_secs','date_of_last_review',
                     'days_since_last_review','days_until_due']]

    return out_df

def add_to_notes(notes_df, idvar, c_df, r_df):
    '''Add fields to `notes_df` from cards/review dfs.

    Parameters
    ----------
    notes_df : pd.DataFrame
        A data frame containings the notes.

    idvar : str
        A unique id for the notes. The field should exist on both
        `notes_df` and `cards_df`.

    c_df : pd.DataFrame
        A data frame with information about cards. The function assumes
        that it was created by `load_cards_and_reviews` and then subset if
        necessary.

    r_df : pd.DataFrame
        A data frame with information about cards. The function assumes
        that it was created by `load_cards_and_reviews` and then subset if
        necessary.

    Returns
    ----------
    A data frame that is equal to `notes_df`, but with the fields
    `days_since_last_review` and `days_until_due`, among others, added.
    See the fields returned from `_calc_days_since_etal_for_notes` for the
    complete list.
    '''

    # just to be explicit about which fields are used
    c_df = c_df[C_DF_VARS + [idvar]]
    r_df = r_df[R_DF_VARS]

    # 1. notes_df - columns: orig_order, id (user-defined note ID)
    #notes_df.index.set_names('orig_order', inplace=True)
    #notes_df.reset_index(inplace=True)

    # 3. c_df - c_id, date_of_last_review
    
    c_nid_by_idvar_df = c_df.drop_duplicates(subset=['c_nid',idvar]).copy()
    check_dups = c_nid_by_idvar_df.duplicated(subset=['c_nid'])
    if check_dups.any():
        print(c_nid_by_advar_df[check_dups])
        raise ValueError(f'`c_nid` field in `c_df` does not map uniquely to '
                         f'{idvar=}')

    notes_w_n_cid_df = notes_df.merge(c_nid_by_idvar_df, how='left', on=idvar)

    notes_w_days_since_df = _calc_days_since_etal_for_notes(c_df, r_df)

    # 4. Merge ex_df and cards_df
    final_df = notes_w_n_cid_df.merge(notes_w_days_since_df,
                                      on='c_nid', how='left')

    return final_df

def load_cards_and_reviews(sqlite_file, deck_name) -> None:
    '''Get cards and reviews for a given deck from database

    Parameters
    ----------
    sqlite_file : str
        Path to the database ('collection.anki2' file). See cautions in
        `parameters.py` listed before the `INPUT_MODE` parameter.
        (Note that neither this function nor other functions in this
        file import from `parameters.py`, but the cautions apply.)

    deck_name : str
        Name of the deck to select. The string provided here must match
        the name in the database exactly or as a prefix before '::'.

    Returns
    ----------
    A 2-tuple for the cards and then reviews data frames (dfs), or, if the
    created cards df has no records, then (None, None) is returned. See
    `create_cards` and `create_reviews` for complete descriptions of
    these returned dfs, but the general idea is that these dfs most
    fields necessary to calculate the statistics presented in the Anki
    statistics tab. (This also means these dfs have more fields than
    necessary for the purpose of the functions in this file, which is
    to add a smaller number of fields to the notes df.)
    '''

    db.connect_readonly(sqlite_file)

    #--------------------------------------------------------------------------
    # 1a. Read cards: this is either the export file where fields were manually
    # selected or it will read from the SQLite database.
    #--------------------------------------------------------------------------
    df_cards_m = create_cards(sqlite_file, INPUT_MODE_SQLITE)

    #--------------------------------------------------------------------------
    # 1b. Filter by deck name, if requested (INPUT_MODE_SQLITE only)
    #--------------------------------------------------------------------------
    if deck_name is not None:
        df_cards_m = add_deck_names_and_filter(df_cards_m, deck_name)
        # TODO: exception raised if `create_reviews` is called with an empty
        # data frame, as the function tries to get the rollover hour from the
        # first record.
        if len(df_cards_m) == 0:
            print('No cards selected')
            db.close()
            return None, None

    #--------------------------------------------------------------------------
    # 1c. Get reviews either from df_cards_m.revlog_entries or by querying the
    # SQLite database.
    #--------------------------------------------------------------------------
    df_reviews = create_reviews(INPUT_MODE_SQLITE, df_cards_m)

    #df_r_and_c = df_cards.merge(df_reviews, how='left', on='c_id')

    #if INPUT_MODE == INPUT_MODE_SQLITE:
    #    df_cards_m = add_fsrs_retrievability(df_cards_m)

    db.close()

    return df_cards_m, df_reviews

