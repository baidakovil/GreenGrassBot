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
"""This file contains @dataclass classes definitions."""

from dataclasses import dataclass, field
from typing import List

import config as cfg


@dataclass
class ArtScrobble:
    """
    Class for keeping user scrobble for 1 artist.
    Args:
        user_id: Tg user_id field
        art_name: artist name as it is on last.fm page
        scrobble_date: date of listening, in format of lfmdate_to_text() at timeconv_service.py
        lfm: last.fm account
        scrobble_count: scrobble count within this day
    """

    user_id: int
    art_name: str
    scrobble_date: str
    lfm: str
    scrobble_count: int


@dataclass
class Event:
    """
    Class for keeping one event and it's lineup.
    Args:
        event_date, place, locality, country: fields from lastfm's XML API answer
        event_source: for future need. The only source at the moment is 'lastfm'
        link: URL where event info was obtained
        lineup: list of artist names playing on the event
    """

    event_date: str
    place: str
    locality: str
    country: str
    event_source: str
    link: str
    lineup: List[str]


@dataclass
class BotUser:
    """
    Class for keeping user info. Code in accs needed to provide default value at init().
    Args:
        user_id, username, first_name, last_name, language_code: Tg user fields.
        accs: list of user last.fm accounts
        reg_datetime: string with registration datetime (see timestamp_to_text in
        timeconv_service.py)
    """

    user_id: int
    username: str
    first_name: str
    last_name: str
    language_code: str
    accs: List[str] = field(default_factory=list)
    reg_datetime: str = ''


@dataclass
class UserSettings:
    """
    Class for keeping user settings.
    Args:
        user_id: Tg user_id field
        min_listens: minimum scrobbles quantity in last cfg.DAYS_PERIOD_MINLISTENS days
        to count on this artist
        notice_day: day to notice in 0-6 format, start with monday, -1 for everyday
        notice_time: UTC 24h time in format '12:00:00'
        nonewevents: whether to show "No new events" message (1 mean: not to show)
        locale: locale code
    """

    user_id: int
    min_listens: int = cfg.DEFAULT_MIN_LISTENS
    notice_day: int = cfg.DEFAULT_NOTICE_DAY
    notice_time: str = cfg.DEFAULT_NOTICE_TIME
    nonewevents: int = cfg.DEFAULT_NONEWEVENTS
    locale: str = cfg.LOCALE_DEFAULT
