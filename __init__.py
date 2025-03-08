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

Users can set input parameters in parameters.py. If INPUT_MODE is set to its
recommended value INPUT_MODE_TEXT, the input file should be tab-delimited with
'"' as the quote character and should contain at least the following columns:
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

