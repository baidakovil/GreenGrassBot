#!/usr/bin/env python
# coding: utf-8

import os
from urllib.request import urlopen
from typing import List, Tuple, Dict, Union
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
import urllib.parse
from urllib.error import HTTPError
import html
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import logging

BOTFOLDER = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger('A.B')
logger.setLevel(logging.DEBUG)

def prettyThree(threeIndentDict, indent=2):
    prettyList = list()
    prettyString = str()
    for key1, value1 in threeIndentDict.items():
        prettyList.append(str(key1) + '\n')
        for key2, value2 in value1.items():
            prettyList.append(' ' * indent + str(key2) + '\n')
            for k, v in value2.items():
                prettyList.append(' ' * 2 * indent + k + ' : ' + v + '\n')
    prettyString = prettyString.join(prettyList)
    return prettyString


def alChar(text):
    alarmCharacters = ('-', '(', ')', '.', '+', '!', '?', '"', '#')
    safetext = "".join(
        [c if c not in alarmCharacters else f'\\{c}' for c in text])
    return safetext


def pageCacher(pageType: str,
               pageId: str,
               url: str
               ) -> str:
    """
    Function to fetch and save user's scrobbles/artist's as html pages.
    Search in cache -> if there is not, downloaded and saved in cache.

    Args:
    pageType: Type of html page, 'eventPage' or 'libraryPage'
    pageId: lower(artistName) or lastfmUser_page_pageNum string
    url: Page url 

    Returns:
    String with text of html page or empty string if page wasn't downloaded.
    """

    htmlText = ''
    if pageType == 'eventPage':
        safeCharacters = (' ', '.', ',', '_', '-', '!')
        safeArtistName = "".join(
            [c for c in pageId if c.isalnum() or c in safeCharacters])
        cacheFileName = os.path.join(
            BOTFOLDER, 'cache/concerts/', safeArtistName+'_lastfm.html')
        try:
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            logger.debug(f'{pageId} event page found in cache')
            cacheHandle.close()
        except FileNotFoundError:
            logger.info(f'Downloading {pageId} event page')
    elif pageType == 'libraryPage':
        userName = pageId.split('_')[0]
        cacheFileName = os.path.join(
            BOTFOLDER, 'cache/library/', f'{userName}/{pageId}.xml')
        try:
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            logger.debug(f'Library {pageId} found in cache')
            cacheHandle.close()
        except FileNotFoundError:
            Path(os.path.join(BOTFOLDER, 'cache/library/', userName)).mkdir(exist_ok=True)
            logger.info(f'Downloading {pageId} library page...')
    if htmlText == '':

        try:
            logger.debug('htmlByte will be loaded from url')
            htmlByte = urlopen(url).read()
            logger.debug('htmlByte was loaded from url')
            #  EXCEPTION CASE
        except HTTPError as e:
            if e.code == 403:
                logger.exception(f'EXCEPTION CASE№1.1HTTPError 403 catched: {e.__class__.__name__}, url: {url}')
                #  CASE№1.1 Stumbled when user hide it's tracks. 
                #           Nothing been did now except user notification, but further work needed. 
                return int(403)
            elif e.code == 404:
                logger.exception(f'EXCEPTION CASE№1.2 HTTPError 404 catched: {e.__class__.__name__}, url: {url}')
                #  CASE№1.2 Stumbled when username was misspelled. 
                #           User notification.
                return int(404)
            else:
                logger.exception(f'EXCEPTION CASE№1.3. HTTPError with unfamiliar e.code: {e.code}. When url opened by pageCacher:, {e.__class__.__name__}, url: {url}')
                # CASE№1.3 Not stumbled yet.
                if isinstance(e.code, int):
                    logger.exception(f'EXCEPTION CASE№1.3A. Code {e.code} (int) will be returned')
                    return int(e.code)
                else:
                    logger.exception(f'EXCEPTION CASE№1.3B. e.code is not int: {e.code}. Code int(90) will be returned finally')
                    return int(90)            
        except Exception as e:
            logger.exception(
                f'EXCEPTION CASE№1.4 (not HTTPError). When url opened:, {e.__class__.__name__}, url: {url}. int(91) will be returned')
            # CASE№1.4 Not stumbled yet.
            return int(91)

        htmlText = htmlByte.decode()

        try:
            if pageType == 'libraryPage':
                Path(os.path.join(BOTFOLDER, 'cache/library/', userName)).mkdir(parents=True, exist_ok=True)
            cacheHandle = open(cacheFileName, 'w', encoding="utf-8")
            cacheHandle.write(htmlText)
            logger.info(f'Cache file been wrote: {cacheFileName}')
            cacheHandle.close()
        except Exception as e:
            logger.exception(f'EXCEPTION catched when writing downloaded html:,\
                 {e.__class__.__name__}, file: {cacheFileName}')
            f'EXCEPTION CASE 2.1.'
            return htmlText
        logger.debug('Done')
    return htmlText


def parserLibrary(lastfmUser: str, timeDelay: timedelta) -> Dict[str, int]:
    """
    Function to obtain scrobbles for last days=timeDelay from cache or from Last.fm.
    Uses pageCacher() to save/load cache and URLs.    

    Args:
    lastfmUser    - Last.fm username
    timeDelay     - Interval in days from now to fetch 

    Return 
    Dictionary with structure {artistName__date:quantity}
    """

    stopParsing = False
    today = datetime.utcnow()
    fromUnix = str(
        int((today - timeDelay).replace(tzinfo=timezone.utc, hour=0, minute=0,
                                        second=0, microsecond=0).timestamp()))

    def loadXML(pageNum):
        """
        page to access Last.fm with requests
        """
        lastfmApiUrl = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&limit=200&user={lastfmUser}&page={str(pageNum)}&from={fromUnix}&api_key={apiKey}'
        pageId = f'{lastfmUser}_page_{pageNum}'
        htmlText = pageCacher(pageType='libraryPage',
                              pageId=pageId, url=lastfmApiUrl)
        #  EXCEPTIONS CASE
        if isinstance(htmlText, int):
            return False, htmlText, 0
        #  NORMAL CASE
        else:
            root = ET.fromstring(htmlText)
            status = root.attrib['status']
            totalPages = int(root[0].get('totalPages'))
        return root, status, totalPages

    artistList = dict()
    with open(os.path.join(BOTFOLDER, 'apikey')) as file:
        apiKey = file.read()

    #  First page
    root, status, totalPages = loadXML(pageNum=1)
    #  EXCEPTION CASE
    if isinstance(status, int):
        return status
    elif status != 'ok': 
        logger.error(f'Tried to load first page, but status is not ok. I wont parse XML')
        return 99
    else:
        logger.info(f'Will load XMLs from Last.fm. Total:{totalPages} pages')
        if totalPages >= 100:
            logger.info('Only 100 pages will be loaded')

    for pageCurrent in range(1,totalPages+1):
        if pageCurrent != 1:
            root, status, totalPages = loadXML(pageNum=pageCurrent)
        # EXCEPTION CASE
        if isinstance(status, int):
            return status
        elif status != 'ok': 
            logger.error(f'Tried to load {pageCurrent} page, but status is not ok. I wont parse XML')
            return 99
        else:
            for track in root[0].findall('track'):
                if not track.attrib.get('nowplaying') == 'true':
                    artistDate = '__'.join([
                                            html.unescape(track.find('artist').text),
                                            track.find('date').text.split(',')[0]
                                            ])
                    artistList[artistDate] = artistList.get(artistDate,0) + 1
    return artistList


def parserLastfmEvent(htmlList: List[str],
                     eventArtist: str,
                     sentEvents: pd.DataFrame,
                         ) -> pd.DataFrame:
    """
    Function to parse html file and return dataframe with concert information.

    Args:
    htmlList    - html file as list of strings
    eventArtist - lower(artistName)
    sentEvents  - events than should be excepted from final dataframe

    Returns:
    Concert information
    """

    htmlIterator = iter(htmlList)
    line = next(htmlIterator)
    oldEventsCount = 0
    artistEventData = list()
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
            eventId = eventArtist + '_in_' + eventTime + '_in_' + eventVenue
            eventNumber = ''
            if not sentEvents.isin([eventId]).values.any():
                artistEventList = list([eventId, eventArtistPaged, eventTime, eventVenue, eventCity, eventCountry])
                artistEventData.append(artistEventList)
            else:
                oldEventsCount += 1
    except StopIteration:
        if oldEventsCount != 0:
            logger.debug(f'{oldEventsCount} sent events found. ')
            if artistEventData == [] :
                logger.debug(f'No concerts from {eventArtist}')
            else :
                logger.debug(f'Done with {eventArtist}')
    return artistEventData


def getLastfmEvents(lastfmUser: str,
                    timeDelay: timedelta,
                    minListens: int,
                    places: Dict[str, str],
                    sentEvents: pd.DataFrame,
                    ) -> pd.DataFrame:
    """
    Function to fetch new concerts from Last.fm. 
    Uses parserLibrary(pageCacher()) to get scrobbles.
    Uses parserLastfmEvent(pageCacher()) to get events.

    Args:
    lastfmUser    - Last.fm username
    timeDelay     - Number of days for which events will be loaded
    minListens    - User preference, min number of listens for
                    a day for notice about events
    places        - Geodata in format {country:city} to filter events
    sentEvents    - Dataframe from file {user_id}_ggb_lastEvents.csv

    Returns:
    Dataframe with concerts, with 7 cols.
    """

    eventsData = list()
    provedArtistSet = set()

    #  fetch user scrobbles from Last.fm
    artistList = parserLibrary(lastfmUser, timeDelay)
    #  EXCEPTIONS
    if isinstance(artistList, int):
        return artistList
    #  filter artists to minListens
    for artistDate, listens in artistList.items():
        if listens >= minListens:
            artist = artistDate.split('__')[0]
            if artist not in provedArtistSet:
                provedArtistSet.add(artist.lower())

    #  obtain concerts for filtered artists
    countArtist = 0
    provedArtistList = sorted(list(provedArtistSet))
    for eventArtist in provedArtistList:
        lastfmEventUrl = 'https://www.last.fm/music/' + \
            urllib.parse.quote(eventArtist, safe='') + '/+events'
        htmlText = pageCacher(pageType='eventPage',
                              pageId=eventArtist, url=lastfmEventUrl)
        if htmlText != '':
            htmlList = htmlText.splitlines()
            #  parsing html to get dataframe
            artistEventData = parserLastfmEvent(
                htmlList, eventArtist, sentEvents)
            #  adding unique (for this dataset) numbers to concerts for telegram command
            if len(artistEventData) > 0:
                countArtist += 1
                fillNumbers = 2 if countArtist < 100 else 3
                for eventList in artistEventData:
                    eventList.insert(0, f'/{str(countArtist).zfill(fillNumbers)}')
                    eventsData.append(eventList)
                artistEventData = []
    eventsDf = pd.DataFrame(eventsData,
                            columns=['eventnumber', 'eventid', 'eventartist', 'eventtime', 'eventvenue', 'eventcity', 
                            'eventcountry'])
    return eventsDf


def getInfoText(userId: int) -> Union[str, int]:
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

    # Reading user preferences and saved dataframes
    listOf = ['lastfmUser', 'timeDelay', 'minListens', 'places', 'sentEvents']
    lastfmUser, timeDelay, twice, places, sentEvents = readSett(listOf, userId)
    # Fetching concerts from Last.fm to dataframe (scrobbles needed)
    eventsDf = getLastfmEvents(lastfmUser, timedelta(
        days=int(timeDelay)), twice, places, sentEvents)
    # ERRORS
    if isinstance(eventsDf, int):
        if eventsDf == 403:
            infoText = alChar(f'Oops! We get error *403*: it seems _{lastfmUser}_\'s tracks are private.\nChange your Last.fm user settings to use this bot. No authentification needed fot this bot')
        elif eventsDf == 404:
            infoText =alChar(f'Ops! We get error *404*: it seems _{lastfmUser}_ is not a correct Last.fm username.')
        else:
            infoText = f'We get error *{eventsDf}* when load tracks from Last.fm. We\'ll check that soon'
        return infoText
    # Forming message for user
    elif isinstance(eventsDf, pd.DataFrame):
        if len(eventsDf) == 0:
            infoText = 'No new concerts'
        else:
            artistsDf = eventsDf[['eventnumber', 'eventartist']
                                ].drop_duplicates(subset='eventnumber')
            infoList = list()
            for i in artistsDf.index:
                eventNumber = artistsDf.at[i, 'eventnumber']
                safeArtistName = alChar(artistsDf.at[i, 'eventartist'])
                infoList.append(f'{eventNumber} {safeArtistName}')
            infoText = '\n*New Events* \n\n' + ' \n'.join(infoList)
    # add/rewrite those events to disk
    writeData(mode='lastEvents', id=userId, data=eventsDf)
    writeData(mode='addSentEvents', id=userId, data=eventsDf)
    return infoText


def getNewsText(userId, command):
    lastEvents = readData(mode='lastEvents', id=userId)
    # if (int(command[1:]) > len(lastEvents)) or (int(command[1:]) == 0):
    #     newsText = 'No such command'
    #     return newsText
    artistsDf = lastEvents.loc[lastEvents.eventnumber == command]
    ids = artistsDf['eventid'].sort_values()
    artist = artistsDf['eventartist'].iat[0]
    prevCountry = None
    newsText = list()
    for i in range(0, len(artistsDf)):
        event = artistsDf.loc[artistsDf.eventid == ids.iat[i]]
        eventTime = datetime.strptime(
            event.eventtime.values[0], '%Y-%m-%d').strftime('%d %b %Y')
        eventCountry = event.eventcountry.values[0]
        eventCity = event.eventcity.values[0]
        eventVenue = event.eventvenue.values[0]
        if (prevCountry is None) or (prevCountry != eventCountry):
            newsText.append(f'\nIn {eventCountry}\n')
        prevCountry = event.eventcountry.values[0]
        newsText.append(f'*{eventTime}* in {eventCity}, {eventVenue}\n')
    newsText = [alChar(string) for string in newsText]
    sentEvents = readData(mode='sentEvents', id=userId)
    new = ' *\(new\)*' if sentEvents['eventartist'].isin(
        [artist]).any().sum() > 0 else ''
    new = ''
    lastfmEventUrl = 'https://www.last.fm/music/' + \
        urllib.parse.quote(artist, safe='') + '/+events'
    newsText.insert(
        0, f'[_{alChar(artist)}_]({alChar(lastfmEventUrl)}) events{new}\n')
    newsText = ''.join(newsText)
    return newsText


def writeData(mode: str, id: str, data: Union[str, pd.DataFrame]) -> None:
    """
    Function to write user data to disk.
    Uses readData() when mode=''addSentEvents.

    Args:
    mode    - 'addSentEvents': delete events sent yesterday or earlier from 
                               {id}_ggb_lastEvents.csv, add events in data to this file.
              'lastEvents'   : rewrite data/{id}__ggb_sentEvents.csv with data.
              'settings'     : rewrite data/{id}_ggb_settings.csv with data.
    id      - telegram user_id
    data    - events or settings

    Returns:
    Nothing.
    """
    if mode == 'addSentEvents':
        if not data.empty:
            data.loc[:, 'eventnumber'] = ''
        prevSentEvents = readData(mode='sentEvents', id=id)
        if not prevSentEvents.empty:
            today = pd.to_datetime(date.today())
            eventTimes = pd.to_datetime(prevSentEvents.loc[:, 'eventtime'])
            oldEvents = prevSentEvents[eventTimes < today].index
            prevSentEvents.drop(labels=oldEvents, inplace=True)
            logger.info(f'{len(oldEvents)} events was deleted from sent events')
        sentEvents = pd.concat(
            [prevSentEvents, data], ignore_index=True)
        sentEvents.reset_index(drop=True, inplace=True)
        dataFilename = os.path.join(
            BOTFOLDER, 'data/', id + '_ggb_sentEvents.csv')
        fileHandle = open(dataFilename, 'w', encoding="utf-8")
        sentEvents.to_csv(path_or_buf=fileHandle,
                          sep='\t', lineterminator='\n')
        
    elif mode == 'lastEvents':
        dataFilename = os.path.join(
            BOTFOLDER, 'data/', id + '_ggb_lastEvents.csv')
        fileHandle = open(dataFilename, 'w', encoding="utf-8")
        data.to_csv(path_or_buf=fileHandle, sep='\t', lineterminator='\n')
    elif mode == 'settings':
        dataFilename = os.path.join(
            BOTFOLDER, 'data/', id + '_ggb_settings.csv')
        fileHandle = open(dataFilename, 'w', encoding="utf-8")
        fileHandle.write(data)
    else:
        logger.warning(f'{mode} is wrong mode for writing')
    fileHandle.close()
    logger.info(f'{mode} is written to: {dataFilename}')


def readData(mode: str, id: int) -> Union[pd.DataFrame, Dict[str, str]]:
    """
    Function to read user data from disk. 
    Returns empty dataframe or empty dict if there is no csv file found.

    Args:
    mode    -   'lastEvents' - return pd.DataFrame with events stored in {id}_ggb_lastEvents.csv
                'sentEvents' - return pd.DataFrame with events stored in {id}_ggb_lastEvents.csv
                'settings'   - return dict {setting:value} stored in {id}_ggb_settings.csv
    id      -    telegram user_id

    Return:
    Data requested.
    """

    if mode in ['lastEvents', 'sentEvents']:
        try:
            if mode == 'lastEvents':
                dataFilename = os.path.join(
                    BOTFOLDER, 'data/', id + '_ggb_lastEvents.csv')
            elif mode == 'sentEvents':
                dataFilename = os.path.join(
                    BOTFOLDER, 'data/', id + '_ggb_sentEvents.csv')
            fileHandle = open(dataFilename, 'r', encoding="utf-8")
            data = pd.read_csv(filepath_or_buffer=fileHandle,
                               sep='\t', lineterminator='\n', index_col=0)
            fileHandle.close()
            logger.debug(f'{mode} data was read from: {dataFilename}')
        except FileNotFoundError:
            data = pd.DataFrame([], columns=['eventnumber', 'eventid', 'eventartist',
                                             'eventtime', 'eventvenue', 'eventcity', 'eventcountry'])
            logger.info(f'{mode} data not found. Empty DF created')
    elif mode == 'settings':
        try:
            dataFilename = os.path.join(
                BOTFOLDER, 'data/', id + '_ggb_settings.csv')
            fileHandle = open(dataFilename, 'r', encoding="utf-8")
            settings = fileHandle.read()
            fileHandle.close()
        except FileNotFoundError:
            logger.info(f'EXCEPTION FileNotFoundError for requested settings file {dataFilename}')
            settings = ''
        if settings == '':
            data = {
                'minListens':2,
                'timeDelay':2,
                'places':{'*':'*'}
                }
        else:
            data = eval(settings)
        logger.debug(f'{mode} data was read from: {dataFilename}')
    else:
        logger.debug(f'{mode} is wrong mode for writing')
    return data


def readSett(listOf: str, id: str) -> tuple:
    """
    Function to obtain user data (events, settings) by single request.
    Uses readData().
    Return ordered tuple by order of datatype or setting in listOf.

    Args:
    listOf - list of named settings to return
    id     - telegram user_id

    Return:
    [tuple([list or pd.DataFrame])]
    """

    data = []
    settList = {'lastfmUser', 'timeDelay', 'minListens', 'places'}
    if len(set(listOf).intersection(settList)):
        settings = readData('settings', id)  # string
    for sett in listOf:
        if sett in settList:
            data.append(settings[sett])  # value to list
        elif sett in ('sentEvents', 'lastEvents'):
            data.append(readData(sett, id))  # dataset to list
    return tuple(data)


def writeSett(id, sett, value):
    settings = readData('settings', id)
    settings[sett] = value
    writeData(mode='settings', id=id, data=str(settings))


def addCountry(countryAnswer, userId):
    fileHandle = open('data/WorldCountryList.csv', 'r', encoding="utf-8")
    data = pd.read_csv(filepath_or_buffer=fileHandle,
                       sep='\t', lineterminator='\n', index_col=0)
    try:
        mask = np.column_stack(
            [data[col] == countryAnswer.strip().lower() for col in data])
        addedCountry = data.loc[mask].iat[0, 0]
        places = readSett(['places'], userId)[0]
        if places == ():
            places = dict()
        places[countryAnswer] = []
        writeSett(userId, 'places', places)
    except IndexError:
        addedCountry = False
    fileHandle.close()
    return addedCountry


def addCity(cityAnswer, country, userId):
    fileHandle = open('data/RussiaCityList.csv', 'r', encoding="utf-8",)
    data = pd.read_csv(filepath_or_buffer=fileHandle,
                       sep='\t', lineterminator='\n', index_col=0)
    try:
        mask = np.column_stack(
            [data[col] == cityAnswer.strip().lower() for col in data])
        addedCity = data.loc[mask].iat[0, 0]
        places = readSett(['places'], userId)[0]
        if addedCity in places[country]:
            return addedCity
        places[country].append(addedCity)
        writeSett(userId, 'places', places)
    except IndexError:
        addedCity = False
    fileHandle.close()
    return addedCity


# userId = '144297913'
# readData(mode='sentEvents', id='userId')
# listOf = ['lastfmUser', 'timeDelay', 'minListens', 'places', 'sentEvents']
# lastfmUser, timeDelay, twice, places, sentEvents = readSett(listOf, userId)
# command = '/10'
# infoText = getNewsText(userId, command)
# logger.info(infoText)
# writeSett(userId, 'userId', 144297913)
# writeSett(userId, 'lastfmUser', 'Anastasia20009')
# writeSett(userId, 'timeDelay', 2)
# writeSett(userId, 'minListens', 2)
# writeSett(userId, 'places', {})
