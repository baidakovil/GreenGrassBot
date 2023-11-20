import html
import logging
import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Union
from urllib.request import urlopen


from config import Cfg
from services.message_service import i34g
from services.custom_classes import Event
from ui.error_builder import error_text

logger = logging.getLogger("A.par")
logger.setLevel(logging.DEBUG)

CFG = Cfg()
api_key = os.getenv("API_KEY")


async def check_valid_lfm(lfm: str, user_id: int) -> Tuple[bool, str]:
    """
    Check if lastfm account is valid and notprivate
    Args:
        lfm: last.fm account to check
    Returns:
        tuple with bool and string: (valid or not, error text)
    # TODO UnicodeEncodeError when non-unicode characters in nickname
    """
    lfm_api_url = await i34g(
        'parse_services.getrecenttracks',
        limit=10,
        lfm=artist_at_url(name_to_url=lfm),
        page=1,
        from_unix=0,
        api_key=api_key,
        locale='en',
    )
    loaded_page = page_loader(lfm_api_url)
    return (
        (False, await error_text(loaded_page, lfm, user_id=user_id))
        if isinstance(loaded_page, int)
        else (True, '')
    )


def from_unix() -> int:
    """
    Calculate unix timestamp correspond to "00:00:00 UTC of day that was
    DAYS_INITIAL_TIMEDELAY days ago". There is no explicit need of reset to 00:00:00,
    that doing for consistency, easy debugging, round numbers.
    Returns:
        unix timestamp
    """
    period = CFG.DAYS_INITIAL_TIMEDELAY
    moment_period_ago = datetime.utcnow() - timedelta(days=period)
    moment_period_ago_00_00_00 = moment_period_ago.replace(
        tzinfo=timezone.utc, hour=0, minute=0, second=0, microsecond=0
    )
    unix_timestamp = moment_period_ago_00_00_00.timestamp()
    return int(unix_timestamp)


async def parser_scrobbles(lfm: str) -> Union[int, Dict]:
    """
    Obtain scrobbles for last CFG.DAYS_INITIAL_TIMEDELAY days.
    #TODO: add storing of time of last scrobble loading: there is no need to load what
    was loaded.
    Args:
        lastfmUser: lastfm username
    Returns:
        Dict with structure {artist_name: {date:count} } if there is events, or empty
        dict, or int with error code.
    """
    current_page, total_pages = 1, 1
    artist_dict = dict()
    sleep_time = CFG.SECONDS_SLEEP_XMLLOAD

    while current_page <= total_pages:
        lfm_url = await i34g(
            'parse_services.getrecenttracks',
            limit=CFG.QTY_SCROBBLES_XML,
            lfm=artist_at_url(name_to_url=lfm),
            page=current_page,
            from_unix=from_unix(),
            api_key=api_key,
            locale='en',
        )
        xml = page_loader(url=lfm_url)
        time.sleep(sleep_time)
        if isinstance(xml, int):
            return xml

        root = ET.fromstring(xml)
        if current_page == 1:
            total_pages = min(100, int(root[0].get("totalPages")))
            logger.info(f"Going to load {total_pages} XML pages")
        tracks = root[0].findall("track")
        if not tracks:
            return {}

        for track in root[0].findall("track"):
            if not track.attrib.get("nowplaying") == "true":
                artist = html.unescape(track.find("artist").text)
                date = track.find("date").text.split(",")[0]
                if not isinstance(artist_dict.get(artist), dict):
                    artist_dict[artist] = dict()
                artist_dict[artist][date] = artist_dict[artist].get(date, 0) + 1
        current_page += 1
    logger.info(f"All XMLs are loaded")
    return artist_dict


def page_loader(url: str) -> Union[int, str]:
    """
    Load pages at url.
    Args:
        url
    Returns:
        page text OR integer error code given by urlopen OR 90
    """
    try:
        page_bytes = urlopen(url)
    except Exception as e:
        return e.code if isinstance(e.code, int) else int(90)
    page_text = page_bytes.read().decode()
    logger.debug(f"URL loaded: ...{url[-95:]}")
    return page_text


def artist_at_url(name_to_url: str) -> str:
    """
    Convert artist name or lfm account name into name used in URL.
    Args:
        name_to_url: string to replace special characters in string using the %xx
        escape.
    Returns:
        string with replaced special characters if any.
    """
    return urllib.parse.quote(name_to_url, safe='')


async def parser_event(art_name: str) -> Union[int, List[Event]]:
    """
    Load event pages and parse html file. Return list of Event objects or int if

    Args:
        art_name: artist name to load events for
    Returns:
        list of Events objects of integer with error
    """
    url = await i34g(
        'parse_services.lastfmeventurl', artist=artist_at_url(art_name), locale='en'
    )
    page = page_loader(url)
    time.sleep(CFG.SECONDS_SLEEP_HTMLLOAD)
    if isinstance(page, int):
        return page

    iterator = iter(page.splitlines())
    line = next(iterator)
    events = []
    try:
        while 'class="header-new-title" itemprop="name">' not in line:
            line = next(iterator)
        for _ in range(0, 1000):
            while 'class="events-list-item-date"' not in line:
                line = next(iterator)
            event_date = line.split('"')[5][:10]
            while 'class="events-list-item-venue--title"' not in line:
                line = next(iterator)
            line = next(iterator)
            eventVenue = html.unescape(line.strip())
            while 'class="events-list-item-venue--address"' not in line:
                line = next(iterator)
            line = next(iterator)
            eventAddress = line.strip()
            event_city = html.unescape(eventAddress.rsplit(",", maxsplit=1)[0])
            event_country = html.unescape(eventAddress.rsplit(", ", maxsplit=1)[1])
            events.append(
                Event(
                    place=eventVenue,
                    locality=event_city,
                    country=event_country,
                    event_date=event_date,
                    event_source='lastfm',
                    link=url,
                    lineup=[art_name],
                )
            )
    except StopIteration:
        logger.debug(f'Parsed event page for {art_name}')
    return events
