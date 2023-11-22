import logging
from typing import Dict, KeysView, List

from config import Cfg
from db.db import Db
from interactions.utils import lfmdate_to_text, text_to_userdate
from services.custom_classes import ArtScrobble
from services.message_service import i34g
from services.parse_services import artist_at_url, parser_event, parser_scrobbles
from ui.error_builder import error_text

logger = logging.getLogger("A.new")
logger.setLevel(logging.DEBUG)

CFG = Cfg()

db = Db()


async def filter_artists(user_id: int, art_names: KeysView) -> List[str]:
    """
    Takes list of scrobbled artists and filters it to those who match conditions to be
    sent to user: rsql_finalquestion() = 1. But before this, load events from lastfm.
    Args:
        user_id: Tg user_id field
        artists: list of scrobbled artists
    Returns:
        list of artists to sent to user
    """
    filtered = []
    for art_name in art_names:
        #  First, check if we need to load events for the artists
        if await db.rsql_artcheck(user_id, art_name):
            #  Second, load new events
            logger.debug(f'Will check: {art_name}')
            events = await parser_event(art_name)
            #  At error, go to next artist
            if isinstance(events, int):
                logger.warning(f"OOOP! Error {events} when load events for {art_name}")
                await db.wsql_artcheck(art_name)
                continue
            #  Write timestamp to db, that artist was checked
            if events:
                await db.wsql_events_lups(events)
            await db.wsql_artcheck(art_name)
        else:
            logger.debug(f"Won't check: {art_name}")
        #  For each of artist in origin list, check if it should be sent to user
        if await db.rsql_finalquestion(user_id, art_name):
            filtered.append(art_name)
    logger.debug(f"Final art_names for user {user_id}: {filtered}")
    return sorted(filtered)


async def save_scrobbles(user_id: int, acc: str, scrobbles_dict: Dict) -> None:
    """
    Saves result of parser_scrobbles() to database.
    Args:
        dict with structure {artist_name: {date:count} }
    """
    if isinstance(scrobbles_dict, dict) and len(scrobbles_dict.keys()):
        for art_name in scrobbles_dict.keys():
            for date, qty in scrobbles_dict[art_name].items():
                date = lfmdate_to_text(date)
                ars = ArtScrobble(
                    user_id=user_id,
                    art_name=art_name,
                    scrobble_date=date,
                    lfm=acc,
                    scrobble_count=qty,
                )
                await db.wsql_scrobbles(ars=ars)
    return None


async def prepare_gigs_text(user_id: int, request: bool) -> str:
    """
    Prepare main bot message — news about events.
    Return:
        Markdown-formatted string with artists OR String "No new concerts" OR String
    with error info for user, for each of it lfm accountss
    """
    usersettings = await db.rsql_settings(user_id)

    shorthand_count = int(await db.rsql_maxshorthand(user_id))
    max_shorthand = CFG.INTEGER_MAX_SHORTHAND
    fill_numbers = 2 if max_shorthand < 100 else 3
    lfm_accs = await db.rsql_lfmuser(user_id)
    gigs_text = ''
    for acc in lfm_accs:
        #  Get scrobbles
        scrobbles_dict = await parser_scrobbles(user_id, acc)
        #  Save scrobbles or add error
        if isinstance(scrobbles_dict, dict) and len(scrobbles_dict.keys()):
            await save_scrobbles(user_id, acc, scrobbles_dict)
        elif isinstance(scrobbles_dict, dict):
            if usersettings.nonewevents or request:
                gigs_text += await i34g(
                    "news_builders.no_scrobbles", acc=acc, user_id=user_id
                )
                continue
        elif isinstance(scrobbles_dict, int):
            gigs_text += await error_text(scrobbles_dict, acc, user_id)
            continue
        else:
            logger.warning('OOOOF! Strange error when loading scrobbles')
            continue
        #  Get and save events
        filtered = await filter_artists(user_id, scrobbles_dict.keys())
        #  Create text for user
        if filtered:
            gig_list = list()
            for art_name in filtered:
                shorthand_count = (
                    shorthand_count + 1 if shorthand_count < max_shorthand else 1
                )
                shorthand = f"/{str(shorthand_count).zfill(fill_numbers)}"
                gig_list.append(f"{shorthand} {art_name}")
                #  Save shorthands and info about sent artist
                await db.wsql_sentarts(user_id, art_name)
                await db.wsql_lastarts(user_id, shorthand_count, art_name)
            news_header = await i34g(
                "news_builders.news_header", acc=acc, user_id=user_id
            )
            #  For each acc add new events =)
            gigs_text += news_header + " \n".join(gig_list) + "\n"
        else:
            #  Add "no_news" message if appropriated
            if usersettings.nonewevents or request:
                gigs_text += await i34g(
                    "news_builders.no_news", acc=acc, user_id=user_id
                )
    return gigs_text


async def prepare_details_text(user_id: int, shorthand: int) -> str:
    """
    Prepare secondary bot message — detailed info about artist's events.
    Args:
        user_id: Tg user_id field
        shorthand: quick link pressed by user
    # TODO 4096 symbols no more
    """
    events = await db.rsql_getallevents(user_id, shorthand)
    if events:
        prev_country = None
        news_text = list()
        for event in events:
            events_artist = event[0]
            event_date = text_to_userdate(event[1])
            event_venue = event[2]
            event_city = event[3]
            event_country = event[4]
            if (prev_country is None) or (prev_country != event_country):
                #  In Russia
                news_text.append(
                    await i34g(
                        "news_builders.in_country",
                        event_country=event_country,
                        user_id=user_id,
                    )
                )
            prev_country = event_country
            #  *David Bowie* in Moscow, Cherkizovsky Stadium
            news_text.append(
                await i34g(
                    "news_builders.date_city_venue",
                    event_date=event_date,
                    event_city=event_city,
                    event_venue=event_venue,
                    user_id=user_id,
                )
            )
        events_artist = events[0][0]
        events_url = await i34g(
            "parse_services.lastfmeventurl",
            artist=artist_at_url(events_artist),
            user_id=user_id,
        )
        #  David Bowie events
        news_text.insert(
            0,
            await i34g(
                "news_builders.details_header",
                events_artist=events_artist,
                events_url=events_url,
                user_id=user_id,
            ),
        )
        news_text = "".join(news_text)
        return news_text
    else:
        return await i34g("news_builders.no_events_shortcut", user_id=user_id)
