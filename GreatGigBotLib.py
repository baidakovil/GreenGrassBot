#!/usr/bin/env python
# coding: utf-8

# In[61]:


from urllib.request import urlopen
from datetime import datetime, timedelta
from pathlib import Path
import urllib.parse
from html import unescape

def printToTelegram(textToTelegram) :
    print(textToTelegram)
    
def prettyThree(threeIndentDict, indent=2):
    prettyList = list()
    prettyString = str()
    for key1, value1 in threeIndentDict.items():
        prettyList.append(str(key1)+'\n')
        for key2, value2 in value1.items():
            prettyList.append(' ' * indent + str(key2) + '\n')
            for k, v in value2.items() :
                prettyList.append(' ' * 2 * indent + k + ' : ' + v + '\n')
    prettyString = prettyString.join(prettyList)
    print('\n', prettyString)

def pageCacher(pageType,pageId,url) :
    htmlList = []
    if pageType == 'eventPage' :
        safeCharacters = (' ','.',',','_','-','!')
        safeArtistName = "".join([c for c in pageId if c.isalnum() or c in safeCharacters])
        cacheFileName = 'cache/concerts/' + safeArtistName + '_lastfm.html'                   
        try :         
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            htmlList = htmlText.splitlines()
            print( pageId + ' event page found in cache..',end='')
            cacheHandle.close()
        except FileNotFoundError:
            print('Downloading {} event page...'.format(pageId), end = '') 
    elif pageType == 'libraryPage' :
        cacheFileName = 'cache/library/{}/{}.html'.format(pageId.split('_')[0],pageId)
        try :
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()  
            htmlList = htmlText.splitlines()
            print( 'Library {} found in cache..'.format(pageId),end='')
            cacheHandle.close()
        except FileNotFoundError:
            Path('cache/library/' + pageId.split('_')[0]).mkdir(exist_ok=True)
            print('Downloading {} library page...'.format(pageId), end = '') 
    if htmlList == [] :
        htmlByte = urlopen(url).read()
        htmlText = htmlByte.decode()   
        htmlList = htmlText.splitlines()
        cacheHandle = open(cacheFileName,'w', encoding="utf-8")
        cacheHandle.write(htmlText)
        cacheHandle.close()
        print('Done')
    return htmlList

def parserLibrary(lastfmUser,timeDelay) -> 'artistList' :    
    pageNum = 0
    today = datetime.utcnow()
    artistList = dict()
    stopParsing = False 
    while not stopParsing:
        if pageNum >= 100 : 
            print('Too many pages')
            break
        pageNum += 1
        lastfmUserUrl = 'https://www.last.fm/user/'+lastfmUser+'/library?page='+str(pageNum)
        pageId = '{}_page_{}'.format(lastfmUser,pageNum)
        htmlList = pageCacher(pageType='libraryPage', pageId = pageId, url=lastfmUserUrl)    
        htmlIterator = iter(htmlList)
        line = next(htmlIterator)
        try :
            for i in range(0,50) :
                while 'class="chartlist-artist' not in line : line = next(htmlIterator)
                while 'title=' not in line : line = next(htmlIterator)
                artist = html.unescape(line.split('"')[1])
                while 'chartlist-timestamp--lang-en' not in line : line = next(htmlIterator)
                while 'span title' not in line : line = next(htmlIterator)        
                timeStr = line.split('"')[1]
                timeStrFormatted = datetime.strptime(timeStr,"%A %d %b %Y, %I:%M%p")
                if (today - timeStrFormatted) > timeDelay : 
                    stopParsing = True
                    print('Parsed. timeDelay reached')
                    break
                else :
                    artistList[artist] = artistList.get(artist,0) + 1 #сделать форматирование по регистру АБВ->Абв
        except StopIteration :
            stopParsing = True
            print('Parsed. No more tracks\n')
        print('Parsed')
    return artistList

def parserLastfmEvent(htmlList,eventArtist) :
    artistEventBasket = dict()
    htmlIterator = iter(htmlList)
    line = next(htmlIterator)  
    try :
        for i in range(0,100) :
            while 'class="events-list-item-date"' not in line : line = next(htmlIterator)
            eventTime = line.split('"')[5][:10]
            while 'class="events-list-item-venue--title"' not in line : line = next(htmlIterator)
            line = next(htmlIterator)
            eventVenue = line.strip()
            while 'class="events-list-item-venue--address"' not in line : line = next(htmlIterator)
            line = next(htmlIterator)
            eventAddress = line.strip()
            artistEventBasket[eventArtist+'-in-'+eventTime]={
                                         'eventartist':eventArtist,
                                         'eventtime':eventTime,
                                         'eventvenue':eventVenue,
                                         'eventcity':eventAddress.split(', ')[0],
                                         'eventcountry':eventAddress.split(', ')[1]}
    except StopIteration :
        if artistEventBasket == {} :
            print('No concerts from ',eventArtist)
        else :
            print('Done with ',eventArtist)
    return artistEventBasket


# In[59]:


def getLastfmEvents(lastfmUser,hoursDelta,minListens) :
    timeDelay = timedelta(hours=hoursDelta)
    eventBasket = dict()
    provedArtistList = list()
   
    artistList = parserLibrary(lastfmUser,timeDelay)
        
    for actArtist, listens in artistList.items() :
        if listens >= minListens :
            provedArtistList.append(actArtist)
    print ('\nprovedArtistList: \n', provedArtistList)
    print ('Artist proved:',len(provedArtistList),'\n')

    for eventArtist in provedArtistList :
        lastfmEventUrl = 'https://www.last.fm/music/' + urllib.parse.quote(eventArtist,safe='') + '/+events'
        htmlList = pageCacher(pageType='eventPage', pageId = eventArtist, url=lastfmEventUrl)
        artistEventBasket = parserLastfmEvent(htmlList, eventArtist)
        if artistEventBasket != {} :
            eventBasket[eventArtist] = artistEventBasket
            artistEventBasket = {}
    return eventBasket


# In[63]:


lastfmUser='ivanshello'
hoursDelta = 200
minListens = 3

events = getLastfmEvents(lastfmUser,hoursDelta,minListens)
prettyThree(events)


# In[42]:


import GreatGigBotLib

lastfmUser='Anastasia20009'
hoursDelta = 100
minListens = 3

events = GreatGigBotLib.getLastfmEvents(lastfmUser,hoursDelta,minListens)
GreatGigBotLib.prettyThree(events)


# In[28]:


eventArtist = '«W » '
lastfmEventUrl = urllib.parse.quote(eventArtist,safe="»«")
print(lastfmEventUrl)

