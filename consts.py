# Define constants
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

"""Define constants.
"""

#------------------------------------------------------------------------------
# Constants (do not require user modification)
#------------------------------------------------------------------------------
# seconds in a day
SECS_IN_DAY = 24 * 60 * 60

INPUT_MODE_TEXT = 1
INPUT_MODE_SQLITE = 2

OFFSET_SOURCE_DB = 0
OFFSET_SOURCE_PYTHON = 1

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
        -2: '7. Buried',  # -2 and -3 pooled for reporting
        -3: '7. Buried',
        }

