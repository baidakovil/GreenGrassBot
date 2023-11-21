import logging
from datetime import datetime

from config import Cfg

logger = logging.getLogger('A.uti')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

# Format for human-readability of event dates in daily news
f_hum = '%d %b %Y'
# Format of date in Last.fm API
f_lfm = '%d %b %Y'
# Format to store dates in SQL
f_sql_date = '%Y-%m-%d'
# Format to store timestamps in SQL
f_sql_timestamp = '%Y-%m-%d %H:%M:%S'


def timestamp_to_text(timestamp: datetime) -> str:
    """
    Convertor for saving timestamps to SQL. Used when write info about user
    registration.
    Args:
        timestamp: timestamp
    Returns:
        string with specific timestamp format
    """
    return timestamp.strftime(f_sql_timestamp)


def text_to_userdate(text: str) -> str:
    """
    Convertor from SQL-storing format '2023-01-02' to '02 Jan 2023' for humans. Used
    when preparing 'details', i.e. event news.
    Args:
        text: string with specific date format
    Returns:
        string with specific date format
    """
    return datetime.strptime(text, f_sql_date).strftime(f_hum)


def lfmdate_to_text(lfmdate: str) -> str:
    """
    Convertor for saving dates from last.fm '15 Nov 2023' to SQL '2023-11-15'. Used when
    saving scrobbles.
    Args:
        lfmdate: string with specific date format
    Returns:
        string with specific date format
    """
    return datetime.strptime(lfmdate, f_lfm).strftime(f_sql_date)


def text_to_date(text: str) -> datetime:
    """
    Convertor for saved date in SQL to timestamp
    """
    return datetime.strptime(text, f_sql_date)


def unix_to_text(unix: int) -> str:
    """
    Convertor for unix timestamp to human readable timestamp. For debugging purposes.
    Args:
        unix timestamp
    Returns:
        string with timestamp in readable format
    """
    return datetime.utcfromtimestamp(unix).strftime(f_sql_timestamp)
