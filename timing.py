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
import math
import time
from typing import Optional, Union, Self

import db
import pandas as pd

from consts import OFFSET_SOURCE_DB, OFFSET_SOURCE_PYTHON, SECS_IN_DAY
from other_functions import get_days_round_to_zero

#------------------------------------------------------------------------------
# Classes
#------------------------------------------------------------------------------
class TimestampSecs:
    """Class for a timestamp represented in seconds (UNIX epoch time)."""
    val: int

    def __init__(self, val: Union[int,float]):
        self.val = math.floor(val)

    def datetime(self, offset: int) -> datetime.datetime:
        """Return tz-aware datetime object with the given offset."""
        timezone = datetime.timezone(datetime.timedelta(hours=-offset/60))
        return datetime.datetime.fromtimestamp(self.val, tz=timezone)

    def adding_secs(self, val_to_add: int) -> Self:
        self.val += val_to_add
        return self

@dataclass
class SchedTimingToday:
    now: TimestampSecs
    days_elapsed: int
    next_day_at: TimestampSecs
    def __str__(self) -> str:
        return f'SchedTimingToday({self.now=},{self.days_elapsed=})'

@dataclass
class TimingConfig:
    """Collection-specific timing information from the database.

    Attributes
    ----------
    rollover_hour : Optional[int]
        Hour defining start of each day (0-23)
    creation_offset : Optional[int]
        Time-zone offset (in minutes) when collection was created
    local_offset : int
        Current local time-zone offset (in minutes) for the collection.
        See `local_offset_source` for details.
    local_offset_source : int (OFFSET_SOURCE_DB, OFFSET_SOURCE_PYTHON)
        `local_offset` will be taken from the database if available, but
        on older databases, it might not be present and is then taken
        from the Python time package. See `get_local_offset` for
        details.
    sched_ver : Optional[int]
        Anki scheduling version. Valid values: 1 or 2.
    creation_stamp : int
        Timestamp in seconds for creation of the collection.
    """
    rollover_hour: Optional[int]
    creation_offset: Optional[int]
    local_offset: int
    local_offset_source: int
    sched_ver: Optional[int]
    creation_stamp: int

    def __init__(self) -> None:
        df_config = db.read_sql_query('select * from config')
        df_config.set_index(['KEY'], verify_integrity=True, inplace=True)
        self.rollover_hour = _get_opt_int(df_config, 'rollover')
        self.creation_offset = _get_opt_int(df_config, 'creationOffset')
        local_offset = _get_opt_int(df_config, 'localOffset')
        if local_offset is not None:
            self.local_offset = local_offset
            self.local_offset_source = OFFSET_SOURCE_DB
        else:
            self.local_offset = round(get_python_local_offset() / 60)
            self.local_offset_source = OFFSET_SOURCE_PYTHON
        self.sched_ver = _get_opt_int(df_config, 'schedVer')
        df_col = db.read_sql_query('select crt from col')
        self.creation_stamp = df_col.iloc[0, 0]

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def _get_opt_int(df: pd.DataFrame, key: str) -> Optional[int]:
    if key in df.index:
        return int(df.at[key,'val'].decode('utf-8'))
    else:
        return None

# For most of the rest, see: timing.rs in Anki repo

def rollover_datetime(date: datetime.datetime,
                      rollover_hour: int) -> datetime.datetime:
    """Return tz-aware datetime object, date as input, hour=rollover_hour."""
    newdate = date.replace(hour=rollover_hour, minute=0, second=0,
                           microsecond=0)
    return newdate


def days_elapsed_(start_date: datetime.datetime,
                  end_date: datetime.datetime,
                  rollover_passed: bool) -> int:
    day_diff = (end_date - start_date).days
    if rollover_passed:
        return day_diff
    else:
        return day_diff - 1

def sched_timing_today_v1(crt: TimestampSecs,
                          now: TimestampSecs) -> SchedTimingToday:
    days_elapsed = get_days_round_to_zero(now.val - crt.val)
    next_day_at = TimestampSecs(crt.val + (days_elapsed + 1)*SECS_IN_DAY)
    return SchedTimingToday(now=now, days_elapsed=days_elapsed,
                            next_day_at=next_day_at)

def sched_timing_today_v2_legacy(crt: TimestampSecs,
                                 rollover: int,
                                 now: TimestampSecs,
                                 current_utc_offset: int) -> SchedTimingToday:
    crt_at_rollover = rollover_datetime(crt.datetime(current_utc_offset),
                                        rollover).timestamp()
    days_elapsed = get_days_round_to_zero(now.val - crt_at_rollover)

    next_day_at = TimestampSecs(
        rollover_datetime(now.datetime(current_utc_offset),
                          rollover).timestamp())
    if next_day_at.val < now.val:
        next_day_at = next_day_at.adding_secs(SECS_IN_DAY)

    return SchedTimingToday(now=now, days_elapsed=days_elapsed,
                            next_day_at=next_day_at)

def sched_timing_today_v2_new(creation_secs: TimestampSecs,
                              current_secs: TimestampSecs,
                              creation_utc_offset: int,
                              current_utc_offset: int,
                              rollover_hour: int) -> SchedTimingToday:
    created_datetime = creation_secs.datetime(creation_utc_offset)
    now_datetime = current_secs.datetime(current_utc_offset)

    rollover_today_datetime = rollover_datetime(now_datetime,
                                                rollover_hour)
    rollover_passed = rollover_today_datetime <= now_datetime
    if rollover_passed:
        next_day_at = TimestampSecs((rollover_today_datetime
                              + datetime.timedelta(days=1)).timestamp())
    else:
        next_day_at = TimestampSecs(rollover_today_datetime.timestamp())

    days_elapsed = days_elapsed_(created_datetime, now_datetime,
		    rollover_passed)

    return SchedTimingToday(now=current_secs, days_elapsed=days_elapsed,
                            next_day_at=next_day_at)

def sched_timing_today(creation_secs: TimestampSecs,
                       current_secs: TimestampSecs,
                       creation_utc_offset: Optional[int],
                       current_utc_offset: int,
                       rollover_hour: Optional[int]) -> SchedTimingToday:
    if rollover_hour is None:
        return sched_timing_today_v1(creation_secs, current_secs)
    elif creation_utc_offset is None:
        return sched_timing_today_v2_legacy(creation_secs,
                 rollover_hour, current_secs, current_utc_offset)
    else:
        return sched_timing_today_v2_new(creation_secs, current_secs,
                 creation_utc_offset, current_utc_offset, rollover_hour)

# we have creation_stamp in TimingConfig and not as a separate parameter
def timing_for_timestamp(now: TimestampSecs,
                         timing_config: TimingConfig,
                        ) -> SchedTimingToday:
    if timing_config.sched_ver == 1:
        rollover_hour = None
    elif timing_config.sched_ver == 2:
        if timing_config.rollover_hour is None:
            rollover_hour = 4
        else:
            rollover_hour = timing_config.rollover_hour
    else:
        raise ValueError(
            f'{timing_config.sched_ver=}, only 1 or 2 supported')
    return sched_timing_today(TimestampSecs(timing_config.creation_stamp),
                              now,
                              timing_config.creation_offset,
                              timing_config.local_offset,
                              rollover_hour)

def get_python_local_offset() -> int:
    """Return local timezone offset from Python time package.

    return time.altzone if time.localtime().tm_isdst else time.timezone

    Returns
    -------
    An integer as seconds west of UTC according to the code above.
    """
    if time.localtime().tm_isdst:
        return time.altzone
    else:
        return time.timezone

def get_hour_from_secs(x: Union[float,int], offset: int) -> int:
    """Return local hour from seconds in epoch time."""
    return math.floor(((float(x) - offset) / 3600) % 24)

def get_next_day_start(rollover_hour: int) -> TimestampSecs:
    """Return date/time of the next start day (i.e., today or tomorrow)."""
    now_local = datetime.datetime.today()
    midnight_local = now_local.replace(hour=0, minute=0, second=0,
                                       microsecond=0)
    if rollover_hour == 0:
        rt_local = midnight_local + datetime.timedelta(days = 1)
    elif now_local.hour < rollover_hour:
        rt_local = (midnight_local
                + datetime.timedelta(days = 0, hours = rollover_hour))
    else:
        rt_local = (midnight_local
                + datetime.timedelta(days = 1, hours = rollover_hour))
    return TimestampSecs(rt_local.timestamp())

