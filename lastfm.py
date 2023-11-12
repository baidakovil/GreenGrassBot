import os
import asyncio
from urllib.request import urlopen
from datetime import datetime, timedelta, timezone
import urllib.parse
from urllib.error import HTTPError
import html
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Union
import logging
from dotenv import load_dotenv
from config import Cfg
from db import ArtScrobble, Event, User, UserSettings
from db import date_to_text
import time

CFG = Cfg()

load_dotenv('.env')
apiKey = os.getenv("API_KEY")

logger = logging.getLogger('A.B')
logger.setLevel(logging.DEBUG)


def text_to_userdate(text):
    f_text = '%Y-%m-%d'
    f_user = '%d %b %Y'
    return datetime.strptime(text, f_text).strftime(f_user)


def alChar(text):
    alarmCharacters = ('-', '(', ')', '.', '+', '!', '?', '"', '#')
    safetext = "".join(
        [c if c not in alarmCharacters else f'\\{c}' for c in text])
    return safetext


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


def getInfoText(user_id: int, db) -> str:
    """
    At this stage, should be run by coroutine function 'getEventsJob' on dialog's question 'Now, run the search?'
    Used getLastfmEvents() to get dataframe with events.
    Read settings with readSett().
    Saves obtained events with writeData().
    Returns short info about which artists have new concerts. 
    Or error text.

    Arguments:
    userId      - telegram userId from job
    
    Return:
    Markdown-formatted string with artists
    OR
    String 'No new concerts'
    OR
    String with error info for user.
    """
    shorthandCount = int(asyncio.run(db.rsql_maxshorthand(user_id)))
    print(f'get shorthandCount: {shorthandCount}')
    fillNumbers = 2 if CFG.INTEGER_MAX_SHORTHAND < 100 else 3
    lastfmUsers = asyncio.run(db.rsql_lfmuser(user_id))
    infoText = ''

    for lastfmUser in lastfmUsers:
        userArts = []
        #  Get and save scrobbles
        artistDict = parserLibrary(lastfmUser)
        if isinstance(artistDict, int):
            if artistDict == 403:
                infoText += alChar(
                    f'Oops! We get error *403*: it seems _{lastfmUser}_\'s tracks are private.\nChange your Last.fm user settings to use this bot. No authentification needed fot this bot')
            elif artistDict == 404:
                infoText += alChar(
                    f'Ops! We get error *404*: it seems _{lastfmUser}_ is not a correct Last.fm username.')
            else:
                infoText += f'We get error *{eventsDf}* when load tracks from Last.fm for {lastfmUser}. We\'ll check that soon'
            continue
        elif isinstance(artistDict, dict):
            if len(artistDict.keys()):
                for art_name in artistDict.keys():
                    for date, qty in artistDict[art_name].items():
                        date = datetime.strptime(
                            date, '%d %b %Y').strftime('%Y-%m-%d')
                        ars = ArtScrobble(
                            user_id=user_id,
                            art_name=art_name,
                            scrobble_date=date,
                            lfm=lastfmUser,
                            scrobble_count=qty,
                        )
                        asyncio.run(db.wsql_scrobbles(ars=ars))
        # logger.debug(f'Scrobbles for lfm {lastfmUser}: {artistDict}')

        #  Get and save events
        for art_name in artistDict.keys():
            if asyncio.run(db.rsql_artcheck(user_id,
                                            art_name,
                                            )):
                # logger.debug(f'Will check: {art_name}')
                eventList = parserLastfmEvent(art_name)
                if isinstance(eventList, str):
                    logger.warning(
                        f'OOOP! Error {eventList} when load events for {art_name}')
                    continue
                asyncio.run(db.wsql_events_lups(eventList))
                asyncio.run(db.wsql_artcheck(art_name))
            # else:
                # logger.debug(f"Won't check: {art_name}")
            if asyncio.run(db.rsql_finalquestion(user_id, art_name)):
                userArts.append(art_name)
        logger.debug(f'Final arts for user {lastfmUser}: {userArts}')

        #  Create text for user
        if not len(userArts):
            infoText += alChar(f'\nNo new events for *{lastfmUser}*\n')
        else:
            infoList = list()
            userArts = sorted(userArts)
            for art_name in userArts:
                shorthandCount = (
                    shorthandCount+1) if shorthandCount < CFG.INTEGER_MAX_SHORTHAND else 1
                shorthand = f'/{str(shorthandCount).zfill(fillNumbers)}'
                infoList.append(f'{shorthand} {alChar(art_name)}')
                asyncio.run(db.wsql_sentarts(user_id, art_name))
                asyncio.run(db.wsql_lastarts(
                    user_id, shorthandCount, art_name))
            infoText += f'\n*New Events for {lastfmUser}* \n\n' + \
                ' \n'.join(infoList) + '\n'
    return infoText


def getNewsText(userId: int, shorthand: str, db) -> str:
    shorthand = int(shorthand)
    eventsList = asyncio.run(db.rsql_getallevents(userId, shorthand))
    if eventsList:
        prevCountry = None
        newsText = list()
        for event in eventsList:
            eventArtist = event[0]
            eventDate = text_to_userdate(event[1])
            eventVenue = event[2]
            eventCity = event[3]
            eventCountry = event[4]
            if (prevCountry is None) or (prevCountry != eventCountry):
                newsText.append(f'\nIn {eventCountry}\n')
            prevCountry = eventCountry
            newsText.append(f'*{eventDate}* in {eventCity}, {eventVenue}\n')
        newsText = [alChar(string) for string in newsText]
        lastfmEventUrl = f"https://www.last.fm/music/{urllib.parse.quote(eventArtist, safe='')}'/+events"
        newsText.insert(
            0, f'[_{alChar(eventArtist)}_]({alChar(lastfmEventUrl)}) events\n')
        newsText = ''.join(newsText)
        return newsText
    else:
        return 'No events under this shortcut'
