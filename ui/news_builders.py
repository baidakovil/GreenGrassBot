import logging
from datetime import datetime
import urllib.parse

from services.parse_services import parserLastfmEvent
from services.parse_services import parserLibrary
from services.message_service import alChar
from config import Cfg

from services.custom_classes import ArtScrobble

logger = logging.getLogger('A.new')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

def text_to_userdate(text):
    f_text = '%Y-%m-%d'
    f_user = '%d %b %Y'
    return datetime.strptime(text, f_text).strftime(f_user)


async def getInfoText(user_id: int, db) -> str:
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
    shorthandCount = int(await db.rsql_maxshorthand(user_id))
    print(f'get shorthandCount: {shorthandCount}')
    fillNumbers = 2 if CFG.INTEGER_MAX_SHORTHAND < 100 else 3
    lastfmUsers = await db.rsql_lfmuser(user_id)
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
                infoText += f'We get error *{artistDict}* when load tracks from Last.fm for {lastfmUser}. We\'ll check that soon'
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
                        await db.wsql_scrobbles(ars=ars)
        # logger.debug(f'Scrobbles for lfm {lastfmUser}: {artistDict}')

        #  Get and save events
        for art_name in artistDict.keys():
            if await db.rsql_artcheck(user_id,
                                            art_name,
                                            ):
                # logger.debug(f'Will check: {art_name}')
                eventList = parserLastfmEvent(art_name)
                if isinstance(eventList, str):
                    logger.warning(
                        f'OOOP! Error {eventList} when load events for {art_name}')
                    continue
                await db.wsql_events_lups(eventList)
                await db.wsql_artcheck(art_name)
            # else:
                # logger.debug(f"Won't check: {art_name}")
            if await db.rsql_finalquestion(user_id, art_name):
                userArts.append(art_name)
        logger.debug(f'Final arts for user {lastfmUser}: {userArts}')

        #  Create text for user
        if userArts:
            infoList = list()
            userArts = sorted(userArts)
            for art_name in userArts:
                shorthandCount = (
                    shorthandCount+1) if shorthandCount < CFG.INTEGER_MAX_SHORTHAND else 1
                shorthand = f'/{str(shorthandCount).zfill(fillNumbers)}'
                infoList.append(f'{shorthand} {alChar(art_name)}')
                await db.wsql_sentarts(user_id, art_name)
                await db.wsql_lastarts(
                    user_id, shorthandCount, art_name)
            infoText += f'\n*New Events*\nfor _{lastfmUser}_\n\n' + \
                ' \n'.join(infoList) + '\n'
        else:
            usersettings = await db.rsql_settings(user_id)
            if not usersettings.nonewevents:
                infoText += alChar(f'\nNo new events for _{lastfmUser}_\n')

    return infoText


async def getNewsText(userId: int, shorthand: str, db) -> str:
    shorthand = int(shorthand)
    eventsList = await db.rsql_getallevents(userId, shorthand)
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
        lastfmEventUrl = f"https://www.last.fm/music/{urllib.parse.quote(eventArtist, safe='')}/+events"
        newsText.insert(
            0, f'[_{alChar(eventArtist)}_]({alChar(lastfmEventUrl)}) events\n')
        newsText = ''.join(newsText)
        return newsText
    else:
        return 'No events under this shortcut'
