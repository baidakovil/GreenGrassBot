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
"""This file contains functions to access last.fm service, both API and HTTP ways."""

import asyncio
import html
import logging
import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union, cast
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from xml.etree.ElementTree import Element

import config as cfg
from db.db_service import Db
from services.custom_classes import Event
from services.logger import logger
from services.message_service import i34g
from services.timeconv_service import text_to_date, unix_to_text
from ui.error_builder import error_text

logger = logging.getLogger("A.par")
logger.setLevel(logging.DEBUG)


api_key = os.environ["API_KEY"]

db = Db()


async def check_valid_lfm(lfm: str, user_id: int) -> Tuple[bool, str]:
    """
    Check if lastfm account is valid and notprivate
    Args:
        lfm: last.fm account to check
    Returns:
        tuple with bool and string: (valid or not, error text)
    # TODO UnicodeEncodeError when non-unicode characters in nickname
    """
    lfm_quoted = artist_at_url(name_to_url=lfm)
    if lfm == lfm_quoted:
        lfm_api_url = await i34g(
            'parse_services.getrecenttracks',
            limit=10,
            lfm_noalarm=lfm_quoted,
            page=1,
            from_unix=0,
            api_key=api_key,
            locale=cfg.LOCALE_TECHNICAL_STORE,
        )
        loaded_page = page_loader(lfm_api_url)
    else:
        loaded_page = int(93)
    return (
        (False, await error_text(loaded_page, lfm, user_id=user_id))
        if isinstance(loaded_page, int)
        else (True, '')
    )


def timedelay_moment() -> datetime:
    """
    Calculate unix timestamp correspond to "00:00:00 UTC of the day that was
    DAYS_INITIAL_TIMEDELAY days ago". There is no explicit need of reset to 00:00:00,
    that doing for consistency, easy debugging, round numbers.
    Args:
        no, it reads from configs
    Returns:
        unix timestamp
    """
    period = cfg.DAYS_INITIAL_TIMEDELAY
    moment_period_ago = datetime.utcnow() - timedelta(days=period)
    moment_period_ago_00_00_00 = moment_period_ago.replace(
        tzinfo=timezone.utc, hour=0, minute=0, second=0, microsecond=0
    )
    return moment_period_ago_00_00_00


async def last_scrobble_moment(user_id: int, lfm: str) -> Optional[datetime]:
    """
    Calculate unix timestamp correspond to "00:00:00 UTC of the day of last saved
    scrobble" to avoid excess scrobble loads
    """
    last_scrobble_day = await db.rsql_lastdayscrobble(user_id=user_id, lfm=lfm)
    if last_scrobble_day is None:
        return None

    last_scrobble_day = text_to_date(last_scrobble_day)
    last_scrobble_day_00_00_00 = last_scrobble_day.replace(
        tzinfo=timezone.utc, hour=0, minute=0, second=0, microsecond=0
    )
    return last_scrobble_day_00_00_00


async def load_scr_moment(user_id: int, lfm: str) -> int:
    """
    Calculate appropriate moment "from_unix" to load scrobbles from. If there no scrob-
    bles newer than cfg.DAYS_INITIAL_TIMEDELAY days ago, it load new scrobbles. Include
    all the day when last scrobbles saved since 00:00 AM.
    Args:
        user_id: Tg user_id field
        lfm: Last.fm profile
    Returns:
        unix timestamp
    """

    timedelay_load = timedelay_moment()
    logger.debug('Max timedelay to load scrobbles: %s', timedelay_load)
    last_scrobble = await last_scrobble_moment(user_id, lfm)
    if last_scrobble is None:
        logger.debug('No previous scrobbles found for user_id %s, lfm %s', user_id, lfm)
        load_scrobble_moment = timedelay_load
    else:
        logger.debug(
            'Previous scrobble found for user_id %s, lfm %s: %s',
            user_id,
            lfm,
            last_scrobble,
        )
        load_scrobble_moment = max(timedelay_load, last_scrobble)
    from_unix = int(load_scrobble_moment.timestamp())
    logger.debug(
        'Conclusion: will load scrobbles from time: %s', unix_to_text(from_unix)
    )
    return from_unix


async def parser_scrobbles(user_id: int, lfm: str) -> Union[int, Dict]:
    """
    Obtain scrobbles for last time, from load_scr_moment() moment.
    Args:
        lfm: lastfm username
    Returns:
        Dict with structure {artist_name: {date:count} } if there is events, or empty
        dict, or int with error code.
    """
    current_page, total_pages = 1, 1
    artist_dict = {}

    while current_page <= total_pages:
        lfm_url = await i34g(
            'parse_services.getrecenttracks',
            limit=cfg.QTY_SCROBBLES_XML,
            lfm_noalarm=artist_at_url(name_to_url=lfm),
            page=current_page,
            from_unix=await load_scr_moment(user_id, lfm),
            api_key=api_key,
            locale=cfg.LOCALE_TECHNICAL_STORE,
        )
        xml = page_loader(url=lfm_url)
        await asyncio.sleep(cfg.SECONDS_SLEEP_XMLLOAD)
        if isinstance(xml, int):
            return xml

        root = ET.fromstring(xml)
        if current_page == 1:
            total_pages_xml = root[0].get("totalPages")
            total_pages = min(100, int(cast(int, total_pages_xml)))
            logger.info(
                "Parser will load %s XMLs for user_id: %s, lfm: %s",
                total_pages,
                user_id,
                lfm,
            )

        tracks = root[0].findall("track")
        if not tracks:
            return {}

        for track in root[0].findall("track"):
            if not track.attrib.get("nowplaying") == "true":
                track_element = track.find("artist")
                assert isinstance(track_element, Element)
                assert isinstance(track_element.text, str)
                artist = html.unescape(track_element.text)
                date_element = track.find("date")
                assert isinstance(date_element, Element)
                assert isinstance(date_element.text, str)
                date = date_element.text.split(",")[0]
                if not isinstance(artist_dict.get(artist), dict):
                    artist_dict[artist] = {}
                artist_dict[artist][date] = artist_dict[artist].get(date, 0) + 1
        current_page += 1
    logger.info("All XMLs are loaded for user_id %s, lfm %s", user_id, lfm)
    return artist_dict


def page_loader(url: str) -> Union[int, str]:
    """
    Load pages at url.
    Args:
        url
    Returns:
        page text OR integer error code given by urlopen OR 90
        #TODO alarm admin about these
    """
    try:
        with urlopen(url) as page_bytes:
            page_text = page_bytes.read().decode()
    except HTTPError as e:
        return e.code if isinstance(e.code, int) else int(90)
    except URLError:
        return int(91)
    except OSError:
        return int(92)
    logger.debug("URL loaded: ...%s", url[-95:])
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
        'parse_services.lastfmeventurl',
        artist=artist_at_url(art_name),
        locale=cfg.LOCALE_TECHNICAL_STORE,
    )
    page = page_loader(url)

    await asyncio.sleep(cfg.SECONDS_SLEEP_HTMLLOAD)
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
            event_venue = html.unescape(line.strip())
            while 'class="events-list-item-venue--address"' not in line:
                line = next(iterator)
            line = next(iterator)
            event_address = line.strip()
            event_city = html.unescape(event_address.rsplit(",", maxsplit=1)[0])
            event_country = html.unescape(event_address.rsplit(", ", maxsplit=1)[1])
            events.append(
                Event(
                    place=event_venue,
                    locality=event_city,
                    country=event_country,
                    event_date=event_date,
                    event_source='lastfm',
                    link=url,
                    lineup=[art_name],
                )
            )
    except StopIteration:
        logger.debug('Parsed event page for %s', art_name)
    return events
