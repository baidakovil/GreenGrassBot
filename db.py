import os
import logging
from pathlib import Path
from typing import List, Union, Tuple
from datetime import datetime, date
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import asdict
import sqlite3
from sqlite3 import IntegrityError, OperationalError

@dataclass
class User:
    """
    Class for keeping user info
    """
    user_id: int
    username: str
    first_name: str
    last_name: str
    language_code: str
    accs: List[str]
    reg_datetime: str

@dataclass
class UserSettings:
    """
    Class for keeping user settings
    """
    user_id: int
    min_listens: int = 1
    notice_day: int = -1
    notice_time: str = '12:00:00'

@dataclass
class ArtScrobble:
    """
    Class for keeping user scrobble for 1 artist
    """
    user_id: int
    art_id: int
    scrobble_date: str
    count: int

@dataclass
class Event:
    """
    Class for keeping one event and lineup
    """
    is_festival: int
    place: str
    locality: str
    country: str
    event_date: str
    event_source: str
    link: str
    lineup: List[int]

BOT_FOLDER = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger('A.Db')
logger.setLevel(logging.DEBUG)

def timestamp_to_text(timestamp):
    f = '%Y-%m-%d %H:%M:%S'
    return timestamp.strftime(f)

def date_to_text(date):
    f = '%Y-%m-%d'
    return date.strftime(f)

class Db:
    """Db works here"""
    def __init__(self, dbpath, dbname, script_pathname):
        self.dbpath = dbpath
        self.dbname = dbname
        self.script_pathname = script_pathname
        self._conn = self.connection()
        logging.info(f'Database connection initiated to: {self.dbname}')

    def create_db(self):
        Path(os.path.join(BOT_FOLDER, self.dbpath)).mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(os.path.join(BOT_FOLDER, self.dbpath, self.dbname))
        connection.execute("PRAGMA foreign_keys = 1")
        logging.info(f'Database created in file: {os.path.join(BOT_FOLDER, self.dbpath, self.dbname)}')
        cursor = connection.cursor()
        with open(os.path.join(BOT_FOLDER, self.script_pathname), 'r') as f:
            script = f.read()
        cursor.executescript(script)
        connection.commit()
        connection.close()
        logging.info(f'Database tables created from script: {os.path.join(BOT_FOLDER, self.script_pathname)}')

    def connection(self):
        db_path = os.path.join(BOT_FOLDER, f'{self.dbname}.db')
        if not os.path.isfile(os.path.join(BOT_FOLDER, self.dbpath, self.dbname)):
            self.create_db()
        connection = sqlite3.connect(os.path.join(BOT_FOLDER, self.dbpath, self.dbname))
        connection.execute("PRAGMA foreign_keys = 1")
        return connection

    
    def _execute_query(self, query, params=None, select=False):
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        if select:
            records = cursor.fetchone()
            cursor.close()
            return records
        else:
            self._conn.commit()
        cursor.close()

    # WRITES/WRITE-READS

    def error_handler(f):
        async def wrapper(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except IntegrityError as E:
                if 'UNIQUE constraint failed' in E.args[0]:
                    logging.warning(f'EXCEPTION CASE№2.1: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.1 try to insert non-unique
            except OperationalError as E:
                if 'database is locked' in E.args[0]:
                    logging.warning(f'EXCEPTION CASE№2.2: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.2 another program use database
                elif 'row value misused' in E.args[0]:
                    logging.warning(f'EXCEPTION CASE№2.3: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.3 stumbled when parentnesses were but they dont needed
                else:
                    logging.warning(f'EXCEPTION CASE№2.10: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.10
            except Exception as E:
                logging.warning(f'EXCEPTION CASE№2.99: {E}')
                # CASE№2.99 unknown exception for me
        return wrapper

    @error_handler
    async def wsql_users(self, user: User) -> None:
        """
        Write all fields to table 'users'
        """
        query = """
        INSERT INTO users (user_id, username, first_name, last_name, language_code)
        VALUES (?, ?, ?, ?, ?);
        """
        self._execute_query(
                        query=query,
                        params=(user.user_id, user.username, user.first_name, user.last_name, user.language_code),
                        )
        logging.info(f"User with username: {user.username} and user_id: {user.user_id} added")

    @error_handler
    async def wsql_useraccs(self, user: User) -> None:
        """
        Write all fields to table 'useraccs'
        """
        for acc in user.accs:
            query = """
            INSERT OR IGNORE INTO useraccs (user_id, lfm)
            VALUES (?,?);
            """
            self._execute_query(
                            query=query,
                            params=(user.user_id, acc),
                            )

        logging.info(f"User with username: {user.username} and user_id: {user.user_id} add lfm account")

    @error_handler
    async def wsql_settings(self, us: UserSettings) -> None:
        """
        write all fields to _usersettings row where UserSettings.user_id = user_id
        """
        query = """
        INSERT INTO usersettings (user_id, min_listens, notice_day, notice_time)
        VALUES (?, ?, ?, ?);
        """
        self._execute_query(
                        query=query,
                        params=(us.user_id, us.min_listens, us.notice_day, us.notice_time),
                        )
        logging.info(f"User with user_id: {us.user_id} updated settings")

    @error_handler
    async def wsql_scrobbles(self, ars: ArtScrobble) -> None:
        """
        write all fields to _scrobbles row
        """
        query = """
        INSERT INTO scrobbles (user_id, art_id, scrobble_date, count)
        VALUES (?, ?, ?, ?);
        """
        self._execute_query(
                        query=query,
                        params=(ars.user_id, ars.art_id, ars.scrobble_date, ars.count),
                        )
        logging.info(f"Added scrobble for user_id: {ars.user_id} ")

    @error_handler
    async def wsql_events_lups(self, ev: Event) -> None:
        """
        write one row to _events. 
        If OK, 
        write n rows to _lineups (n=count(art_id)) 
        """
        query_ev = """
        INSERT INTO events (event_date, place, locality, country, is_festival, event_source, link)
        SELECT :event_date, :place, :locality, :country, :is_festival, :event_source, :link
        WHERE NOT EXISTS(
            SELECT 1 from events WHERE event_date=:event_date AND place=:place AND locality=:locality
            );
        """
        query_lup = """
            INSERT INTO lineups (event_id, art_id)
            VALUES ((SELECT event_id FROM events WHERE event_date=? AND place=? AND locality=?), ?)
            """
        self._execute_query(
                        query=query_ev,
                        params=asdict(ev),
                        )
        for art_id in ev.lineup:
            self._execute_query(
                            query=query_lup,
                            params=(ev.event_date, ev.place, ev.locality, art_id),
                            )
        logging.info(f"Added event with event_date:{ev.event_date}, event_place:{ev.place}")

    @error_handler
    async def wsql_artcheck(self, art_ids: List[str]) -> None:
        """
        write row to _artchecks with wsql_artcheck
        """
        query = """
            INSERT OR IGNORE INTO artchecks(art_id, check_datetime)
            VALUES (?, ?);
            """
        check_datetime = timestamp_to_text(datetime.now())
        for art_id in art_ids:
            self._execute_query(
                            query=query,
                            params=(art_id, check_datetime),
                            )
        logging.info(f"Added or ignored art_checks")

    @error_handler
    async def wsql_sentarts(self, user_id, event_id, art_id) -> None:
        """
        write all fields to _sentarts
        """
        sent_datetime = timestamp_to_text(datetime.now())
        query = """
        INSERT INTO sentarts (user_id, event_id, art_id, sent_datetime)
        VALUES (?,?,?,?);
        """
        self._execute_query(
                query=query,
                params=(user_id, event_id, art_id, sent_datetime)
                )
        logging.info(f"Added sentarts for user_id: {user_id}")

    @error_handler
    async def wsql_lastarts(self, user_id, art_id, shorthand, shorthand_date) -> None:
        """
        write all fields to _lastarts
        """
        shorthand_date = date_to_text(datetime.now())
        query = """
        INSERT INTO lastarts (user_id, art_id, shorthand, shorthand_date)
        VALUES (?,?,?,?);
        """
        self._execute_query(
                query=query,
                params=(user_id, art_id, shorthand, shorthand_date)
                )
        logging.info(f"Added lastarts for user_id: {user_id}")

    @error_handler
    async def wrsql_getartid(self, art_name: str) -> List[int]:
        """
        write row to artnames if there is no art_name with it, then
        read all art_id for correspond art_name
        """
        query = """
        INSERT INTO artnames (art_name, default_name)
        SELECT ?, 1
        WHERE NOT EXISTS(
            SELECT 1 from artnames WHERE art_name=?
        );
        """
        self._execute_query(
            query=query,
            params=(art_name, art_name)
            )
        logging.info(f"Added art_name: {art_name}")

    # READS

    async def rsql_userid(self, user_id: int) -> int:
        """
        check if exist user_id in _users
        """
        query = f"""
        SELECT COUNT(*) from users 
        WHERE user_id = (?)
        """
        record = self._execute_query(query, params=(user_id,), select=True)
        return record[0]

    async def rsql_userid(user_id) -> bool:
        """
        check if exist user_id in _users
        """
        ...

    async def rsql_lfm_quantity(user_id) -> int:
        """
        read count(lfm) for user_id
        """
        ...

    async def rsql_artcheck(art_id) -> datetime:
        """
        read DateTime for art_id in _artchecks
        """
        ...

    async def rsql_getartnames(art_id) -> List[str]:
        """
        read all art_name for correspond art_id in _artnames
        Return: list of art_name's
        """

    async def rsql_geteventids(art_id, min_date) -> List[str]:
        """
        read all event_id for correspond art_id in _lineups, if event_date for this event_id > min_date
        Return: list of event_id's
        """
        ...

    async def rsql_getevents(event_id) -> Event:
        """
        read event info for event_id
        Return: class Event instance
        """
        ...

    async def rsql_lastevents(user_id, shorthand) -> Tuple[str, date]:
        """
        read event_id to know what event user is interested
        Return: tuple(art_id, shorthand_date)
        """
        ...

    async def rsql_checkevents(event_date, art_id) -> bool:
        """
        check if there event for this date (_events) for this art_id (_lineups)
        """
        ...

    def rsql_finalquestion(user_id, date, art_name) -> bool:
        """
        Answers should this art_name be sent to user at this day (date=today always?)
        """
        ...



"""
PIPE FOR DB USE EACH TIME WHEN EVENTS FETCHED:

Textual:
|-> 
Wait until scheduled time to sent news to user ->
Get Scrobbles with API -> 
Write scrobbles -> 
Check events for artists in scrobbles -> 
Write events ->
Write artchecks ->
Sent events -> 
Write sentevents ->
Write lastevents ->
Update scheduled job ->
->|

1. Write scrobbles:
Get art_id's with wrsql_getartid(art_name) ->
Add scrobbles with wsql_scrobbles(ArtScrobble) ->

2. Check events for artists in scrobbles:
Check should this art_id be checked with rsql_artcheck(art_id) ->
For those art_ids who not fresh, get art_names_to_load with def rsql_getartnames(art_id) -> 
Check events with LastFM for these art_names ->  

3. Write events:
Add artists if they was not already added, with wsql_artname(art_name) -> 
Write new events and lineups with wsql_events_lups(Event) ->

4. Write artchecks:
Add row to _artchecks with wsql_artcheck

5. Sent artists:
Use rsql_finalquestion(user_id, date, art_name) for every art_name from (1)

6. Write sentarts:
Write as many rows as many arts was sent, wsql_sentarts()

7. Write lastarts:
Write as many rows as many arts was sent, wsql_lastarts()
"""
