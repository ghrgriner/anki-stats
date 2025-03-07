# Wrappers for database functions.
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

"""Wrappers for database functions.
"""

import os

import sqlite3
import pandas as pd

_DB_CON = None

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def connect_readonly(file):
    global _DB_CON
    abspath = os.path.abspath(file)
    connect_str = f'file:{abspath}?mode=ro'
    connection = sqlite3.connect(connect_str, uri=True)
    _DB_CON = connection

def read_sql_query(query):
    return pd.read_sql_query(query, _DB_CON)

def close():
    return _DB_CON.close()

