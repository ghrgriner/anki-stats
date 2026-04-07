# Parameters that can be set by the user
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

"""Parameters that can be set by the user.
"""

from consts import INPUT_MODE_TEXT, INPUT_MODE_SQLITE # pylint: disable=unused-import

#------------------------------------------------------------------------------
# Parameters (for modification by user)
#------------------------------------------------------------------------------
INPUT_FILE = 'input/cards.csv'

# We recommend using INPUT_MODE_TEXT. If INPUT_MODE_SQLITE is used, the
# INPUT_FILE must be the path to a collection.anki2 file. We only provide a
# connection function in `db.py` that is meant to open the database read-only,
# but nevertheless, you should not attempt to write to the Anki database as
# this can easily corrupt the collection. Therefore, only use INPUT_MODE_SQLITE
# if you have reviewed the code in this package and are satisfied with the
# database operations being performed. Alternatively, make a copy of your
# `collection.anki2` for use with this package and specify the path to the
# copy.
INPUT_MODE = INPUT_MODE_TEXT

# Only used when INPUT_MODE == INPUT_MODE_SQLITE to filter the cards (if
# desired), since all cards in the collection are retrieved from database.
# Decks will be selected if the deck name matches exactly or matches as a
# prefix before '::'.
DECK_NAME = None

# Path to optional input file if user wants to use additional fields export
# from the browser (see corresponding export program).
CARDS_BROWSER_INPUT_FILE = None

# Will be passed to pd.set_option('display.max_rows')
PD_DISPLAY_MAX_ROWS = 500

