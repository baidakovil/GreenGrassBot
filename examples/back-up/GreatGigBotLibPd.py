#!/usr/bin/env python
# coding: utf-8


from urllib.request import urlopen
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.parse
import html
import xml.etree.ElementTree as ET
import pandas as pd


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
    alarmCharacters = ('-', '(', ')', '.', '+', '!', '?', '"')
    safetext = "".join([c if c not in alarmCharacters else f'\\{c}' for c in text])
    return safetext


def pageCacher(pageType, pageId, url):
    htmlText = ''
    if pageType == 'eventPage':
        safeCharacters = (' ', '.', ',', '_', '-', '!')
        safeArtistName = "".join([c for c in pageId if c.isalnum() or c in safeCharacters])
        cacheFileName = 'cache/concerts/' + safeArtistName + '_lastfm.html'
        try:
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            #             print( pageId + ' event page found in cache..',end='')
            cacheHandle.close()
        except FileNotFoundError:
            print('Downloading {} event page...'.format(pageId), end='')
    elif pageType == 'libraryPage':
        cacheFileName = 'cache/library/{}/{}.xml'.format(pageId.split('_')[0], pageId)
        try:
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            #             print( 'Library {} found in cache..'.format(pageId),end='')
            cacheHandle.close()
        except FileNotFoundError:
            Path('cache/library/' + pageId.split('_')[0]).mkdir(exist_ok=True)
    #             print('Downloading {} library page...'.format(pageId), end = '')
    if htmlText == '':
        htmlByte = urlopen(url).read()
        htmlText = htmlByte.decode()
        cacheHandle = open(cacheFileName, 'w', encoding="utf-8")
        cacheHandle.write(htmlText)
        cacheHandle.close()
    #         print('Done')
    return htmlText


def parserLibrary(lastfmUser, days) -> 'artistList':
    pageNum = 0
    stopParsing = False
    today = datetime.utcnow()
    fromUnix = str(
        int((today - days).replace(tzinfo=timezone.utc, hour=0, minute=0, second=0, microsecond=0).timestamp()))
    artistList = dict()
    apiKey = '89526a9d914d0c88108c6fd31c55ab3c'
    while not stopParsing:
        if pageNum >= 100:
            print('Too many pages')
            break
        pageNum += 1
        lastfmApiUrl = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&limit=200'         f'&user={lastfmUser}&page={str(pageNum)}&from={fromUnix}&api_key={apiKey}'
        pageId = f'{lastfmUser}_page_{pageNum}'
        htmlText = pageCacher(pageType='libraryPage', pageId=pageId, url=lastfmApiUrl)
        root = ET.fromstring(htmlText)
        if root.attrib['status'] != 'ok':
            htmlText = 'Can not parse'
            stopParsing = True
        try:
            for i in range(0, 199):
                artist = html.unescape(root[0][i][0].text)
                date = root[0][i][10].text.split(',')[0]
                artistDate = artist + '__' + date
                artistList[artistDate] = artistList.get(artistDate,
                                                        0) + 1  # сделать форматирование по регистру АБВ->Абв
        except IndexError:
            stopParsing = True
    #             print('Parsed. No more tracks\n')
    #         print('Parsed')
    return artistList


def parserLastfmEvent(htmlList, eventArtist, old):
    htmlIterator = iter(htmlList)
    line = next(htmlIterator)
    oldEventsCount = 0
    artistEventData = list()
    try:
        while 'class="header-new-title" itemprop="name">' not in line: line = next(htmlIterator)
        eventArtistPaged = line.split('itemprop="name">')[1].split('<')[0]
        for i in range(0, 100):
            while 'class="events-list-item-date"' not in line: line = next(htmlIterator)
            eventTime = line.split('"')[5][:10]
            while 'class="events-list-item-venue--title"' not in line: line = next(htmlIterator)
            line = next(htmlIterator)
            eventVenue = html.unescape(line.strip())
            while 'class="events-list-item-venue--address"' not in line: line = next(htmlIterator)
            line = next(htmlIterator)
            eventAddress = line.strip()
            eventCity = html.unescape(eventAddress.rsplit(',', maxsplit=1)[0])
            eventCountry = html.unescape(eventAddress.rsplit(', ', maxsplit=1)[1])
            eventId = eventArtist + '_in_' + eventTime + '_in_' + eventVenue
            eventNumber = ''
            if not old.isin([eventId]).values.any():
                artistEventList = list([eventId, eventArtistPaged, eventTime, eventVenue, eventCity, eventCountry])
                artistEventData.append(artistEventList)
            else:
                oldEventsCount += 1
    except StopIteration:
        if oldEventsCount != 0: print(f'{oldEventsCount} sent events found. ', end='')
    #         if artistEventData == [] :
    #             print('No concerts from',eventArtist)
    #         else :
    #             print('Done with',eventArtist)
    return artistEventData


def getLastfmEvents(lastfmUser, timeDelay, minListens, places, sentEvents):

    eventsData = list()
    eventNumbers = dict()
    provedArtistSet = set()

    artistList = parserLibrary(lastfmUser, timeDelay)

    for artistDate, listens in artistList.items():
        if listens >= minListens:
            artist = artistDate.split('__')[0]
            if artist not in provedArtistSet:
                provedArtistSet.add(artist.lower())
    countArtist = 0
    provedArtistList = sorted(list(provedArtistSet))
    for eventArtist in provedArtistList:
        lastfmEventUrl = 'https://www.last.fm/music/' + urllib.parse.quote(eventArtist, safe='') + '/+events'
        htmlText = pageCacher(pageType='eventPage', pageId=eventArtist, url=lastfmEventUrl)
        htmlList = htmlText.splitlines()
        artistEventData = parserLastfmEvent(htmlList, eventArtist, sentEvents)
        if artistEventData != []:
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


def getInfoText(userId):
    listOf = ['lastfmUser', 'timeDelay', 'minListens', 'places', 'sentEvents']
    lastfmUser, timeDelay, twice, places, sentEvents = readSett(listOf, userId)
    eventsDf = getLastfmEvents(lastfmUser, timedelta(days=int(timeDelay)), twice, places, sentEvents)
    if eventsDf['eventid'].count() == 0:
        infoText = 'No new concerts'
    else:
        artistsDf = eventsDf[['eventnumber', 'eventartist']].drop_duplicates(subset='eventnumber')
        infoList = list()
        for i in artistsDf.index:
            eventNumber = artistsDf.at[i, 'eventnumber']
            safeArtistName = alChar(artistsDf.at[i, 'eventartist'])
            infoList.append(f'{eventNumber} {safeArtistName}')
        advice = 'Musics free you\. \n'
        infoText = advice + '\n*New Events* \n\n' + ' \n'.join(infoList)
    return infoText


def writeData(mode, id, data):
    if mode in ['lastEvents', 'sentEvents']:
        if mode == 'lastEvents':
            dataFilename = 'data/' + id + '_ggb_lastEvents.csv'
        elif mode == 'sentEvents':
            dataFilename = 'data/' + id + '_ggb_sentEvents.csv'
        fileHandle = open(dataFilename, 'w', encoding="utf-8")
        data.to_csv(path_or_buf=fileHandle, sep='\t', line_terminator='\n')
    elif mode == 'settings':
        dataFilename = 'data/' + id + '_ggb_settings.csv'
        fileHandle = open(dataFilename, 'w', encoding="utf-8")
        fileHandle.write(data)
    else:
        print(f'{mode} is wrong mode for writing')
    fileHandle.close()
    print(f'{mode} is written to: ', dataFilename)


def readData(mode, id):
    if mode in ['lastEvents', 'sentEvents']:
        try:
            if mode == 'lastEvents':
                dataFilename = 'data/' + id + '_ggb_lastEvents.csv'
            elif mode == 'sentEvents':
                dataFilename = 'data/' + id + '_ggb_sentEvents.csv'
            fileHandle = open(dataFilename, 'r', encoding="utf-8")
            data = pd.read_csv(filepath_or_buffer=fileHandle, sep='\t', lineterminator='\n', index_col=0)
            fileHandle.close()
            print(f'{mode} data was read from: {dataFilename}')
        except FileNotFoundError:
            data = pd.Series([], dtype='boolean')
            print(f'{mode} data not found. Empty DF created')
    elif mode == 'settings':
        dataFilename = 'data/' + id + '_ggb_settings.csv'
        fileHandle = open(dataFilename, 'r', encoding="utf-8")
        data = eval(fileHandle.read())
        fileHandle.close()
        print(f'{mode} data was read from: {dataFilename}')
    else:
        print(f'{mode} is wrong mode for writing')
    return data


def readSett(listOf, id):
    data = []
    settList = {'lastfmUser', 'timeDelay', 'minListens', 'places'}
    if len(set(listOf).intersection(settList)):
        settings = readData('settings', id)
    for sett in listOf:
        if sett in settList:
            data.append(settings[sett])
        elif sett in ('sentEvents', 'lastEvents'):
            data.append(readData(sett, id))
    return tuple(data)

userId = '144297913'
infoText = getInfoText(userId)
print(infoText)