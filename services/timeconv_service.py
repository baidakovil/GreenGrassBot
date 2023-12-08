# Green Grass Bot — Ties the music you're listening to with the concert it's playing at.
# Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>

# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <https://www.gnu.org/licenses/>.
"""This file contains functions to convert different time formats."""

import logging
from datetime import datetime

from services.logger import logger

logger = logging.getLogger('A.uti')
logger.setLevel(logging.DEBUG)


#  Format for human-readability of event dates in daily news ('02 Jan 2023')
FORMAT_HUMAN = '%d %b %Y'
#  Format of date in Last.fm API ('02 Jan 2023')
FORMAT_LFM = '%d %b %Y'
#  Format to store dates in SQL ('2023-01-02')
FORMAT_SQL_DATE = '%Y-%m-%d'
#  Format to store timestamps in SQL
FORMAT_SQL_TIMESTAMP = '%Y-%m-%d %H:%M:%S'


def timestamp_to_text(timestamp: datetime) -> str:
    """
    Convertor for saving timestamps to SQL. Used when write info about user
    registration.
    Args:
        timestamp: timestamp
    Returns:
        string with specific timestamp format
    """
    return timestamp.strftime(FORMAT_SQL_TIMESTAMP)


def text_to_userdate(text: str) -> str:
    """
    Convertor from SQL-storing format to  for humans. Used
    when preparing 'details', i.e. event news.
    Args:
        text: string with specific date format
    Returns:
        string with specific date format
    """
    return datetime.strptime(text, FORMAT_SQL_DATE).strftime(FORMAT_HUMAN)


def lfmdate_to_text(lfmdate: str) -> str:
    """
    Convertor for saving dates from last.fm to SQL. Used when
    saving scrobbles.
    Args:
        lfmdate: string with specific date format
    Returns:
        string with specific date format
    """
    return datetime.strptime(lfmdate, FORMAT_LFM).strftime(FORMAT_SQL_DATE)


def text_to_date(text: str) -> datetime:
    """
    Convertor for saved date in SQL to timestamp
    """
    return datetime.strptime(text, FORMAT_SQL_DATE)


def unix_to_text(unix: int) -> str:
    """
    Convertor for unix timestamp to human readable timestamp. For debugging purposes.
    Args:
        unix timestamp
    Returns:
        string with timestamp in readable format
    """
    return datetime.utcfromtimestamp(unix).strftime(FORMAT_SQL_TIMESTAMP)
