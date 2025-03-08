# Timing functions.
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

"""Timing functions
"""

from dataclasses import dataclass
import datetime
from typing import Optional

import db

from other_functions import get_days_round_to_zero

#------------------------------------------------------------------------------
# Classes
#------------------------------------------------------------------------------
class TimestampSecs:
    val: int

    def datetime(self, offset):
        """Return tz-aware datetime object with the given offset."""
        timezone = datetime.timezone(datetime.timedelta(hours=-offset/60))
        return datetime.datetime.fromtimestamp(self.val, tz=timezone)

    def __init__(self, val):
        self.val = val

@dataclass
class SchedTimingToday:
    # omit next_day_at for now
    now: TimestampSecs
    days_elapsed: int
    #next_day_at: TimestampSecs

class TimingConfig:
    """Collection-specific timing information from the database.

    Attributes
    ----------
    rollover_hour : Optional[int]
        Hour defining start of each day (0-23)
    creation_offset : Optional[int]
        Time-zone offset (in minutes) when collection was created
    local_offset : Optional[int]
        Current local time-zone offset (in minutes) for the collection.
        This is obtained from the Anki collection and not, for example,
        by querying the operating system.
    sched_ver : Optional[int]
        Anki scheduling version. Valid values: 1 or 2.
    creation_stamp : int
        Timestamp in seconds for creation of the collection.
    """
    rollover_hour: Optional[int]
    creation_offset: Optional[int]
    local_offset: Optional[int]
    sched_ver: Optional[int]
    creation_stamp: int

    def __init__(self):
        df_config = db.read_sql_query('select * from config')
        df_config.set_index(['KEY'], verify_integrity=True, inplace=True)
        self.rollover_hour = _get_opt_int(df_config, 'rollover')
        self.creation_offset = _get_opt_int(df_config, 'creationOffset')
        self.local_offset = _get_opt_int(df_config, 'localOffset')
        self.sched_ver = _get_opt_int(df_config, 'schedVer')
        df_col = db.read_sql_query('select crt from col')
        self.creation_stamp = df_col.iloc[0, 0]

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def _get_opt_int(df, key) -> Optional[int]:
    if key in df.index:
        return int(df.at[key,'val'].decode('utf-8'))
    else:
        return None

# For most of the rest, see: timing.rs in Anki repo

def rollover_datetime(date, rollover_hour):
    """Return tz-aware datetime object, date as input, hour=rollover_hour."""
    newdate = date.replace(hour=rollover_hour, minute=0, second=0,
                           microsecond=0)
    return newdate


def days_elapsed_(start_date, end_date, rollover_passed):
    day_diff = (end_date - start_date).days
    if rollover_passed:
        return day_diff
    else:
        return day_diff - 1

def sched_timing_today_v1(crt, now):
    days_elapsed = get_days_round_to_zero(now - crt)
    return SchedTimingToday(now=now, days_elapsed=days_elapsed)

def sched_timing_today_v2_legacy(crt, rollover, now, current_utc_offset):
    crt_at_rollover = rollover_datetime(crt.datetime(current_utc_offset),
                                        rollover).timestamp()
    days_elapsed = get_days_round_to_zero(now.val - crt_at_rollover)
    return SchedTimingToday(now=now, days_elapsed=days_elapsed)

def sched_timing_today_v2_new(creation_secs, creation_utc_offset,
        current_secs, current_utc_offset, rollover_hour):
    created_datetime = creation_secs.datetime(creation_utc_offset)
    now_datetime = current_secs.datetime(current_utc_offset)

    rollover_today_datetime = rollover_datetime(now_datetime,
                                                rollover_hour)
    rollover_passed = rollover_today_datetime <= now_datetime

    days_elapsed = days_elapsed_(created_datetime, now_datetime,
		    rollover_passed)
    return SchedTimingToday(now=current_secs, days_elapsed=days_elapsed)

def sched_timing_today(creation_secs, current_secs, creation_utc_offset,
                       current_utc_offset, rollover_hour):
    if rollover_hour is None:
        return sched_timing_today_v1(creation_secs, current_secs)
    elif creation_utc_offset is None:
        return sched_timing_today_v2_legacy(creation_secs,
                 rollover_hour, current_secs, current_utc_offset)
    else:
        return sched_timing_today_v2_new(creation_secs,
                 creation_utc_offset, current_secs, current_utc_offset,
                 rollover_hour)

def timing_for_timestamp(now, timing_config, creation_stamp):
    #  rollover_hour, creation_offset, local_offset, sched_ver
    print(timing_config)
    if timing_config['sched_ver'] == 1:
        rollover_hour = None
    elif timing_config['sched_ver'] == 2:
        if timing_config['rollover_hour'] is None:
            rollover_hour = 4
        else:
            rollover_hour = timing_config['rollover_hour']
    else:
        raise ValueError(
            f"{timing_config['sched_ver']=}, only 1 or 2 supported")
    return sched_timing_today(creation_stamp,
                              now,
                              timing_config['creation_offset'],
                              timing_config['local_offset'],
                              rollover_hour)
