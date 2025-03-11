# Main entry point.
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

"""Main entry point.
"""

import csv

import pandas as pd

import db
from parameters import (
    INPUT_FILE, INPUT_MODE, DECK_NAME, PD_DISPLAY_MAX_ROWS,
    CARDS_BROWSER_INPUT_FILE,
    )
from consts import INPUT_MODE_SQLITE
from prepare_data import (
    create_cards, create_reviews, add_fsrs_retrievability,
    add_deck_names_and_filter,
                         )
from custom_output import create_all_custom_figures
from standard_output import print_stats_tables

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def main() -> None:
    pd.set_option('display.max_rows', PD_DISPLAY_MAX_ROWS)

    if INPUT_MODE == INPUT_MODE_SQLITE: db.connect_readonly(INPUT_FILE)

    #--------------------------------------------------------------------------
    # 1a. Read cards: this is either the export file where fields were manually
    # selected or it will read from the SQLite database.
    #--------------------------------------------------------------------------
    df_cards_m = create_cards(INPUT_FILE, INPUT_MODE)

    #--------------------------------------------------------------------------
    # 1b. Filter by deck name, if requested (INPUT_MODE_SQLITE only)
    #--------------------------------------------------------------------------
    if DECK_NAME is not None and INPUT_MODE == INPUT_MODE_SQLITE:
        df_cards_m = add_deck_names_and_filter(df_cards_m, DECK_NAME)
        if len(df_cards_m) == 0:
            print("No cards selected")
            return

    #--------------------------------------------------------------------------
    # 1c. Get reviews either from df_cards_m.revlog_entries or by querying the
    # SQLite database.
    #--------------------------------------------------------------------------
    df_reviews = create_reviews(INPUT_MODE, df_cards_m)

    if INPUT_MODE == INPUT_MODE_SQLITE:
        df_cards_m = add_fsrs_retrievability(df_cards_m)

    if INPUT_MODE == INPUT_MODE_SQLITE: db.close()

    #--------------------------------------------------------------------------
    # 1c. Read card file that was exported from the browser, if the user
    # decided to include one.
    #--------------------------------------------------------------------------
    if CARDS_BROWSER_INPUT_FILE is not None:
        df_cards_b = pd.read_csv(CARDS_BROWSER_INPUT_FILE, sep='\t',
                                 quoting=csv.QUOTE_NONE, index_col=False,
                                 dtype={'Difficulty': str, 'Ease': str})
        df_cards_b.set_index(['cid'], verify_integrity=True, inplace=True)

    #--------------------------------------------------------------------------
    # 2. Merge above sets as needed
    #--------------------------------------------------------------------------
    if CARDS_BROWSER_INPUT_FILE is not None:
        df_cards = df_cards_m.merge(df_cards_b, how='left', left_index=True,
                                    right_index=True)
    else:
        df_cards = df_cards_m
    df_r_and_c = df_cards.merge(df_reviews, how='left', on='c_id')

    #--------------------------------------------------------------------------
    # 3. Create tables matching the text/tables/figures from the Anki `Stats`
    # window.
    #--------------------------------------------------------------------------
    print_stats_tables(df_cards=df_cards_m, df_reviews=df_reviews,
                       df_r_and_c=df_r_and_c)

    #--------------------------------------------------------------------------
    # 4. Create custom figure(s) that are not available in the Anki `Stats`
    # window. As an example, here we repeat Figure 4 stratified by card type.
    #--------------------------------------------------------------------------
    create_all_custom_figures(df_cards)
    #custom_listings(df_cards)

#------------------------------------------------------------------------------
# End Functions
#------------------------------------------------------------------------------

if __name__ == '__main__':
    #sys.exit(main())
    main()

