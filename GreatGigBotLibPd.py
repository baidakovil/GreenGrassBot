#!/usr/bin/env python
# coding: utf-8


from urllib.request import urlopen
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
import urllib.parse
import html
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np


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
            print( pageId + ' event page found in cache..',end='')
            cacheHandle.close()
        except FileNotFoundError:
            print('Downloading {} event page...'.format(pageId), end='')
    elif pageType == 'libraryPage':
        cacheFileName = 'cache/library/{}/{}.xml'.format(pageId.split('_')[0], pageId)
        try:
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            print( 'Library {} found in cache..'.format(pageId),end='')
            cacheHandle.close()
        except FileNotFoundError:
            Path('cache/library/' + pageId.split('_')[0]).mkdir(exist_ok=True)
            print('Downloading {} library page...'.format(pageId), end = '')
    if htmlText == '':
        try:
            htmlByte = urlopen(url).read()
            htmlText = htmlByte.decode()
            if pageType == 'libraryPage':
                Path('/cache/library/'+pageId).mkdir(parents=True, exist_ok=True)
            cacheHandle = open(cacheFileName, 'w', encoding="utf-8")
            cacheHandle.write(htmlText)
            cacheHandle.close()
            print('Done')
        except :
            htmlText = '404'
            print('404 when downloading')
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
        if htmlText != '404' :
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
        # infoText = advice + '\n*New Events* \n\n' + ' \n'.join(infoList)
        infoText = '\n*New Events* \n\n' + ' \n'.join(infoList)
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
        eventTime = datetime.strptime(event.eventtime.values[0], '%Y-%m-%d').strftime('%d %b %Y')
        eventCountry = event.eventcountry.values[0]
        eventCity = event.eventcity.values[0]
        eventVenue = event.eventvenue.values[0]
        if (prevCountry is None) or (prevCountry != eventCountry):
            newsText.append(f'\nIn {eventCountry}\n')
        prevCountry = event.eventcountry.values[0]
        newsText.append(f'*{eventTime}* in {eventCity}, {eventVenue}\n')
    newsText = [alChar(string) for string in newsText]
    # sentEvents = readData(mode='sentEvents',id=userId)
    # new = ' *\(new\)*' if sentEvents['eventartist'].isin([artist]).any().sum() > 0 else ''
    new = ''
    lastfmEventUrl = 'https://www.last.fm/music/' + urllib.parse.quote(artist, safe='') + '/+events'
    newsText.insert(0, f'[_{alChar(artist)}_]({alChar(lastfmEventUrl)}) events{new}\n')
    newsText = ''.join(newsText)
    return newsText


def writeData(mode, id, data):
    if mode == 'addSentEvents':
        if not data.empty:
            data.loc[:, 'eventnumber'] = ''
        prevSentEvents = readData(mode='sentEvents', id=id)
        if not prevSentEvents.empty:
            today = pd.to_datetime(date.today())
            eventTimes = pd.to_datetime(prevSentEvents.loc[:, 'eventtime'])
            oldEvents = prevSentEvents[eventTimes < today].index
            prevSentEvents.drop(labels=oldEvents, inplace=True)
            print(f'{len(oldEvents)} events was deleted. ', end='')
        # print(f'type oldevents: {type(data)}, type prevSentEvents: {type(prevSentEvents)}')
        sentEvents = prevSentEvents.append(data)  # copy=false?
        sentEvents.reset_index(drop=True, inplace=True)
        dataFilename = 'data/' + id + '_ggb_sentEvents.csv'
        fileHandle = open(dataFilename, 'w', encoding="utf-8")
        sentEvents.to_csv(path_or_buf=fileHandle, sep='\t', line_terminator='\n')
    elif mode == 'lastEvents':
        dataFilename = 'data/' + id + '_ggb_lastEvents.csv'
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
            data = pd.DataFrame([], columns=['eventnumber', 'eventid', 'eventartist',
                                             'eventtime', 'eventvenue', 'eventcity', 'eventcountry'])
            print(f'{mode} data not found. Empty DF created')
    elif mode == 'settings':
        dataFilename = 'data/' + id + '_ggb_settings.csv'
        fileHandle = open(dataFilename, 'r', encoding="utf-8")
        settings = fileHandle.read()
        data = dict() if settings == '' else eval(settings)
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


def writeSett(id, sett, value):
    settings = readData('settings', id)
    settings[sett] = value
    writeData(mode='settings', id=id, data=str(settings))


def addCountry(countryAnswer, userId):
    fileHandle = open('data/WorldCountryList.csv', 'r', encoding="utf-8")
    data = pd.read_csv(filepath_or_buffer=fileHandle, sep='\t', lineterminator='\n',index_col=0)
    try:
        mask = np.column_stack([data[col] == countryAnswer.strip().lower() for col in data])
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
    data = pd.read_csv(filepath_or_buffer=fileHandle, sep='\t', lineterminator='\n', index_col=0)
    try:
        mask = np.column_stack([data[col] == cityAnswer.strip().lower() for col in data])
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
# print(infoText)
# writeSett(userId, 'userId', 144297913)
# writeSett(userId, 'lastfmUser', 'Anastasia20009')
# writeSett(userId, 'timeDelay', 2)
# writeSett(userId, 'minListens', 2)
# writeSett(userId, 'places', {})
