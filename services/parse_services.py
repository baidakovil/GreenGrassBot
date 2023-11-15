import os
from typing import List, Dict
from datetime import datetime, timedelta, timezone
import urllib.parse
from urllib.request import urlopen
from urllib.error import HTTPError
import xml.etree.ElementTree as ET
import html
import time

import logging

from services.custom_classes import Event
from config import Cfg

logger = logging.getLogger('A.par')
logger.setLevel(logging.DEBUG)

CFG = Cfg()
apiKey = os.getenv("API_KEY")


def check_valid_lfm(userId, lastfmUser, db):
    """
    Check if lastfm account is valid and notprivate
    """
    lastfmApiUrl = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&limit=200&user={lastfmUser}&page=1&api_key={apiKey}'
    htmlText = pageLoader(url=lastfmApiUrl)
    if isinstance(htmlText, int):
        if htmlText == 403:
            return (False, f'Oops! We get error *403*: it seems _{lastfmUser}_\'s tracks are private.\nChange your Last.fm user settings to use this bot. No authentification needed fot this bot')
        elif htmlText == 404:
            return (False, f'Ops! We get error *404*: it seems _{lastfmUser}_ is not a correct Last.fm username.')
        else:
            return (False, f'O! We get error *{htmlText}* when load tracks from Last.fm for {lastfmUser}. We\'ll check that soon')
    else:
        return (True, '')


def parserLibrary(lastfmUser: str) -> Dict:
    """
    Function to obtain scrobbles for last days=timeDelay from cache or from Last.fm.
    Uses pageCacher() to save/load cache and URLs.    

    Args:
    lastfmUser    - Last.fm username
    timeDelay     - Interval in days from now to fetch 

    Return 
    Dictionary with structure {artistName__date:quantity}
    """
    timeDelay = CFG.DAYS_INITIAL_TIMEDELAY
    fromUnix = int((datetime.utcnow() - timedelta(days=int(timeDelay))).replace(tzinfo=timezone.utc, hour=0, minute=0,
                                                                                second=0, microsecond=0).timestamp())
    pageCurrent, totalPages = 1, 1
    artistDict = dict()
    while pageCurrent <= totalPages:
        lastfmApiUrl = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&limit=200&user={lastfmUser}&page={pageCurrent}&from={fromUnix}&api_key={apiKey}'
        htmlText = pageLoader(url=lastfmApiUrl)
        time.sleep(CFG.SECONDS_SLEEP_JSONLOAD)
        if isinstance(htmlText, int):
            return htmlText
        root = ET.fromstring(htmlText)
        status = root.attrib['status']
        if pageCurrent == 1:
            totalPages = min(100, int(root[0].get('totalPages')))
            logger.info(f'Will load {totalPages} pages')
        for track in root[0].findall('track'):
            if not track.attrib.get('nowplaying') == 'true':
                artist = html.unescape(track.find('artist').text)
                date = track.find('date').text.split(',')[0]
                if not isinstance(artistDict.get(artist), dict):
                    artistDict[artist] = dict()
                artistDict[artist][date] = artistDict[artist].get(date, 0)+1
        pageCurrent += 1
    return artistDict


def pageLoader(url: str) -> str:

    logger.debug(f'Will load url: {url}')
    try:
        htmlByte = urlopen(url)
    except HTTPError as e:
        if e.code == 403:
            logger.warning(
                f'EXCEPTION CASE№1.1 HTTPError 403 catched: {e.__class__.__name__}, url: {url}')
            #  CASE№1.1 Stumbled when user hide it's tracks.
            return int(403)
        elif e.code == 404:
            logger.warning(
                f'EXCEPTION CASE№1.2 HTTPError 404 catched: {e.__class__.__name__}, url: {url}')
            #  CASE№1.2 Stumbled when username was misspelled.
            return int(404)
        else:
            logger.warning(
                f'EXCEPTION CASE№1.3. HTTPError with unfamiliar e.code: {e.code}. When url opened by pageCacher:, {e.__class__.__name__}, url: {url}')
            # CASE№1.3 Not stumbled yet.
            return int(90)
    except Exception as e:
        logger.warning(
            f'EXCEPTION CASE№1.4 (not HTTPError). When url opened:, {e.__class__.__name__}, url: {url}. int(91) will be returned')
        # CASE№1.4 Not stumbled yet.
        return int(91)
    htmlText = htmlByte.read().decode()
    logger.debug(f'URL opened ok')
    return htmlText


def parserLastfmEvent(eventArtist: str) -> List[Event]:
    """
    Load event pages with pageLoader() and parse html file.

    Args:
    eventArtist - artist name

    Returns:
    List with Events
    """
    url = f"https://www.last.fm/music/{urllib.parse.quote(eventArtist,safe='')}/+events"
    htmlText = pageLoader(url=url)
    time.sleep(CFG.SECONDS_SLEEP_HTMLLOAD)
    if isinstance(htmlText, int):
        return htmlText
    htmlIterator = iter(htmlText.splitlines())
    line = next(htmlIterator)
    eventList = []
    try:
        while 'class="header-new-title" itemprop="name">' not in line:
            line = next(htmlIterator)
        eventArtistPaged = line.split('itemprop="name">')[1].split('<')[0]
        for i in range(0, 100):
            while 'class="events-list-item-date"' not in line:
                line = next(htmlIterator)
            eventTime = line.split('"')[5][:10]
            while 'class="events-list-item-venue--title"' not in line:
                line = next(htmlIterator)
            line = next(htmlIterator)
            eventVenue = html.unescape(line.strip())
            while 'class="events-list-item-venue--address"' not in line:
                line = next(htmlIterator)
            line = next(htmlIterator)
            eventAddress = line.strip()
            eventCity = html.unescape(eventAddress.rsplit(',', maxsplit=1)[0])
            eventCountry = html.unescape(
                eventAddress.rsplit(', ', maxsplit=1)[1])
            ev = Event(
                place=eventVenue,
                locality=eventCity,
                country=eventCountry,
                event_date=eventTime,
                event_source='lastfm',
                link=url,
                lineup=[eventArtist])
            eventList.append(ev)
    except StopIteration:
        logger.debug(f'Done with {eventArtist}')
    return eventList
