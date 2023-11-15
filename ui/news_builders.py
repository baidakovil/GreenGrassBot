import logging
from datetime import datetime
import urllib.parse
import i18n

from interactions.utils import text_to_userdate
from services.parse_services import parserLastfmEvent
from services.parse_services import parserLibrary
from services.message_service import alChar
from services.custom_classes import ArtScrobble
from config import Cfg

logger = logging.getLogger('A.new')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


async def prepare_gigs_text(user_id: int, db) -> str:
    """
    Prepare main bot message — news about events. Return:
    Markdown-formatted string with artists OR
    String "No new concerts" OR
    String with error info for user.
    """
    shorthand_count = int(await db.rsql_maxshorthand(user_id))
    fill_numbers = 2 if CFG.INTEGER_MAX_SHORTHAND < 100 else 3
    lfm_accs = await db.rsql_lfmuser(user_id)
    infoText = ''
    for acc in lfm_accs:
        artists = []
        #  Get and save scrobbles
        artist_dict = parserLibrary(acc)
        if isinstance(artist_dict, int):
            if artist_dict == 403:
                infoText += i18n.t('news_builders.403', acc=acc)
            elif artist_dict == 404:
                infoText += i18n.t('news_builders.404', acc=acc)
            else:
                infoText += i18n.t('news_builders.some_error',
                                   err=artist_dict, acc=acc)
            continue
        elif isinstance(artist_dict, dict):
            if len(artist_dict.keys()):
                for art_name in artist_dict.keys():
                    for date, qty in artist_dict[art_name].items():
                        date = datetime.strptime(
                            date, '%d %b %Y').strftime('%Y-%m-%d')
                        ars = ArtScrobble(
                            user_id=user_id,
                            art_name=art_name,
                            scrobble_date=date,
                            lfm=acc,
                            scrobble_count=qty,
                        )
                        await db.wsql_scrobbles(ars=ars)

        #  Get and save events
        for art_name in artist_dict.keys():
            if await db.rsql_artcheck(user_id, art_name):
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
                artists.append(art_name)
        logger.debug(f'Final arts for user {acc}: {artists}')

        #  Create text for user
        if artists:
            infoList = list()
            artists = sorted(artists)
            for art_name in artists:
                shorthand_count = (
                    shorthand_count+1) if shorthand_count < CFG.INTEGER_MAX_SHORTHAND else 1
                shorthand = f'/{str(shorthand_count).zfill(fill_numbers)}'
                infoList.append(f'{shorthand} {art_name}')
                await db.wsql_sentarts(user_id, art_name)
                await db.wsql_lastarts(user_id, shorthand_count, art_name)
                news_header = i18n.t('news_builders.news_header', acc=acc)
            infoText += news_header + ' \n'.join(infoList) + '\n'
        else:
            usersettings = await db.rsql_settings(user_id)
            if not usersettings.nonewevents:
                no_news_text = i18n.t('news_builders.no_news', acc=acc)
                infoText += no_news_text
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
        return i18n.t('news_builders.no_events_shortcut')
