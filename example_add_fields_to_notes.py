# Example program for adding selected fields to input notes file
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
#-----------------------------------------------------------------------------

'''This is an example program that uses the functions in this package for 
a perhaps more practical task than the example in `anki_stats.py`, which
recreates the statistics in the Anki Statistics tab. It adds selected card
information from Anki to all the notes in a 'raw' input file.

Consider the scenario where a user stores their notes in a spreadsheet,
and they upload the notes (possibly after some processing) as a text file
to Anki. It can then be useful to add information to this spreadsheet from
Anki (not for upload, but maybe for other tasks). For example, the user
might want to know when a note was last studied or when it will be due for
study.

This program creates a file that the user can then use to paste back into
the spreadsheet. The columns created in this example program are
`days_since_last_review`, `days_since_last_lapse`, and `days_until_due`.
More fields are possible, see `add_to_notes` documentation for details.
The 'raw' file that is the input to this program is the text file exported
from the spreadsheet (before any other processing).
'''

import csv
import datetime
import sys

import pandas as pd

from add_to_notes_wrapper import load_cards_and_reviews, add_to_notes

#-----------------------------------------------------------------------------

#---------------------
# Parameters
#---------------------

# Path to database, i.e., the 'collection.anki2' file
# See cautions in `parameters.py` listed before the `INPUT_MODE` parameter.
SQLITE_FILE = '/path/to/collection.anki2'
# Notes raw input file. See file docstring for further details
NOTES_RAW_INPUT_FILE = '/path/to/notes_raw_input_file.txt'
# Output file
OUTPUT_FILE = 'notes_output.txt'
# Id variable on NOTES_RAW_INPUT_FILE. It is assumed that notes uploaded to
# Anki have a unique id obtained by applying `input_to_uploaded_id` to this
# field. In this example, I refer to this uploaded unique id as `uploaded_id`.
IDVAR = 'id'
# Deck name. Cards and reviews from this deck will be used. The string 
# provided here must match the name in the database exactly or as a prefix
# before '::'.
DECK_NAME = 'SelectedDeck'
# Position of the uploaded unique id in the uploaded notes
UPLOADED_ID_POS = 0
# See comment before `IDVAR`.
def input_to_uploaded_id(x):
    return 'SOME_PREFIX_' + str(x)

# Subset the cards prior to calculating the new output variables. This code
# will be very user-dependent. In this example, we omit New cards (since these
# won't have a due date or 'days since last review'). Suspended cards are also
# omitted. Finally, we assume a given note is associated with multiple card
# types, but only two are selected here.
def subset_cards(df):
    # c_ord: card types, seq num starting at 0
    # c_type != 0 -> card not 'New'
    # c_queue != -1 -> card not 'Suspended'
    return df[ df.c_ord.isin([2,3]) & (df.c_type != 0) &
                   (df.c_queue != -1) ]

#---------------------
# Functions
#---------------------
def write_output(df, raw_idvar, output_file):
    final_set = df[[raw_idvar, 'uploaded_id','days_since_last_review',
                    'days_since_last_lapse','days_until_due']]
    # The floats exported are actually either integer or np.nan, so can be
    # formatted to 0 decimal places when exporting. If more control is needed,
    # can use the following:

    #for var in vars_to_convert_to_str:
    #    df[var] = df[var].map(
    #        lambda x: str(int(x)) if not pd.isna(x) else '')
    final_set.to_csv(output_file, sep='\t', quoting=csv.QUOTE_NONE,
                     index=None, float_format='%.0f')

######################
# Main Entry Point
######################

cards, reviews = load_cards_and_reviews(sqlite_file=SQLITE_FILE,
                                        deck_name='SPDEFull')

cards = subset_cards(cards)

cards['uploaded_id'] = cards.flds.map(
                        lambda x: x.split('\x1f')[UPLOADED_ID_POS])

notes_input = pd.read_csv(NOTES_RAW_INPUT_FILE,
                          usecols=[IDVAR],
                          sep='\t', quoting=csv.QUOTE_NONE)
notes_input['uploaded_id'] = notes_input[IDVAR].map(input_to_uploaded_id)

notes_output = add_to_notes(notes_df=notes_input, idvar='uploaded_id',
                            c_df=cards, r_df=reviews)

write_output(df=notes_output, raw_idvar=IDVAR, output_file=OUTPUT_FILE)

