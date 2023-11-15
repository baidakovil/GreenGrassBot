from dataclasses import dataclass
from typing import List

from config import Cfg

CFG = Cfg()

@dataclass
class ArtScrobble:
    """
    Class for keeping user scrobble for 1 artist
    """
    user_id: int
    art_name: str
    scrobble_date: str
    lfm: str
    scrobble_count: int


@dataclass
class Event:
    """
    Class for keeping one event and lineup
    """
    event_date: str
    place: str
    locality: str
    country: str
    event_source: str
    link: str
    lineup: List[int]


@dataclass
class User:
    """
    Class for keeping user info
    """
    user_id: int
    username: str
    first_name: str
    last_name: str
    language_code: str
    accs: List[str] = None
    reg_datetime: str = None

@dataclass
class UserSettings:
    """
    Class for keeping user settings
    """
    user_id: int
    min_listens: int = CFG.DEFAULT_MIN_LISTENS
    notice_day: int = CFG.DEFAULT_NOTICE_DAY
    notice_time: str = CFG.DEFAULT_NOTICE_TIME
    nonewevents: int = 1