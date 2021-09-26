#!/usr/bin/env python
# coding: utf-8

# In[52]:


from urllib.request import urlopen
from datetime import datetime, timedelta

def printToTelegram(textToTelegram) :
    print(textToTelegram)

lastfmUser='Anastasia20009'
daysDelta = 3
hoursDelta = 0
minListens = 3

artistList = dict()
timeDelay = timedelta(days=daysDelta,hours=hoursDelta)
today = datetime.utcnow()
overtime = False
noMoreTracks = False

def pageCacher(pageType,pageId,url) :
    htmlList = []
    if pageType == 'eventPage' :
        cacheFileName = pageId + '_lastfm.html'                   #'/cache/concerts/'
        try :         
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()
            htmlList = htmlText.splitlines()
            print( pageId + 'event page found in cache..',end='')
            cacheHandle.close()
        except FileNotFoundError:
            print('Downloading {} event page...'.format(pageId), end = '')            
    elif pageType == 'libraryPage' :
        cacheFileName = '{}_page_{}.html'.format(pageId, pageNum) #/cache/library/
        try :
            cacheHandle = open(cacheFileName, 'r', encoding="utf-8")
            htmlText = cacheHandle.read()  
            htmlList = htmlText.splitlines()
            print( 'Library page {} found in cache..'.format(pageNum),end='')  
            cacheHandle.close()
        except FileNotFoundError:
            print('Downloading {} library page...'.format(pageNum), end = '')
    if htmlList == [] :
        htmlByte = urlopen(url).read()
        htmlText = htmlByte.decode()   
        htmlList = htmlText.splitlines()
        cacheHandle = open(cacheFileName,'w', encoding="utf-8")
        cacheHandle.write(htmlText)
        cacheHandle.close()
        print('Done')
    return htmlList

def parserLibrary(htmlList) :
    htmlIterator = iter(htmlList)
    line = next(htmlIterator)
    try :
        for i in range(0,50) :
            while 'class="chartlist-artist' not in line : line = next(htmlIterator)
            while 'title=' not in line : line = next(htmlIterator)
            artist = line.split('"')[1]
            while 'chartlist-timestamp--lang-en' not in line : line = next(htmlIterator)
            while 'span title' not in line : line = next(htmlIterator)        
            timeStr = line.split('"')[1]
            timeStrFormatted = datetime.strptime(timeStr,"%A %d %b %Y, %I:%M%p")
            if (today - timeStrFormatted) > timeDelay : 
                overtime = True
                print('Parsed. timeDelay reached on page ',pageNum)
                return overtime
            else :
                artistList[artist] = artistList.get(artist,0) + 1 #сделать форматирование по регистру АБВ->Абв
    except StopIteration :
        noMoreTracks = True
        print('No more tracks')
        return noMoreTracks
    print('Parsed')


# In[53]:


pageNum = 0
stopParsing = False

artistList = {}
while not stopParsing:
    if pageNum >= 100 : 
        print('Too many pages')
        break
    pageNum += 1
    lastfmUserUrl = 'https://www.last.fm/user/'+lastfmUser+'/library?page='+str(pageNum)   
    htmlList = pageCacher(pageType='libraryPage',pageId=lastfmUser,url=lastfmUserUrl)
    stopParsing = parserLibrary(htmlList)

provedArtistList = list()
for actArtist, listens in artistList.items() :
    if listens >= minListens :
        provedArtistList.append(actArtist)
print ('provedArtistList:', provedArtistList)
print ('Artist proved:',len(provedArtistList))


# In[55]:


import urllib.parse
artistEventBasket = dict()
eventBasket = dict()

def parserLastfmEvent(htmlList) :
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
            return
        else :
            print('Done with ',eventArtist)
            return
        
for eventArtist in provedArtistList :
    lastfmEventUrl = 'https://www.last.fm/music/' + urllib.parse.quote(eventArtist,safe='') + '/+events'
    htmlList = pageCacher(pageType='eventPage',pageId=eventArtist,url=lastfmEventUrl)
    parserLastfmEvent(htmlList)
    if artistEventBasket != {} :
        eventBasket[eventArtist] = artistEventBasket
        artistEventBasket = {}
    
def prettyThree(threeIndentDict, indent=0):
    prettyList = list()
    prettyString = str()
    for key1, value1 in threeIndentDict.items():
        prettyList.append(str(key1)+'\n')
        for key2, value2 in value1.items():
            prettyList.append(' ' * indent + str(key2) + '\n')
            for k, v in value2.items() :
                prettyList.append(' ' * 2 * indent + k + ' : ' + v + '\n')
    prettyString = prettyString.join(prettyList)
    printToTelegram(prettyString)
                
prettyThree(eventBasket,4)
print('Event basket was sent to Telegram')


# In[135]:


def prettyThree(threeIndentDict, indent=0):
    prettyList = list()
    prettyString = str()
    for key1, value1 in threeIndentDict.items():
        prettyList.append(str(key1)+'\n')
        for key2, value2 in value1.items():
            prettyList.append(' ' * indent + str(key2) + '\n')
            for k, v in value2.items() :
                prettyList.append(' ' * 2 * indent + k + ' : ' + v + '\n')
    prettyString = prettyString.join(prettyList)
    printToTelegram(prettyString)
                
prettyThree(eventBasket, 4)


# In[20]:


htmlList

