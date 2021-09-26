# -*- coding: windows-1251 -*-
import logging
from urllib.request import urlopen
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hey this is my bot! Lastfm run 6')

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Currently I am in Alpha stage, help me also!')

def piracy(update, context):
    update.message.reply_text('Ahhan, FBI wants to know your location!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    


def lastfm(update, context) :

    from urllib.request import urlopen
    from datetime import datetime, timedelta

    lastfmUser='Anastasia20009'
    daysDelta = 4
    hoursDelta = 0
    minListens = 3

    artistList = dict()
    timeDelay = timedelta(days=daysDelta,hours=hoursDelta)
    today = datetime.utcnow()
    overtime = False
    noMoreTracks = False

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
                    print('Overtime')
                    return overtime
                else :
                    artistList[artist] = artistList.get(artist,0) + 1 #сделать форматирование по регистру АБВ->Абв
        except StopIteration :
            noMoreTracks = True
            print('No more tracks')
            return noMoreTracks
            
    pageNum = 0
    stopParsing = False

    while not stopParsing:
        if pageNum >= 100 : 
            print('Too many pages')
            break
        pageNum += 1
        artistUrl = 'https://www.last.fm/user/'+lastfmUser+'/library?page='+str(pageNum)
        htmlByte = urlopen(artistUrl).read()
        htmlText = htmlByte.decode()   
        htmlList = htmlText.splitlines()
        stopParsing = parserLibrary(htmlList)

    provedArtistList = list()
    for actArtist, listens in artistList.items() :
        if listens >= minListens :
            provedArtistList.append(actArtist)
    #print ('provedArtistList:', provedArtistList)
    print ('Artist proved:',len(provedArtistList))

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
        print('Download ' + eventArtist + ' event page...', end = '')
        htmlByte = urlopen(lastfmEventUrl).read()
        htmlText = htmlByte.decode()   
        htmlList = htmlText.splitlines()
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
        update.message.reply_text(prettyString)
                
    prettyThree(eventBasket, 4)
        
def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1956526158:AAHeeFZFzkmQeMIVcS1kCXzCm0zfKmeK53Q", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("piracy", piracy))
    dp.add_handler(CommandHandler("lastfm", lastfm))
    
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
